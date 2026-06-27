# Business Logic

Domain behavior and rules that should remain true regardless of UI, deployment, or implementation layout.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- The repo owns versioned baseline packs and semantic classifiers; tenant enablement and configuration live in control9.
- Baseline packs cover IAM expansion, new roles, cross-account access, destructive changes, network boundary changes, production target, secrets exposure hints, unapproved pipeline sources, cost thresholds, deploy verification mismatch, and off-path findings.
- Policies produce allow, deny, require approval, and observe decisions.
- OPA/Rego import or interop is a later enterprise option, not the default contract.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `business_logic/domain_model.md` - Domain Model
- `business_logic/user_stories.md` - User Stories
- `business_logic/error_state.md` - Error States
- `business_logic/error_handling.md` - Error Handling
