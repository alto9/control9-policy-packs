# Compatibility metadata fixtures

Shared layout for pack manifest compatibility metadata fixtures used by `./scripts/run-fixtures.sh --suite compatibility-metadata`.

## Purpose

These fixtures prove that the Control9 SaaS policy engine can validate pack manifests **before** loading policy artifacts or running classifier evaluation. Cases cover accepted manifests and fail-closed rejection for missing metadata, malformed semver ranges, incompatible engine versions, missing artifact references, and digest mismatches.

## Layout

```text
fixtures/compatibility/
  suites/
    compatibility-metadata/
      manifest.json
      ex-<case-id>/
        input/
          case.json
        expected/
          compatibility-result.json
        pack/                 # optional synthetic pack root for reject cases
          manifest.json
          policies/...
          fixtures/...
        notes.md
```

## Input contract

`input/case.json` declares:

- `policyEngineVersion` — control9 policy-engine version under test
- `manifestPath` — repository-relative path to the manifest file

## Expected result contract

`expected/compatibility-result.json` uses schema version `alto9.io/compatibility-result/v1alpha1` and declares:

- `fixtureId`, `packName`, `packVersion`
- `compatible` — whether validation should succeed for the declared engine version
- `failureReasons` — substrings that must appear in validation errors for reject cases

Reports include pack version, compatibility result, fixture identity, and failure reasons only. Raw IaC payloads, secret values, tenant overrides, and customer identifiers are not printed.

## Commands

```bash
./scripts/run-fixtures.sh --suite compatibility-metadata
./scripts/run-fixtures.sh --all
python3 scripts/validate-pack-manifest.py packs/production-infra-baseline/manifest.json --policy-engine-version 0.5.0
```

See also [`docs/compatibility-metadata.md`](../../docs/compatibility-metadata.md).
