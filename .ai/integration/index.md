# Integration

External service, API, authorization, and asynchronous boundary contracts.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.
- Pack outputs are explainable enough for the SaaS UI, CI summaries, and evidence timeline records.
- Future OPA/Rego boundaries should remain optional and not expand the MVP surface.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `integration/api_contracts.md` - API Contracts
- `integration/hosted_ai_inference.md` - Hosted AI Inference
- `integration/external_systems.md` - External Systems
- `integration/messaging_async.md` - Messaging And Async
- `integration/authorization.md` - Authorization
