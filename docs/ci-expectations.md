# CI expectations

Continuous integration for `control9-policy-packs` proves that baseline packs are structurally valid, fixture-complete, deterministic, and documented before merge.

CI runs on pull requests and on pushes to `main`. The workflow lives at [`.github/workflows/ci.yml`](../.github/workflows/ci.yml).

## Required checks

| Check | Command | What it proves |
|-------|---------|----------------|
| Pack manifest validation | `python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json` | Manifest schema, semver, release status, compatibility metadata, artifact paths, SHA-256 digests, and absence of tenant-specific fields |
| Classifier fixture validation | `python3 scripts/validate-classifier-fixtures.py` | Fixture structure, baseline rule coverage, edge-case coverage, deterministic ordering, JSON validity, and forbidden secret patterns |
| Shared classifier suite runner | `./scripts/run-fixtures.sh --all` | Shared `fixtures/classifiers/` layout, expected result shape, suite manifests, deterministic ordering, and cross-file consistency |
| Compatibility metadata suite runner | `./scripts/run-fixtures.sh --suite compatibility-metadata` | Manifest compatibility acceptance and fail-closed rejection cases with pack version and clear failure reasons in reports |
| Decision record validation | `python3 scripts/validate-decision-records.py` | Policy rules include reason and risk summary, fixture expectations match policy metadata, golden decision records stay in sync, and decision output excludes tenant-specific fields |
| Docs and examples validation | `python3 scripts/validate-docs-examples.py` | Required documentation exists, example manifests validate, and reviewer example paths referenced by docs are present |
| Whitespace hygiene | `git diff --check` | No trailing whitespace or conflict markers in the diff |

The orchestration script runs all Python checks plus whitespace hygiene:

```bash
./scripts/validate-policy-pack.sh
```

## Manifest validation

Manifest validation fails release readiness when:

- `compatibility.policyEngine.semverRange` is missing or malformed
- The running policy-engine version falls outside `compatibility.policyEngine.semverRange` when `--policy-engine-version` is supplied
- Referenced policy documents, compiled artifacts, or fixture suites are missing
- Declared `sha256:` digests do not match file contents
- Tenant-specific fields appear in the manifest
- `releaseStatus: replaced` lacks a `deprecation.replacement` block

See [`pack-versioning.md`](pack-versioning.md) and [`release-process.md`](release-process.md) for semver and release-status rules.

## Classifier and rule fixture coverage

Classifier fixture CI enforces:

- Every baseline rule ID in `production-infra-baseline` appears in at least one fixture case
- Required edge situations (`unknown-resource-type`, `parser-error`, `unsupported-tool`, `partial-summary`) are documented
- `expected.classifierLabels` and `expected.matchedRules` use deterministic sort order
- Input envelope and artifact paths resolve to files under the pack fixtures tree
- Fixtures do not contain live credentials or private key material

When live classifiers are implemented, CI will extend to compare classifier output against fixture expectations. Until then, the fixture contract is the source of truth for expected semantic labels, matched rule IDs, decision metadata, reason, risk summary, evidence references, and ordering.

## Decision record validation

Decision record CI enforces:

- Every baseline rule in the policy YAML defines `reason`, `riskSummary`, and applicable `changeTypes`
- Each classifier fixture case declares expected `reason`, `riskSummary`, `changeTypes`, and case-level `evidenceReferences` on matched rules
- Golden records under `fixtures/expected-decisions/` match the policy document and fixture inputs
- Reason and risk summary text do not contain live credential patterns
- Decision records do not include tenant enablement, approver groups, or customer override state

See [`decision-records.md`](decision-records.md) for the schema and redaction expectations.

Generate or refresh golden decision records locally:

```bash
python3 scripts/validate-decision-records.py --sync-fixtures --write-expected
python3 scripts/validate-decision-records.py
```

Generate a reviewer-readable fixture report locally:

```bash
python3 scripts/validate-classifier-fixtures.py --report
python3 scripts/validate-classifier-fixtures.py --report --output /tmp/classifier-fixture-report.md
```

## Deterministic output checks

Determinism requirements:

- Matched rules sort by severity rank, decision rank, `ruleId`, `classifierLabel`, then `resourceIdentity` (all ascending)
- Classifier labels sort lexicographically
- The same input envelope must produce the same shared semantic fields in shadow and enforce evaluation; only mode-specific response metadata may differ (enforced by control9 integration tests when classifiers ship)

The classifier fixture validator enforces ordering on expected outputs today. Nondeterministic ordering in new fixtures fails CI.

## Docs and example checks

Docs validation confirms:

- Core documentation files exist (`docs/release-process.md`, `docs/ci-expectations.md`, `docs/policy-authoring.md`, and sibling guides)
- The reviewer example manifest under `examples/manifests/` validates against the pack manifest rules
- Classifier example directories referenced in `examples/classifiers/README.md` exist
- Key README links resolve to files in the repository

Contributors should update docs when adding fixture categories, changing release rules, or introducing new example paths.

## Local workflow before opening a PR

From the repository root:

```bash
./scripts/validate-policy-pack.sh
python3 scripts/validate-classifier-fixtures.py --report
git diff --check
git status --short
```

Expected outcomes:

- All validation commands exit `0`
- Fixture report lists every baseline rule with at least one covering case
- `git diff --check` reports no whitespace errors

## Future CI extensions

These checks are **not** MVP blockers but are documented boundaries for later work:

- Live classifier execution against fixture inputs
- Compiled artifact regeneration and digest verification when compiled policy artifacts ship
- Shadow vs enforce mode parity tests owned jointly with control9
- OPA/Rego import/export validation (optional enterprise boundary; see [`policy-authoring.md`](policy-authoring.md))

## Related documents

- [`release-process.md`](release-process.md)
- [`classifier-fixtures.md`](classifier-fixtures.md)
- [`policy-authoring.md`](policy-authoring.md)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
