# Baseline rule catalog

This document describes the stable rule categories, product decisions, severities, exception semantics, and decision-evidence fields for the `production-infra-baseline` pack at `0.1.0`.

Tenant enablement, approver group membership, cost threshold values, pipeline allowlists, and customer overrides stay in [control9](https://github.com/alto9/control9). This repository defines reusable pack semantics only.

## Rule categories

| Rule ID | Category | Decision | Severity | Risk area |
|---------|----------|----------|----------|-----------|
| `allow-low-risk-dev-iac` | production-mutation | allow | low | Routine low-risk development IaC |
| `require-approval-prod-mutation` | production-mutation | require_approval | medium | Production create/update mutations |
| `require-approval-prod-iam-expansion` | iam-expansion | require_approval | high | IAM policy expansion in production |
| `require-approval-prod-new-role` | new-role | require_approval | high | New or materially changed production roles |
| `require-approval-prod-cross-account-access` | cross-account-access | require_approval | critical | Cross-account trust or access grants |
| `deny-prod-destructive-change` | destructive-change | deny | critical | Destructive production change without break-glass |
| `require-approval-prod-destructive-break-glass` | destructive-change | require_approval | critical | Destructive production change with break-glass signal |
| `require-approval-prod-network-boundary-change` | network-boundary | require_approval | high | Security group, NACL, routing, peering, endpoint exposure |
| `require-approval-secrets-exposure-hint` | secrets-exposure-hint | require_approval | high | Secret material hints in plan, template, diff, or command output |
| `require-approval-unapproved-pipeline-source` | unapproved-pipeline-source | require_approval | high | Untrusted or unregistered pipeline deploy authority |
| `observe-cost-threshold-breach` | cost-threshold | observe | medium | Estimated cost or budget threshold signals |
| `require-approval-deploy-verification-mismatch` | deploy-verification-mismatch | require_approval | high | Plan, template, or artifact fingerprint drift after approval |
| `observe-off-path-cloud-mutation` | off-path-finding | observe | high | Cloud mutation without a matching Control9 decision |

The authoritative machine-readable catalog lives in `packs/production-infra-baseline/policies/production-infra-baseline.yaml`.

## Reason text

Each rule defines:

- **`reason`**: the default human-readable sentence used in SaaS UI, GitHub/GitLab feedback, and evidence exports.
- **`reasonPattern`**: a template with `{placeholders}` the policy engine may fill from classifier output (`environment`, `tool`, `changeTypes`, `changeRisk`, and similar fields).

Reason text must stay understandable without parser internals. Do not embed raw secret values, credentials, or full resource payloads in reasons.

## Exception and break-glass semantics

This pack documents high-level exception behavior only:

1. **Break-glass signal** — When an action envelope includes `breakGlass: true`, destructive production rules route to `require-approval-prod-destructive-break-glass` instead of `deny-prod-destructive-change`. The signal name is declared in the policy document under `spec.exceptions.breakGlassSignal`.
2. **Approval routing** — Rules reference approver **roles** (`productionPlatformLeads`, `securityAndPlatformLeads`, `breakGlassApprovers`). control9 maps those roles to tenant-specific approver groups and notification channels.
3. **Temporary policy exceptions** — Time-bound overrides, emergency waivers, and customer-specific exception windows are owned by control9. They are not stored in this repository.
4. **Shadow vs enforce** — The same rule logic applies in shadow and enforce mode. control9 changes only whether the integration may block, wait, or continue immediately.

Destructive production changes **deny by default** unless the break-glass signal is present, in which case they **require approval** before proceed.

Off-path findings are **observed** at **high** severity so the SaaS evidence timeline can surface them without implying the integration evaluated a live policy pack locally.

## Decision evidence for control9 (issue #3 boundary)

This repository supplies the **reusable decision evidence content** that control9 embeds in decision payloads. It does **not** define the full SaaS API response envelope, HTTP status codes, correlation identifiers, tenant configuration, approval routing state, or integration rendering hints. Those remain owned by control9 (see control9 issue #3 and `.ai/integration/api_contracts.md` in each repo).

For each matched baseline rule, the pack contributes:

| Pack field | control9 payload use |
|------------|-------------------|
| `metadata.name` / manifest `pack.name` | Policy pack identity |
| `spec.packVersion` / manifest `version` | Pinned policy pack version on the decision |
| Matched `rules[].id` | `matchedRuleId` (stable rule identifier) |
| `rules[].category` | Risk grouping for UI, exports, and search |
| `rules[].decision` | Product effect: `allow`, `deny`, `require_approval`, `observe` |
| `rules[].severity` / `riskLevel` | Severity or risk surfaced to humans and evidence |
| `rules[].reason` / rendered `reasonPattern` | Primary human-readable reason text |
| `rules[].changeTypes` | Relevant change types attached to the decision |
| Classifier labels (from fixtures, issue #10) | Matched classifier labels on the evidence record |
| Manifest artifact digests | Provenance for which policy document produced the decision |

control9 wraps those fields with tenant scope, runtime mode, correlation identifiers, required action, approval request handles, and integration-specific rendering metadata.

## Fixture expectations

`packs/production-infra-baseline/fixtures/suite.json` indexes one expectation entry per baseline rule ID plus the `classifier-input-fixtures` suite.

Classifier input shapes, example artifacts, deterministic output ordering, and edge-case behavior are documented in `docs/classifier-fixtures.md`. Machine-readable cases live in `packs/production-infra-baseline/fixtures/classifier-cases.json`. Validate locally with:

```bash
python3 scripts/validate-classifier-fixtures.py
```
