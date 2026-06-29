# Explainable policy decision records

This document defines the reusable decision evidence content that baseline policy packs produce and that [control9](https://github.com/alto9/control9) embeds in SaaS decision payloads, CI feedback, fixture reports, and evidence exports.

Tenant enablement, approval routing, customer overrides, and the complete API response envelope remain owned by control9. This repository owns pack identity, matched rule metadata, plain-language reason and risk text, relevant change types, classifier labels, evidence references, and fixture identity.

## Decision record shape

Machine-readable schema: [`schemas/policy-decision-record.v1alpha1.schema.json`](../schemas/policy-decision-record.v1alpha1.schema.json)

Each explainable decision record includes:

| Field | Purpose |
|-------|---------|
| `packName` / `packVersion` | Which policy pack version produced the decision |
| `fixtureId` | Stable fixture case identity when evaluating fixtures |
| `matchedRules[].ruleId` | Stable rule identifier from the policy document |
| `matchedRules[].category` | Risk grouping for UI, exports, and search |
| `matchedRules[].decision` | Product effect: `allow`, `deny`, `require_approval`, `observe` |
| `matchedRules[].severity` / `riskLevel` | Human-facing severity or risk |
| `matchedRules[].reason` | Primary reason text shown to humans |
| `matchedRules[].riskSummary` | Plain-language risk summary for platform and security reviewers |
| `matchedRules[].changeTypes` | Relevant change types attached to the decision |
| `matchedRules[].classifierLabels` | Matched semantic classifier labels |
| `matchedRules[].evidenceReferences` | Pointers to envelope, artifact, policy document, manifest, and fixture inputs |
| `parserLimitations` | Parser limitations that affected the result, when present |

Golden fixture outputs live under `packs/production-infra-baseline/fixtures/expected-decisions/`. Reviewer-facing example: [`examples/decisions/terraform-prod-iam-expansion.json`](../examples/decisions/terraform-prod-iam-expansion.json).

## Reason and risk summary guidance

Write complete sentences in plain language. A platform engineer or security reviewer should understand why a rule fired without opening parser code or raw IaC payloads.

**Reason text** states what happened and what the operator should do next. Example:

> Production IAM expansion increases authority and needs human review.

**Risk summary** states the underlying risk in reviewer-friendly terms. Example:

> Expands who can perform actions in the account and increases privilege escalation risk.

Guidelines:

1. Prefer short, complete sentences over internal label names or parser jargon.
2. Use `reasonPattern` in the policy YAML when dynamic context (`{changeTypes}`, `{environment}`, `{tool}`) improves clarity.
3. Keep deny and require-approval text actionable.
4. Shadow and enforce mode use the same reason, risk summary, matched rule, and change types. control9 changes only the product response surface.

See also [`policy-authoring.md`](policy-authoring.md) and the reason text section in [`baseline-rule-catalog.md`](baseline-rule-catalog.md).

## Redaction expectations

Decision output must **not** include:

- Raw secret values, access keys, private keys, or credential material
- Excessive template, plan, or diff fragments beyond what reviewers need
- Tenant-specific approver group membership or routing configuration
- Customer override or exception state

Decision output **may** include:

- Pack name, version, and policy document digest
- Matched rule ID, category, decision effect, severity, reason, and risk summary
- Normalized resource identity and classifier labels
- Evidence references that point to redacted envelope and artifact inputs
- Parser limitation codes such as `parse-error`, `partial-summary`, or `unsupported-tool`

Fixture validation scans envelope and artifact inputs for common secret patterns. Reasons and risk summaries are also scanned during decision record validation.

## Fixture and live evaluation parity

Classifier fixtures declare the same explainable decision content that the SaaS policy engine consumes for live evaluation:

- `classifier-cases.json` carries expected `reason`, `riskSummary`, `changeTypes`, and case-level `evidenceReferences` on each matched rule.
- `fixtures/expected-decisions/<case-id>.json` stores the golden decision record for deterministic comparison.
- Live evaluation must produce the same matched rule metadata, reason, risk summary, relevant change types, classifier labels, and deterministic ordering as fixture expectations for the same input envelope and pack version.

## Validate locally

```bash
python3 scripts/validate-decision-records.py
./scripts/validate-policy-pack.sh
```

Regenerate golden outputs after policy or fixture changes:

```bash
python3 scripts/validate-decision-records.py --sync-fixtures --write-expected
```

## Related documents

- [`baseline-rule-catalog.md`](baseline-rule-catalog.md)
- [`classifier-fixtures.md`](classifier-fixtures.md)
- [`ci-expectations.md`](ci-expectations.md)
- [`policy-authoring.md`](policy-authoring.md)
