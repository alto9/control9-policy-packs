# Operations

Build, deployment, observability, and security contracts.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- Policy-pack releases are pinned, auditable, and compatible with SaaS policy-engine versions.
- CI runs fixture coverage for classifier and rule behavior.
- Public reviewability is valuable because policy decisions affect production deploy authority.
- Urgent policy fixes need a rollout path that respects tenant pinning and SaaS compatibility.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `operations/build_packaging.md` - Build And Packaging
- `operations/deployment_environments.md` - Deployment Environments
- `operations/observability.md` - Observability
- `operations/security.md` - Security
