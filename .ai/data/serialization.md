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
- Manifest serialization includes pack identity, semantic version, manifest schema version, SaaS policy-engine compatibility range, release status, policy document references, compiled artifact references when present, fixture suite references, artifact digests or fingerprints, deprecation or replacement metadata when applicable, and provenance.
- Compiled artifacts are referenced by manifest metadata and fixture reports. Human-readable examples remain reviewable without requiring readers to inspect compiled output.
- Classifier fixture files separate source input, expected semantic labels, expected policy result metadata, and fixture notes so reviewer-facing examples can stay readable while machine checks remain deterministic.
- Fixture expected output includes enough stable identity to compare CDK/CloudFormation and Terraform/OpenTofu results without depending on parser ordering: fixture ID, tool family, normalized resource identity, matched classifier labels, relevant change types, matched rule IDs when policy evaluation is included, decision effect, severity or risk, reason, risk summary, evidence references, and parser limitations when present.
- Shadow/enforce comparison fixtures serialize the same stable decision fields for each mode and explicitly separate mode-specific response metadata from the shared semantic result, so equality checks can prove the policy result is unchanged while the product response changes.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack serialization.
