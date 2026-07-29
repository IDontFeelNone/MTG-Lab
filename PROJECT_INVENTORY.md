# PROJECT_INVENTORY.md

> Canonical project inventory for MTG Lab.
>
> This document is the first file read at the beginning of every development session. It serves as the authoritative source of project organization, implementation progress, architecture, and roadmap.

## Architecture v12 Inventory
- Current architecture: v12
- Canonical data-first design
- Deterministic pipelines
- Modular implementation
- AI-assisted analytics

## Documentation Inventory
- README.md
- CHANGELOG.md
- PROJECT_INVENTORY.md
- Planned: CONTRIBUTING.md, ARCHITECTURE.md, DATA_MODEL.md, VALIDATION.md, API.md

## Module Inventory
- Repository
- Schemas
- Validation
- Ingestion — generic, evidence-preserving acquisition-to-parse foundation
- Mystery Booster 2 dataset
- Probability engine
- Simulation
- Analytics
- Market intelligence

## Dataset Inventory
Primary dataset: Mystery Booster 2

## Mystery Booster 2 Repository Status
- Foundation established
- Canonical product foundation recorded at `data/canonical/games/magic/products/mystery_booster_2/`
- Product record schema-validated and loadable through the repository layer
- Source registry and acquisition manifest are schema-validated and cross-reference checked
- Raw evidence ingestion foundation preserves acquired bytes outside canonical data and returns parsed intermediate artifacts only
- Card list, slot definitions, print sheets, collation, and probabilities intentionally unpopulated

## Completed Work
- Repository initialized
- README
- CHANGELOG
- Architecture v12 defined
- Development workflow established
- Versioned canonical schemas and validation infrastructure
- Mystery Booster 2 canonical product foundation
- Source registry and acquisition manifest foundation
- Evidence-preserving ingestion pipeline foundation

## Remaining Work
- Acquired source evidence and product-specific parsers
- Candidate normalization and canonical-data validation integration
- Complete card repository
- Slot definitions
- Print sheets
- Probability engine
- Monte Carlo simulation
- Analytics
- Market intelligence

## Migration Order
1. Foundation
2. Card repository
3. Slot definitions
4. Print sheets
5. Probability
6. Validation
7. Simulation
8. Analytics
9. Market intelligence
10. Release

## Commit Plan
- Foundation
- Canonical card repository
- Slot definitions
- Print sheets
- Validation
- Probability engine
- Monte Carlo
- Analytics
- Market intelligence
- Release Candidate

## Session Startup Protocol
1. Read PROJECT_INVENTORY.md
2. Read CHANGELOG.md
3. Continue from the next unfinished milestone
4. Update PROJECT_INVENTORY.md
5. Update CHANGELOG.md
6. Commit completed work
