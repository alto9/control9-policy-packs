#!/usr/bin/env python3
"""Unit tests for validate-pack-manifest.py."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_MODULE_PATH = Path(__file__).with_name("validate-pack-manifest.py")
_SPEC = importlib.util.spec_from_file_location("validate_pack_manifest", _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

_sha256_digest_for_file = _MODULE._sha256_digest_for_file
refresh_manifest = _MODULE.refresh_manifest
validate_manifest = _MODULE.validate_manifest


def _digest_for_bytes(data: bytes) -> str:
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def _minimal_manifest(
    *,
    policy_digest: str,
    fixture_digest: str,
    compiled: list[dict[str, str]] | None = None,
) -> dict:
    return {
        "manifestSchemaVersion": "alto9.io/pack-manifest/v1alpha1",
        "pack": {
            "name": "test-pack",
            "displayName": "Test Pack",
            "description": "Pack used by unit tests.",
        },
        "version": "0.1.0",
        "releaseStatus": "draft",
        "compatibility": {
            "policyEngine": {
                "semverRange": ">=0.1.0 <1.0.0",
            },
        },
        "artifacts": {
            "policyDocuments": [
                {
                    "path": "policies/test.yaml",
                    "digest": policy_digest,
                    "mediaType": "application/yaml",
                    "description": "Policy document.",
                }
            ],
            "compiled": compiled if compiled is not None else [],
            "fixtureSuites": [
                {
                    "path": "fixtures/suite.json",
                    "digest": fixture_digest,
                    "mediaType": "application/json",
                    "description": "Fixture suite.",
                }
            ],
        },
        "provenance": {
            "sourceRepository": "https://github.com/alto9/control9-policy-packs",
            "sourceRef": "main",
            "contentOrigin": "repository",
            "maintainers": ["platform-engineering"],
        },
    }


class ValidatePackManifestTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.pack_root = Path(self.temp_dir.name)
        self.policy_path = self.pack_root / "policies" / "test.yaml"
        self.fixture_path = self.pack_root / "fixtures" / "suite.json"
        self.policy_path.parent.mkdir(parents=True)
        self.fixture_path.parent.mkdir(parents=True)
        self.policy_bytes = b"rules:\n  - ruleId: test-rule\n"
        self.fixture_bytes = b'{"cases": []}\n'
        self.policy_path.write_bytes(self.policy_bytes)
        self.fixture_path.write_bytes(self.fixture_bytes)
        self.manifest_path = self.pack_root / "manifest.json"
        self._write_manifest(
            _digest_for_bytes(self.policy_bytes),
            _digest_for_bytes(self.fixture_bytes),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def _write_manifest(
        self,
        policy_digest: str,
        fixture_digest: str,
        *,
        compiled: list[dict[str, str]] | None = None,
    ) -> None:
        manifest = _minimal_manifest(
            policy_digest=policy_digest,
            fixture_digest=fixture_digest,
            compiled=compiled,
        )
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def test_check_mode_passes_with_current_digests(self) -> None:
        errors = validate_manifest(self.manifest_path)
        self.assertEqual(errors, [])

    def test_check_mode_fails_on_stale_digest(self) -> None:
        self._write_manifest(
            "sha256:" + ("0" * 64),
            _digest_for_bytes(self.fixture_bytes),
        )

        errors = validate_manifest(self.manifest_path)
        self.assertTrue(any("digest mismatch" in error for error in errors))

    def test_refresh_updates_stale_digests(self) -> None:
        stale_policy = "sha256:" + ("0" * 64)
        self._write_manifest(stale_policy, _digest_for_bytes(self.fixture_bytes))

        changes, errors = refresh_manifest(self.manifest_path)
        self.assertEqual(errors, [])
        self.assertEqual(changes, 1)

        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(
            manifest["artifacts"]["policyDocuments"][0]["digest"],
            _digest_for_bytes(self.policy_bytes),
        )
        self.assertEqual(validate_manifest(self.manifest_path), [])

    def test_refresh_is_idempotent(self) -> None:
        stale_policy = "sha256:" + ("0" * 64)
        self._write_manifest(stale_policy, _digest_for_bytes(self.fixture_bytes))

        refresh_manifest(self.manifest_path)
        before = self.manifest_path.read_bytes()

        changes, errors = refresh_manifest(self.manifest_path)
        after = self.manifest_path.read_bytes()

        self.assertEqual(errors, [])
        self.assertEqual(changes, 0)
        self.assertEqual(before, after)

    def test_refresh_refuses_missing_artifact_path(self) -> None:
        self._write_manifest(
            _digest_for_bytes(self.policy_bytes),
            _digest_for_bytes(self.fixture_bytes),
        )
        self.fixture_path.unlink()

        changes, errors = refresh_manifest(self.manifest_path)
        self.assertEqual(changes, 0)
        self.assertTrue(any("missing referenced artifact" in error for error in errors))

    def test_refresh_supports_empty_compiled_array(self) -> None:
        errors = validate_manifest(self.manifest_path)
        self.assertEqual(errors, [])

        changes, refresh_errors = refresh_manifest(self.manifest_path)
        self.assertEqual(refresh_errors, [])
        self.assertEqual(changes, 0)

    def test_refresh_updates_only_digest_fields(self) -> None:
        stale_policy = "sha256:" + ("0" * 64)
        self._write_manifest(stale_policy, _digest_for_bytes(self.fixture_bytes))
        before = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        refresh_manifest(self.manifest_path)
        after = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        before_policy = before["artifacts"]["policyDocuments"][0].copy()
        after_policy = after["artifacts"]["policyDocuments"][0].copy()
        before_policy.pop("digest")
        after_policy.pop("digest")
        self.assertEqual(before_policy, after_policy)
        self.assertNotEqual(
            before["artifacts"]["policyDocuments"][0]["digest"],
            after["artifacts"]["policyDocuments"][0]["digest"],
        )

    def test_sha256_digest_for_file_matches_pattern(self) -> None:
        digest = _sha256_digest_for_file(self.policy_path)
        self.assertTrue(digest.startswith("sha256:"))
        self.assertEqual(len(digest), len("sha256:") + 64)


if __name__ == "__main__":
    unittest.main()
