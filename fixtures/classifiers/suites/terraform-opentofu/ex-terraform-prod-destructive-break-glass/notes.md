# ex-terraform-prod-destructive-break-glass

Same destructive change with break-glass routes to approval.

**Tool family:** `terraform`

**Resource identity:** `aws_rds_cluster.legacy`

**Classifier labels:** `database-delete`

**Matched rule:** `require-approval-prod-destructive-break-glass` -> `require_approval` (critical)
**Reason:** Destructive production change submitted under break-glass requires explicit approval.
**Risk summary:** Destructive production change under break-glass still needs explicit human approval before proceed.
