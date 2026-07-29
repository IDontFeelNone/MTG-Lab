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

Phase 62 — Evidence Repository Foundation complete;
awaiting review and approval for the next milestone

## Last Merged PR

PR #12 — Phase 61 implementation proposal.

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
- Canonical Print Sheet and Slot contracts now implement the existing Tier 0
  fields, game scoping, and provenance requirements. Generic loaders validate
  the full dependency graph and produce deterministic rule snapshots.
- Controlled review, promotion, immutable audits, and dependency-safe rollback
  are enabled for Print Sheet and Slot candidates. No canonical Print Sheet or
  Slot data has been populated.
- A deterministic bounded ingestion workflow combines multiple approved sources
  with field-level attribution. Wave 1 retained parsed and candidate artifacts
  and promoted three Mystery Booster 2 Cards followed by their three Printings,
  with six immutable approval audits.
- A stable `data/sources/` evidence archive now loads versioned manifests and
  archived files only after path, size, SHA-256, duplicate, canonical-source,
  and claim-level provenance validation.

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
- Canonical Print Sheet and Slot repository paths, source-backed provenance,
  structural and referential validation, deterministic snapshots, promotion,
  and rollback were implemented and verified with temporary synthetic data.
- Mystery Booster 2 Card and Printing Wave 1 validated the complete ingestion
  workflow with three evidence-supported pairs and no rule-data population.
- Evidence Repository Foundation established the canonical archive layout,
  manifest contract, verified loader, and provenance validation using existing
  Wave 1 evidence without adding canonical domain records.

## Current Focus

Awaiting review of Phase 62. No additional Card or Printing wave and no
canonical Mystery Booster 2 Print Sheet or Slot population milestone is approved.

## Open Risks

- The controlled title fixture is deliberately not a complete page archive and cannot support card or collation claims.
- Product-specific evidence may be incomplete or contradictory.
- Canonical data must not be populated from unreviewed intermediate candidates.
- Downstream probability and simulation work remains blocked on validated product data.

## Technical Debt

- Canonical promotion supports Product, Card, Printing, Print Sheet, and Slot
  candidates but still requires manual application-workflow decisions; other
  entity definitions remain future work.
- Only fourteen Cards and Printings are populated; comprehensive card data,
  slots, sheets, collation, probabilities, simulations, and market data remain unpopulated.
- Roadmap technical-debt categories require specific tracked items as work is discovered.

## Upcoming Milestones

1. Review the Phase 62 Evidence Repository Foundation.
2. Require separate approval for Wave 2 or any Mystery Booster 2 rule population.
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
