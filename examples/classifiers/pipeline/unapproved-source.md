# Unapproved pipeline source example

Pipeline fixtures use envelope metadata only. No raw workflow secrets appear in examples.

**Input envelope:** `packs/production-infra-baseline/fixtures/inputs/pipeline/unapproved-source-envelope.json`

**Source authority:** `unregistered`

**Resource identity:** `acme/example-app:deploy-prod.yml`

**Classifier labels:** `untrusted-pipeline-source`

**Matched rule:** `require-approval-unapproved-pipeline-source` → `require_approval` (high)

See case `cf-pipeline-unapproved-source` in `classifier-cases.json`.
