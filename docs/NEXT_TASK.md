# Next Task

> **Status: Current** — Phase 82 implemented; GitHub Actions merge gate pending.

## Phase 82 current state

The generic Raw Data Acquisition Framework is implemented without changing Architecture
v12. It provides immutable checksum-addressed raw snapshots, a source-neutral provider
boundary with an offline fixture provider, deterministic normalized source records, a
Phase 80 candidate-assertion bridge with change/conflict reports, separately auditable
and resumable acquisition runs, security controls, and an explicit-stage offline CLI.
No complete Mystery Booster 2 dataset or canonical record was added. See
`RAW_DATA_ACQUISITION_FRAMEWORK.md`.

## Architectural and operational boundary

Downloaded bytes are not canonical truth. Acquisition, normalization, assertion creation,
and existing reviewed canonical promotion remain separate. Provider trust is explicit
and defaults to unknown/unverified. Architecture v12 remains frozen; the pre-implementation
inventory found no Tier 0 decision was needed.

## Next action and merge gate

Review the Phase 82 pull request and wait for GitHub Actions. Do not recommend merge until
all Actions checks are green. After a green merge, the next separately authorized work may
create a terms-compliant provider adapter and reviewed acquisition run for Mystery Booster
2; full population still requires independent completeness and evidence review. Live market
history, scraping, automatic promotion, probability, simulation, and intelligence features
remain out of scope.

## Retained prior state

Phase 80 resolved the generic canonical contract gaps and Phase 81 established that MB2
population was blocked only by the absence of a reviewed reproducible acquisition workflow.
Phase 82 supplies that workflow; it does not itself satisfy the complete-source evidence gate.

## Prior baseline (retained for history)


> **Status: Current** — Phase 81 evidence-acquisition gate.

## Current approved milestone

**Phase 81 — Mystery Booster 2 Canonical Dataset v1 (evidence-blocked)**

Phase 80 resolved the Phase 79 contract/importer blockers without changing Architecture
v12. Review `MYSTERY_BOOSTER_2_DATASET.md`. Do not promote a complete MB2 dataset until
a content-complete, terms-compliant normalized source is retained and independently
reviewed with explicit expected counts.

## Remaining approved actions

- Review the blocker inventory and architectural-fit findings.
- Run the CI-equivalent 141-test suite and documentation hygiene checks.
- Observe the GitHub Actions result for the pull request.
- Recommend merge only after GitHub Actions is green.

## After the Phase 79 review

No implementation milestone is currently approved. Stop after the green merge handoff
and request explicit authorization for one bounded contract/importer resolution.

Possible future work is recorded, but not authorized, in two separate tracks:

1. non-breaking consolidation candidates from `../ARCHITECTURE_REVIEW_v1.md`; and
2. evidence-dependent MB2 research or rule work, which remains gated by a content-
   complete, independently reviewed handoff relevant to unresolved outcome-affecting
   claims.

Neither track permits Architecture v12 redesign, inferred MB2 behavior, or unreviewed
canonical promotion.

## Phase 80 — Canonical Card, Printing, Evidence, and Uncertainty Contract (2026-07-30)

Phase 80 adds the compatible v3 Card/Printing and assertion-level evidence contract,
explicit partial-knowledge semantics, deterministic promotion, legacy projections,
and fail-closed simulation readiness. Historical canonical records remain unchanged;
full Mystery Booster 2 population remains out of scope. See
`docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`. Do not recommend merge until
GitHub Actions are green.