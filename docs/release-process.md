# Release process

This document defines how baseline policy packs move from draft content in this repository to pinned releases consumed by the [control9](https://github.com/alto9/control9) SaaS policy engine.

Pack semver rules live in [`pack-versioning.md`](pack-versioning.md). This document covers release workflow, urgent fixes, provenance, and compatibility checks.

## Release ownership

| Concern | Owner |
|---------|-------|
| Pack manifest, policy documents, fixtures, examples | `control9-policy-packs` |
| Tenant enablement, overrides, approver groups, approval routing | `control9` |
| Signed action envelopes and CI integration surfaces | `control9-integrations` |

A release from this repository is **not** a tenant rollout. control9 pins a pack version per tenant after compatibility checks pass.

## Semantic version releases

Follow [`pack-versioning.md`](pack-versioning.md) when choosing **patch**, **minor**, or **major** bumps.

Typical flow for a pack release:

1. Update pack content under `packs/<pack-name>/` (policy document, fixtures, manifest).
2. Bump `version` in `packs/<pack-name>/manifest.json`.
3. Refresh artifact `digest` values for every referenced file.
4. Set `releaseStatus` (`draft` → `released` when criteria are met).
5. Confirm `compatibility.policyEngine.semverRange` matches the control9 engine build that will load the pack.
6. Run the local validation suite (see [`ci-expectations.md`](ci-expectations.md)).
7. Open a pull request with release notes summarizing rule, fixture, and compatibility changes.
8. After merge, tag the repository at the released commit when the pack reaches `releaseStatus: released`.

Initial MVP packs start at **`0.1.0`** with `releaseStatus: draft`. Promote to **`1.0.0`** with `releaseStatus: released` only when baseline rules, fixtures, docs, and CI checks meet the release checklist below.

## Urgent patch-level fixes

Use a **patch** release when evaluation semantics for unchanged inputs stay the same but a fix is needed quickly:

- Incorrect reason text that misleads reviewers or downstream evidence exports
- Fixture or digest corrections that unblock control9 loading
- Metadata fixes (provenance, compatibility floor documentation)
- Classifier label corrections that do not change product decisions for existing fixture cases

Process for urgent patches:

1. Branch from `main` or the active integration branch for the parent issue.
2. Apply the minimal compatible fix; avoid unrelated refactors.
3. Bump the **patch** version only unless semver rules require otherwise.
4. Run the full local validation suite before opening the PR.
5. Note the engine floor in the PR body if `compatibility.policyEngine.semverRange` changes.
6. Merge and tag promptly so control9 can pin the patch without waiting for unrelated work.

Do **not** use patch releases to rename rules, change decisions for the same input envelope, or alter manifest schema version. Those require **minor** or **major** bumps per [`pack-versioning.md`](pack-versioning.md).

## Provenance and audit trail

Every manifest must include a `provenance` block:

- `sourceRepository`: canonical Git URL for this repository
- `sourceRef`: branch, tag, or commit identifier used at release time
- `contentOrigin`: `repository` for built-in packs maintained here
- `maintainers`: owning team identifiers (for example `platform-engineering`)

Release PRs must keep provenance accurate. control9 and evidence exports surface pack name, version, and artifact digests so operators can trace a decision back to the exact policy document bytes.

## SaaS policy-engine compatibility

Before marking a pack `released`:

1. Confirm the running control9 policy-engine version satisfies `compatibility.policyEngine.semverRange`.
2. Confirm control9 can load every artifact path and digest declared in the manifest.
3. Confirm fixture suites referenced by the manifest validate locally and in CI.

If a release requires a newer engine bugfix, document the floor in the PR and bump the semver range only when the change is intentional. Narrowing the range on a **major** release is expected; narrowing on a patch requires explicit justification in release notes.

## Release checklist

Use this checklist before setting `releaseStatus: released`:

- [ ] Semver bump matches the change type (patch, minor, major).
- [ ] `manifestSchemaVersion` unchanged unless a documented migration exists.
- [ ] All artifact and fixture digests match file contents.
- [ ] `python3 scripts/validate-policy-pack.sh` passes locally.
- [ ] Classifier fixtures cover every baseline rule ID and required edge situation.
- [ ] Policy reason text is readable on SaaS, GitHub/GitLab, and evidence export surfaces (see [`policy-authoring.md`](policy-authoring.md)).
- [ ] Reviewer examples under `examples/` match fixture expectations.
- [ ] Release notes describe compatibility and any engine floor changes.
- [ ] Deprecation or replacement metadata is present when retiring a version.

## Deprecation and replacement

When retiring a pack version, follow the deprecation section in [`pack-versioning.md`](pack-versioning.md). control9 stops accepting new pins after `sunsetDate` and surfaces the replacement version in admin and evidence views.

## Related documents

- [`pack-versioning.md`](pack-versioning.md)
- [`ci-expectations.md`](ci-expectations.md)
- [`policy-authoring.md`](policy-authoring.md)
- [`CONTRIBUTING.md`](../CONTRIBUTING.md)
