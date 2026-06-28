# Deployment Environments

This doc describes environments and rollout boundaries without locking exact account or stack names.

## Contract

- Policy-pack releases are pinned, auditable, and compatible with SaaS policy-engine versions.
- CI runs fixture coverage for classifier and rule behavior.
- Urgent policy fixes roll out as patch releases with explicit compatibility metadata, provenance, fixture coverage, and release notes.
- control9 may adopt an urgent fixed pack for SaaS-managed defaults after compatibility checks pass, while customer-pinned pack versions remain pinned until SaaS configuration or customer action selects the new version.
- Urgent fixes must not silently mutate an already pinned pack version.

## Open implementation decisions

No unresolved implementation decisions remain here for issue #2. Tenant rollout controls are tracked by issue #4.
