# Interface

Human-facing surfaces, interaction flows, and presentation contracts.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- Policy documents and examples express infrastructure governance meaning in language platform and security teams can review.
- Decision reasons work in the SaaS UI, GitHub/GitLab feedback, and evidence exports.
- Docs distinguish built-in, recommended, custom, enterprise, and managed-control concepts without storing tenant config here.
- Fixture reports should make classifier behavior understandable during review.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `interface/input_handling.md` - Input Handling
- `interface/presentation.md` - Presentation
- `interface/interaction_flow.md` - Interaction Flow
- `interface/accessibility.md` - Accessibility
