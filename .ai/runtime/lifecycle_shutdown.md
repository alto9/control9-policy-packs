# Lifecycle And Shutdown

This doc describes cancellation, completion, rerun, retry, cleanup, and terminal-state behavior.

## Contract

- Packs execute through tests and the SaaS policy engine, not the public integration.
- The same input envelope produces the same policy result in fixture tests and live evaluation.
- Unknown resource types, partial summaries, parser errors, and unsupported IaC tools do not produce invented allow/deny conclusions.
- Unsupported or partial inputs produce deterministic classifier limitations that can lead to `observe` or `require_approval` when the baseline pack treats uncertainty as risk.
- Parser errors are represented as evaluation errors or limitation findings with redacted context; they do not expose raw secrets or unbounded source payloads.
- Fixture runs treat unsupported and partial input cases as first-class coverage so live evaluation and local tests agree on terminal behavior.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2.
