# Session State

## Purpose

Provide the repository-owned handoff between development sessions. This file records the current project state; it replaces assumptions based on previous conversations.

## Last Updated

2026-07-29

## Current Version

v0.x (pre-alpha, unreleased)

## Current Architecture Version

v12

## Current Phase

Phase 55 — Data Model migration complete; awaiting approval for the next milestone

## Last Merged PR

PR #1 — candidate artifact JSON serialization and mutable-aliasing fixes.

## Repository Status

- Active development using Mystery Booster 2 as the reference implementation.
- Product, source registry, acquisition manifest, evidence-preserving ingestion, parsed artifact, normalized candidate, provenance, and candidate-validation foundations are implemented.
- Intermediate artifacts remain non-canonical until an explicitly approved,
  validation-gated product promotion succeeds.
- The approved Mystery Booster 2 official product-page target has a controlled,
  hash-recorded title-evidence fixture and deterministic product-specific parsing
  and normalization into schema-valid, provenance-complete intermediate artifacts.
- Explicitly reviewed and validated product candidates can be promoted or
  rejected through an immutable audit trail; promotion is idempotent and
  conflict-safe, and rollback is approval-gated and auditable.

## Completed Milestones

- Approved Tier 0 Data Model Specification migrated to `docs/DATA_MODEL.md`.
- Repository, architecture, and documentation foundation.
- Versioned schemas and schema-validation infrastructure.
- Mystery Booster 2 product, source, and acquisition foundations.
- Deterministic hashing and evidence-preserving ingestion foundation.
- Immutable parsed-record and normalized-candidate artifacts.
- Field-level provenance, cross-artifact validation, and hash-safe intermediate storage.
- JSON-compatible artifact serialization without mutable aliasing.
- Controlled official Mystery Booster 2 title-evidence acquisition, parsing, and normalization.
- Controlled canonical product promotion, rejection, conflict detection, immutable audit history, and rollback.

## Current Focus

Awaiting approval for the next focused implementation milestone.

## Open Risks

- The controlled title fixture is deliberately not a complete page archive and cannot support card or collation claims.
- Product-specific evidence may be incomplete or contradictory.
- Canonical data must not be populated from unreviewed intermediate candidates.
- Downstream probability and simulation work remains blocked on validated product data.

## Technical Debt

- Canonical promotion currently supports only product candidates and manual application-workflow decisions.
- Cards, printings, slots, sheets, collation, probabilities, simulations, and market data remain unpopulated.
- Roadmap technical-debt categories require specific tracked items as work is discovered.

## Upcoming Milestones

1. Card and printing repository population.
2. Slot, print-sheet, and collation definitions.
3. Probability, simulation, analytics, and market-intelligence layers.

## Next Session Checklist

1. Read `PROJECT_INVENTORY.md`, `docs/SESSION_STATE.md`, and `docs/NEXT_TASK.md`.
2. Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and `CHANGELOG.md`.
3. Verify the checkout, branch, and working-tree status.
4. Confirm the objective and acceptance criteria before editing.
5. Implement only the approved milestone.
6. Run the complete test suite and relevant validation.
7. Update repository documentation to reflect implementation changes.
8. Commit the focused change, open or update its PR, and stop when it is ready for review.
