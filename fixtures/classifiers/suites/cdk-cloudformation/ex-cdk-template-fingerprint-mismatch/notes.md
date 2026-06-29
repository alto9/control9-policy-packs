# ex-cdk-template-fingerprint-mismatch

CDK deploy where the approved template fingerprint differs from the current synthesized artifact.

**Tool family:** `cdk`

**Resource identity:** `ProdAppBucket`

**Classifier labels:** `plan-fingerprint-mismatch`, `resource-update`

**Matched rules:** deploy verification mismatch (high) and production mutation (medium).

Template fingerprint drift must route to deploy verification before apply proceeds.
