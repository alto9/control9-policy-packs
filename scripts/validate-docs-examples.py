#!/usr/bin/env python3
"""Validate required docs, example manifests, and reviewer example paths."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DOCS = [
    "docs/release-process.md",
    "docs/ci-expectations.md",
    "docs/compatibility-metadata.md",
    "docs/policy-authoring.md",
    "docs/pack-versioning.md",
    "docs/baseline-rule-catalog.md",
    "docs/classifier-fixtures.md",
    "docs/decision-records.md",
    "CONTRIBUTING.md",
]

REQUIRED_EXAMPLE_DIRS = [
    "examples/classifiers/cdk",
    "examples/classifiers/cloudformation",
    "examples/classifiers/terraform",
    "examples/classifiers/pipeline",
    "examples/classifiers/cloud-audit",
    "examples/decisions",
]

EXAMPLE_MANIFEST = REPO_ROOT / "examples/manifests/production-infra-baseline.v0.1.0.json"
WORKING_MANIFEST = REPO_ROOT / "packs/production-infra-baseline/manifest.json"

EXAMPLE_MANIFEST_REQUIRED = {
    "manifestSchemaVersion",
    "pack",
    "version",
    "releaseStatus",
    "compatibility",
    "artifacts",
    "provenance",
}


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_example_manifest_structure(path: Path, errors: list[str]) -> None:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        _fail(errors, f"invalid JSON in {path.relative_to(REPO_ROOT)}: {exc}")
        return

    if not isinstance(manifest, dict):
        _fail(errors, f"{path.relative_to(REPO_ROOT)} root must be a JSON object")
        return

    missing = sorted(EXAMPLE_MANIFEST_REQUIRED - set(manifest))
    if missing:
        _fail(errors, f"example manifest missing fields: {', '.join(missing)}")

    pack = manifest.get("pack")
    if isinstance(pack, dict) and pack.get("name") != "production-infra-baseline":
        _fail(errors, "example manifest pack.name must be production-infra-baseline")


def validate_docs_examples() -> list[str]:
    errors: list[str] = []

    for rel in REQUIRED_DOCS:
        path = REPO_ROOT / rel
        if not path.is_file():
            _fail(errors, f"missing required doc: {rel}")

    for rel in REQUIRED_EXAMPLE_DIRS:
        path = REPO_ROOT / rel
        if not path.is_dir():
            _fail(errors, f"missing reviewer example directory: {rel}")

    if not EXAMPLE_MANIFEST.is_file():
        _fail(errors, f"missing example manifest: {EXAMPLE_MANIFEST.relative_to(REPO_ROOT)}")
    else:
        _validate_example_manifest_structure(EXAMPLE_MANIFEST, errors)

    if not WORKING_MANIFEST.is_file():
        _fail(errors, f"missing working manifest: {WORKING_MANIFEST.relative_to(REPO_ROOT)}")

    readme = REPO_ROOT / "README.md"
    if readme.is_file():
        text = readme.read_text(encoding="utf-8")
        for token in (
            "docs/pack-versioning.md",
            "docs/baseline-rule-catalog.md",
            "docs/classifier-fixtures.md",
            "docs/decision-records.md",
            "CONTRIBUTING.md",
        ):
            if token not in text:
                _fail(errors, f"README.md should link to {token}")

    policy_doc = REPO_ROOT / "packs/production-infra-baseline/policies/production-infra-baseline.yaml"
    if not policy_doc.is_file():
        _fail(errors, "missing baseline policy document")

    suite = REPO_ROOT / "packs/production-infra-baseline/fixtures/suite.json"
    if suite.is_file():
        try:
            json.loads(suite.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            _fail(errors, f"invalid fixtures/suite.json: {exc}")
    else:
        _fail(errors, "missing fixtures/suite.json")

    return errors


def main() -> int:
    errors = validate_docs_examples()
    if errors:
        print("Docs and examples validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {len(REQUIRED_DOCS)} docs, {len(REQUIRED_EXAMPLE_DIRS)} example dirs, example manifest structure valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
