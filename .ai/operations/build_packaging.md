# Build And Packaging

This doc describes how artifacts are produced, versioned, reviewed, or packaged.

## Contract

- Policy-pack releases are pinned, auditable, and compatible with SaaS policy-engine versions.
- CI runs fixture coverage for classifier and rule behavior.
- Policy-pack releases use semantic versions. Patch versions carry compatible policy fixes, minor versions add compatible baseline coverage or metadata, and major versions signal compatibility-breaking manifest, artifact, or evaluation changes.
- Release artifacts include manifest metadata, readable policy documents, compiled policy artifacts when present, fixture suites, fixture reports, provenance, and compatibility metadata.
- CI expectations include manifest validation, fixture coverage for classifier and rule behavior, deterministic output checks, docs/example checks, and verification that compiled artifacts match their source policy documents.
- Deprecation rules identify affected pack versions, replacement versions, compatibility constraints, and the point at which control9 should stop accepting a deprecated pack for new pins.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2. Exact CI command names are implementation details and must be documented when introduced.
