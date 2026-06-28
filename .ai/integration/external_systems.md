# External Systems

This doc describes external systems and the direction of responsibility at each boundary.

## Contract

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.
- OPA/Rego import or export is not part of the MVP baseline pack contract.
- Future OPA/Rego interop, if added, must sit at an explicit import/export boundary and must not replace the repository's readable baseline policy documents, manifests, compiled artifacts, and fixtures.
- External CI systems and public integrations continue to exchange signed summaries, fingerprints, and decision results through control9 rather than evaluating this repository's full pack content locally.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2.
