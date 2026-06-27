# Messaging And Async

This doc describes asynchronous delivery, replay, notification, retry, and webhook expectations at a product level.

## Contract

- control9 consumes pack versions to produce deterministic decisions.
- control9-integrations sends summaries and fingerprints and does not evaluate complete policy packs locally.
