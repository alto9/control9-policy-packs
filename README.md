# control9-policy-packs

Versioned baseline policy packs and semantic classifiers for Control9.

Control9 is a CI/CD-native governance layer for infrastructure changes. This repository owns the repeatable policy content that turns raw CDK, CloudFormation, Terraform, OpenTofu, pipeline, and cloud audit inputs into decisions a platform team can understand and trust.

The goal is not to expose a bag of low-level rules. The goal is to encode common infrastructure governance meaning: IAM expansion, new roles, cross-account access, destructive production changes, network boundary changes, secrets exposure hints, unapproved pipeline sources, deploy artifact mismatches, and off-path cloud mutations.

## What This Repo Owns

- Baseline policy packs for Control9 shadow mode and enforce mode.
- Semantic classifiers for CDK/CloudFormation and Terraform/OpenTofu changes.
- Friendly policy documents that can be reviewed by platform and security teams.
- Compiled or machine-readable policy artifacts consumed by the Control9 policy engine.
- Rule fixtures that prove decisions are deterministic.
- Examples for production infrastructure governance, approval routing, deploy verification, and off-path detection.
- Version metadata so every Control9 decision can record which policy pack produced it.

## Policy Decisions

Policies should produce one of four product decisions:

- `allow`: the action can proceed.
- `deny`: the action is blocked with a clear reason.
- `require_approval`: the action pauses for an authorized human approval.
- `observe`: the action is recorded as a shadow-mode or detection finding without blocking.

Every decision should include:

- Policy pack name and version.
- Matched rule identifier.
- Decision reason.
- Risk summary.
- Relevant change types.
- Required approver group when approval is needed.
- Evidence retention and redaction defaults where applicable.

## Baseline MVP Pack

The first built-in policy pack should cover common production infrastructure risk:

- Allow low-risk development IaC changes.
- Require approval for production IAM expansion.
- Require approval for new production roles and cross-account access.
- Deny destructive production changes unless an approved break-glass path exists.
- Require approval when an untrusted pipeline source asks for deploy authority.
- Observe direct cloud changes that do not match a Control9 decision.
- Flag secrets exposure hints in plans, templates, diffs, and command summaries.
- Flag deploy verification mismatches when the plan or template fingerprint changed after approval.

## Example Policy Shape

```yaml
apiVersion: alto9.io/v1alpha1
kind: ChangeControlPolicy
metadata:
  name: production-infra-baseline
  owner: platform-engineering
defaults:
  mode: enforce
  evidence:
    retainDays: 365
    redactSecrets: true
    store: alto9-managed

rules:
  - id: allow-low-risk-dev-iac
    when:
      environment: dev
      tools: ["terraform", "opentofu", "cdk"]
      changeRisk: low
    decision: allow
    reason: "Low-risk development infrastructure changes stay fast."

  - id: require-approval-for-prod-iam-expansion
    when:
      environment: production
      changeTypes: ["iam-policy-expanded", "new-role", "cross-account-access"]
    decision: require_approval
    approvers: productionPlatformLeads
    approvalTtl: 4h
    reason: "Production IAM expansion changes authority and needs human review."

  - id: deny-unapproved-prod-destroy
    when:
      environment: production
      changeTypes: ["resource-destroy", "database-delete", "network-boundary-remove"]
      breakGlass: false
    decision: deny
    reason: "Destructive production changes require an approved break-glass path."
```

## Classifier Scope

Classifiers should derive policy-relevant meaning from supported inputs:

- AWS CDK: `cdk synth`, `cdk diff`, synthesized CloudFormation templates, stack metadata, account metadata, and template fingerprints.
- CloudFormation: template diffs, change set summaries, stack events, CloudTrail and CloudFormation update correlation.
- Terraform/OpenTofu: `terraform plan -out`, `terraform show -json`, resource deltas, provider metadata, target workspace, and plan fingerprints.
- Shell deploy steps: command classification, artifact fingerprint, environment metadata, and requested authority when wrapped by GitHub/GitLab pipelines.
- Cloud audit events: CloudTrail, CloudFormation, and deployment events that can be correlated against prior Control9 decisions.

## Design Principles

- Policies express infrastructure governance meaning, not only raw syntax.
- The same input envelope must produce the same decision in tests and production.
- Shadow mode and enforce mode use the same policy logic. Only the product response changes.
- Every decision records enough policy metadata to support audit and evidence search.
- OPA/Rego import is not the default contract. Add it later only if enterprise buyers need it.
- Baseline packs should be boring and reviewable. Platform teams should understand why a rule fired.

## Baseline Rule Catalog

The `production-infra-baseline` pack defines stable rule IDs, product decisions, severities, reason patterns, break-glass semantics, and fixture expectations for every baseline risk area. See:

- Policy document: `packs/production-infra-baseline/policies/production-infra-baseline.yaml`
- Reviewer guide: `docs/baseline-rule-catalog.md`
- Fixture expectation index: `packs/production-infra-baseline/fixtures/suite.json`

## Pack Manifests

Each built-in pack ships a repository-owned manifest under `packs/<pack-name>/manifest.json`. Manifests pin pack identity, semantic version, release status, SaaS policy-engine compatibility, artifact references, and provenance. Tenant enablement, overrides, and customer approver groups stay in control9.

- Schema: `schemas/pack-manifest.v1alpha1.schema.json`
- Versioning rules: `docs/pack-versioning.md`
- MVP pack manifest: `packs/production-infra-baseline/manifest.json`
- Reviewer example: `examples/manifests/production-infra-baseline.v0.1.0.json`

Validate a manifest locally:

```bash
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json
```

## Near-Term Build Priorities

- Expand baseline rule categories and fixtures for `production-infra-baseline`.
- Add fixtures for CDK/CloudFormation and Terraform/OpenTofu classifier output.
- Implement MVP classifiers for IAM expansion, new role, destructive change, network boundary change, production target, secrets exposure hints, and unapproved pipeline source.
- Add deploy verification and off-path detection rules.
- Create shadow-mode assessment mappings so Alto9 can turn repeated customer findings into enforce-mode configuration.

## Related Repositories

- `control9`: SaaS control plane, policy engine, approval workflow, evidence timeline, and admin UI.
- `control9-integrations`: GitHub Action and GitLab CI component that send signed action envelopes to Control9.
- `control9-www`: public marketing site, pricing, assessment CTA, and docs links.
