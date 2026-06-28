# Domain Model

This doc names the core concepts and ownership boundaries for the domain.

## Contract

- The repo owns versioned baseline packs and semantic classifiers; tenant enablement and configuration live in control9.
- Baseline packs cover IAM expansion, new roles, cross-account access, destructive changes, network boundary changes, production target, secrets exposure hints, unapproved pipeline sources, cost thresholds, deploy verification mismatch, and off-path findings.
- The built-in MVP baseline pack is `production-infra-baseline`.
- Baseline rule categories use stable rule IDs and map each matched condition to one Control9 product decision: `allow`, `deny`, `require_approval`, or `observe`.
- Severity and risk levels describe product impact rather than parser internals. Destructive production changes deny by default unless a break-glass or exception signal is present; IAM expansion, new roles, cross-account access, network boundary changes, cost threshold breaches, secrets exposure hints, unapproved pipeline sources, and deploy verification mismatches require approval or observation according to documented risk.
- Explainable policy decisions identify the policy pack name and version, matched rule ID, decision effect, severity or risk, human-readable reason, risk summary, relevant change types, matched classifier labels, and evidence or fixture references needed to reproduce why the decision fired.
- Off-path cloud mutations are observed as high-severity findings so the SaaS evidence timeline can surface them without implying the integration evaluated a live policy pack locally.
- High-level exception semantics belong in reusable pack content, but tenant-specific enablement, approver groups, overrides, and configuration belong in control9.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack decision semantics. Tenant configuration boundaries are tracked outside this contract.
