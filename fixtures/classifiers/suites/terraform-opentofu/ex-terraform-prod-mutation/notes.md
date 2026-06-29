# ex-terraform-prod-mutation

Production resource update requires approval.

**Tool family:** `terraform`

**Resource identity:** `aws_s3_bucket.prod_app`

**Classifier labels:** `resource-update`

**Matched rule:** `require-approval-prod-mutation` -> `require_approval` (medium)
**Reason:** Production infrastructure mutation changes live systems and needs human review.
**Risk summary:** Changes live production resources; a mistaken apply could cause outage or data loss.
