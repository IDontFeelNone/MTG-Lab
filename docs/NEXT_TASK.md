# Next Task

## Current Objective

Implement controlled real-evidence acquisition and the first product-specific parsing and normalization path for Mystery Booster 2.

## Background

The generic acquisition, raw-evidence, parsed-artifact, normalized-candidate, provenance, validation, and intermediate-storage foundations are complete. The next milestone must exercise those generic systems with approved real Mystery Booster 2 evidence without writing unreviewed data into the canonical repository.

## Acceptance Criteria

- Select and document an approved Mystery Booster 2 acquisition target from the existing manifest.
- Acquire or fixture its evidence through the existing evidence-preserving pipeline.
- Add a product-specific parser that produces schema-valid parsed artifacts.
- Add a product-specific normalizer that produces schema-valid candidates with field provenance.
- Preserve raw evidence and trace every candidate field to its source record.
- Keep all outputs outside canonical data.
- Cover successful, partial, and invalid or failed inputs with deterministic tests.
- Update the inventory, session state, roadmap, and changelog with the completed scope.

## Constraints

- Do not hard-code Mystery Booster 2 behavior into reusable probability, simulation, or repository engines.
- Do not introduce canonical promotion without separate approval.
- Do not infer missing product facts or collation rules.
- Preserve immutable evidence and deterministic artifact identifiers and hashes.
- Keep the milestone small enough for focused review.

## Files Expected To Change

- Product-specific modules under `src/ingestion/` or a clearly scoped subpackage.
- Focused tests under `tests/`.
- Approved source or acquisition metadata under `data/canonical/games/magic/products/mystery_booster_2/`, only if required.
- `PROJECT_INVENTORY.md`, `docs/SESSION_STATE.md`, `docs/NEXT_TASK.md`, `docs/ROADMAP.md`, and `CHANGELOG.md`.

Exact files must be determined from the approved acquisition target before implementation.

## Testing Requirements

- Run `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -v`.
- Run `git diff --check`.
- Validate every new parsed and normalized document against its versioned JSON Schema.
- Verify evidence hashing and storage remain deterministic and idempotent.

## Definition of Done

The approved real-evidence path produces deterministic, schema-valid, provenance-complete intermediate artifacts; no canonical data is promoted; all tests and validations pass; documentation reflects the new state; and a focused PR is ready for review.
