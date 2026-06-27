# External Systems

This doc describes external systems and the direction of responsibility at each boundary.

## Contract

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.

## Open implementation decisions

Implementation-level items not yet fully specified. `/refine-issue` resolves these into timeless contract prose and removes or collapses bullets when done.

### Control9 project plan
- Describe optional future import/export boundaries for OPA/Rego without making them MVP requirements.
