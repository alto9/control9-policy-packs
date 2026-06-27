# Execution Model

This doc describes how the repo executes its main work at runtime.

## Contract

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.

## Open implementation decisions

Implementation-level items not yet fully specified. `/refine-issue` resolves these into timeless contract prose and removes or collapses bullets when done.

### Control9 project plan
- Define local fixture runner behavior, classifier execution order, deterministic sorting, compatibility checks, and SaaS pack pinning expectations.
