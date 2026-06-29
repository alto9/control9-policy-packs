# Classifier fixtures and examples

This document defines supported classifier input shapes, example expectations, deterministic output ordering, and edge-case behavior for the `production-infra-baseline` pack at `0.1.0`.

Machine-readable cases live in `packs/production-infra-baseline/fixtures/classifier-cases.json`. Reviewer-facing input samples live under `examples/classifiers/` and `packs/production-infra-baseline/fixtures/inputs/`.

## Input envelope shape

Every classifier fixture declares an **input envelope** that wraps a tool artifact plus evaluation context. Envelopes use `schemaVersion: alto9.io/classifier-input-envelope/v1alpha1`.

| Field | Required | Meaning |
|-------|----------|---------|
| `schemaVersion` | yes | Envelope schema identifier |
| `toolFamily` | yes | `cdk`, `cloudformation`, `terraform`, `opentofu`, `pipeline`, or `cloud-audit` |
| `tool` | yes | Concrete tool name (`cdk`, `cloudformation`, `terraform`, `opentofu`, `github-actions`, `cloudtrail`, …) |
| `environment` | yes | Target environment label (`dev`, `staging`, `production`) |
| `accountId` | when cloud-scoped | AWS account or cloud scope identifier |
| `workspace` | for Terraform/OpenTofu | Workspace or stack target name |
| `stackName` | for CDK/CloudFormation | Stack or template identity |
| `artifactRef` | usually | Relative path, media type, and fingerprint of the primary artifact |
| `pipeline` | for pipeline fixtures | Source authority, workflow identity, registration status |
| `deployVerification` | for fingerprint cases | Approved and current artifact fingerprints |
| `costSignals` | for cost cases | Estimated delta and threshold metadata |
| `breakGlass` | for destructive cases | Break-glass signal (`true` routes to approval instead of deny) |
| `auditEvent` | for off-path cases | Observed cloud mutation summary |

Envelopes carry **context**, not tenant configuration. Approver groups, cost threshold values, and pipeline allowlists remain in control9.

## Supported artifact shapes

### CDK / synthesized CloudFormation

Examples represent:

- Stack or template identity (`stackName`, template fingerprint)
- Logical resource identity (`logicalId`, CloudFormation `Type`)
- Resource actions (`create`, `update`, `delete`)
- IAM policy expansion, new roles, cross-account principals
- Destructive operations and network boundary resources
- Template fingerprints for deploy verification

See `examples/classifiers/cdk/` and `fixtures/inputs/cdk/`.

### CloudFormation templates and change summaries

Examples represent:

- Template resource blocks with stable logical IDs
- Change set actions (`Add`, `Modify`, `Remove`, `Replace`)
- Stack-level destructive signals
- Partial summaries that omit resource types (edge case)

See `examples/classifiers/cloudformation/` and `fixtures/inputs/cloudformation/`.

### Terraform / OpenTofu plan JSON

Examples represent:

- Workspace or environment identity
- Resource address (`aws_iam_role.example`)
- Provider metadata
- `resource_changes[].change.actions` sequence
- IAM, network, destructive, secrets hint, and cost signals
- Plan fingerprints

See `examples/classifiers/terraform/` and `fixtures/inputs/terraform/`.

### Pipeline metadata

Examples represent:

- Source authority (registered vs unregistered workflow)
- Requested deploy authority
- Artifact fingerprint attached to the pipeline run

See `fixtures/inputs/pipeline/`.

### Cloud audit / off-path signals

Examples represent:

- Event source and time
- Cloud resource identity
- Actor or principal summary
- Correlation result (`no-matching-decision`)
- Redaction defaults (no raw credential payloads)

See `fixtures/inputs/cloud-audit/`.

## Semantic labels and change types

Classifiers emit **classifier labels** that align with baseline `changeTypes` in `production-infra-baseline.yaml`. Examples:

| Baseline risk | Classifier labels / change types |
|---------------|----------------------------------|
| Production mutation | `resource-create`, `resource-update` |
| IAM expansion | `iam-policy-expanded`, `managed-policy-attachment` |
| New role | `new-role`, `role-trust-policy-changed` |
| Cross-account access | `cross-account-access`, `cross-account-trust` |
| Destructive change | `resource-destroy`, `stack-delete`, `database-delete` |
| Network boundary | `security-group-ingress-expanded`, `vpc-peering-added` |
| Secrets hint | `secret-value-in-plan` (redacted evidence only) |
| Unapproved pipeline | `untrusted-pipeline-source`, `unregistered-workflow` |
| Cost threshold | `estimated-cost-increase`, `budget-threshold-exceeded` |
| Deploy mismatch | `plan-fingerprint-mismatch`, `template-fingerprint-mismatch` |
| Off-path finding | `off-path-cloud-mutation`, `audit-event-without-decision` |

Fixtures document **meaning**, not parser internals. Resource identity uses stable addresses or logical IDs only.

## Deterministic output ordering

Matched classifier labels and baseline rule IDs are sorted before comparison and fixture reports. Sort keys, in order:

1. **Severity rank** (ascending): `critical` → `high` → `medium` → `low`
2. **Decision rank** (ascending): `deny` → `require_approval` → `observe` → `allow`
3. **`ruleId`** (ascending, Unicode code point order)
4. **`classifierLabel`** (ascending)
5. **`resourceIdentity`** (ascending)

The runner in `scripts/validate-classifier-fixtures.py` enforces this ordering on every `expected.matchedRules` entry and on aggregated label lists.

Shadow and enforce modes must produce the same ordered semantic result; only the product response surface may differ (see `.ai/runtime/execution_model.md`).

## Edge-case behavior

| Situation | Expected classifier behavior | Baseline policy effect |
|-----------|-------------------------------|------------------------|
| **Unknown resource type** | Emit `parser-limitation:unknown-resource-type`; classify known deltas only | Production uncertainty routes to `require_approval` when mutation is detected; otherwise `observe` |
| **Parser error** | Emit `parser-limitation:parse-error`; omit unreliable labels | `require_approval` for production envelopes; fixture records limitation metadata |
| **Unsupported IaC tool** | Emit `parser-limitation:unsupported-tool`; no resource deltas | `observe` with limitation metadata; no silent allow |
| **Partial summary** | Emit `parser-limitation:partial-summary`; classify present fields only | Match rules for detected high-risk change types; note missing fields in fixture notes |

Parser limitations are listed in `expected.parserLimitations` on each case. They never include raw secret values or full template/plan bodies.

## Secrets and redaction

Examples use **synthetic or redacted** secret hints:

- Placeholder values like `[REDACTED_SECRET_REF]` or `***`
- Metadata fields such as `secretsHint: true` without literal secret material
- No AWS access keys, private keys, or live tokens in fixtures

## Local validation

From the repository root:

```bash
python3 scripts/validate-classifier-fixtures.py
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json
git diff --check
```

The classifier fixture runner validates structure, baseline risk coverage, input file presence, deterministic ordering, and forbidden secret patterns. It does **not** execute live classifiers yet; it proves the fixture contract that implementation and CI will enforce.

## Related documents

- Rule catalog: `docs/baseline-rule-catalog.md`
- Rule expectation index: `packs/production-infra-baseline/fixtures/suite.json`
- Classifier cases: `packs/production-infra-baseline/fixtures/classifier-cases.json`
- Reviewer examples: `examples/classifiers/README.md`
