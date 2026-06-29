# Policy pack versioning

This document defines how `control9-policy-packs` versions baseline packs so the Control9 SaaS policy engine can pin, load, and reject incompatible releases deterministically.

## Scope

These rules apply to repository-owned pack manifests under `packs/<pack-name>/manifest.json`. They do **not** cover tenant enablement, per-tenant overrides, customer approver groups, or approval routing. Those settings live in [control9](https://github.com/alto9/control9).

## Semantic versioning

Each pack release uses [Semantic Versioning 2.0.0](https://semver.org/):

| Version part | When to bump | Examples |
|--------------|--------------|----------|
| **PATCH** (`x.y.Z`) | Compatible policy fixes, clarifications, metadata corrections, or fixture additions that do not change evaluation for unchanged inputs | Tighten reason text, fix a misclassified fixture, correct a digest |
| **MINOR** (`x.Y.0`) | Backward-compatible baseline coverage: new rule categories, new classifier labels, new fixtures, or additive manifest fields accepted by the current manifest schema | Add off-path fixture suite, add a new `require_approval` rule with no change to existing rule outcomes |
| **MAJOR** (`X.0.0`) | Compatibility-breaking changes: manifest schema version changes, renamed or removed rules, changed decision effects for the same input envelope, incompatible artifact layout, or policy-engine range changes that exclude previously supported engine versions | Remove a rule ID, change `deny` to `allow` for the same condition, bump `manifestSchemaVersion` |

Initial releases for a new pack start at **`0.1.0`** with `releaseStatus: draft` until baseline rules and fixtures meet release criteria, then move to **`1.0.0`** with `releaseStatus: released`.

## Manifest schema version

The `manifestSchemaVersion` field identifies the JSON Schema contract (`schemas/pack-manifest.v1alpha1.schema.json`). A **major** pack version bump is required when:

- the manifest schema version changes, or
- required manifest fields are added or removed in a way control9 cannot accept silently.

Patch and minor pack releases must keep the same `manifestSchemaVersion` unless an explicit migration path is documented.

## Policy-engine compatibility

The `compatibility.policyEngine.semverRange` field declares which control9 policy-engine versions may load the pack. control9 must reject a pin when the running engine version falls outside this range.

Guidelines:

- **Initial releases** target a narrow range tied to the engine build that implements the manifest consumer (for example `>=0.1.0 <1.0.0`).
- **Patch releases** keep the same semver range unless the fix requires a newer engine bugfix; document the engine floor in the release notes when it changes.
- **Minor releases** may widen the range when new content remains compatible with older engines.
- **Major releases** may narrow or shift the range when evaluation semantics or artifact contracts change.

## Release status

| Status | Meaning for control9 |
|--------|----------------------|
| `draft` | Pack metadata and artifact references exist; not for production pins. Useful for early integration and review. |
| `released` | Pack may be pinned for shadow and enforce evaluation when compatibility checks pass. |
| `deprecated` | Existing pins may continue temporarily; new pins should be rejected or require explicit override policy in control9. |
| `replaced` | Superseded by another pack version; new pins must use the replacement declared in `deprecation.replacement`. |

## Deprecation and replacement

When retiring a pack version:

1. Set `releaseStatus` to `deprecated` or `replaced`.
2. Populate the optional `deprecation` block with `reason`, `deprecatedAt`, and `sunsetDate`.
3. Set `deprecation.replacement.packName` and `deprecation.replacement.minVersion` to the successor release.
4. Bump the **major** version if evaluation semantics changed; otherwise use **patch** or **minor** for metadata-only deprecation.

control9 should stop accepting new pins after `sunsetDate` and surface the replacement in admin and evidence views.

## Artifact integrity

Every referenced policy document, compiled artifact, and fixture suite entry in the manifest includes a `sha256:` digest computed over the file bytes at release time. Release readiness fails when:

- a referenced path is missing,
- a digest does not match file contents, or
- compatibility metadata is absent or malformed.

Run the local validator before opening a release PR:

```bash
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json
```

## Examples

Reviewable manifest examples live under `examples/manifests/`. The canonical working manifest for the built-in MVP pack is `packs/production-infra-baseline/manifest.json`.
