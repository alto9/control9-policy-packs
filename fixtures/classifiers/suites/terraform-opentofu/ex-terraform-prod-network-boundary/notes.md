# ex-terraform-prod-network-boundary

Security group ingress expanded to the public internet.

**Tool family:** `terraform`

**Resource identity:** `aws_security_group.web`

**Classifier labels:** `security-group-ingress-expanded`

**Matched rule:** `require-approval-prod-network-boundary-change` -> `require_approval` (high)
**Reason:** Production network boundary changes can expose internal systems.
**Risk summary:** Network boundary changes can expose internal systems to broader ingress or routing risk.
