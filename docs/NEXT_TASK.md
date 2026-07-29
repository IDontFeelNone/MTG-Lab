# Next Task

## Phase 54 — Controlled Canonical Promotion

**Status:** Complete

## Current Objective

Implement the first controlled canonical-promotion workflow for the canonical
product entity used by the Mystery Booster 2 ingestion pipeline.

## Scope

This first increment is intentionally limited to product candidates. It does
not promote cards, printings, slots, print sheets, collation, probabilities, or
market data, and it does not introduce automated approval.

## Acceptance Criteria

- Promotion requires an explicit application-workflow approval decision.
- Only schema-valid candidate artifacts whose selected product candidate is
  validated and cross-artifact valid are eligible.
- Complete candidate and field provenance is preserved in permanent audit history.
- Promotion and audit identifiers are deterministic, and repeated operations
  are idempotent.
- Conflicting canonical product data is reported and never overwritten.
- Rejection records the decision and leaves canonical data unchanged.
- Rollback uses promotion audit history, refuses unsafe state changes, and
  records its own permanent audit event.
- Validation cannot be bypassed.
- Unit and integration tests cover success, rejection, invalid input,
  idempotency, conflict, and rollback.
- Outputs remain limited to canonical product data and non-canonical audit history.

## Constraints

- Preserve the Git repository as the canonical source of truth.
- Do not redesign or expand the canonical product domain model.
- Do not introduce persistence, probability, simulation, analytics, or
  promotion support for other entity types.
- Do not silently merge or overwrite canonical data.
- If implementation requires expanding the canonical domain model, migrate the
  approved `DATA_MODEL.md` to `docs/DATA_MODEL.md` and stop for architectural
  review before implementing the expansion.

## Testing Requirements

- Run `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v`.
- Validate every written canonical product and audit record against its
  versioned JSON Schema.
- Verify promotion, rejection, and rollback audit storage is deterministic and
  immutable.
- Run `git diff --check`.

## Definition of Done

An explicitly reviewed, validated product candidate can be promoted without
overwriting canonical data; the complete decision and provenance are retained
in immutable audit history; repeated promotion is idempotent; rejection and
rollback are safe and auditable; all tests pass; and documentation accurately
reflects Phase 54.
