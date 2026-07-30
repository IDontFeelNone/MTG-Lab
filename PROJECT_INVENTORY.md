# PROJECT_INVENTORY.md

> Canonical project inventory for MTG Lab.

## Architecture v12 Inventory
- Current architecture: v12
- Current implementation phase: Phase 65 — Mystery Booster 2 Product-Rule Evidence Sufficiency Assessment complete
- Canonical data-first design
- Deterministic pipelines
- Modular implementation
- AI-assisted analytics

## Module Inventory
- Repository, schemas, validation, and ingestion
- Ingestion includes raw evidence, parsed artifacts, normalized candidate artifacts, field provenance, and candidate validation
- Evidence repository includes game-scoped archived bundles, a versioned
  manifest contract, content-verified loading, and canonical-source provenance validation
- Repository includes explicitly reviewed, validated, auditable, idempotent,
  conflict-safe, and reversible canonical product promotion
- Repository includes schema-valid canonical Card and Printing records,
  deterministic stable identifiers and output, source-backed field provenance,
  and game-scoped Printing-to-Card referential validation
- Repository includes an entity-agnostic candidate-review and canonical-promotion
  framework enabled for Card, Printing, Print Sheet, and Slot, with explicit
  decisions, immutable audits, idempotency, conflict protection, and
  referentially safe rollback
- Research Log is defined as a Tier 0 architectural subsystem; implementation remains future work
- Deterministic pre-promotion population review reports are schema-validated and retained outside canonical data
- A schema-validated Rule Claim Matrix and evidence sufficiency report retain MB2 rule research outside canonical data
- Probability, simulation, analytics, and market intelligence remain future work

## Mystery Booster 2 Repository Status
- Canonical product, source registry, and acquisition manifest foundations are validated
- Intermediate artifacts are stored outside canonical data at `data/intermediate/parsed/` and `data/intermediate/candidates/`
- The approved official product-page target has a controlled, hash-recorded evidence fixture and a deterministic Mystery Booster 2 title parser and normalizer
- Parsed and normalized product candidates are traceable and schema-validated;
  controlled promotion is available only for explicitly reviewed product candidates
- An initial fixed increment of ten reviewed Cards and their Printings, in
  addition to the foundation pair, is populated from an official source.
  Deterministic multi-source Waves 1 and 2 add four evidence-supported Mystery
  Booster 2 Cards and their Printings; Wave 2 loads its input exclusively from
  the verified Evidence Repository and reuses existing canonical Source Records;
  Phase 65 confirms preserved evidence remains insufficient for canonical rules; slots, sheets, collation, probabilities, simulations, and market data remain unpopulated

## Completed Work
- Approved Tier 0 Data Model Specification migrated to `docs/DATA_MODEL.md`
- Versioned schemas and validation infrastructure
- Mystery Booster 2 product/source/acquisition foundations
- Evidence-preserving ingestion pipeline foundation
- Parsed-record and normalized-candidate artifact foundation with field-level provenance and candidate validation
- Controlled Mystery Booster 2 official product-page title acquisition, parsing, and normalization path
- Controlled canonical product promotion with immutable decision and rollback audit history
- Canonical Card and Printing repository foundation with structural, provenance,
  identity-path, source-reference, and Printing-to-Card validation
- Generic controlled candidate review and canonical promotion enabled for Card
  and Printing while retaining the existing Product workflow
- Fixed, source-attributed ten-Card and ten-Printing candidate population,
  canonical promotion, and immutable promotion audit history
- Approved Rules Engine architecture migrated to `docs/RULES_ENGINE.md`, with
  the Tier 0 repository-layer boundaries for Print Sheets and Slots recorded
- Canonical Print Sheet and Slot contracts, loaders, deterministic snapshots,
  dependency validation, controlled promotion, and dependency-safe rollback
- Bounded, deterministic, multi-source Card and Printing ingestion demonstrated
  with three Mystery Booster 2 pairs, retained intermediate artifacts, controlled
  dependency-order promotion, and six immutable audits
- Evidence repository foundation with a canonical `data/sources/` layout,
  versioned manifests, archived-file integrity checks, and provenance validation
  demonstrated on the existing Wave 1 extract
- Evidence-backed Wave 2 population with one new Card and Printing, verified
  artifact-to-record source attribution, existing-Card promotion filtering,
  deterministic intermediate artifacts, and immutable promotion audits
- Scalable complete-batch ingestion for up to twenty-five verified Printings,
  manifest-declared population boundaries, and retained deterministic review reports
- Evidence-backed MB2 rule-claim research with stable claim identities, verified evidence references, explicit unknowns, blocker reporting, and a no-redesign architectural sufficiency assessment

## Remaining Work
- Broader reviewed Card and Printing evidence acquisition and population,
  canonical promotion definitions for other entity types, and any automated approval workflow
- Complete card repository, populated slots and print sheets, probability, simulation,
  analytics, and market intelligence

## Documentation Migration Backlog

This backlog records migration status only. A related schema or implementation
does not make an absent specification canonical. Specifications remain deferred
until their subsystem implementation unless separately approved.

### Tier 0 / Architectural

| Specification | Status | Repository basis |
| --- | --- | --- |
| `DATA_MODEL.md` | Canonical | Approved Tier 0 specification at `docs/DATA_MODEL.md`. |
| `DATA_REPOSITORY.md` | Partial | Tier and layer definitions cover Print Sheet and Slot lifecycle boundaries; further subsystem-driven expansion remains pending. |
| `RULES_ENGINE.md` | Canonical | Approved Tier 0 specification at `docs/RULES_ENGINE.md`. |

### Tier 1 / Subsystem Specifications

| Specification | Status | Repository basis |
| --- | --- | --- |
| `DATABASE_ENGINE.md` | Deferred until subsystem implementation | No specification exists; persistence is outside Phase 56. |
| `IMPORT_PIPELINE.md` | Deferred until subsystem implementation | Ingestion code exists, but no canonical subsystem specification exists. |
| `API_CONTRACT.md` | Deferred until subsystem implementation | No API subsystem is implemented or specified. |
| `SIMULATION_ENGINE.md` | Deferred until subsystem implementation | No simulation subsystem is implemented or specified. |
| `ANALYTICS_ENGINE.md` | Deferred until subsystem implementation | No analytics subsystem is implemented or specified. |
| `COLLECTION_MANAGER.md` | Deferred until subsystem implementation | No collection subsystem is implemented or specified. |
| `MARKET_INTELLIGENCE.md` | Deferred until subsystem implementation | No market subsystem is implemented or specified. |
| `AI_ADVISOR.md` | Deferred until subsystem implementation | Vision documents exist, but no canonical advisor specification exists. |

## Session Startup Protocol
Repository-driven session management is defined by:

- `docs/SESSION_STATE.md` — current version, phase, milestone status, risks, and handoff checklist
- `docs/NEXT_TASK.md` — the single approved next objective and its definition of done
- `docs/HANDOFF.md` — the concise, replaceable transfer note from the most recent session
- `docs/AI_CONTRIBUTING.md` — the authoritative governance, contributor responsibilities, and collaboration guide
- `docs/DEVELOPMENT_PLAYBOOK.md` — reusable implementation patterns and engineering procedures
- `docs/LESSONS_LEARNED.md` — reusable engineering knowledge and historical implementation insight
- `docs/RESEARCH_LOG_ARCHITECTURE.md` — Tier 0 architecture for versioned, evidence-grounded domain research
- `docs/RULES_ENGINE.md` — Tier 0 architecture for data-driven product-rule interpretation
- `docs/CODEX_WORKFLOW.md` — the standard operating procedure for Codex sessions

At session startup, read those documents together with `PROJECT_INVENTORY.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and `CHANGELOG.md`. `AI_CONTRIBUTING.md` governs collaboration and document priority, `DEVELOPMENT_PLAYBOOK.md` supplies repeatable procedures, and `LESSONS_LEARNED.md` preserves reusable engineering insight. `HANDOFF.md` supplies only the immediate transition; ongoing status belongs in `SESSION_STATE.md`, approved work in `NEXT_TASK.md`, and history in `CHANGELOG.md`. Continue only from the repository-defined next task; do not rely on previous chat history.
