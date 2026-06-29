# ex-opentofu-prod-mutation

OpenTofu production create follows the same mutation semantics as Terraform.

**Tool family:** `opentofu`

**Resource identity:** `aws_dynamodb_table.sessions`

**Classifier labels:** `resource-create`

**Matched rule:** `require-approval-prod-mutation` → `require_approval` (medium)

**Reason:** Production infrastructure mutation changes live systems and needs human review.

**Risk summary:** Changes live production resources; a mistaken apply could cause outage or data loss.
