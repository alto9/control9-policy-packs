# ex-terraform-prod-iam-expansion

Expanded IAM inline policy actions in production.

**Tool family:** `terraform`

**Resource identity:** `aws_iam_role_policy.prod_app`

**Classifier labels:** `iam-policy-expanded`

**Matched rule:** `require-approval-prod-iam-expansion` -> `require_approval` (high)
**Reason:** Production IAM expansion increases authority and needs human review.
**Risk summary:** Expands who can perform actions in the account and increases privilege escalation risk.
