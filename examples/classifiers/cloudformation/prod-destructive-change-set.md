# CloudFormation destructive change set example

Change set summaries represent logical resource identity and destructive actions.

**Input artifact:** `packs/production-infra-baseline/fixtures/inputs/cloudformation/prod-destructive-change-set.json`

**Stack identity:** `ProdAppStack`

**Logical resource identity:** `LegacyDatabase` (`AWS::RDS::DBInstance`, action `Remove`)

**Classifier labels:** `resource-destroy`

**Matched rule:** `deny-prod-destructive-change` → `deny` (critical)

See case `cf-cloudformation-prod-destructive` in `classifier-cases.json`.
