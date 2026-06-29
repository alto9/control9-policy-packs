# Off-path cloud audit example

Cloud audit fixtures represent mutations observed without a matching Control9 decision.

**Input envelope:** `packs/production-infra-baseline/fixtures/inputs/cloud-audit/off-path-mutation-envelope.json`

**Resource identity:** `arn:aws:s3:::prod-shared-data`

**Correlation result:** `no-matching-decision`

**Classifier labels:** `off-path-cloud-mutation`

**Matched rule:** `observe-off-path-cloud-mutation` → `observe` (high)

Evidence uses redaction defaults; no credential payloads are stored.

See case `cf-cloud-audit-off-path` in `classifier-cases.json`.
