# ex-terraform-prod-destructive-deny

Destructive production database delete without break-glass is denied.

**Tool family:** `terraform`

**Resource identity:** `aws_rds_cluster.legacy`

**Classifier labels:** `database-delete`

**Matched rule:** `deny-prod-destructive-change` -> `deny` (critical)
**Reason:** Destructive production changes require an approved break-glass path.
**Risk summary:** Irreversible or highly disruptive production deletion without an approved break-glass path.
