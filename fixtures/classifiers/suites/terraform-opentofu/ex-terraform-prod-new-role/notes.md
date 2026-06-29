# ex-terraform-prod-new-role

New production IAM role creation.

**Tool family:** `terraform`

**Resource identity:** `aws_iam_role.batch_worker`

**Classifier labels:** `new-role`

**Matched rule:** `require-approval-prod-new-role` -> `require_approval` (high)
**Reason:** New or materially changed production roles change who can act in the account.
**Risk summary:** Introduces or changes production role identities and trust relationships.
