# Presentation

This doc describes how information is presented and distinguished for users.

## Contract

- Policy documents and examples express infrastructure governance meaning in language platform and security teams can review.
- Decision reasons work in the SaaS UI, GitHub/GitLab feedback, and evidence exports.
- Policy documents use stable rule IDs, short titles, supported input scope, decision effect, severity or risk, readable reason text, evidence expectations, and fixture references.
- Reason text explains the infrastructure governance risk in plain language and avoids exposing raw secret values, excessive payload fragments, or parser-only jargon.
- Risk summaries are short, action-oriented statements that name the policy concern and expected reviewer attention without requiring readers to inspect raw IaC or audit payloads first.
- Decision presentation must expose pack version, matched rule ID, decision effect, severity or risk, relevant change types, reason, and risk summary as text fields suitable for the SaaS UI, GitHub/GitLab feedback, fixture reports, and evidence exports.
- Examples are grouped by policy meaning and supported tool family so reviewers can trace a baseline risk from input summary to classifier label, matched rule, and expected decision.
- Fixture reports should be readable as review artifacts: they include pack version, fixture identity, matched rules, classifier labels, decision effect, severity or risk, and pass/fail status.
- Managed-control pack documentation is generated or maintained from the same source concepts used by manifests and fixtures so docs do not drift from released policy content.

## Open implementation decisions

No unresolved implementation decisions remain here for baseline pack presentation. Exact docs generation commands can be chosen during implementation if they preserve the presentation contract above.
