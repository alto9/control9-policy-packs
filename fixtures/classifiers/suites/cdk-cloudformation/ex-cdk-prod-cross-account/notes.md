# ex-cdk-prod-cross-account

CDK synthesized template adding a cross-account principal to an S3 bucket policy in production.

**Tool family:** `cdk`

**Resource identity:** `SharedDataBucketPolicy`

**Classifier labels:** `cross-account-access`

**Matched rule:** `require-approval-prod-cross-account-access` -> `require_approval` (critical)

**Reason:** Cross-account access expands blast radius across account boundaries.

**Risk summary:** Grants cross-account access and expands blast radius beyond a single account boundary.
