# PROJECT_INVENTORY.md

> Canonical project inventory for MTG Lab.

## Architecture v12 Inventory
- Current architecture: v12
- Current implementation phase: Phase 54 — Controlled Canonical Promotion complete
- Canonical data-first design
- Deterministic pipelines
- Modular implementation
- AI-assisted analytics

## Module Inventory
- Repository, schemas, validation, and ingestion
- Ingestion includes raw evidence, parsed artifacts, normalized candidate artifacts, field provenance, and candidate validation
- Repository includes explicitly reviewed, validated, auditable, idempotent,
  conflict-safe, and reversible canonical product promotion
- Research Log is defined as a Tier 0 architectural subsystem; implementation remains future work
- Probability, simulation, analytics, and market intelligence remain future work

## Mystery Booster 2 Repository Status
- Canonical product, source registry, and acquisition manifest foundations are validated
- Intermediate artifacts are stored outside canonical data at `data/intermediate/parsed/` and `data/intermediate/candidates/`
- The approved official product-page target has a controlled, hash-recorded evidence fixture and a deterministic Mystery Booster 2 title parser and normalizer
- Parsed and normalized product candidates are traceable and schema-validated;
  controlled promotion is available only for explicitly reviewed product candidates
- Cards, printings, slots, sheets, collation, probabilities, simulations, and market data remain unpopulated

## Completed Work
- Versioned schemas and validation infrastructure
- Mystery Booster 2 product/source/acquisition foundations
- Evidence-preserving ingestion pipeline foundation
- Parsed-record and normalized-candidate artifact foundation with field-level provenance and candidate validation
- Controlled Mystery Booster 2 official product-page title acquisition, parsing, and normalization path
- Controlled canonical product promotion with immutable decision and rollback audit history

## Remaining Work
- Canonical promotion for entity types beyond products and any automated approval workflow
- Complete card repository, slots, print sheets, probability, simulation, analytics, and market intelligence

## Documentation Migration

Architectural documents are migrated with the implementation milestone that
requires them; no standalone migration sprint is planned.

### Tier 0
- `DATA_MODEL.md` — Not Started
- `DATA_REPOSITORY.md` — In Progress
- `DATABASE_ENGINE.md` — Not Started

### Tier 1
- `IMPORT_PIPELINE.md` — Not Started
- `SIMULATION_ENGINE.md` — Not Started
- `ANALYTICS_ENGINE.md` — Not Started
- `IMPLEMENTATION_PLAN.md` — Not Started

## Session Startup Protocol
Repository-driven session management is defined by:

- `docs/SESSION_STATE.md` — current version, phase, milestone status, risks, and handoff checklist
- `docs/NEXT_TASK.md` — the single approved next objective and its definition of done
- `docs/HANDOFF.md` — the concise, replaceable transfer note from the most recent session
- `docs/AI_CONTRIBUTING.md` — the authoritative governance, contributor responsibilities, and collaboration guide
- `docs/DEVELOPMENT_PLAYBOOK.md` — reusable implementation patterns and engineering procedures
- `docs/LESSONS_LEARNED.md` — reusable engineering knowledge and historical implementation insight
- `docs/RESEARCH_LOG_ARCHITECTURE.md` — Tier 0 architecture for versioned, evidence-grounded domain research
- `docs/CODEX_WORKFLOW.md` — the standard operating procedure for Codex sessions

At session startup, read those documents together with `PROJECT_INVENTORY.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and `CHANGELOG.md`. `AI_CONTRIBUTING.md` governs collaboration and document priority, `DEVELOPMENT_PLAYBOOK.md` supplies repeatable procedures, and `LESSONS_LEARNED.md` preserves reusable engineering insight. `HANDOFF.md` supplies only the immediate transition; ongoing status belongs in `SESSION_STATE.md`, approved work in `NEXT_TASK.md`, and history in `CHANGELOG.md`. Continue only from the repository-defined next task; do not rely on previous chat history.
