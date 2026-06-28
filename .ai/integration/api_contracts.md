# API Contracts

This doc describes service boundaries and request or response responsibilities without exact endpoint names.

## Contract

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.
- The pack consumption boundary is manifest-driven: control9 selects a pinned pack version, checks SaaS policy-engine compatibility metadata, loads referenced policy artifacts, and evaluates fixtures or live envelopes against that version.
- Fixture runner expectations are part of the pack contract. Runner output includes pack version, compatibility result, matched classifier labels, matched rule IDs, decision effect, severity or risk level, reason, and fixture identity.
- Release metadata must be sufficient for control9 to reject incompatible packs and for evidence records to identify the policy content used for a decision.
- This repo defines the reusable decision evidence content consumed by control9: pack identity and version, matched rule metadata, matched classifier labels, decision effect, severity or risk, reason, risk summary, relevant change types, evidence references, fixture references, and parser limitations when present.
- The complete SaaS API response envelope, tenant configuration, approval routing, and customer-specific override state remain owned by control9.

## Open implementation decisions

No unresolved implementation decisions remain here for the policy-pack consumption boundary.
