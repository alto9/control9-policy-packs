# ex-cdk-dev-low-risk

Negative control: CDK synthesized template with a low-risk development S3 bucket create.

**Tool family:** `cdk`

**Resource identity:** `DevLogsBucket`

**Classifier labels:** `resource-create`

**Matched rule:** `allow-low-risk-dev-iac` -> `allow` (low)

Unrelated development creates must not match high-risk production classifier labels.
