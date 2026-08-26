"""Classify CDK synthesized templates and CloudFormation change sets."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from classifiers.common import (
    FIXTURE_RESULT_SCHEMA_VERSION,
    cross_account_principals,
    envelope_labels,
    policy_change_types,
    scan_output_for_secrets,
    sorted_unique,
)

PUBLIC_CIDRS = frozenset({"0.0.0.0/0", "::/0"})


def _as_dict(value: Any) -> dict[str, Any] | None:
    return value if isinstance(value, dict) else None


def _policy_expanded(previous_actions: Any, current_actions: Any) -> bool:
    if not isinstance(previous_actions, list) or not isinstance(current_actions, list):
        return False
    previous = {action for action in previous_actions if isinstance(action, str)}
    current = {action for action in current_actions if isinstance(action, str)}
    if not current:
        return False
    if current - previous:
        return True
    return any(action.endswith(":*") and action not in previous for action in current)


def _classify_cdk_resource(
    logical_id: str,
    resource: dict[str, Any],
    *,
    account_id: str | None,
) -> list[str]:
    resource_type = resource.get("Type")
    if not isinstance(resource_type, str):
        return []

    properties = _as_dict(resource.get("Properties")) or {}
    metadata = _as_dict(resource.get("Metadata")) or {}
    cdk_diff = _as_dict(metadata.get("cdk-diff")) or {}

    if resource_type == "AWS::S3::BucketPolicy":
        policy_document = _as_dict(properties.get("PolicyDocument"))
        if policy_document and cross_account_principals(policy_document, account_id):
            return ["cross-account-access"]

    if resource_type in {"AWS::IAM::Policy", "AWS::IAM::RolePolicy", "AWS::IAM::UserPolicy"}:
        if _policy_expanded(cdk_diff.get("previousActions"), cdk_diff.get("currentActions")):
            return ["iam-policy-expanded"]

    if resource_type == "AWS::IAM::Role":
        return ["new-role"]

    change_type = cdk_diff.get("changeType")
    if change_type == "modify":
        return ["resource-update"]

    return ["resource-create"]


def _primary_labels(labels_by_resource: dict[str, list[str]]) -> dict[str, list[str]]:
    all_labels = {label for labels in labels_by_resource.values() for label in labels}
    filtered: dict[str, list[str]] = defaultdict(list)

    for resource, labels in labels_by_resource.items():
        kept = list(labels)
        if "iam-policy-expanded" in all_labels:
            kept = [label for label in kept if label != "new-role"]
        if "cross-account-access" in all_labels:
            kept = [label for label in kept if label != "resource-create"]
        if kept:
            filtered[resource] = kept

    return filtered


def _parse_cdk_template(
    artifact: dict[str, Any],
    *,
    account_id: str | None,
) -> dict[str, list[str]]:
    labels_by_resource: dict[str, list[str]] = defaultdict(list)
    resources = artifact.get("Resources")
    if not isinstance(resources, dict):
        return labels_by_resource

    for logical_id, resource in resources.items():
        if not isinstance(logical_id, str) or not isinstance(resource, dict):
            continue
        labels_by_resource[logical_id].extend(
            _classify_cdk_resource(logical_id, resource, account_id=account_id)
        )

    return labels_by_resource


def _ingress_expanded(change_summary: dict[str, Any]) -> bool:
    before = change_summary.get("ingressBefore")
    after = change_summary.get("ingressAfter")
    if isinstance(before, str) and isinstance(after, str):
        return after in PUBLIC_CIDRS and before not in PUBLIC_CIDRS
    return False


def _partial_summary_network_signal(logical_id: str, action: str) -> bool:
    return action == "Modify" and "SecurityGroup" in logical_id


def _classify_cf_change(
    change: dict[str, Any],
    *,
    account_id: str | None,
    change_summary: dict[str, Any],
) -> tuple[str, list[str], bool]:
    resource_change = _as_dict(change.get("ResourceChange")) or change
    logical_id = resource_change.get("LogicalResourceId")
    if not isinstance(logical_id, str) or not logical_id:
        return "", [], False

    action = resource_change.get("Action")
    action_text = action if isinstance(action, str) else ""
    resource_type = resource_change.get("ResourceType")
    partial_summary = resource_type is None

    labels: list[str] = []
    if partial_summary:
        labels.append("parser-limitation:partial-summary")

    if isinstance(change_summary.get("addedPrincipal"), str):
        principal = change_summary["addedPrincipal"]
        match_account = cross_account_principals(
            {"Statement": [{"Effect": "Allow", "Principal": {"AWS": principal}, "Action": "*"}]},
            account_id,
        )
        if match_account or (
            account_id
            and "arn:aws:iam::" in principal
            and account_id not in principal
        ):
            labels.append("cross-account-access")
            return logical_id, labels, partial_summary

    if resource_type == "AWS::EC2::SecurityGroup" and action_text == "Modify":
        if _ingress_expanded(change_summary):
            labels.append("security-group-ingress-expanded")
            return logical_id, labels, partial_summary

    if partial_summary and _partial_summary_network_signal(logical_id, action_text):
        labels.append("security-group-ingress-expanded")
        return logical_id, labels, partial_summary

    if action_text == "Remove":
        labels.append("resource-destroy")
        return logical_id, labels, partial_summary

    if action_text == "Modify" and resource_type == "AWS::S3::BucketPolicy":
        labels.append("cross-account-access")
        return logical_id, labels, partial_summary

    if action_text == "Modify":
        labels.append("resource-update")
    elif action_text == "Add":
        labels.append("resource-create")

    return logical_id, labels, partial_summary


def _parse_cloudformation_change_set(
    artifact: dict[str, Any],
    *,
    account_id: str | None,
) -> tuple[dict[str, list[str]], list[str]]:
    labels_by_resource: dict[str, list[str]] = defaultdict(list)
    parser_limitations: list[str] = []
    change_summary = _as_dict(artifact.get("changeSummary")) or {}

    changes = artifact.get("Changes")
    if not isinstance(changes, list):
        return labels_by_resource, parser_limitations

    saw_partial_summary = False
    for change in changes:
        if not isinstance(change, dict):
            continue
        logical_id, labels, partial_summary = _classify_cf_change(
            change,
            account_id=account_id,
            change_summary=change_summary,
        )
        if not logical_id:
            continue
        if partial_summary:
            saw_partial_summary = True
        labels_by_resource[logical_id].extend(labels)

    if saw_partial_summary:
        parser_limitations.append("partial-summary")

    return labels_by_resource, parser_limitations


def classify(
    envelope: dict[str, Any],
    artifact: dict[str, Any],
    *,
    fixture_id: str,
) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    tool_family = envelope.get("toolFamily")
    if tool_family not in {"cdk", "cloudformation"}:
        raise ValueError(f"unsupported toolFamily for cdk/cloudformation classifier: {tool_family!r}")

    account_id = envelope.get("accountId") if isinstance(envelope.get("accountId"), str) else None
    parser_limitations: list[str] = []

    if tool_family == "cdk":
        labels_by_resource = _parse_cdk_template(artifact, account_id=account_id)
    else:
        labels_by_resource, parser_limitations = _parse_cloudformation_change_set(
            artifact,
            account_id=account_id,
        )

    for label in envelope_labels(envelope):
        for resource_identity in labels_by_resource:
            labels_by_resource[resource_identity].append(label)
            if label == "plan-fingerprint-mismatch":
                updated: list[str] = []
                for existing in labels_by_resource[resource_identity]:
                    if existing == "resource-create":
                        updated.append("resource-update")
                    else:
                        updated.append(existing)
                labels_by_resource[resource_identity] = updated

    labels_by_resource = _primary_labels(labels_by_resource)

    label_resource_pairs: list[tuple[str, str]] = []
    all_labels: list[str] = []
    resource_identities: list[str] = []

    for resource_identity in sorted(labels_by_resource):
        resource_labels = sorted_unique(labels_by_resource[resource_identity])
        if not resource_labels:
            continue
        resource_identities.append(resource_identity)
        all_labels.extend(resource_labels)
        for label in resource_labels:
            label_resource_pairs.append((label, resource_identity))

    classifier_labels = sorted_unique(all_labels)
    change_types = policy_change_types(classifier_labels)

    result = {
        "fixtureResultSchemaVersion": FIXTURE_RESULT_SCHEMA_VERSION,
        "fixtureId": fixture_id,
        "toolFamily": tool_family,
        "classifierLabels": classifier_labels,
        "changeTypes": change_types,
        "resourceIdentities": resource_identities,
        "parserLimitations": parser_limitations,
    }
    scan_output_for_secrets(result)
    return result, label_resource_pairs
