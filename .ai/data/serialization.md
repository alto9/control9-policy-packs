# Serialization

This doc describes boundary shapes, redaction expectations, fingerprints, summaries, and exported representations at a product level.

## Contract

- Pack data includes readable policy documents, compiled artifacts, classifier metadata, fixture examples, version manifests, and compatibility metadata.
- Every decision carries enough policy metadata to explain the pack version, matched rule, risk summary, reason, and fixture coverage.
- CDK/CloudFormation examples represent stack or template identity, logical resource identity, resource action, IAM policy deltas, new roles, cross-account principals, destructive operations, network boundary changes, template fingerprints, and parser limitations when present.
- Terraform/OpenTofu examples represent workspace or environment identity, resource address, provider metadata, action sequence, IAM and network deltas, destructive operations, secrets exposure hints, cost threshold signals, plan fingerprints, and parser limitations when present.
- Pipeline and deploy examples represent source authority, artifact or plan fingerprints, requested deploy authority, approval relationship, and deploy verification mismatch signals.
- Cloud audit/off-path examples represent observed event source, cloud resource identity, actor or principal summary, event time, correlation result, and evidence redaction defaults.
- Decision output serializes the pack name, pack semantic version, matched rule ID, matched classifier labels, product decision, severity or risk, reason, risk summary, relevant change types, evidence references, fixture identity when applicable, and parser limitations when they affect the result.
- Decision output does not serialize raw secret values, excessive template or plan fragments, tenant-specific approver configuration, or customer override state.
- Compiled artifacts are referenced by manifest metadata and fixture reports. Human-readable examples remain reviewable without requiring readers to inspect compiled output.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack serialization.
