# Policy authoring and documentation style

This document defines how readable policy documents, reason text, fixture reports, and generated documentation should read for platform teams, security reviewers, and downstream Control9 surfaces.

## Policy document shape

Baseline packs use the `ChangeControlPolicy` document under `packs/<pack-name>/policies/`. The authoritative example is `packs/production-infra-baseline/policies/production-infra-baseline.yaml`.

Each rule entry must include:

| Field | Purpose |
|-------|---------|
| `id` | Stable rule identifier referenced by fixtures, evidence, and SaaS UI |
| `category` | Risk grouping for catalogs and exports |
| `decision` | Product effect: `allow`, `deny`, `require_approval`, or `observe` |
| `severity` | Human-facing risk level |
| `riskSummary` | Plain-language risk summary for reviewers and evidence exports |
| `when` | Declarative conditions (environment, tool, change types, break-glass signals) |
| `reason` | Default sentence shown to humans |
| `reasonPattern` | Optional template with `{placeholders}` filled from classifier output |

Keep policy documents **boring and reviewable**. A platform engineer should understand why a rule fires without reading parser code.

## Reason and risk summary readability

Reason and risk summary text appear in:

- Control9 SaaS decision and evidence views
- GitHub and GitLab integration feedback
- Evidence exports and audit timelines
- Fixture reports and golden decision records

Guidelines:

1. Write complete sentences in plain language. Prefer "Production IAM expansion increases authority and needs human review." over internal label names.
2. Use `riskSummary` to explain the underlying risk in reviewer-friendly terms without repeating the full reason sentence.
3. Use `reasonPattern` when the sentence should include dynamic context (`{changeTypes}`, `{environment}`, `{tool}`).
4. Do **not** embed raw secret values, credentials, access keys, or full resource payloads in reasons or risk summaries.
5. Do **not** reference parser internals, stack traces, or unstable resource addresses unless they add necessary context for approval.
6. Keep deny and require-approval reasons actionable: state what changed and what the operator must do next.

See also [`decision-records.md`](decision-records.md) and the reason text section in [`baseline-rule-catalog.md`](baseline-rule-catalog.md).

## Fixture report output

Classifier fixtures prove expected labels, matched rules, decisions, and ordering. Reviewers should be able to scan coverage without opening every JSON file.

Generate a fixture report after local validation:

```bash
python3 scripts/validate-classifier-fixtures.py --report
```

The report includes:

- Total case count and edge-case coverage
- A table mapping each baseline rule ID to covering fixture case IDs
- Edge situations and their fixture case IDs
- A reminder that live classifier execution is not yet part of CI

Treat the report as a release-readiness artifact alongside the manifest digest check. New classifier categories must appear in the report before the pack version moves toward `released`.

## Generated and hand-written documentation

This repository uses hand-maintained Markdown under `docs/` and reviewer examples under `examples/`. There is no required doc generator for MVP releases.

When adding documentation:

- Prefer stable links to pack paths (`packs/...`, `examples/...`) over issue numbers.
- Update [`README.md`](../README.md) when introducing a new guide or validation command.
- Keep catalog tables in sync with the policy YAML and `fixtures/suite.json`.
- Mirror complex fixture behavior in `examples/classifiers/` with short narratives, not only JSON.

If a future docs generator is added, it must:

- Read from the policy YAML and fixture indexes as source of truth
- Fail CI when generated output drifts from source files
- Not replace the human-readable rule catalog without an explicit migration

## OPA/Rego boundary (future optional)

**OPA/Rego import and export is not part of the MVP product contract.**

- Baseline packs are authored as readable `ChangeControlPolicy` YAML plus machine-checkable fixtures.
- control9 evaluates packs through its policy engine; this repository does not ship Rego modules as the default artifact type.
- Enterprise buyers may request OPA/Rego interchange later. If added, it will be an **optional** import/export boundary with its own schema version, validation command, and compatibility metadata. It will not replace the YAML + fixture contract for baseline packs unless explicitly migrated.

Until that optional boundary exists:

- Do not add Rego sources to MVP manifests as required artifacts.
- Do not document OPA as the primary authoring path in contribution guides.
- Mention OPA/Rego only as a future integration option, as in [`README.md`](../README.md) design principles.

## Related documents

- [`baseline-rule-catalog.md`](baseline-rule-catalog.md)
- [`classifier-fixtures.md`](classifier-fixtures.md)
- [`release-process.md`](release-process.md)
- [`ci-expectations.md`](ci-expectations.md)
- [`decision-records.md`](decision-records.md)
