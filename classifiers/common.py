"""Shared classifier helpers."""

from __future__ import annotations

import json
import re
from typing import Any

FIXTURE_RESULT_SCHEMA_VERSION = "alto9.io/classifier-fixture-result/v1alpha1"

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]

AWS_ACCOUNT_ARN = re.compile(r"arn:aws:iam::(\d{12}):")


def sorted_unique(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(values))


def policy_change_types(classifier_labels: list[str]) -> list[str]:
    return sorted_unique(
        label for label in classifier_labels if not label.startswith("parser-limitation:")
    )


def envelope_labels(envelope: dict[str, Any]) -> list[str]:
    labels: list[str] = []

    cost_signals = envelope.get("costSignals")
    if isinstance(cost_signals, dict) and cost_signals.get("signal") == "budget-threshold-exceeded":
        labels.append("budget-threshold-exceeded")

    deploy_verification = envelope.get("deployVerification")
    if isinstance(deploy_verification, dict):
        approved = deploy_verification.get("approvedFingerprint")
        current = deploy_verification.get("currentFingerprint")
        if (
            isinstance(approved, str)
            and isinstance(current, str)
            and approved
            and current
            and approved != current
        ):
            labels.append("plan-fingerprint-mismatch")

    return labels


def scan_output_for_secrets(result: dict[str, Any]) -> None:
    serialized = json.dumps(result, separators=(",", ":"), sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            raise ValueError("classifier output matched forbidden secret pattern")


def cross_account_principals(policy: dict[str, Any], account_id: str | None) -> bool:
    if not account_id:
        return False
    statements = policy.get("Statement")
    if not isinstance(statements, list):
        return False
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        principal = statement.get("Principal")
        if not isinstance(principal, dict):
            continue
        aws_value = principal.get("AWS")
        principals: list[str] = []
        if isinstance(aws_value, str):
            principals.append(aws_value)
        elif isinstance(aws_value, list):
            principals.extend(item for item in aws_value if isinstance(item, str))
        for principal_arn in principals:
            match = AWS_ACCOUNT_ARN.search(principal_arn)
            if match and match.group(1) != account_id:
                return True
    return False
