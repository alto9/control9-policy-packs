# Data Model

This doc describes durable and transient data concepts without freezing physical table or field names.

## Contract

- Pack data includes readable policy documents, compiled artifacts, classifier metadata, fixture examples, version manifests, and compatibility metadata.
- Every decision carries enough policy metadata to explain the pack version, matched rule, risk summary, reason, and fixture coverage.
- A pack manifest represents pack identity, semantic version, release status, SaaS policy-engine compatibility range, policy document references, compiled artifact references, fixture suite references, and provenance.
- Manifest data is reusable product content. It does not store tenant enablement, tenant overrides, customer approver groups, or customer-specific exception settings.
- Baseline examples are organized around supported inputs and policy meanings: CDK/CloudFormation, Terraform/OpenTofu, pipeline metadata, deploy fingerprints, and cloud audit/off-path signals.
- Version rules distinguish ordinary baseline evolution, patch-level urgent policy fixes, compatibility-breaking changes, and deprecations.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2. Exact physical file names can be chosen during implementation if they preserve the manifest responsibilities above.
