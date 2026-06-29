# Compatibility metadata

Pack manifests in `control9-policy-packs` expose reusable compatibility metadata that the Control9 SaaS policy engine validates **before** loading policy artifacts or evaluating fixtures and live envelopes.

## Scope

This repository owns:

- Manifest schema and examples under `schemas/pack-manifest.v1alpha1.schema.json` and `examples/manifests/`
- Local validation via `scripts/validate-pack-manifest.py`
- Compatibility metadata fixture suites under `fixtures/compatibility/`

This repository does **not** own tenant enablement, tenant overrides, customer approver groups, or customer-specific exception settings. Those live in [control9](https://github.com/alto9/control9).

## Manifest fields consumed by control9

Before evaluation, control9 checks manifest metadata for:

| Field group | Purpose |
|-------------|---------|
| Pack identity | `pack.name`, `pack.displayName`, `pack.description` |
| Pack version | `version` (semantic version pinned for evaluation) |
| Manifest schema | `manifestSchemaVersion` |
| Engine compatibility | `compatibility.policyEngine.semverRange` |
| Release status | `releaseStatus` and optional `deprecation` |
| Artifacts | `artifacts.policyDocuments`, optional `artifacts.compiled`, `artifacts.fixtureSuites` with `path` and `sha256:` digests |
| Provenance | `provenance.sourceRepository`, `sourceRef`, `contentOrigin`, and related release metadata |

Validation fails closed when required metadata is missing, semver ranges are malformed, the running policy-engine version falls outside the declared range, referenced artifacts or fixture suites are missing, or declared digests do not match file contents.

## SaaS consumption flow

```text
control9 pin request
  -> load manifest.json for pinned pack version
  -> validate manifest schema + tenant-field boundary
  -> verify policy-engine version satisfies compatibility.policyEngine.semverRange
  -> verify artifact paths exist and sha256 digests match
  -> only then load policy documents / compiled artifacts / fixture suites
  -> evaluate live envelope or fixture input against pinned pack version
```

control9 must not silently fall back to another pack version when compatibility validation fails.

## Local validation

Validate the built-in MVP pack manifest:

```bash
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json --policy-engine-version 0.5.0
```

Run compatibility fixture suites:

```bash
./scripts/run-fixtures.sh --suite compatibility-metadata
./scripts/run-fixtures.sh --all
```

Fixture reports include pack version, compatibility result, fixture identity, and clear failure reasons without dumping raw IaC payloads or secret values.

## Fixture coverage

The `compatibility-metadata` suite includes:

- One accepted manifest (`ex-valid-production-baseline`) using the canonical MVP pack
- Rejected manifests for missing required metadata, malformed semver range, incompatible engine version, missing referenced artifacts, and digest mismatch

See [`fixtures/compatibility/README.md`](../fixtures/compatibility/README.md) for layout and result schema details.

## Related documents

- [`pack-versioning.md`](pack-versioning.md)
- [`release-process.md`](release-process.md)
- [`ci-expectations.md`](ci-expectations.md)
- [`README.md`](../README.md)
