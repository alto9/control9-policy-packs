# Contributing to control9-policy-packs

Thank you for helping improve Control9 baseline policy packs. This repository is public-facing policy content: manifests, readable policy documents, fixtures, and reviewer examples that the Control9 SaaS policy engine loads at pinned versions.

## Before you start

1. Read [`README.md`](README.md) for repository scope and design principles.
2. Read [`docs/release-process.md`](docs/release-process.md) and [`docs/pack-versioning.md`](docs/pack-versioning.md) for semver and release rules.
3. Read [`docs/policy-authoring.md`](docs/policy-authoring.md) for reason text and documentation style.
4. Open or claim a GitHub issue before large changes so maintainers can confirm scope.

Tenant enablement, approver groups, and customer overrides belong in [control9](https://github.com/alto9/control9), not in pack manifests or policy YAML here.

## Development setup

Prerequisites:

- Git
- Python 3.9+ (stdlib only for validation scripts)

Clone the repository and run local validation from the root:

```bash
git clone https://github.com/alto9/control9-policy-packs.git
cd control9-policy-packs
./scripts/validate-policy-pack.sh
```

## Making changes

Typical change types:

| Change | What to update |
|--------|----------------|
| New or updated baseline rule | Policy YAML, `fixtures/suite.json`, classifier fixtures, `docs/baseline-rule-catalog.md`, examples |
| New classifier fixture category | `classifier-cases.json`, input files, `examples/classifiers/`, `docs/classifier-fixtures.md` |
| Pack version or release metadata | `manifest.json` digests, `docs/pack-versioning.md` if rules change, release notes in PR |
| Documentation only | Relevant `docs/` file and README links |

Always refresh manifest artifact digests when referenced files change:

```bash
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json
```

The validator reports digest mismatches with the expected `sha256:` value.

## Pull request expectations

1. Branch from `main` or the active integration branch linked to your issue (for example `feature/issue-2` for baseline MVP work).
2. Keep PRs focused on one issue or coherent slice of pack content.
3. Run `./scripts/validate-policy-pack.sh` before requesting review.
4. Include a short summary of semver impact (patch, minor, major, or docs-only).
5. Link the GitHub issue in the PR description.
6. Add or update reviewer examples when fixture behavior is hard to understand from JSON alone.

CI must pass before merge. See [`docs/ci-expectations.md`](docs/ci-expectations.md) for the check list.

## Review criteria

Reviewers evaluate:

- **Semantics**: Does the change express infrastructure governance meaning, not only syntax?
- **Determinism**: Do fixtures document stable ordering and expected decisions?
- **Readability**: Will reason text make sense in SaaS UI, GitHub/GitLab feedback, and evidence exports?
- **Scope**: Are tenant-specific settings absent from manifests and policy documents?
- **Compatibility**: Does the semver bump match [`docs/pack-versioning.md`](docs/pack-versioning.md)?
- **Coverage**: Does every new rule ID have fixture and catalog coverage?
- **Security**: Do fixtures avoid live secrets and private key material?

Approval requires at least one maintainer review for pack content changes. Documentation-only PRs may merge with maintainer discretion when CI is green.

## What we do not accept in MVP pull requests

- Tenant IDs, approver group membership, or customer override blocks in pack manifests
- OPA/Rego modules as required baseline artifacts (optional future boundary; see [`docs/policy-authoring.md`](docs/policy-authoring.md))
- Rule changes without fixture updates
- Breaking evaluation changes without a major version bump

## Reporting problems

Open a GitHub issue with:

- Pack name and version (if known)
- Expected vs actual decision or fixture behavior
- Redacted sample input (no live credentials)

## Related documents

- [`docs/ci-expectations.md`](docs/ci-expectations.md)
- [`docs/release-process.md`](docs/release-process.md)
- [`docs/classifier-fixtures.md`](docs/classifier-fixtures.md)
