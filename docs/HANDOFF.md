# Handoff

> **Status: Current — Phase 88 implementation handoff; GitHub Actions pending.**

Phase 87 is merged and its missing reproducible MB2 source remains an explicit evidence gap.
Phase 88 introduces `src/external_ingestion/`, its CLI integration, tests, and
`EXTERNAL_DATASET_INGESTION.md`. Start review at that contract, then inspect
`external_ingestion/framework.py`, `mtglab/__main__.py`, and
`test_external_dataset_ingestion.py`.

The framework validates and registers supplied bytes, invokes the existing acquisition and
Knowledge Review Package functions, and stops at `awaiting_human_review`. It neither imports
MB2 nor invokes canonical promotion. Do not recommend merge until GitHub Actions are green.
