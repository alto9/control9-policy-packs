# Runtime

Startup, configuration, execution, and lifecycle contracts.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.
- Shadow and enforce modes use the same classification and policy result.
- Unknown resource types, partial summaries, parser errors, and unsupported tools degrade into explainable outcomes rather than silent success.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `runtime/configuration.md` - Configuration
- `runtime/startup_bootstrap.md` - Startup Bootstrap
- `runtime/lifecycle_shutdown.md` - Lifecycle And Shutdown
- `runtime/execution_model.md` - Execution Model
