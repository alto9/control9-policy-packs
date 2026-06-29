# ex-cdk-prod-iam-expansion

CDK synthesized template where an inline IAM policy expands S3 actions from read-only to full access in production.

**Tool family:** `cdk`

**Resource identity:** `AppRolePolicy`

**Classifier labels:** `iam-policy-expanded`

**Matched rule:** `require-approval-prod-iam-expansion` -> `require_approval` (high)

**Reason:** Production IAM expansion increases authority and needs human review.

**Risk summary:** Expands who can perform actions in the account and increases privilege escalation risk.
