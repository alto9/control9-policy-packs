# Execution Model

This doc describes how the repo executes its main work at runtime.

## Contract

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.
- Local fixture execution loads a pinned pack version, validates manifest compatibility, runs semantic classifiers, evaluates baseline rules, and emits deterministic matched classifier labels and rule IDs.
- Manifest compatibility validation fails closed when required compatibility metadata is missing, malformed, outside the SaaS policy-engine version range under test, or points at missing artifact or fixture references.
- Fixture and live evaluation results emit the same explainable decision content: pack version, matched rule, product decision, severity or risk, reason, risk summary, relevant change types, evidence references, and fixture identity when applicable.
- Shadow-mode and enforce-mode fixture pairs reuse the same input envelope, pack version, classifier execution, and baseline policy evaluation. Their matched classifier labels, matched rule IDs, product decision, severity or risk, reason, risk summary, relevant change types, evidence references, parser limitations, and deterministic ordering must match; only the product response surface may differ between observing a result and acting on it.
- Classifier execution order is stable across runs. Output sorting is deterministic by severity or risk, decision effect, rule ID, classifier label, and resource identity so fixture reports do not flap.
- SaaS evaluation pins an explicit policy-pack version and rejects incompatible pack metadata instead of silently falling back to another version.
- Fixture expectations cover supported CDK/CloudFormation and Terraform/OpenTofu inputs, deploy verification fingerprints, unapproved pipeline sources, secrets hints, cost threshold signals, and off-path cloud audit findings.
- CDK/CloudFormation classifier fixtures cover synthesized template input, template or stack diff input, stack or template identity, logical resource identity, resource actions, IAM policy expansion, new role and cross-account principal signals, destructive operations, network boundary changes, template fingerprints, and parser limitations when present.
- Terraform/OpenTofu classifier fixtures cover plan JSON input, workspace or environment identity, resource address, provider metadata, action sequence, IAM and network deltas, destructive operations, secrets exposure hints, cost threshold signals, plan fingerprints, and parser limitations when present.
- Fixture cases are organized by supported tool family and semantic classifier label. Each fixture declares the input envelope, expected classifier labels, expected rule or decision metadata, and fixture identity needed to reproduce the result.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack execution. Exact runner command names are implementation details, but any introduced runner must document and preserve the behavior above.
