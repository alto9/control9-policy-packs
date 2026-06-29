#!/usr/bin/env python3
"""Validate classifier fixture structure, coverage, ordering, and redaction rules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_ROOT = REPO_ROOT / "packs" / "production-infra-baseline" / "fixtures"
CASES_PATH = FIXTURES_ROOT / "classifier-cases.json"

REQUIRED_RULE_IDS = {
    "allow-low-risk-dev-iac",
    "require-approval-prod-mutation",
    "require-approval-prod-iam-expansion",
    "require-approval-prod-new-role",
    "require-approval-prod-cross-account-access",
    "deny-prod-destructive-change",
    "require-approval-prod-destructive-break-glass",
    "require-approval-prod-network-boundary-change",
    "require-approval-secrets-exposure-hint",
    "require-approval-unapproved-pipeline-source",
    "observe-cost-threshold-breach",
    "require-approval-deploy-verification-mismatch",
    "observe-off-path-cloud-mutation",
}

REQUIRED_EDGE_SITUATIONS = {
    "unknown-resource-type",
    "parser-error",
    "unsupported-tool",
    "partial-summary",
}

SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
DECISION_RANK = {"deny": 0, "require_approval": 1, "observe": 2, "allow": 3}

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]

INTENTIONALLY_INVALID_JSON = {
    FIXTURES_ROOT / "inputs/edge-cases/malformed-plan.json",
}


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


def _label_sort_key(label: str) -> str:
    return label


def _is_sorted_rules(rules: list[dict[str, Any]]) -> bool:
    keys = [_rule_sort_key(rule) for rule in rules]
    return keys == sorted(keys)


def _is_sorted_labels(labels: list[str]) -> bool:
    return labels == sorted(labels, key=_label_sort_key)


def _scan_secrets(path: Path, errors: list[str]) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            _fail(errors, f"possible secret pattern in {path.relative_to(REPO_ROOT)}")


def _validate_json_file(path: Path, errors: list[str]) -> None:
    if path in INTENTIONALLY_INVALID_JSON:
        try:
            json.loads(path.read_text(encoding="utf-8"))
            _fail(errors, f"expected invalid JSON for parser-error fixture: {path}")
        except json.JSONDecodeError:
            return
        return
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(errors, f"invalid JSON in {path}: {exc}")


def _validate_case(case: dict[str, Any], errors: list[str], *, edge: bool = False) -> set[str]:
    matched: set[str] = set()
    case_id = case.get("id", "<unknown>")
    prefix = f"case {case_id}"

    if edge and case.get("situation") not in REQUIRED_EDGE_SITUATIONS:
        _fail(errors, f"{prefix}: invalid edge situation")

    input_block = case.get("input")
    if not isinstance(input_block, dict):
        _fail(errors, f"{prefix}: input must be an object")
        return matched

    for key in ("envelopePath",):
        if key not in input_block:
            _fail(errors, f"{prefix}: input.{key} is required")

    for rel_key in ("envelopePath", "artifactPath"):
        rel = input_block.get(rel_key)
        if not rel:
            continue
        target = FIXTURES_ROOT / rel
        if not target.is_file():
            _fail(errors, f"{prefix}: missing {rel_key} file {target}")
        else:
            _validate_json_file(target, errors)
            _scan_secrets(target, errors)

    expected = case.get("expected")
    if not isinstance(expected, dict):
        _fail(errors, f"{prefix}: expected must be an object")
        return matched

    labels = expected.get("classifierLabels")
    if not isinstance(labels, list):
        _fail(errors, f"{prefix}: expected.classifierLabels must be an array")
    elif not _is_sorted_labels(labels):
        _fail(errors, f"{prefix}: expected.classifierLabels are not deterministically sorted")

    rules = expected.get("matchedRules")
    if not isinstance(rules, list) or not rules:
        _fail(errors, f"{prefix}: expected.matchedRules must be a non-empty array")
    else:
        if not _is_sorted_rules(rules):
            _fail(errors, f"{prefix}: expected.matchedRules are not deterministically sorted")
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            rule_id = rule.get("ruleId")
            if isinstance(rule_id, str):
                matched.add(rule_id)
            for field in ("decision", "severity", "ruleId"):
                if field not in rule:
                    _fail(errors, f"{prefix}: matched rule missing {field}")

    limitations = expected.get("parserLimitations")
    if limitations is not None and not isinstance(limitations, list):
        _fail(errors, f"{prefix}: expected.parserLimitations must be an array when present")

    return matched


def _load_cases_document() -> tuple[dict[str, Any] | None, list[str]]:
    if not CASES_PATH.is_file():
        return None, [f"classifier cases not found: {CASES_PATH}"]

    try:
        document = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, [f"invalid classifier-cases.json: {exc}"]

    if not isinstance(document, dict):
        return None, ["classifier-cases.json root must be an object"]
    return document, []


def _rule_coverage(document: dict[str, Any]) -> dict[str, list[str]]:
    coverage: dict[str, list[str]] = {rule_id: [] for rule_id in sorted(REQUIRED_RULE_IDS)}
    edge_coverage: dict[str, list[str]] = {situation: [] for situation in sorted(REQUIRED_EDGE_SITUATIONS)}

    def record(case: dict[str, Any], *, edge: bool = False) -> None:
        case_id = str(case.get("id", "<unknown>"))
        expected = case.get("expected")
        if isinstance(expected, dict):
            rules = expected.get("matchedRules")
            if isinstance(rules, list):
                for rule in rules:
                    if isinstance(rule, dict):
                        rule_id = rule.get("ruleId")
                        if isinstance(rule_id, str) and rule_id in coverage:
                            coverage[rule_id].append(case_id)
        if edge:
            situation = case.get("situation")
            if isinstance(situation, str) and situation in edge_coverage:
                edge_coverage[situation].append(case_id)

    for case in document.get("cases") or []:
        if isinstance(case, dict):
            record(case)
    for case in document.get("edgeCases") or []:
        if isinstance(case, dict):
            record(case, edge=True)

    coverage["_edge_cases"] = []
    for situation, case_ids in edge_coverage.items():
        coverage[f"edge:{situation}"] = case_ids
    return coverage


def render_fixture_report(document: dict[str, Any]) -> str:
    cases = [case for case in (document.get("cases") or []) if isinstance(case, dict)]
    edge_cases = [case for case in (document.get("edgeCases") or []) if isinstance(case, dict)]
    coverage = _rule_coverage(document)

    lines = [
        "# Classifier fixture report",
        "",
        f"- Pack: `production-infra-baseline`",
        f"- Cases: {len(cases)}",
        f"- Edge cases: {len(edge_cases)}",
        f"- Required baseline rules: {len(REQUIRED_RULE_IDS)}",
        "",
        "## Baseline rule coverage",
        "",
        "| Rule ID | Fixture case IDs |",
        "|---------|------------------|",
    ]

    for rule_id in sorted(REQUIRED_RULE_IDS):
        case_ids = ", ".join(coverage.get(rule_id, [])) or "(none)"
        lines.append(f"| `{rule_id}` | {case_ids} |")

    lines.extend(
        [
            "",
            "## Edge situations",
            "",
            "| Situation | Fixture case IDs |",
            "|-----------|------------------|",
        ]
    )
    for situation in sorted(REQUIRED_EDGE_SITUATIONS):
        case_ids = ", ".join(coverage.get(f"edge:{situation}", [])) or "(none)"
        lines.append(f"| `{situation}` | {case_ids} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report summarizes fixture expectations only.",
            "- Live classifier execution against these inputs is not yet part of CI.",
            "- Regenerate with `python3 scripts/validate-classifier-fixtures.py --report`.",
            "",
        ]
    )
    return "\n".join(lines)


def validate_classifier_fixtures() -> list[str]:
    errors: list[str] = []
    document, load_errors = _load_cases_document()
    if load_errors:
        return load_errors
    assert document is not None

    if document.get("classifierFixtureSchemaVersion") != "alto9.io/classifier-fixture/v1alpha1":
        _fail(errors, "classifierFixtureSchemaVersion must be alto9.io/classifier-fixture/v1alpha1")

    cases = document.get("cases")
    edge_cases = document.get("edgeCases")
    if not isinstance(cases, list) or not cases:
        _fail(errors, "cases must be a non-empty array")
        cases = []
    if not isinstance(edge_cases, list) or len(edge_cases) < len(REQUIRED_EDGE_SITUATIONS):
        _fail(errors, "edgeCases must document all required edge situations")

    covered_rules: set[str] = set()
    covered_edges: set[str] = set()

    for case in cases:
        if isinstance(case, dict):
            covered_rules.update(_validate_case(case, errors))

    for case in edge_cases or []:
        if isinstance(case, dict):
            covered_rules.update(_validate_case(case, errors, edge=True))
            situation = case.get("situation")
            if isinstance(situation, str):
                covered_edges.add(situation)

    missing_rules = REQUIRED_RULE_IDS - covered_rules
    if missing_rules:
        _fail(
            errors,
            "missing baseline rule coverage in classifier fixtures: "
            + ", ".join(sorted(missing_rules)),
        )

    missing_edges = REQUIRED_EDGE_SITUATIONS - covered_edges
    if missing_edges:
        _fail(
            errors,
            "missing edge-case coverage: " + ", ".join(sorted(missing_edges)),
        )

    return errors


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--report",
        action="store_true",
        help="Print a reviewer-readable fixture coverage report (runs validation first)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write the fixture report to this path instead of stdout",
    )
    args = parser.parse_args()

    errors = validate_classifier_fixtures()
    if errors:
        print("Classifier fixture validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    if args.report:
        document, load_errors = _load_cases_document()
        if load_errors:
            for error in load_errors:
                print(f"  - {error}", file=sys.stderr)
            return 1
        assert document is not None
        report = render_fixture_report(document)
        if args.output:
            args.output.write_text(report, encoding="utf-8")
            print(f"OK: fixture report written to {args.output}")
        else:
            print(report)
        return 0

    print(f"OK: {len(REQUIRED_RULE_IDS)} baseline rules covered, {len(REQUIRED_EDGE_SITUATIONS)} edge cases documented")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
