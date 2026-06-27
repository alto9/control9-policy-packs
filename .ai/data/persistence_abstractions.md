# Persistence Abstractions

This doc describes storage ownership and retention expectations without binding implementation details beyond accepted product choices.

## Contract

- Pack data includes readable policy documents, compiled artifacts, classifier metadata, fixture examples, version manifests, and compatibility metadata.
- Every decision carries enough policy metadata to explain the pack version, matched rule, risk summary, reason, and fixture coverage.
