# PROJECT_INVENTORY.md

> Canonical project inventory for MTG Lab.

## Architecture v12 Inventory
- Current architecture: v12
- Canonical data-first design
- Deterministic pipelines
- Modular implementation
- AI-assisted analytics

## Module Inventory
- Repository, schemas, validation, and ingestion
- Ingestion includes raw evidence, parsed artifacts, normalized candidate artifacts, field provenance, and candidate validation
- Probability, simulation, analytics, and market intelligence remain future work

## Mystery Booster 2 Repository Status
- Canonical product, source registry, and acquisition manifest foundations are validated
- Intermediate artifacts are stored outside canonical data at `data/intermediate/parsed/` and `data/intermediate/candidates/`
- Parsed and normalized candidates are traceable and schema-validated; canonical promotion is intentionally unavailable
- Cards, printings, slots, sheets, collation, probabilities, simulations, and market data remain unpopulated

## Completed Work
- Versioned schemas and validation infrastructure
- Mystery Booster 2 product/source/acquisition foundations
- Evidence-preserving ingestion pipeline foundation
- Parsed-record and normalized-candidate artifact foundation with field-level provenance and candidate validation

## Remaining Work
- Controlled real evidence acquisition and product-specific parsing/normalization
- Human or approved automated canonical promotion workflow
- Complete card repository, slots, print sheets, probability, simulation, analytics, and market intelligence

## Session Startup Protocol
1. Read PROJECT_INVENTORY.md and CHANGELOG.md
2. Continue from the next approved milestone
3. Update inventory and changelog with completed work
4. Commit and verify the work
