# Data

Product data ownership, persistence, serialization, and consistency contracts.

## Repo role

Versioned baseline policy packs and semantic classifiers for Control9. It owns explainable policy content, fixtures, compatibility metadata, and classifier behavior consumed by the SaaS policy engine.

## Contract stance

- Pack data includes readable policy documents, compiled artifacts, classifier metadata, fixture examples, version manifests, and compatibility metadata.
- Every decision carries enough policy metadata to explain the pack version, matched rule, risk summary, reason, and fixture coverage.
- Classifier inputs align with summaries and fingerprints from control9-integrations.
- Tenant-specific durable policy state stays in control9.

## Initiative constraints

- Baseline packs cover common production infrastructure risk across CDK/CloudFormation and Terraform/OpenTofu.
- Tenant-specific durable policy state belongs in control9, not this public policy-pack repo.
- Shadow and enforce modes use the same semantic classification and policy result; only the product response changes.

## Mapped child docs

- `data/data_model.md` - Data Model
- `data/persistence_abstractions.md` - Persistence Abstractions
- `data/serialization.md` - Serialization
- `data/consistency.md` - Consistency
