# ex-terraform-secrets-hint

Secret material hint in plan output uses redacted placeholder only.

**Tool family:** `terraform`

**Resource identity:** `aws_secretsmanager_secret_version.app`

**Classifier labels:** `secret-value-in-plan`

**Matched rule:** `require-approval-secrets-exposure-hint` -> `require_approval` (high)
**Reason:** Possible secret material appeared in plan, template, diff, or command output.
**Risk summary:** Possible secret material in artifacts; review before proceed to avoid credential leakage.
