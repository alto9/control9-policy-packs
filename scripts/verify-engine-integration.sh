#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY_PACKS_ROOT="${POLICY_PACKS_ROOT:-$ROOT_DIR}"
CONTROL9_POLICY_ROOT="${CONTROL9_POLICY_ROOT:-$(cd "$ROOT_DIR/../control9" && pwd)}"

SUITE="${1:-all}"
if [[ "${1:-}" == "--suite" ]]; then
  SUITE="${2:-all}"
fi

run_classifier_integration() {
  local PACK_FIXTURE_ID="cf-terraform-deploy-fingerprint-mismatch"
  local CLOUD_AUDIT_FIXTURE_ID="cf-cloud-audit-off-path"
  local SUITE_FIXTURE_ID="ex-terraform-deploy-fingerprint-mismatch"
  local SUITE_FIXTURE_DIR="$POLICY_PACKS_ROOT/fixtures/classifiers/suites/terraform-opentofu/$SUITE_FIXTURE_ID"

  local PACK_GOLDEN="$POLICY_PACKS_ROOT/packs/production-infra-baseline/fixtures/expected-decisions/$PACK_FIXTURE_ID.json"
  local CLOUD_AUDIT_GOLDEN="$POLICY_PACKS_ROOT/packs/production-infra-baseline/fixtures/expected-decisions/$CLOUD_AUDIT_FIXTURE_ID.json"
  local SUITE_GOLDEN="$SUITE_FIXTURE_DIR/expected/policy-result.json"

  local TMP_DIR
  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "$TMP_DIR"' RETURN

  local PACK_OUTPUT="$TMP_DIR/pack-decision-record.json"
  local CLOUD_AUDIT_OUTPUT="$TMP_DIR/cloud-audit-decision-record.json"
  local SUITE_OUTPUT="$TMP_DIR/classifier-policy-result.json"

  local EVALUATE_FIXTURE="$CONTROL9_POLICY_ROOT/packages/policy/scripts/evaluate-fixture.mjs"

  echo "Evaluating pack fixture $PACK_FIXTURE_ID"
  POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" node "$EVALUATE_FIXTURE" pack \
    --fixture-id "$PACK_FIXTURE_ID" \
    --envelope-path "inputs/terraform/deploy-fingerprint-mismatch-envelope.json" \
    --artifact-path "inputs/terraform/prod-mutation-plan.json" \
    --fixture-case-path "classifier-cases.json#$PACK_FIXTURE_ID" \
    --policy-packs-root "$POLICY_PACKS_ROOT" \
    --output "$PACK_OUTPUT"

  echo "Evaluating pack fixture $CLOUD_AUDIT_FIXTURE_ID"
  POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" node "$EVALUATE_FIXTURE" pack \
    --fixture-id "$CLOUD_AUDIT_FIXTURE_ID" \
    --envelope-path "inputs/cloud-audit/off-path-mutation-envelope.json" \
    --fixture-case-path "classifier-cases.json#$CLOUD_AUDIT_FIXTURE_ID" \
    --policy-packs-root "$POLICY_PACKS_ROOT" \
    --output "$CLOUD_AUDIT_OUTPUT"

  echo "Evaluating suite fixture $SUITE_FIXTURE_ID"
  POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" node "$EVALUATE_FIXTURE" suite \
    --fixture-id "$SUITE_FIXTURE_ID" \
    --fixture-dir "$SUITE_FIXTURE_DIR" \
    --policy-packs-root "$POLICY_PACKS_ROOT" \
    --output "$SUITE_OUTPUT"

  echo "Diffing pack decision record against golden"
  diff -u "$PACK_GOLDEN" "$PACK_OUTPUT"

  echo "Diffing cloud-audit decision record against golden"
  diff -u "$CLOUD_AUDIT_GOLDEN" "$CLOUD_AUDIT_OUTPUT"

  echo "Diffing suite policy result against golden semantic fields"
  python3 - <<'PY' "$SUITE_GOLDEN" "$SUITE_OUTPUT"
import json
import sys

golden_path, actual_path = sys.argv[1:3]
golden = json.load(open(golden_path, encoding="utf-8"))
actual = json.load(open(actual_path, encoding="utf-8"))

for key in ("fixtureResultSchemaVersion", "fixtureId", "toolFamily", "matchedRules", "evidenceReferences"):
    if golden.get(key) != actual.get(key):
        raise SystemExit(f"Mismatch for {key}:\nexpected={golden.get(key)!r}\nactual={actual.get(key)!r}")

print("Suite policy result matches golden semantic fields.")
PY
}

run_compatibility_metadata_integration() {
  echo "Running compatibility-metadata engine integration tests"
  (
    cd "$CONTROL9_POLICY_ROOT"
    POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" npm test -w @control9/policy -- compatibility-metadata
  )
}

echo "Building @control9/policy in $CONTROL9_POLICY_ROOT"
(
  cd "$CONTROL9_POLICY_ROOT"
  npm run build -w @control9/policy
)

case "$SUITE" in
  all)
    run_classifier_integration
    run_compatibility_metadata_integration
    ;;
  compatibility-metadata)
    run_compatibility_metadata_integration
    ;;
  classifiers|deploy-verification)
    run_classifier_integration
    ;;
  *)
    echo "Unknown suite: $SUITE" >&2
    echo "Usage: $0 [--suite all|compatibility-metadata|classifiers]" >&2
    exit 2
    ;;
esac

echo "Engine integration verification passed."
