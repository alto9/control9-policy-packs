# ex-shadow-enforce-dev-allow

Low-risk development resource create. Shared semantic classification and policy result must match in shadow and enforce modes.

**Tool family:** `terraform`

**Pinned pack version:** `0.1.0`

**Resource identity:** `aws_s3_bucket.dev_logs`

**Classifier labels:** `resource-create`

**Matched rule:** `allow-low-risk-dev-iac` -> `allow` (low)

**Mode response difference:** Both modes allow the change without blocking the workflow. Response summaries match because allow decisions do not add shadow-mode suffix text.
