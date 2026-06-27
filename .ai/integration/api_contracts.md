# API Contracts

This doc describes service boundaries and request or response responsibilities without exact endpoint names.

## Contract

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.

## Open implementation decisions

Implementation-level items not yet fully specified. `/refine-issue` resolves these into timeless contract prose and removes or collapses bullets when done.

### Control9 project plan
- Define pack consumption boundary, compatibility checks, fixture runner expectations, and release metadata.
- Specify how policy reasons, matched rule IDs, classifier labels, and severity map into SaaS decision responses.
