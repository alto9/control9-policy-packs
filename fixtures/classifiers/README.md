# Classifier fixtures

Shared layout for semantic classifier fixture suites used by `./scripts/run-fixtures.sh`.

Each suite lives under `suites/<suite-id>/` and groups fixtures for a supported tool family set. The `cdk-cloudformation` suite covers CDK and CloudFormation semantics; issue #16 extends `terraform-opentofu` coverage.

## Layout

```
fixtures/classifiers/
  README.md
  suites/
    <suite-id>/
      manifest.json
      <fixture-id>/
        notes.md
        input/
          envelope.json          # classifier input envelope
          artifact.json          # primary IaC artifact (optional for some edge cases)
        expected/
          classifier-output.json # semantic labels, change types, resource identities, parser limitations
          policy-result.json     # matched rules, decisions, evidence references
```

## Expected result fields

Fixture assertions use the contract from `.ai/data/serialization.md` and `.ai/runtime/execution_model.md`:

| Field | File | Meaning |
|-------|------|---------|
| `fixtureId` | both expected files | Stable fixture identifier |
| `toolFamily` | both expected files | Supported tool family |
| `classifierLabels` | `classifier-output.json` | Matched semantic classifier labels |
| `changeTypes` | `classifier-output.json` | Policy-relevant change types |
| `resourceIdentities` | `classifier-output.json` | Normalized resource identity |
| `parserLimitations` | `classifier-output.json` | Parser limitation metadata when present |
| `matchedRules` | `policy-result.json` | Matched rule IDs, product decision, severity, reason, risk summary |
| `evidenceReferences` | `policy-result.json` | Envelope, artifact, policy document, and manifest references |

Matched rules and classifier labels sort deterministically by severity rank, decision rank, `ruleId`, `classifierLabel`, then `resourceIdentity` (all ascending).

## Suites

| Suite ID | Tool families | Purpose |
|----------|---------------|---------|
| `cdk-cloudformation` | `cdk`, `cloudformation` | CDK synthesized templates and CloudFormation template diffs |
| `terraform-opentofu` | `terraform`, `opentofu` | Terraform and OpenTofu plan JSON inputs |

## Local commands

From the repository root:

```bash
./scripts/run-fixtures.sh --all
./scripts/run-fixtures.sh --suite cdk-cloudformation
./scripts/run-fixtures.sh --suite terraform-opentofu
git diff --check
```

The runner validates fixture structure, expected result shape, deterministic ordering, cross-file consistency, and forbidden secret patterns. It does not execute live classifiers yet; it proves the fixture contract that implementation and CI will enforce.

Schema: `schemas/classifier-fixture-result.v1alpha1.schema.json`
