"""Classify Terraform/OpenTofu plan JSON against a classifier input envelope."""

from __future__ import annotations

import json
import re
from typing import Any

from classifiers.terraform_opentofu.plan_parser import parse_plan
from classifiers.terraform_opentofu.rules import classify_resource_change, envelope_labels

FIXTURE_RESULT_SCHEMA_VERSION = "alto9.io/classifier-fixture-result/v1alpha1"

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"(?i)password\s*[:=]\s*['\"]?[^'\"\s]{8,}"),
]


def _sorted_unique(values: list[str]) -> list[str]:
    return sorted(dict.fromkeys(values))


def _policy_change_types(classifier_labels: list[str]) -> list[str]:
    return _sorted_unique(
        label for label in classifier_labels if not label.startswith("parser-limitation:")
    )


def _scan_output_for_secrets(result: dict[str, Any]) -> None:
    serialized = json.dumps(result, separators=(",", ":"), sort_keys=True)
    for pattern in SECRET_PATTERNS:
        if pattern.search(serialized):
            raise ValueError("classifier output matched forbidden secret pattern")


def classify(envelope: dict[str, Any], artifact: dict[str, Any], *, fixture_id: str) -> dict[str, Any]:
    tool_family = envelope.get("toolFamily")
    if tool_family not in {"terraform", "opentofu"}:
        raise ValueError(f"unsupported toolFamily for terraform classifier: {tool_family!r}")

    parsed_plan = parse_plan(artifact)
    account_id = envelope.get("accountId") if isinstance(envelope.get("accountId"), str) else None

    labels = envelope_labels(envelope)
    envelope_only = set(labels)
    resource_identities: list[str] = []

    for change in parsed_plan.resource_changes:
        resource_identities.append(change.address)
        resource_labels = classify_resource_change(
            change,
            account_id=account_id,
            envelope_only_labels=envelope_only,
        )
        labels.extend(resource_labels)

    parser_limitations: list[str] = []
    if parsed_plan.has_partial_summary:
        parser_limitations.append("partial-summary")
        labels.append("parser-limitation:partial-summary")

    classifier_labels = _sorted_unique(labels)
    change_types = _policy_change_types(classifier_labels)
    sorted_identities = _sorted_unique(resource_identities)

    result = {
        "fixtureResultSchemaVersion": FIXTURE_RESULT_SCHEMA_VERSION,
        "fixtureId": fixture_id,
        "toolFamily": tool_family,
        "classifierLabels": classifier_labels,
        "changeTypes": change_types,
        "resourceIdentities": sorted_identities,
        "parserLimitations": parser_limitations,
    }
    _scan_output_for_secrets(result)
    return result
