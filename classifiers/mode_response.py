"""Project mode-specific response metadata from a shared policy result."""

from __future__ import annotations

from typing import Any

from classifiers.common import scan_output_for_secrets

MODE_RESPONSE_SCHEMA_VERSION = "alto9.io/mode-response/v1alpha1"
SHADOW_NON_BLOCK_SUFFIX = " Shadow mode is active, so this workflow is not blocked by Control9."


def primary_decision(policy_result: dict[str, Any]) -> str | None:
    rules = policy_result.get("matchedRules")
    if not isinstance(rules, list) or not rules:
        return None
    first_rule = rules[0]
    if not isinstance(first_rule, dict):
        return None
    decision = first_rule.get("decision")
    return decision if isinstance(decision, str) else None


def expected_mode_behavior(decision: str, runtime_mode: str) -> tuple[bool, bool]:
    """Return (blocksWorkflow, isAdvisory) for a decision and runtime mode."""
    if decision == "observe":
        return False, True
    if decision == "allow":
        return False, False
    if runtime_mode == "shadow":
        if decision == "require_approval":
            return False, True
        return False, False
    if decision in {"deny", "require_approval"}:
        return True, False
    return False, False


def project_mode_response(
    policy_result: dict[str, Any],
    *,
    runtime_mode: str,
    pack_version: str,
) -> dict[str, Any]:
    decision = primary_decision(policy_result)
    if decision is None:
        raise ValueError("policy result has no primary decision")

    rules = policy_result.get("matchedRules") or []
    first_rule = rules[0] if rules and isinstance(rules[0], dict) else {}
    reason = first_rule.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("policy result primary rule missing reason")

    blocks_workflow, is_advisory = expected_mode_behavior(decision, runtime_mode)
    response_summary = reason
    if runtime_mode == "shadow" and decision in {"deny", "require_approval"}:
        response_summary = f"{reason}{SHADOW_NON_BLOCK_SUFFIX}"

    result = {
        "modeResponseSchemaVersion": MODE_RESPONSE_SCHEMA_VERSION,
        "runtimeMode": runtime_mode,
        "packVersion": pack_version,
        "blocksWorkflow": blocks_workflow,
        "isAdvisory": is_advisory,
        "responseSummary": response_summary,
    }
    scan_output_for_secrets(result)
    return result
