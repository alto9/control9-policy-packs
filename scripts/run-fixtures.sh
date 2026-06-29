#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run-fixtures.sh --all
  ./scripts/run-fixtures.sh --suite <suite-id> [--suite <suite-id> ...]

Known suites:
  cdk-cloudformation
  terraform-opentofu
EOF
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

python_args=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      python_args+=(--all)
      shift
      ;;
    --suite)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --suite" >&2
        exit 2
      fi
      python_args+=(--suite "$2")
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

python3 scripts/run-classifier-fixtures.py --report "${python_args[@]}"
