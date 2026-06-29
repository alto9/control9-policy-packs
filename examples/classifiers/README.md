# Classifier examples

Reviewer-facing examples trace baseline infrastructure risks from **input summary** → **classifier labels** → **matched rule** → **expected decision**.

Each subdirectory mirrors a supported tool family. Files show representative artifact fragments and envelope context without freezing parser internals.

| Directory | Covers |
|-----------|--------|
| `cdk/` | Synthesized templates, stack identity, IAM and network deltas |
| `cloudformation/` | Templates and change-set summaries |
| `terraform/` | Plan JSON, workspace identity, resource addresses |
| `pipeline/` | Unapproved pipeline source metadata |
| `cloud-audit/` | Off-path CloudTrail-style findings |

Machine-checkable expectations live in `packs/production-infra-baseline/fixtures/classifier-cases.json`. Full contract documentation: `docs/classifier-fixtures.md`.

Run local checks:

```bash
python3 scripts/validate-classifier-fixtures.py
```
