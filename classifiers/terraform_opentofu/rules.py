"""Semantic classification rules for Terraform/OpenTofu plan changes."""

from __future__ import annotations

import re
from typing import Any

from classifiers.terraform_opentofu.plan_parser import ResourceChange, policy_document

AWS_ACCOUNT_ARN = re.compile(r"arn:aws:iam::(\d{12}):")

DATABASE_DELETE_TYPES = frozenset(
    {
        "aws_rds_cluster",
        "aws_db_instance",
        "aws_rds_cluster_instance",
    }
)

IAM_POLICY_TYPES = frozenset(
    {
        "aws_iam_role_policy",
        "aws_iam_policy",
        "aws_iam_user_policy",
    }
)

PUBLIC_CIDRS = frozenset({"0.0.0.0/0", "::/0"})


def _ingress_cidrs(ingress_rules: Any) -> set[str]:
    cidrs: set[str] = set()
    if not isinstance(ingress_rules, list):
        return cidrs
    for rule in ingress_rules:
        if not isinstance(rule, dict):
            continue
        blocks = rule.get("cidr_blocks")
        if isinstance(blocks, list):
            cidrs.update(str(block) for block in blocks if isinstance(block, str))
    return cidrs


def _policy_actions(policy: dict[str, Any]) -> set[str]:
    actions: set[str] = set()
    statements = policy.get("Statement")
    if not isinstance(statements, list):
        return actions
    for statement in statements:
        if not isinstance(statement, dict):
            continue
        action_value = statement.get("Action")
        if isinstance(action_value, str):
            actions.add(action_value)
        elif isinstance(action_value, list):
            actions.update(item for item in action_value if isinstance(item, str))
    return actions


def _policy_expanded(before: dict[str, Any] | None, after: dict[str, Any] | None) -> bool:
    before_policy = policy_document((before or {}).get("policy"))
    after_policy = policy_document((after or {}).get("policy"))
    if before_policy is None or after_policy is None:
        return False
    before_actions = _policy_actions(before_policy)
    after_actions = _policy_actions(after_policy)
    if not after_actions:
        return False
    if after_actions - before_actions:
        return True
    for action in after_actions:
        if action.endswith(":*") and action not in before_actions:
            return True
    return len(after_actions) > len(before_actions)


def _cross_account_principals(policy: dict[str, Any], account_id: str | None) -> bool:
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


def _secrets_hint(change: ResourceChange) -> bool:
    for side in (change.before, change.after):
        if not isinstance(side, dict):
            continue
        if side.get("secretsHint") is True:
            return True
        secret_string = side.get("secret_string")
        if isinstance(secret_string, str) and (
            "[REDACTED" in secret_string or secret_string.strip() == "***"
        ):
            return True
    resource_type = change.resource_type or ""
    if "secretsmanager_secret" in resource_type and "update" in change.actions:
        if isinstance(change.after, dict) and change.after.get("secretsHint") is True:
            return True
    return False


def _network_boundary_expanded(change: ResourceChange) -> bool:
    resource_type = change.resource_type or ""
    if resource_type != "aws_security_group" and "security_group" not in change.address:
        return False
    before_cidrs = _ingress_cidrs((change.before or {}).get("ingress"))
    after_cidrs = _ingress_cidrs((change.after or {}).get("ingress"))
    newly_public = (after_cidrs & PUBLIC_CIDRS) - (before_cidrs & PUBLIC_CIDRS)
    return bool(newly_public)


def classify_resource_change(
    change: ResourceChange,
    *,
    account_id: str | None,
    envelope_only_labels: set[str],
) -> list[str]:
    if "budget-threshold-exceeded" in envelope_only_labels:
        return []

    labels: list[str] = []

    if _secrets_hint(change):
        labels.append("secret-value-in-plan")
        return labels

    if change.resource_type in DATABASE_DELETE_TYPES and "delete" in change.actions:
        labels.append("database-delete")
        return labels

    if change.resource_type in IAM_POLICY_TYPES and "update" in change.actions:
        if _policy_expanded(change.before, change.after):
            labels.append("iam-policy-expanded")
            return labels

    if change.resource_type == "aws_iam_role" and "create" in change.actions:
        labels.append("new-role")
        return labels

    if change.resource_type == "aws_s3_bucket_policy" and change.actions:
        after_policy = policy_document((change.after or {}).get("policy"))
        if after_policy and _cross_account_principals(after_policy, account_id):
            labels.append("cross-account-access")
            return labels

    if _network_boundary_expanded(change):
        labels.append("security-group-ingress-expanded")
        return labels

    if "create" in change.actions:
        labels.append("resource-create")
    elif "update" in change.actions:
        labels.append("resource-update")
    elif "delete" in change.actions:
        labels.append("resource-destroy")

    return labels


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
