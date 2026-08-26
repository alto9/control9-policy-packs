"""Evaluate production-infra-baseline policy rules against classifier output."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import yaml

from classifiers.common import FIXTURE_RESULT_SCHEMA_VERSION, scan_output_for_secrets

REPO_ROOT = Path(__file__).resolve().parent.parent
PACK_ROOT = REPO_ROOT / "packs" / "production-infra-baseline"
POLICY_PATH = PACK_ROOT / "policies" / "production-infra-baseline.yaml"
MANIFEST_PATH = PACK_ROOT / "manifest.json"

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DECISION_RANK = {"deny": 0, "require_approval": 1, "observe": 2, "allow": 3}


def _file_digest(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _load_policy_rules() -> list[dict[str, Any]]:
    document = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("policy document root must be an object")
    spec = document.get("spec")
    if not isinstance(spec, dict):
        raise ValueError("policy document spec must be an object")
    rules = spec.get("rules")
    if not isinstance(rules, list):
        raise ValueError("policy document rules must be an array")
    return [rule for rule in rules if isinstance(rule, dict)]


def _default_change_risk(envelope: dict[str, Any]) -> str:
    explicit = envelope.get("changeRisk")
    if isinstance(explicit, str) and explicit:
        return explicit
    environment = envelope.get("environment")
    if environment == "dev":
        return "low"
    return "medium"


def _rule_match_change_type(label: str, classifier_change_types: list[str]) -> str | None:
    if label.startswith("parser-limitation:"):
        return "resource-update"
    if label in classifier_change_types:
        return label
    return None


def _output_change_types(label: str, classifier_change_types: list[str]) -> list[str]:
    if label in classifier_change_types:
        return [label]
    if label.startswith("parser-limitation:"):
        return list(classifier_change_types)
    return list(classifier_change_types)


def _rule_matches(
    rule: dict[str, Any],
    *,
    envelope: dict[str, Any],
    change_type: str,
) -> bool:
    when = rule.get("when")
    if not isinstance(when, dict):
        return False

    environment = envelope.get("environment")
    if when.get("environment") and when.get("environment") != environment:
        return False

    tool = envelope.get("tool") or envelope.get("toolFamily")
    tools = when.get("tools")
    if isinstance(tools, list) and tool not in tools:
        return False

    expected_risk = when.get("changeRisk")
    if isinstance(expected_risk, str) and expected_risk != _default_change_risk(envelope):
        return False

    when_change_types = when.get("changeTypes")
    if isinstance(when_change_types, list) and change_type not in when_change_types:
        return False

    if "breakGlass" in when:
        break_glass = envelope.get("breakGlass") is True
        if when.get("breakGlass") != break_glass:
            return False

    return True


def _find_rule(
    rules: list[dict[str, Any]],
    *,
    envelope: dict[str, Any],
    change_type: str,
) -> dict[str, Any] | None:
    for rule in rules:
        if _rule_matches(rule, envelope=envelope, change_type=change_type):
            return rule
    return None


def _rule_sort_key(rule: dict[str, Any]) -> tuple[int, int, str, str, str]:
    return (
        SEVERITY_RANK[rule["severity"]],
        DECISION_RANK[rule["decision"]],
        rule["ruleId"],
        rule.get("classifierLabel", ""),
        rule.get("resourceIdentity", ""),
    )


def evaluate_policy(
    envelope: dict[str, Any],
    classifier_output: dict[str, Any],
    *,
    fixture_id: str,
    label_resource_pairs: list[tuple[str, str]],
) -> dict[str, Any]:
    rules = _load_policy_rules()
    classifier_change_types = classifier_output.get("changeTypes") or []
    if not isinstance(classifier_change_types, list):
        classifier_change_types = []

    matched_rules: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    for label, resource_identity in label_resource_pairs:
        change_type = _rule_match_change_type(label, classifier_change_types)
        if change_type is None:
            continue
        rule = _find_rule(rules, envelope=envelope, change_type=change_type)
        if rule is None:
            continue
        rule_id = rule.get("id")
        if not isinstance(rule_id, str):
            continue
        dedupe_key = (rule_id, label, resource_identity)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        matched_rules.append(
            {
                "ruleId": rule_id,
                "decision": rule.get("decision"),
                "severity": rule.get("severity"),
                "classifierLabel": label,
                "resourceIdentity": resource_identity,
                "reason": rule.get("reason"),
                "riskSummary": rule.get("riskSummary"),
                "changeTypes": _output_change_types(label, classifier_change_types),
            }
        )

    matched_rules.sort(key=_rule_sort_key)

    tool_family = classifier_output.get("toolFamily")
    result = {
        "fixtureResultSchemaVersion": FIXTURE_RESULT_SCHEMA_VERSION,
        "fixtureId": fixture_id,
        "toolFamily": tool_family,
        "matchedRules": matched_rules,
        "evidenceReferences": [
            {"kind": "envelope", "path": "input/envelope.json"},
            {"kind": "artifact", "path": "input/artifact.json"},
            {"kind": "policyDocument", "digest": _file_digest(POLICY_PATH)},
            {"kind": "manifest", "digest": _file_digest(MANIFEST_PATH)},
        ],
    }
    scan_output_for_secrets(result)
    return result
