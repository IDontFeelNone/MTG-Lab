# Repository Reconciliation Plan

> **Status: Superseded Historical Plan** — retained as the pre-implementation structure
> assessment from 2026-07-28. Phases 56–76 subsequently created or populated many of
> the packages it calls empty or missing. `../PROJECT_INVENTORY.md` and
> `../ARCHITECTURE_REVIEW_v1.md` are the current inventory and implementation assessment;
> none of this plan's proposed migrations is authorized by its retention.

**Original status:** Proposed — no structural changes applied
**Date:** 2026-07-28  
**Scope:** Reconcile the source tree with the approved MTG Lab architecture before feature implementation.

## Authority and Constraints

This plan is subordinate to the following authoritative documents:

- `README.md`
- `PROJECT_INVENTORY.md`
- `docs/AI_ARCHITECTURE_VISION.md`
- `docs/DATA_REPOSITORY.md`
- `docs/ROADMAP.md`

It does not replace or amend them. Directory moves, deletions, and package creation require a separately approved implementation milestone.

## Current Confirmed Structure

The repository already contains canonical package initializers for:

- `src/ingestion/` — source ingestion, normalization, and validation pipelines
- `src/repository/` — normalized datasets, metadata, schemas, and repository access
- `src/probability/` — probability models, sheet reconstruction, pack odds, and statistics

The following empty placeholder directories are also present:

- `src/importer/`
- `src/parser/`
- `src/simulation/`
- `src/market/`
- `src/models/`
- `data/raw/`, `data/processed/`, `data/canonical/`, and `data/validation/`
- `docs/`, `tests/`, `scripts/`, and `notebooks/`

The data layers align directly with `docs/DATA_REPOSITORY.md`.

## Decisions Document

A decisions record has already been migrated and is available at
`docs/DECISIONS.md`. It contains accepted architectural and engineering
decisions and is the recommended permanent location. No copy of
`DECISIONS.md` exists at repository root.

Future decisions should be appended to `docs/DECISIONS.md` using sequential
decision identifiers, status, decision statement, and rationale. It should not
be duplicated at the root.

## Obsolete or Misaligned Directories

| Directory | Finding | Proposed disposition |
| --- | --- | --- |
| `src/importer/` | Duplicates the responsibility of the established `src/ingestion/` package. It contains only a placeholder. | Deprecate now; remove the placeholder in an approved structural migration. Do not add code here. |
| `src/parser/` | Its ownership is ambiguous. Parsing raw external records is an ingestion concern, while validation of normalized records belongs to validation. | Do not implement as a peer package. Place source-format parsers under `src/ingestion/parsers/` when needed. |
| `src/models/` | Its scope overlaps with the architecture's schema and repository concerns. | Do not add new code until a domain-model versus serialization-schema boundary is approved. |
| `docs/.gitkeep` | Redundant because `docs/` now contains tracked documentation. | Eligible for removal only in an approved cleanup. |

The remaining placeholder directories are not obsolete: simulation and market
are named architectural capabilities, and the data layers are explicitly
approved.

## Missing Packages and Directories

The approved architecture identifies several responsibilities that do not yet
have confirmed package locations:

- `src/validation/` — reusable validation engine and integrity checks
- `src/simulation/` — deterministic pack and product simulation
- `src/analytics/` — derived metrics, expected value, and reporting
- `src/market/` — market-data acquisition and market analysis
- `src/schemas/` — explicit schemas for dataset interchange and validation
- `tests/unit/`, `tests/integration/`, and `tests/regression/` — the test
  hierarchy required by the engineering standards
- `games/magic/mystery_booster_2/` — product-specific definitions, if the
  repository adopts the multi-game layout shown in the README
- `exports/` — published derived outputs, if retained by the architecture

These are proposed additions, not present changes. The product-data location
must be decided before creating `games/`: it must be consistent with the
repository and data-layer design rather than duplicating canonical datasets.

## Recommended Canonical Package Layout

```text
src/
  ingestion/       External-source acquisition, parsing, normalization
    parsers/       Source-format-specific parsers
  repository/      Canonical dataset access, metadata, persistence
  schemas/         Dataset contracts and validation schemas
  validation/      Cross-dataset integrity and probability validation
  probability/    Exact odds, print-sheet reconstruction, statistics
  simulation/     Seeded pack/product simulation
  analytics/      Derived metrics, EV, and reporting
  market/          Market-data adapters and market analysis
```

Responsibility boundaries:

- **Ingestion** transforms external sources into normalized candidates; it
  owns parsers. It does not become the canonical source of truth.
- **Repository** owns approved canonical data and repository access.
- **Schemas** defines explicit data contracts shared across packages.
- **Validation** verifies candidates and canonical datasets before probability
  and simulation use.
- **Probability** calculates deterministic analytical results from validated
  models.
- **Simulation** consumes validated product definitions and records seed,
  configuration, and data version for reproducibility.
- **Analytics** combines repository, probability, simulation, and market
  outputs without duplicating their responsibilities.
- **Market** isolates provider-specific retrieval from reusable analysis.

## Proposed Migration Sequence

1. Declare `src/ingestion/` the sole import pipeline in project inventory or
   a later approved decision record.
2. Move any future parser implementation directly into
   `src/ingestion/parsers/`; do not populate `src/parser/`.
3. Establish the `schemas` and `validation` boundary before introducing
   product datasets or simulation code.
4. Create the unit, integration, and regression test hierarchy alongside the
   first corresponding feature.
5. Remove only the obsolete placeholders (`src/importer/`,
   `src/parser/`, and redundant `docs/.gitkeep`) in a dedicated, approved
   structural migration after confirming they contain no work.
6. Decide the relationship between `data/canonical/` and
   `games/magic/mystery_booster_2/` before adding a multi-game product tree.

## Non-Goals

- No directory was renamed, moved, created, or deleted by this reconciliation.
- No authoritative documentation was rewritten.
- No runtime behavior or package import path changed.
