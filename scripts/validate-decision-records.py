#!/usr/bin/env python3
"""Validate explainable policy decision records against pack rules and classifier fixtures."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PACK_ROOT = REPO_ROOT / "packs" / "production-infra-baseline"
POLICY_PATH = PACK_ROOT / "policies" / "production-infra-baseline.yaml"
MANIFEST_PATH = PACK_ROOT / "manifest.json"
CASES_PATH = PACK_ROOT / "fixtures" / "classifier-cases.json"
EXPECTED_DIR = PACK_ROOT / "fixtures" / "expected-decisions"
SCHEMA_PATH = REPO_ROOT / "schemas" / "policy-decision-record.v1alpha1.schema.json"

DECISION_RECORD_VERSION = "alto9.io/policy-decision-record/v1alpha1"
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]
FORBIDDEN_DECISION_KEYS = {
    "tenant",
    "tenantId",
    "approverGroups",
    "approverGroup",
    "overrides",
    "override",
    "customerConfig",
}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _policy_digest() -> str:
    digest = hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _load_policy_rules() -> dict[str, dict[str, Any]]:
    document = yaml.safe_load(POLICY_PATH.read_text(encoding="utf-8"))
    rules = document.get("spec", {}).get("rules") or []
    catalog: dict[str, dict[str, Any]] = {}
    for rule in rules:
        if isinstance(rule, dict) and isinstance(rule.get("id"), str):
            catalog[rule["id"]] = rule
    return catalog


def _rule_change_types(rule: dict[str, Any]) -> list[str]:
    direct = rule.get("changeTypes")
    if isinstance(direct, list) and direct:
        return [str(item) for item in direct]
    when = rule.get("when")
    if isinstance(when, dict):
        nested = when.get("changeTypes")
        if isinstance(nested, list) and nested:
            return [str(item) for item in nested]
    return []


def _validate_policy_rules(rules: dict[str, dict[str, Any]], errors: list[str]) -> None:
    for rule_id, rule in sorted(rules.items()):
        prefix = f"policy rule {rule_id}"
        for field in ("decision", "severity", "reason", "category"):
            if not rule.get(field):
                _fail(errors, f"{prefix}: missing {field}")
        if not rule.get("riskSummary"):
            _fail(errors, f"{prefix}: missing riskSummary")
        if not _rule_change_types(rule):
            _fail(errors, f"{prefix}: missing changeTypes")
        reason = rule.get("reason")
        risk_summary = rule.get("riskSummary")
        if isinstance(reason, str):
            for pattern in SECRET_PATTERNS:
                if pattern.search(reason):
                    _fail(errors, f"{prefix}: reason contains possible secret pattern")
        if isinstance(risk_summary, str):
            for pattern in SECRET_PATTERNS:
                if pattern.search(risk_summary):
                    _fail(errors, f"{prefix}: riskSummary contains possible secret pattern")


def _evidence_references(
    case: dict[str, Any],
    rule_id: str,
    *,
    policy_digest: str,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    input_block = case.get("input") or {}
    envelope = input_block.get("envelopePath")
    artifact = input_block.get("artifactPath")
    case_id = case.get("id")
    if isinstance(envelope, str):
        refs.append({"kind": "envelope", "path": envelope})
    if isinstance(artifact, str):
        refs.append({"kind": "artifact", "path": artifact})
    refs.append({"kind": "policyDocument", "digest": policy_digest, "ruleId": rule_id})
    if isinstance(case_id, str):
        refs.append({"kind": "fixtureCase", "path": f"classifier-cases.json#{case_id}"})
    return refs


def _build_decision_record(
    case: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    *,
    policy_digest: str,
    pack_name: str,
    pack_version: str,
) -> dict[str, Any]:
    expected = case.get("expected") or {}
    matched_rules = expected.get("matchedRules") or []
    record_rules: list[dict[str, Any]] = []
    case_change_types = expected.get("changeTypes") or []

    for matched in matched_rules:
        if not isinstance(matched, dict):
            continue
        rule_id = matched.get("ruleId")
        if not isinstance(rule_id, str) or rule_id not in rules:
            continue
        policy_rule = rules[rule_id]
        classifier_label = matched.get("classifierLabel")
        labels = [classifier_label] if isinstance(classifier_label, str) and classifier_label else []
        if not labels and isinstance(expected.get("classifierLabels"), list):
            labels = [label for label in expected["classifierLabels"] if isinstance(label, str)]
        change_types = [
            label
            for label in labels
            if not str(label).startswith("parser-limitation:")
        ] or list(case_change_types)

        record_rules.append(
            {
                "ruleId": rule_id,
                "category": policy_rule["category"],
                "decision": policy_rule["decision"],
                "severity": policy_rule["severity"],
                "riskLevel": policy_rule.get("riskLevel", policy_rule["severity"]),
                "reason": policy_rule["reason"],
                "riskSummary": policy_rule["riskSummary"],
                "changeTypes": change_types or _rule_change_types(policy_rule)[:1],
                "classifierLabels": labels or change_types[:1],
                "resourceIdentity": matched.get("resourceIdentity", ""),
                "evidenceReferences": _evidence_references(case, rule_id, policy_digest=policy_digest),
            }
        )

    return {
        "decisionRecordSchemaVersion": DECISION_RECORD_VERSION,
        "packName": pack_name,
        "packVersion": pack_version,
        "fixtureId": case.get("id"),
        "toolFamily": case.get("toolFamily"),
        "matchedRules": record_rules,
        "parserLimitations": expected.get("parserLimitations") or [],
    }


def _validate_fixture_expectations(
    document: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    policy_digest: str,
) -> None:
    pack_name = document.get("packName")
    pack_version = document.get("packVersion")

    def validate_case(case: dict[str, Any], *, edge: bool = False) -> None:
        case_id = case.get("id", "<unknown>")
        prefix = f"case {case_id}"
        expected = case.get("expected")
        if not isinstance(expected, dict):
            _fail(errors, f"{prefix}: expected must be an object")
            return

        matched_rules = expected.get("matchedRules")
        if not isinstance(matched_rules, list) or not matched_rules:
            _fail(errors, f"{prefix}: expected.matchedRules must be a non-empty array")
            return

        if "evidenceReferences" not in expected:
            _fail(errors, f"{prefix}: expected.evidenceReferences is required")
        else:
            refs = expected.get("evidenceReferences")
            if not isinstance(refs, list) or not refs:
                _fail(errors, f"{prefix}: expected.evidenceReferences must be a non-empty array")

        for matched in matched_rules:
            if not isinstance(matched, dict):
                continue
            rule_id = matched.get("ruleId")
            rule_prefix = f"{prefix} rule {rule_id}"
            if not isinstance(rule_id, str) or rule_id not in rules:
                _fail(errors, f"{rule_prefix}: unknown ruleId")
                continue
            policy_rule = rules[rule_id]
            for field in ("decision", "severity", "reason", "riskSummary", "changeTypes"):
                if field not in matched:
                    _fail(errors, f"{rule_prefix}: matchedRules entry missing {field}")
            if matched.get("decision") != policy_rule.get("decision"):
                _fail(
                    errors,
                    f"{rule_prefix}: decision {matched.get('decision')!r} != policy {policy_rule.get('decision')!r}",
                )
            if matched.get("severity") != policy_rule.get("severity"):
                _fail(
                    errors,
                    f"{rule_prefix}: severity {matched.get('severity')!r} != policy {policy_rule.get('severity')!r}",
                )
            if matched.get("reason") != policy_rule.get("reason"):
                _fail(errors, f"{rule_prefix}: reason does not match policy document")
            if matched.get("riskSummary") != policy_rule.get("riskSummary"):
                _fail(errors, f"{rule_prefix}: riskSummary does not match policy document")

            for field_name in ("reason", "riskSummary"):
                value = matched.get(field_name)
                if isinstance(value, str):
                    for pattern in SECRET_PATTERNS:
                        if pattern.search(value):
                            _fail(errors, f"{rule_prefix}: {field_name} contains possible secret pattern")

        record = _build_decision_record(
            case,
            rules,
            policy_digest=policy_digest,
            pack_name=str(pack_name),
            pack_version=str(pack_version),
        )
        for key in _collect_keys(record):
            leaf = key.split(".")[-1].split("[", 1)[0]
            if leaf in FORBIDDEN_DECISION_KEYS:
                _fail(errors, f"{prefix}: forbidden tenant-specific field in decision record: {key}")

        if edge and not record.get("parserLimitations"):
            limitations = expected.get("parserLimitations")
            if not limitations:
                _fail(errors, f"{prefix}: edge case should document parserLimitations when applicable")

    for case in document.get("cases") or []:
        if isinstance(case, dict):
            validate_case(case)
    for case in document.get("edgeCases") or []:
        if isinstance(case, dict):
            validate_case(case, edge=True)


def _collect_keys(value: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()
    if isinstance(value, dict):
        for key, nested in value.items():
            full = f"{prefix}.{key}" if prefix else key
            keys.add(full)
            keys.update(_collect_keys(nested, full))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            keys.update(_collect_keys(nested, f"{prefix}[{index}]"))
    return keys


def _validate_expected_decision_files(
    document: dict[str, Any],
    rules: dict[str, dict[str, Any]],
    errors: list[str],
    *,
    policy_digest: str,
) -> None:
    if not EXPECTED_DIR.is_dir():
        _fail(errors, f"missing expected decision directory: {EXPECTED_DIR}")
        return

    pack_name = str(document.get("packName"))
    pack_version = str(document.get("packVersion"))
    all_cases = [
        *(case for case in (document.get("cases") or []) if isinstance(case, dict)),
        *(case for case in (document.get("edgeCases") or []) if isinstance(case, dict)),
    ]

    for case in all_cases:
        case_id = case.get("id")
        if not isinstance(case_id, str):
            continue
        target = EXPECTED_DIR / f"{case_id}.json"
        if not target.is_file():
            _fail(errors, f"missing expected decision record: {target.relative_to(REPO_ROOT)}")
            continue
        try:
            stored = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail(errors, f"invalid JSON in {target}: {exc}")
            continue
        expected = _build_decision_record(
            case,
            rules,
            policy_digest=policy_digest,
            pack_name=pack_name,
            pack_version=pack_version,
        )
        if stored != expected:
            _fail(
                errors,
                f"expected decision drift for {case_id}: regenerate with --write-expected",
            )


def _sync_fixture_expectations(document: dict[str, Any], rules: dict[str, dict[str, Any]], *, policy_digest: str) -> None:
    def sync_case(case: dict[str, Any]) -> None:
        expected = case.setdefault("expected", {})
        matched_rules = expected.get("matchedRules") or []
        synced_rules: list[dict[str, Any]] = []
        case_change_types = expected.get("changeTypes") or []
        envelope = (case.get("input") or {}).get("envelopePath")
        artifact = (case.get("input") or {}).get("artifactPath")
        refs: list[dict[str, Any]] = []
        if isinstance(envelope, str):
            refs.append({"kind": "envelope", "path": envelope})
        if isinstance(artifact, str):
            refs.append({"kind": "artifact", "path": artifact})
        refs.append({"kind": "policyDocument", "digest": policy_digest})
        refs.append({"kind": "manifest", "digest": _manifest_digest()})
        expected["evidenceReferences"] = refs

        for matched in matched_rules:
            if not isinstance(matched, dict):
                continue
            rule_id = matched.get("ruleId")
            if not isinstance(rule_id, str) or rule_id not in rules:
                synced_rules.append(matched)
                continue
            policy_rule = rules[rule_id]
            classifier_label = matched.get("classifierLabel")
            labels = [classifier_label] if isinstance(classifier_label, str) and classifier_label else []
            change_types = [
                label
                for label in labels
                if not str(label).startswith("parser-limitation:")
            ] or list(case_change_types)
            synced_rules.append(
                {
                    **matched,
                    "decision": policy_rule["decision"],
                    "severity": policy_rule["severity"],
                    "reason": policy_rule["reason"],
                    "riskSummary": policy_rule["riskSummary"],
                    "changeTypes": change_types or _rule_change_types(policy_rule)[:1],
                }
            )
        expected["matchedRules"] = synced_rules

    for case in document.get("cases") or []:
        if isinstance(case, dict):
            sync_case(case)
    for case in document.get("edgeCases") or []:
        if isinstance(case, dict):
            sync_case(case)


def _manifest_digest() -> str:
    digest = hashlib.sha256(MANIFEST_PATH.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def _write_expected_decision_files(document: dict[str, Any], rules: dict[str, dict[str, Any]], *, policy_digest: str) -> None:
    EXPECTED_DIR.mkdir(parents=True, exist_ok=True)
    pack_name = str(document.get("packName"))
    pack_version = str(document.get("packVersion"))
    all_cases = [
        *(case for case in (document.get("cases") or []) if isinstance(case, dict)),
        *(case for case in (document.get("edgeCases") or []) if isinstance(case, dict)),
    ]
    for case in all_cases:
        case_id = case.get("id")
        if not isinstance(case_id, str):
            continue
        record = _build_decision_record(
            case,
            rules,
            policy_digest=policy_digest,
            pack_name=pack_name,
            pack_version=pack_version,
        )
        target = EXPECTED_DIR / f"{case_id}.json"
        target.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def validate_decision_records(*, check_expected_files: bool = True) -> list[str]:
    errors: list[str] = []
    if not POLICY_PATH.is_file():
        return [f"policy document not found: {POLICY_PATH}"]
    if not CASES_PATH.is_file():
        return [f"classifier cases not found: {CASES_PATH}"]
    if not SCHEMA_PATH.is_file():
        return [f"decision record schema not found: {SCHEMA_PATH}"]

    rules = _load_policy_rules()
    if not rules:
        return ["policy document contains no rules"]

    _validate_policy_rules(rules, errors)
    policy_digest = _policy_digest()

    try:
        document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid classifier-cases.json: {exc}"]

    if not isinstance(document, dict):
        return ["classifier-cases.json root must be an object"]

    _validate_fixture_expectations(document, rules, errors, policy_digest=policy_digest)
    if check_expected_files:
        _validate_expected_decision_files(document, rules, errors, policy_digest=policy_digest)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sync-fixtures",
        action="store_true",
        help="Write reason, riskSummary, changeTypes, and evidenceReferences into classifier-cases.json",
    )
    parser.add_argument(
        "--write-expected",
        action="store_true",
        help="Regenerate golden decision records under fixtures/expected-decisions/",
    )
    parser.add_argument(
        "--skip-expected",
        action="store_true",
        help="Validate fixtures only; do not require golden expected-decision files",
    )
    args = parser.parse_args()

    rules = _load_policy_rules()
    policy_digest = _policy_digest()
    document = json.loads(CASES_PATH.read_text(encoding="utf-8"))

    if args.sync_fixtures:
        _sync_fixture_expectations(document, rules, policy_digest=policy_digest)
        CASES_PATH.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"OK: synced fixture expectations in {CASES_PATH.relative_to(REPO_ROOT)}")

    if args.write_expected:
        _write_expected_decision_files(document, rules, policy_digest=policy_digest)
        print(f"OK: wrote expected decision records to {EXPECTED_DIR.relative_to(REPO_ROOT)}")

    errors = validate_decision_records(check_expected_files=not args.skip_expected and not args.sync_fixtures)
    if errors:
        print("Decision record validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    case_count = len(document.get("cases") or []) + len(document.get("edgeCases") or [])
    print(f"OK: {len(rules)} policy rules, {case_count} fixture cases, decision records validated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
