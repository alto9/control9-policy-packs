"""Parse Terraform/OpenTofu plan JSON resource changes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResourceChange:
    address: str
    resource_type: str | None
    actions: list[str]
    before: dict[str, Any] | None
    after: dict[str, Any] | None
    missing_type: bool = False


@dataclass
class ParsedPlan:
    resource_changes: list[ResourceChange] = field(default_factory=list)
    has_partial_summary: bool = False


def _as_dict(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    return None


def parse_plan(artifact: dict[str, Any]) -> ParsedPlan:
    parsed = ParsedPlan()
    raw_changes = artifact.get("resource_changes")
    if not isinstance(raw_changes, list):
        return parsed

    for entry in raw_changes:
        if not isinstance(entry, dict):
            continue
        address = entry.get("address")
        if not isinstance(address, str) or not address:
            continue

        resource_type = entry.get("type")
        missing_type = resource_type is None
        if missing_type:
            parsed.has_partial_summary = True
        elif not isinstance(resource_type, str):
            resource_type = None

        change = _as_dict(entry.get("change")) or {}
        actions = change.get("actions")
        if not isinstance(actions, list):
            actions = []

        parsed.resource_changes.append(
            ResourceChange(
                address=address,
                resource_type=resource_type,
                actions=[action for action in actions if isinstance(action, str)],
                before=_as_dict(change.get("before")),
                after=_as_dict(change.get("after")),
                missing_type=missing_type,
            )
        )

    if artifact.get("parserNotes") and parsed.has_partial_summary:
        parsed.has_partial_summary = True

    return parsed


def policy_document(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            document = json.loads(value)
        except json.JSONDecodeError:
            return None
        return document if isinstance(document, dict) else None
    return None
