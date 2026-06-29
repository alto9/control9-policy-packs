# ex-shadow-enforce-prod-destructive-deny

Destructive production database delete without break-glass. Shared semantic classification and policy result must match in shadow and enforce modes.

**Tool family:** `terraform`

**Pinned pack version:** `0.1.0`

**Resource identity:** `aws_rds_cluster.legacy`

**Classifier labels:** `database-delete`

**Matched rule:** `deny-prod-destructive-change` -> `deny` (critical)

**Mode response difference:** Shadow mode reports the deny decision without blocking the workflow. Enforce mode blocks the workflow with the same policy reason.
