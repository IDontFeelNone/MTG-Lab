# Next Task

> **Status: Current** — Phase 79 architectural blocker resolution gate.

## Current approved milestone

**Phase 79 — Mystery Booster 2 Canonical Dataset v1 (blocked)**

Review `PHASE_79_PREIMPLEMENTATION_REVIEW.md`. Do not populate MB2 data or extend the
importer until a separately approved, product-agnostic change can represent the
required fields, assertion classes, and unknown collation without arbitrary metadata.

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
