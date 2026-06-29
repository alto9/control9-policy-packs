# Terraform production IAM expansion example

This example shows how a Terraform plan JSON fragment maps to baseline classifier labels.

**Input artifact:** `packs/production-infra-baseline/fixtures/inputs/terraform/prod-iam-expansion-plan.json`

**Envelope context:** production workspace `prod`, tool `terraform`

**Resource identity:** `aws_iam_role_policy.prod_app`

**Classifier labels:** `iam-policy-expanded`

**Matched rule:** `require-approval-prod-iam-expansion` → `require_approval` (high)

See the machine-readable case `cf-terraform-prod-iam-expansion` in `classifier-cases.json`.
