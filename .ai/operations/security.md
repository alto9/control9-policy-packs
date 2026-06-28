# Security

This doc describes security, privacy, and trust requirements that apply across implementation choices.

## Contract

- Policy-pack releases are pinned, auditable, and compatible with SaaS policy-engine versions.
- CI runs fixture coverage for classifier and rule behavior.
- Public contributions to baseline policy content require reviewer attention to governance meaning, fixture coverage, secret redaction, compatibility metadata, and downstream reason text.
- Contributions that add or change rule effects must include representative fixtures and must not weaken production protections without a clear versioned release note.
- Examples and fixture outputs must redact or synthesize secrets and sensitive customer identifiers.
- Reviewers treat compiled artifacts as generated release assets and verify they match readable source policy content before release.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2.
