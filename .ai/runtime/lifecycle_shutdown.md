# Lifecycle And Shutdown

This doc describes cancellation, completion, rerun, retry, cleanup, and terminal-state behavior.

## Contract

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.

## Open implementation decisions

Implementation-level items not yet fully specified. `/refine-issue` resolves these into timeless contract prose and removes or collapses bullets when done.

### Control9 project plan
- Specify how policy evaluation handles unknown resource types, partial summaries, parser errors, and unsupported IaC tools.
