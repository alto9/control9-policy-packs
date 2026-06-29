#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CLASSIFIER_SUITES=(cdk-cloudformation terraform-opentofu shadow-enforce)
COMPATIBILITY_SUITES=(compatibility-metadata)

usage() {
  cat <<'EOF'
Usage:
  ./scripts/run-fixtures.sh --all
  ./scripts/run-fixtures.sh --suite <suite-id> [--suite <suite-id> ...]

Known suites:
  compatibility-metadata
  cdk-cloudformation
  terraform-opentofu
  shadow-enforce
EOF
}

contains() {
  local needle="$1"
  shift
  local item
  for item in "$@"; do
    if [[ "$item" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

if [[ $# -eq 0 ]]; then
  usage
  exit 2
fi

run_all=false
requested_suites=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --all)
      run_all=true
      shift
      ;;
    --suite)
      if [[ $# -lt 2 ]]; then
        echo "missing value for --suite" >&2
        exit 2
      fi
      requested_suites+=("$2")
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

if $run_all; then
  requested_suites=("${COMPATIBILITY_SUITES[@]}" "${CLASSIFIER_SUITES[@]}")
fi

if [[ ${#requested_suites[@]} -eq 0 ]]; then
  usage
  exit 2
fi

compatibility_args=()
classifier_args=()
for suite_id in "${requested_suites[@]}"; do
  if contains "$suite_id" "${COMPATIBILITY_SUITES[@]}"; then
    compatibility_args+=(--suite "$suite_id")
  elif contains "$suite_id" "${CLASSIFIER_SUITES[@]}"; then
    classifier_args+=(--suite "$suite_id")
  else
    echo "Unknown suite: $suite_id" >&2
    usage
    exit 2
  fi
done

if [[ ${#compatibility_args[@]} -gt 0 ]]; then
  python3 scripts/run-compatibility-fixtures.py --report "${compatibility_args[@]}"
fi

if [[ ${#classifier_args[@]} -gt 0 ]]; then
  python3 scripts/run-classifier-fixtures.py --report "${classifier_args[@]}"
fi
