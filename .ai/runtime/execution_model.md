# Execution Model

This doc describes how the repo executes its main work at runtime.

## Contract

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.
- Local fixture execution loads a pinned pack version, validates manifest compatibility, runs semantic classifiers, evaluates baseline rules, and emits deterministic matched classifier labels and rule IDs.
- Fixture and live evaluation results emit the same explainable decision content: pack version, matched rule, product decision, severity or risk, reason, risk summary, relevant change types, evidence references, and fixture identity when applicable.
- Classifier execution order is stable across runs. Output sorting is deterministic by severity or risk, decision effect, rule ID, classifier label, and resource identity so fixture reports do not flap.
- SaaS evaluation pins an explicit policy-pack version and rejects incompatible pack metadata instead of silently falling back to another version.
- Fixture expectations cover supported CDK/CloudFormation and Terraform/OpenTofu inputs, deploy verification fingerprints, unapproved pipeline sources, secrets hints, cost threshold signals, and off-path cloud audit findings.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack execution. Exact runner command names are implementation details, but any introduced runner must document and preserve the behavior above.
