#!/usr/bin/env python3
"""Run shared classifier fixture suites under fixtures/classifiers/."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_ROOT = REPO_ROOT / "fixtures" / "classifiers"
SUITES_ROOT = FIXTURES_ROOT / "suites"

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DECISION_RANK = {"deny": 0, "require_approval": 1, "observe": 2, "allow": 3}

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]

KNOWN_SUITES = ("cdk-cloudformation", "terraform-opentofu")


@dataclass
class CaseResult:
    suite_id: str
    fixture_id: str
    tool_family: str
    passed: bool
    labels: list[str] = field(default_factory=list)
    failure_reason: str | None = None


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _rule_sort_key(rule: dict[str, Any]) -> tuple[int, int, str, str, str]:
    return (
        SEVERITY_RANK[rule["severity"]],
        DECISION_RANK[rule["decision"]],
        rule["ruleId"],
        rule.get("classifierLabel", ""),
        rule.get("resourceIdentity", ""),
    )


def _is_sorted_rules(rules: list[dict[str, Any]]) -> bool:
    keys = [_rule_sort_key(rule) for rule in rules]
    return keys == sorted(keys)


def _is_sorted_labels(labels: list[str]) -> bool:
    return labels == sorted(labels)


def _load_json(path: Path, errors: list[str], *, label: str) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(errors, f"{label}: invalid JSON in {path.relative_to(REPO_ROOT)}: {exc}")
        return None
    if not isinstance(document, dict):
        _fail(errors, f"{label}: root must be an object in {path.relative_to(REPO_ROOT)}")
        return None
    return document


def _scan_secrets(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            _fail(
                errors,
                f"possible secret pattern in {path.relative_to(REPO_ROOT)}",
            )


def _compare_list_field(
    field_name: str,
    expected: list[str],
    actual: list[str],
    errors: list[str],
    *,
    prefix: str,
) -> None:
    if expected != actual:
        _fail(
            errors,
            f"{prefix}: {field_name} mismatch\n"
            f"  expected: {expected!r}\n"
            f"  actual:   {actual!r}",
        )


def _validate_classifier_output(
    document: dict[str, Any],
    errors: list[str],
    *,
    prefix: str,
    expected_fixture_id: str,
    allowed_tool_families: set[str],
) -> str | None:
    if document.get("fixtureResultSchemaVersion") != "alto9.io/classifier-fixture-result/v1alpha1":
        _fail(errors, f"{prefix}: fixtureResultSchemaVersion must be alto9.io/classifier-fixture-result/v1alpha1")

    fixture_id = document.get("fixtureId")
    if fixture_id != expected_fixture_id:
        _fail(errors, f"{prefix}: fixtureId must be {expected_fixture_id!r}, got {fixture_id!r}")

    tool_family = document.get("toolFamily")
    if not isinstance(tool_family, str) or tool_family not in allowed_tool_families:
        _fail(
            errors,
            f"{prefix}: toolFamily must be one of {sorted(allowed_tool_families)}, got {tool_family!r}",
        )

    labels = document.get("classifierLabels")
    if not isinstance(labels, list) or not labels:
        _fail(errors, f"{prefix}: classifierLabels must be a non-empty array")
    elif not _is_sorted_labels(labels):
        _fail(errors, f"{prefix}: classifierLabels are not deterministically sorted")

    change_types = document.get("changeTypes")
    if not isinstance(change_types, list) or not change_types:
        _fail(errors, f"{prefix}: changeTypes must be a non-empty array")
    elif change_types != sorted(change_types):
        _fail(errors, f"{prefix}: changeTypes are not deterministically sorted")

    resource_identities = document.get("resourceIdentities")
    if not isinstance(resource_identities, list) or not resource_identities:
        _fail(errors, f"{prefix}: resourceIdentities must be a non-empty array")
    elif resource_identities != sorted(resource_identities):
        _fail(errors, f"{prefix}: resourceIdentities are not deterministically sorted")

    limitations = document.get("parserLimitations")
    if limitations is None:
        limitations = []
    if not isinstance(limitations, list):
        _fail(errors, f"{prefix}: parserLimitations must be an array when present")

    return tool_family if isinstance(tool_family, str) else None


def _validate_policy_result(
    document: dict[str, Any],
    classifier_output: dict[str, Any],
    errors: list[str],
    *,
    prefix: str,
    expected_fixture_id: str,
    allowed_tool_families: set[str],
) -> None:
    if document.get("fixtureResultSchemaVersion") != "alto9.io/classifier-fixture-result/v1alpha1":
        _fail(errors, f"{prefix}: fixtureResultSchemaVersion must be alto9.io/classifier-fixture-result/v1alpha1")

    fixture_id = document.get("fixtureId")
    if fixture_id != expected_fixture_id:
        _fail(errors, f"{prefix}: fixtureId must be {expected_fixture_id!r}, got {fixture_id!r}")

    tool_family = document.get("toolFamily")
    if tool_family != classifier_output.get("toolFamily"):
        _fail(
            errors,
            f"{prefix}: toolFamily mismatch with classifier-output.json\n"
            f"  expected: {classifier_output.get('toolFamily')!r}\n"
            f"  actual:   {tool_family!r}",
        )
    if not isinstance(tool_family, str) or tool_family not in allowed_tool_families:
        _fail(
            errors,
            f"{prefix}: toolFamily must be one of {sorted(allowed_tool_families)}, got {tool_family!r}",
        )

    rules = document.get("matchedRules")
    if not isinstance(rules, list) or not rules:
        _fail(errors, f"{prefix}: matchedRules must be a non-empty array")
        return

    if not _is_sorted_rules(rules):
        _fail(errors, f"{prefix}: matchedRules are not deterministically sorted")

    expected_labels = classifier_output.get("classifierLabels") or []
    actual_labels = sorted({rule.get("classifierLabel") for rule in rules if isinstance(rule, dict)})
    _compare_list_field("classifierLabels", list(expected_labels), actual_labels, errors, prefix=prefix)

    expected_identities = classifier_output.get("resourceIdentities") or []
    actual_identities = sorted({rule.get("resourceIdentity") for rule in rules if isinstance(rule, dict)})
    _compare_list_field(
        "resourceIdentities",
        list(expected_identities),
        actual_identities,
        errors,
        prefix=prefix,
    )

    for rule in rules:
        if not isinstance(rule, dict):
            continue
        for field in ("ruleId", "decision", "severity", "classifierLabel", "resourceIdentity", "reason", "riskSummary", "changeTypes"):
            if field not in rule:
                _fail(errors, f"{prefix}: matched rule missing {field}")

    evidence = document.get("evidenceReferences")
    if not isinstance(evidence, list) or not evidence:
        _fail(errors, f"{prefix}: evidenceReferences must be a non-empty array")


def _validate_case(
    suite_id: str,
    suite_dir: Path,
    case_id: str,
    allowed_tool_families: set[str],
) -> tuple[CaseResult, list[str]]:
    errors: list[str] = []
    case_dir = suite_dir / case_id
    prefix = f"{suite_id}/{case_id}"

    required_paths = [
        case_dir / "notes.md",
        case_dir / "input" / "envelope.json",
        case_dir / "expected" / "classifier-output.json",
        case_dir / "expected" / "policy-result.json",
    ]
    for path in required_paths:
        if not path.is_file():
            _fail(errors, f"{prefix}: missing required file {path.relative_to(REPO_ROOT)}")

    envelope_path = case_dir / "input" / "envelope.json"
    artifact_path = case_dir / "input" / "artifact.json"
    classifier_path = case_dir / "expected" / "classifier-output.json"
    policy_path = case_dir / "expected" / "policy-result.json"

    scan_paths = [case_dir / "notes.md", envelope_path, classifier_path, policy_path]
    if artifact_path.is_file():
        scan_paths.append(artifact_path)
    for path in scan_paths:
        if path.is_file():
            _scan_secrets(path, errors)

    envelope = _load_json(envelope_path, errors, label=prefix) if envelope_path.is_file() else None
    if envelope is not None:
        envelope_family = envelope.get("toolFamily")
        if envelope_family not in allowed_tool_families:
            _fail(
                errors,
                f"{prefix}: envelope toolFamily {envelope_family!r} not allowed for suite {suite_id}",
            )

    classifier_output = (
        _load_json(classifier_path, errors, label=prefix) if classifier_path.is_file() else None
    )
    tool_family = ""
    if classifier_output is not None:
        validated_family = _validate_classifier_output(
            classifier_output,
            errors,
            prefix=f"{prefix}/expected/classifier-output.json",
            expected_fixture_id=case_id,
            allowed_tool_families=allowed_tool_families,
        )
        tool_family = validated_family or ""

    policy_result = _load_json(policy_path, errors, label=prefix) if policy_path.is_file() else None
    if policy_result is not None and classifier_output is not None:
        _validate_policy_result(
            policy_result,
            classifier_output,
            errors,
            prefix=f"{prefix}/expected/policy-result.json",
            expected_fixture_id=case_id,
            allowed_tool_families=allowed_tool_families,
        )

    labels = list(classifier_output.get("classifierLabels") or []) if classifier_output else []
    passed = not errors
    result = CaseResult(
        suite_id=suite_id,
        fixture_id=case_id,
        tool_family=tool_family,
        passed=passed,
        labels=labels,
        failure_reason=errors[0] if errors else None,
    )
    return result, errors


def _load_suite_manifest(suite_id: str) -> tuple[Path | None, dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    suite_dir = SUITES_ROOT / suite_id
    manifest_path = suite_dir / "manifest.json"
    if not manifest_path.is_file():
        return None, None, [f"suite manifest not found: {manifest_path.relative_to(REPO_ROOT)}"]

    document = _load_json(manifest_path, errors, label=suite_id)
    if document is None:
        return suite_dir, None, errors

    if document.get("classifierSuiteSchemaVersion") != "alto9.io/classifier-suite/v1alpha1":
        _fail(errors, f"{suite_id}: classifierSuiteSchemaVersion must be alto9.io/classifier-suite/v1alpha1")
    if document.get("id") != suite_id:
        _fail(errors, f"{suite_id}: manifest id must match directory name")

    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        _fail(errors, f"{suite_id}: cases must be a non-empty array")

    tool_families = document.get("toolFamilies")
    if not isinstance(tool_families, list) or not tool_families:
        _fail(errors, f"{suite_id}: toolFamilies must be a non-empty array")

    return suite_dir, document, errors


def run_suites(suite_ids: list[str]) -> tuple[list[CaseResult], list[str]]:
    results: list[CaseResult] = []
    errors: list[str] = []

    for suite_id in suite_ids:
        suite_dir, manifest, manifest_errors = _load_suite_manifest(suite_id)
        if manifest_errors:
            errors.extend(manifest_errors)
            continue
        assert suite_dir is not None and manifest is not None

        allowed_tool_families = set(manifest.get("toolFamilies") or [])
        for case_id in manifest.get("cases") or []:
            if not isinstance(case_id, str):
                _fail(errors, f"{suite_id}: case IDs must be strings")
                continue
            case_result, case_errors = _validate_case(suite_id, suite_dir, case_id, allowed_tool_families)
            results.append(case_result)
            errors.extend(case_errors)

    return results, errors


def render_report(results: list[CaseResult], suite_ids: list[str]) -> str:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed

    lines = [
        "# Classifier fixture run report",
        "",
        f"- Suites: {', '.join(suite_ids)}",
        f"- Fixtures: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Suite | Fixture ID | Tool family | Labels | Status | Failure |",
        "|-------|------------|-------------|--------|--------|---------|",
    ]

    for result in sorted(results, key=lambda item: (item.suite_id, item.fixture_id)):
        labels = ", ".join(result.labels) or "(none)"
        status = "pass" if result.passed else "FAIL"
        failure = result.failure_reason or ""
        if len(failure) > 120:
            failure = failure[:117] + "..."
        lines.append(
            f"| `{result.suite_id}` | `{result.fixture_id}` | `{result.tool_family}` | {labels} | {status} | {failure} |"
        )

    lines.extend(
        [
            "",
            "Failures show expected versus actual metadata only. Raw IaC payloads are not printed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run every known classifier suite")
    group.add_argument("--suite", action="append", dest="suites", help="Run a single suite by ID")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a reviewer-readable fixture report after validation",
    )
    args = parser.parse_args()

    suite_ids = list(KNOWN_SUITES) if args.all else list(dict.fromkeys(args.suites or []))
    unknown = [suite_id for suite_id in suite_ids if suite_id not in KNOWN_SUITES]
    if unknown:
        print(
            f"Unknown suite(s): {', '.join(unknown)}. Known suites: {', '.join(KNOWN_SUITES)}",
            file=sys.stderr,
        )
        return 2

    results, errors = run_suites(suite_ids)
    if args.report:
        print(render_report(results, suite_ids))

    if errors:
        print("Classifier fixture run failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    passed = sum(1 for result in results if result.passed)
    print(
        f"OK: {passed} fixture(s) passed across {len(suite_ids)} suite(s): {', '.join(suite_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
