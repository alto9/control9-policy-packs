# Error Handling

This doc describes how the domain responds when a product-level state cannot continue normally.

## Contract

- The repo owns versioned baseline packs and semantic classifiers; tenant enablement and configuration live in control9.
- Baseline packs cover IAM expansion, new roles, cross-account access, destructive changes, network boundary changes, production target, secrets exposure hints, unapproved pipeline sources, cost thresholds, deploy verification mismatch, and off-path findings.
