#!/usr/bin/env python3
"""Validate a Control9 policy pack manifest and referenced artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

MANIFEST_SCHEMA_VERSION = "alto9.io/pack-manifest/v1alpha1"
SEMVER_PATTERN = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
PACK_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9-]*$")
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
FORBIDDEN_KEYS = {
    "tenant",
    "tenantId",
    "tenantEnablement",
    "enablement",
    "overrides",
    "override",
    "approverGroups",
    "approverGroup",
    "customerConfig",
    "customerConfiguration",
    "perTenant",
}


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


def _fail(errors: list[str], message: str) -> None:
    errors.append(message)


def _validate_manifest_structure(manifest: dict[str, Any], errors: list[str]) -> None:
    required = [
        "manifestSchemaVersion",
        "pack",
        "version",
        "releaseStatus",
        "compatibility",
        "artifacts",
        "provenance",
    ]
    for field in required:
        if field not in manifest:
            _fail(errors, f"missing required field: {field}")

    if manifest.get("manifestSchemaVersion") != MANIFEST_SCHEMA_VERSION:
        _fail(
            errors,
            f"manifestSchemaVersion must be {MANIFEST_SCHEMA_VERSION!r}",
        )

    pack = manifest.get("pack")
    if isinstance(pack, dict):
        for field in ("name", "displayName", "description"):
            if not pack.get(field):
                _fail(errors, f"pack.{field} is required")
        name = pack.get("name")
        if isinstance(name, str) and not PACK_NAME_PATTERN.match(name):
            _fail(errors, "pack.name must be lowercase kebab-case")
    else:
        _fail(errors, "pack must be an object")

    version = manifest.get("version")
    if not isinstance(version, str) or not SEMVER_PATTERN.match(version):
        _fail(errors, "version must be a valid semantic version")

    release_status = manifest.get("releaseStatus")
    if release_status not in {"draft", "released", "deprecated", "replaced"}:
        _fail(errors, "releaseStatus must be draft, released, deprecated, or replaced")

    compatibility = manifest.get("compatibility")
    if isinstance(compatibility, dict):
        engine = compatibility.get("policyEngine")
        if not isinstance(engine, dict) or not engine.get("semverRange"):
            _fail(errors, "compatibility.policyEngine.semverRange is required")
    else:
        _fail(errors, "compatibility must be an object")

    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, dict):
        for collection in ("policyDocuments", "fixtureSuites"):
            items = artifacts.get(collection)
            if not isinstance(items, list) or not items:
                _fail(errors, f"artifacts.{collection} must be a non-empty array")
        compiled = artifacts.get("compiled")
        if compiled is not None and not isinstance(compiled, list):
            _fail(errors, "artifacts.compiled must be an array when present")
    else:
        _fail(errors, "artifacts must be an object")

    provenance = manifest.get("provenance")
    if isinstance(provenance, dict):
        if not provenance.get("sourceRepository"):
            _fail(errors, "provenance.sourceRepository is required")
        if provenance.get("contentOrigin") not in {
            "repository",
            "fork",
            "vendor-import",
        }:
            _fail(errors, "provenance.contentOrigin is invalid")
    else:
        _fail(errors, "provenance must be an object")

    deprecation = manifest.get("deprecation")
    if deprecation is not None:
        if not isinstance(deprecation, dict) or not deprecation.get("reason"):
            _fail(errors, "deprecation.reason is required when deprecation is present")
        replacement = deprecation.get("replacement") if isinstance(deprecation, dict) else None
        if release_status == "replaced" and not replacement:
            _fail(errors, "deprecation.replacement is required when releaseStatus is replaced")


def _validate_artifact_refs(
    manifest: dict[str, Any], pack_root: Path, errors: list[str]
) -> None:
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, dict):
        return

    collections = [
        ("policyDocuments", artifacts.get("policyDocuments")),
        ("compiled", artifacts.get("compiled") or []),
        ("fixtureSuites", artifacts.get("fixtureSuites")),
    ]

    for collection_name, items in collections:
        if not isinstance(items, list):
            continue
        for index, item in enumerate(items):
            prefix = f"artifacts.{collection_name}[{index}]"
            if not isinstance(item, dict):
                _fail(errors, f"{prefix} must be an object")
                continue
            path_value = item.get("path")
            digest_value = item.get("digest")
            if not isinstance(path_value, str) or path_value.startswith("/"):
                _fail(errors, f"{prefix}.path must be a repository-relative path")
                continue
            if not isinstance(digest_value, str) or not DIGEST_PATTERN.match(digest_value):
                _fail(errors, f"{prefix}.digest must be sha256:<hex>")
                continue

            target = pack_root / path_value
            if not target.is_file():
                _fail(errors, f"missing referenced artifact: {target}")
                continue

            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            expected = digest_value.removeprefix("sha256:")
            if actual != expected:
                _fail(
                    errors,
                    f"digest mismatch for {path_value}: expected sha256:{expected}, got sha256:{actual}",
                )


def _validate_no_tenant_fields(manifest: dict[str, Any], errors: list[str]) -> None:
    for key in _collect_keys(manifest):
        leaf = key.split(".")[-1].split("[", 1)[0]
        if leaf in FORBIDDEN_KEYS:
            _fail(errors, f"tenant-specific field is not allowed in pack manifests: {key}")


def validate_manifest(manifest_path: Path) -> list[str]:
    errors: list[str] = []
    if not manifest_path.is_file():
        return [f"manifest not found: {manifest_path}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if not isinstance(manifest, dict):
        return ["manifest root must be a JSON object"]

    _validate_no_tenant_fields(manifest, errors)
    _validate_manifest_structure(manifest, errors)
    _validate_artifact_refs(manifest, manifest_path.parent, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "manifest",
        type=Path,
        help="Path to manifest.json (for example packs/production-infra-baseline/manifest.json)",
    )
    args = parser.parse_args()
    errors = validate_manifest(args.manifest.resolve())
    if errors:
        print("Pack manifest validation failed:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
