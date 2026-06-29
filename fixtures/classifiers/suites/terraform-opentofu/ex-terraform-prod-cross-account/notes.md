# ex-terraform-prod-cross-account

Cross-account principal added to a bucket policy.

**Tool family:** `terraform`

**Resource identity:** `aws_s3_bucket_policy.shared_data`

**Classifier labels:** `cross-account-access`

**Matched rule:** `require-approval-prod-cross-account-access` -> `require_approval` (critical)
**Reason:** Cross-account access expands blast radius across account boundaries.
**Risk summary:** Grants cross-account access and expands blast radius beyond a single account boundary.
