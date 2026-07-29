# Next Task

## Phase 56 — Card and Printing Repository Foundation

**Status:** Complete

## Objective

Establish the first canonical Card and Printing repository records and validate
the identity relationship defined in `docs/DATA_MODEL.md`.

## Scope

- Define canonical repository representations for Card and Printing records.
- Create a small, authoritative initial dataset sufficient to validate the model.
- Establish and document stable Card and Printing identifiers.
- Represent and validate the required Card-to-Printing relationship.
- Preserve source evidence and field-level provenance.
- Produce deterministic canonical output.
- Implement structural and referential validation.
- Integrate with the existing controlled-review and canonical-promotion lifecycle
  where applicable without introducing automated approval.
- Add unit and integration tests and synchronize relevant documentation.
- Add a documentation-migration backlog to `PROJECT_INVENTORY.md`; record status
  only and do not migrate subsystem specifications.

## Constraints

- Do not expand or redesign `docs/DATA_MODEL.md`.
- Do not introduce product-specific logic.
- Do not implement slots, sheets, collation, probabilities, pack generation,
  simulation, analytics, market intelligence, API behavior, or AI behavior.
- Do not introduce or modify SQLAlchemy models, database migrations, or
  persistence behavior unless explicitly required by approved architecture.
- Do not populate the complete Mystery Booster 2 card list.
- Stop and request approval if implementation reveals a genuine architectural defect.

## Acceptance Criteria

- Canonical Card and Printing records validate successfully.
- Every Printing references an existing Card.
- Stable identifiers are deterministic and documented.
- Source and field-level provenance are preserved.
- Invalid or orphaned records are rejected with useful errors.
- Canonical output is reproducible.
- Existing tests continue to pass and new behavior has unit and integration coverage.
- `PROJECT_INVENTORY.md` accurately reflects implementation and
  documentation-migration status.

## Testing Requirements

- Run `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v`.
- Validate every canonical Card, Printing, and referenced Source Record against
  its versioned JSON Schema.
- Verify deterministic serialization and Card-to-Printing referential validation.
- Verify invalid, duplicate, path-mismatched, and orphaned records are rejected.
- Run `git diff --check`.

## Definition of Done

A small reviewed canonical Card and Printing dataset is schema-valid,
provenance-complete, deterministic, and referentially valid; invalid and
orphaned records fail with useful errors; tests pass; repository documentation
reflects Phase 56; the focused milestone is committed and ready for review in
one pull request.

## Recommended Next Milestone

Define a focused, approval-gated Card and Printing candidate ingestion and
promotion increment. Phase 56 does not approve or begin that work.
