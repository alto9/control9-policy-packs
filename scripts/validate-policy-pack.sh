#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MANIFEST="${1:-packs/production-infra-baseline/manifest.json}"

echo "==> Validating pack manifest: ${MANIFEST}"
python3 scripts/validate-pack-manifest.py "${MANIFEST}"

echo "==> Validating classifier fixtures"
python3 scripts/validate-classifier-fixtures.py

echo "==> Running shared classifier fixture suites"
./scripts/run-fixtures.sh --all

echo "==> Validating explainable decision records"
python3 scripts/validate-decision-records.py

echo "==> Validating docs and examples"
python3 scripts/validate-docs-examples.py

echo "==> Checking diff whitespace"
git diff --check

echo "OK: policy pack validation passed"
