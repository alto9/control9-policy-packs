#!/usr/bin/env python3
"""Run compatibility metadata fixture suites under fixtures/compatibility/."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_ROOT = REPO_ROOT / "fixtures" / "compatibility"
SUITES_ROOT = FIXTURES_ROOT / "suites"

KNOWN_SUITES = ("compatibility-metadata",)
RESULT_SCHEMA_VERSION = "alto9.io/compatibility-result/v1alpha1"
SUITE_SCHEMA_VERSION = "alto9.io/compatibility-suite/v1alpha1"

_validator_spec = importlib.util.spec_from_file_location(
    "validate_pack_manifest",
    REPO_ROOT / "scripts" / "validate-pack-manifest.py",
)
if _validator_spec is None or _validator_spec.loader is None:
    raise RuntimeError("unable to load validate-pack-manifest.py")
_validator_module = importlib.util.module_from_spec(_validator_spec)
_validator_spec.loader.exec_module(_validator_module)
validate_manifest = _validator_module.validate_manifest


@dataclass
class CaseResult:
    suite_id: str
    fixture_id: str
    pack_name: str
    pack_version: str
    passed: bool
    compatible: bool | None = None
    failure_reason: str | None = None
    validation_errors: list[str] = field(default_factory=list)


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _load_json(path: Path, errors: list[str], *, label: str) -> dict | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(errors, f"{label}: invalid JSON in {path.relative_to(REPO_ROOT)}: {exc}")
        return None
    if not isinstance(document, dict):
        _fail(errors, f"{label}: root must be an object in {path.relative_to(REPO_ROOT)}")
        return None
    return document


def _resolve_manifest_path(case_dir: Path, input_doc: dict[str, Any]) -> Path | None:
    manifest_path_value = input_doc.get("manifestPath")
    if not isinstance(manifest_path_value, str) or not manifest_path_value.strip():
        return None
    manifest_path = (REPO_ROOT / manifest_path_value).resolve()
    if not manifest_path.is_file():
        return None
    return manifest_path


def _validate_case(
    suite_id: str,
    suite_dir: Path,
    case_id: str,
) -> tuple[CaseResult, list[str]]:
    errors: list[str] = []
    case_dir = suite_dir / case_id
    prefix = f"{suite_id}/{case_id}"

    input_path = case_dir / "input" / "case.json"
    expected_path = case_dir / "expected" / "compatibility-result.json"

    input_doc = _load_json(input_path, errors, label=prefix)
    expected_doc = _load_json(expected_path, errors, label=prefix)
    if input_doc is None or expected_doc is None:
        return (
            CaseResult(
                suite_id=suite_id,
                fixture_id=case_id,
                pack_name="(unknown)",
                pack_version="(unknown)",
                passed=False,
                failure_reason="missing or invalid fixture input/expected files",
            ),
            errors,
        )

    if expected_doc.get("compatibilityResultSchemaVersion") != RESULT_SCHEMA_VERSION:
        _fail(
            errors,
            f"{prefix}: compatibilityResultSchemaVersion must be {RESULT_SCHEMA_VERSION!r}",
        )

    expected_fixture_id = expected_doc.get("fixtureId")
    if expected_fixture_id != case_id:
        _fail(
            errors,
            f"{prefix}: fixtureId must be {case_id!r}, got {expected_fixture_id!r}",
        )

    engine_version = input_doc.get("policyEngineVersion")
    if not isinstance(engine_version, str) or not engine_version.strip():
        _fail(errors, f"{prefix}: policyEngineVersion must be a non-empty string")

    manifest_path = _resolve_manifest_path(case_dir, input_doc)
    if manifest_path is None:
        _fail(errors, f"{prefix}: manifestPath must resolve to an existing manifest file")
        validation_errors = ["manifestPath must resolve to an existing manifest file"]
        compatible = False
        pack_name = str(expected_doc.get("packName") or "(unknown)")
        pack_version = str(expected_doc.get("packVersion") or "(unknown)")
    else:
        validation_errors = validate_manifest(
            manifest_path,
            policy_engine_version=engine_version if isinstance(engine_version, str) else None,
        )
        compatible = len(validation_errors) == 0
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            manifest = {}
        pack = manifest.get("pack") if isinstance(manifest, dict) else {}
        pack_name = (
            pack.get("name")
            if isinstance(pack, dict) and isinstance(pack.get("name"), str)
            else str(expected_doc.get("packName") or "(unknown)")
        )
        pack_version = (
            manifest.get("version")
            if isinstance(manifest, dict) and isinstance(manifest.get("version"), str)
            else str(expected_doc.get("packVersion") or "(unknown)")
        )

    expected_compatible = expected_doc.get("compatible")
    if not isinstance(expected_compatible, bool):
        _fail(errors, f"{prefix}: expected compatible must be a boolean")

    expected_reasons = expected_doc.get("failureReasons")
    if not isinstance(expected_reasons, list):
        _fail(errors, f"{prefix}: expected failureReasons must be an array")
        expected_reasons = []

    expected_pack_version = expected_doc.get("packVersion")
    if not isinstance(expected_pack_version, str) or not expected_pack_version.strip():
        _fail(errors, f"{prefix}: expected packVersion must be a non-empty string")

    expected_pack_name = expected_doc.get("packName")
    if not isinstance(expected_pack_name, str) or not expected_pack_name.strip():
        _fail(errors, f"{prefix}: expected packName must be a non-empty string")

    passed = True
    failure_reason: str | None = None

    if isinstance(expected_compatible, bool) and compatible is not None:
        if compatible != expected_compatible:
            passed = False
            failure_reason = (
                f"compatibility mismatch: expected compatible={expected_compatible}, "
                f"actual compatible={compatible}"
            )

    if passed and isinstance(expected_pack_version, str) and pack_version != expected_pack_version:
        passed = False
        failure_reason = (
            f"packVersion mismatch: expected {expected_pack_version!r}, got {pack_version!r}"
        )

    if passed and isinstance(expected_pack_name, str) and pack_name != expected_pack_name:
        passed = False
        failure_reason = (
            f"packName mismatch: expected {expected_pack_name!r}, got {pack_name!r}"
        )

    if passed and expected_reasons:
        combined_errors = "; ".join(validation_errors)
        for reason_fragment in expected_reasons:
            if not isinstance(reason_fragment, str) or not reason_fragment.strip():
                _fail(errors, f"{prefix}: failureReasons entries must be non-empty strings")
                passed = False
                continue
            if reason_fragment not in combined_errors:
                passed = False
                failure_reason = (
                    f"expected failure reason fragment not found: {reason_fragment!r}\n"
                    f"  actual errors: {validation_errors!r}"
                )
                break

    if passed and expected_compatible is False and not expected_reasons and validation_errors:
        passed = False
        failure_reason = "reject case must declare at least one failureReasons fragment"

    result = CaseResult(
        suite_id=suite_id,
        fixture_id=case_id,
        pack_name=pack_name,
        pack_version=pack_version,
        passed=passed and not errors,
        compatible=compatible,
        failure_reason=failure_reason,
        validation_errors=validation_errors,
    )
    return result, errors


def _load_suite_manifest(suite_id: str) -> tuple[Path | None, dict | None, list[str]]:
    errors: list[str] = []
    suite_dir = SUITES_ROOT / suite_id
    manifest_path = suite_dir / "manifest.json"
    if not manifest_path.is_file():
        return None, None, [f"{suite_id}: suite manifest not found at {manifest_path.relative_to(REPO_ROOT)}"]

    document = _load_json(manifest_path, errors, label=suite_id)
    if document is None:
        return suite_dir, None, errors

    if document.get("compatibilitySuiteSchemaVersion") != SUITE_SCHEMA_VERSION:
        _fail(
            errors,
            f"{suite_id}: compatibilitySuiteSchemaVersion must be {SUITE_SCHEMA_VERSION!r}",
        )

    if document.get("id") != suite_id:
        _fail(errors, f"{suite_id}: manifest id must match directory name")

    cases = document.get("cases")
    if not isinstance(cases, list) or not cases:
        _fail(errors, f"{suite_id}: cases must be a non-empty array")

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

        for case_id in manifest.get("cases") or []:
            if not isinstance(case_id, str):
                _fail(errors, f"{suite_id}: case IDs must be strings")
                continue
            case_result, case_errors = _validate_case(suite_id, suite_dir, case_id)
            results.append(case_result)
            errors.extend(case_errors)

    return results, errors


def render_report(results: list[CaseResult], suite_ids: list[str]) -> str:
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed

    lines = [
        "# Compatibility metadata fixture run report",
        "",
        f"- Suites: {', '.join(suite_ids)}",
        f"- Fixtures: {len(results)}",
        f"- Passed: {passed}",
        f"- Failed: {failed}",
        "",
        "| Suite | Fixture ID | Pack | Version | Compatible | Status | Failure |",
        "|-------|------------|------|---------|------------|--------|---------|",
    ]

    for result in sorted(results, key=lambda item: (item.suite_id, item.fixture_id)):
        status = "pass" if result.passed else "FAIL"
        compatible = "yes" if result.compatible else "no" if result.compatible is False else "n/a"
        failure = result.failure_reason or ""
        if not failure and result.validation_errors and result.compatible is False:
            failure = result.validation_errors[0]
        if len(failure) > 120:
            failure = failure[:117] + "..."
        lines.append(
            f"| `{result.suite_id}` | `{result.fixture_id}` | `{result.pack_name}` | "
            f"`{result.pack_version}` | {compatible} | {status} | {failure} |"
        )

    lines.extend(
        [
            "",
            "Reports include pack version and compatibility result only. Raw IaC payloads, "
            "secret values, tenant overrides, and customer identifiers are not printed.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Run every known compatibility suite")
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
        print("Compatibility fixture run failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    passed = sum(1 for result in results if result.passed)
    print(
        f"OK: {passed} compatibility fixture(s) passed across "
        f"{len(suite_ids)} suite(s): {', '.join(suite_ids)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
