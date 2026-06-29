# ex-terraform-deploy-fingerprint-mismatch

Approved plan fingerprint differs from current artifact fingerprint.

**Tool family:** `terraform`

**Resource identity:** `aws_s3_bucket.prod_app`

**Classifier labels:** `plan-fingerprint-mismatch`, `resource-update`

**Matched rule:** `require-approval-deploy-verification-mismatch` -> `require_approval` (high)
**Reason:** Deploy artifact or plan fingerprint changed after the prior approval.
**Risk summary:** Approved artifact no longer matches the deploy target; possible tampering or drift.
**Matched rule:** `require-approval-prod-mutation` -> `require_approval` (medium)
**Reason:** Production infrastructure mutation changes live systems and needs human review.
**Risk summary:** Changes live production resources; a mistaken apply could cause outage or data loss.
