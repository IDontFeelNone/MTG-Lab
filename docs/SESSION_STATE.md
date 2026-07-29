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

Phase 59 — Rules Engine architecture migration complete; awaiting review and
approval for the next milestone

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
- The first canonical Card and Printing records are source-backed and
  provenance-complete. Repository loading enforces structural validity,
  identity paths, source references, field coverage, and the Printing-to-Card
  relationship, and produces deterministic canonical snapshots.
- Entity-agnostic controlled review and promotion is enabled for Card and
  Printing candidates through explicit repository definitions. Approval,
  rejection, idempotency, conflict handling, immutable audit history, and
  rollback are shared; repository validation prevents orphaning relationships.

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
- Canonical Card and Printing repository representation, initial authoritative
  dataset, deterministic identifiers and output, field provenance, and
  structural and referential validation.
- Generic candidate-review and canonical-promotion framework enabled for Card
  and Printing, with the existing Product workflow retained as a compatibility facade.
- A fixed increment of ten Limited Edition Alpha Cards and their ten Printings
  was preserved as candidates, explicitly approved, promoted in dependency
  order, and recorded in immutable audits from an official Gatherer source.
- Approved Rules Engine architecture is now canonical at
  `docs/RULES_ENGINE.md`; the Tier 0 data-repository layers now explicitly place
  Print Sheet and Slot candidates, canonical records, validation, and derived
  output within the existing repository lifecycle.

## Current Focus

Awaiting review of the architecture migration. No Print Sheet or Slot
implementation milestone is approved.

## Open Risks

- The controlled title fixture is deliberately not a complete page archive and cannot support card or collation claims.
- Product-specific evidence may be incomplete or contradictory.
- Canonical data must not be populated from unreviewed intermediate candidates.
- Downstream probability and simulation work remains blocked on validated product data.

## Technical Debt

- Canonical promotion supports Product, Card, and Printing candidates but still
  requires manual application-workflow decisions; other entity definitions remain future work.
- Only eleven Cards and Printings are populated; comprehensive card data,
  slots, sheets, collation, probabilities, simulations, and market data remain unpopulated.
- Roadmap technical-debt categories require specific tracked items as work is discovered.

## Upcoming Milestones

1. Review the Phase 59 Rules Engine architecture migration.
2. After approval, define a bounded Print Sheet and Slot implementation
   milestone.
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
