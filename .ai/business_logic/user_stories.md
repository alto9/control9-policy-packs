# User Stories

This doc captures durable user outcomes and milestone-shaped behavior without issue numbers.

## Contract

- The repo owns versioned baseline packs and semantic classifiers; tenant enablement and configuration live in control9.
- Baseline packs cover IAM expansion, new roles, cross-account access, destructive changes, network boundary changes, production target, secrets exposure hints, unapproved pipeline sources, cost thresholds, deploy verification mismatch, and off-path findings.
- Repeated assessment findings map into enforce-mode recommended controls by matching the same baseline rule categories used by `production-infra-baseline`.
- Assessment-to-enforce recommendations name the baseline rule, risk summary, suggested product decision, fixture evidence, and any SaaS-owned configuration needed before enforcement.
- This repo defines the reusable recommended-control content and fixtures; control9 decides tenant-specific enablement, approval routing, exceptions, and rollout state.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2. Tenant-specific adoption workflow is tracked by issue #4.
