# Handoff

> **Status: Current — Phase 86 implementation handoff.** The pilot deterministically imports 35 of 39 records, rejects three, leaves one unresolved, and preserves acquisition/review/promotion audit. Do not recommend merge until GitHub Actions are green.

> **Status: Current — Phase 85 implementation handoff.**

Phase 85 adds the deterministic Canonical Promotion Engine consuming Phase 84 Knowledge
Review Packages. Read `CANONICAL_PROMOTION_ENGINE.md`, then inspect
`src/acquisition/promotion.py`, its acquisition CLI integration, and
`tests/test_canonical_promotion_engine.py`. Architecture v12 and existing canonical records
are unchanged. MB2 population, Simulation, Intelligence, and market analysis remain out of
scope.

The remaining work is Project Architect review and GitHub Actions. Do not recommend merge
until Actions are green. If recommended after green CI, the Project Owner merges; that merge
is acceptance and no post-merge approval message is expected.
