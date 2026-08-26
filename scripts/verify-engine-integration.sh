#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
POLICY_PACKS_ROOT="${POLICY_PACKS_ROOT:-$ROOT_DIR}"
CONTROL9_POLICY_ROOT="${CONTROL9_POLICY_ROOT:-$(cd "$ROOT_DIR/../control9" && pwd)}"

PACK_FIXTURE_ID="cf-terraform-deploy-fingerprint-mismatch"
SUITE_FIXTURE_ID="ex-terraform-deploy-fingerprint-mismatch"
SUITE_FIXTURE_DIR="$POLICY_PACKS_ROOT/fixtures/classifiers/suites/terraform-opentofu/$SUITE_FIXTURE_ID"

PACK_GOLDEN="$POLICY_PACKS_ROOT/packs/production-infra-baseline/fixtures/expected-decisions/$PACK_FIXTURE_ID.json"
SUITE_GOLDEN="$SUITE_FIXTURE_DIR/expected/policy-result.json"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PACK_OUTPUT="$TMP_DIR/pack-decision-record.json"
SUITE_OUTPUT="$TMP_DIR/classifier-policy-result.json"

echo "Building @control9/policy in $CONTROL9_POLICY_ROOT"
(
  cd "$CONTROL9_POLICY_ROOT"
  npm run build -w @control9/policy
)

EVALUATE_FIXTURE="$CONTROL9_POLICY_ROOT/packages/policy/scripts/evaluate-fixture.mjs"

echo "Evaluating pack fixture $PACK_FIXTURE_ID"
POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" node "$EVALUATE_FIXTURE" pack \
  --fixture-id "$PACK_FIXTURE_ID" \
  --envelope-path "inputs/terraform/deploy-fingerprint-mismatch-envelope.json" \
  --artifact-path "inputs/terraform/prod-mutation-plan.json" \
  --fixture-case-path "classifier-cases.json#$PACK_FIXTURE_ID" \
  --policy-packs-root "$POLICY_PACKS_ROOT" \
  --output "$PACK_OUTPUT"

echo "Evaluating suite fixture $SUITE_FIXTURE_ID"
POLICY_PACKS_ROOT="$POLICY_PACKS_ROOT" node "$EVALUATE_FIXTURE" suite \
  --fixture-id "$SUITE_FIXTURE_ID" \
  --fixture-dir "$SUITE_FIXTURE_DIR" \
  --policy-packs-root "$POLICY_PACKS_ROOT" \
  --output "$SUITE_OUTPUT"

echo "Diffing pack decision record against golden"
diff -u "$PACK_GOLDEN" "$PACK_OUTPUT"

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

echo "Engine integration verification passed."
