# ex-cdk-prod-new-role

CDK synthesized template with a new IAM role logical resource in production.

**Tool family:** `cdk`

**Resource identity:** `BatchWorkerRole`

**Classifier labels:** `new-role`

**Matched rule:** `require-approval-prod-new-role` → `require_approval` (high)

**Reason:** New or materially changed production roles change who can act in the account.

**Risk summary:** Introduces or changes production role identities and trust relationships.

This bootstrap fixture proves the shared layout. Full CDK and CloudFormation coverage lands in issue #15.
