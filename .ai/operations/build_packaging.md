# Build And Packaging

This doc describes how artifacts are produced, versioned, reviewed, or packaged.

## Contract

- Policy-pack releases are pinned, auditable, and compatible with SaaS policy-engine versions.
- CI runs fixture coverage for classifier and rule behavior.
- Policy-pack releases use semantic versions. Patch versions carry compatible policy fixes, minor versions add compatible baseline coverage or metadata, and major versions signal compatibility-breaking manifest, artifact, or evaluation changes.
- Release artifacts include manifest metadata, readable policy documents, compiled policy artifacts when present, fixture suites, fixture reports, provenance, and compatibility metadata.
- CI expectations include manifest validation, fixture coverage for classifier and rule behavior, deterministic output checks, docs/example checks, and verification that compiled artifacts match their source policy documents.
- Classifier fixture CI fails when a supported CDK/CloudFormation or Terraform/OpenTofu fixture produces unexpected semantic labels, matched rule IDs, decision metadata, evidence references, parser limitation metadata, or nondeterministic ordering.
- Shadow/enforce fixture CI fails when the same input envelope produces different shared semantic classification or policy result fields across modes, while allowing only mode-specific response metadata to differ.
- New classifier fixture categories include a local runner command and reviewer-readable fixture report output before they are treated as release-ready pack content.
- Deprecation rules identify affected pack versions, replacement versions, compatibility constraints, and the point at which control9 should stop accepting a deprecated pack for new pins.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2. Exact CI command names are implementation details and must be documented when introduced.
