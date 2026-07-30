## Phase 88 — External Dataset Ingestion Framework

- Added provider-agnostic JSON, CSV, and ZIP ingestion with a canonical external dataset
  manifest, checksum and structure validation, safe archive handling, deterministic
  registration, duplicate detection, and extensible format adapters.
- Composed verified supplied bytes into the unchanged raw acquisition and Knowledge Review
  Package pipeline. Ingestion stops at human review and never invokes canonical promotion.
- Added `ingest`, `ingest validate`, `ingest inspect`, and `ingest list` CLI operations,
  comprehensive failure/idempotence tests, and the ingestion contract documentation.
- Reconciled current-state documents to record Phase 87 as merged and evidence-blocked
  before establishing Phase 88. Architecture v12 remains unchanged; no MB2 data was imported.

## Phase 87 — Mystery Booster 2 Acquisition Pilot (evidence-blocked)

- Completed the pre-implementation source and Architecture v12 compatibility assessment.
- Stopped before acquisition because no retrievable, immutable, legally reviewed 25–50-card raw source was available; no dataset was registered and no canonical data was promoted.
- Added `docs/MYSTERY_BOOSTER_2_ACQUISITION_PILOT.md` with source inventory, evidence gap, limitations, and reproduction requirements.

# Changelog

## Phase 86 — Canonical Dataset Import Framework (Pilot)

- Added first-class dataset registration, deterministic entity resolution, governed import sessions, reporting, unified CLI commands, and a reviewed non-MB2 pilot.
- Composed the existing acquisition, review, and promotion engines without changing Architecture v12.

## Unreleased

- Phase 85 Canonical Promotion Engine v1: fail-closed Knowledge Review Package validation, deterministic provenance-preserving canonical versions, immutable success/failure audits, supersession chains, compensating rollback, replay verification, acquisition CLI commands, and comprehensive tests. Architecture v12 remains unchanged and no MB2 data was imported.

## Evidence Review Engine

- Added a product-agnostic pre-promotion engine for external evidence handoffs.
- Added versioned handoff and review-report schemas, deterministic JSON and
  Markdown renderers, integrity/provenance/completeness checks, duplicate and
  explicit-claim conflict detection, and comprehensive unit coverage.
- Preserved the Phase 66 evidence-waiting boundary: no product-specific logic,
  canonical data, rules, generators, probabilities, or simulations were added.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]

### Added

- Phase 84 Knowledge Acquisition Pipeline v1: deterministic dataset identities, independent
  provider policies, pre-review validation, machine-readable reports, review packages,
  offline collectible-card fixtures, CLI stages, documentation, and tests. No canonical
  promotion or Mystery Booster 2 population was performed; Architecture v12 is unchanged.

### Changed

- Phase 83.1 reconciled authoritative project-state documentation after the successful
  Phase 83 merge: Phase 83 is complete, Phase 82 remains the latest runtime milestone,
  Architecture v12 is unchanged, the active baseline is 154 passing tests, and no prior
  pull-request merge gate or follow-on implementation authorization remains active.

### Added

- Phase 83 Tier 0 institutional memory: a Project Constitution and amendment process, a
  chronological Architect's Notebook, an architectural Future Vision, and a user-question
  compass. Project-state documents now cross-reference their roles. This documentation-only
  milestone leaves Architecture v12, runtime behavior, schemas, canonical data, providers,
  simulation, and intelligence implementation unchanged.


### Added

- Phase 82 generic raw data acquisition framework: immutable checksum-addressed snapshots, provider abstraction and offline fixture, normalized source records, Phase 80 candidate-assertion bridge and change reports, auditable resumable acquisition runs, security controls, explicit-stage CLI, documentation, and comprehensive tests. No canonical records or MB2 population were added; Architecture v12 remains unchanged.

- Phase 79 pre-implementation inventory and architectural-fit review. The review found
  blocking Card/Printing field, assertion-provenance, unknown-collation, and v2 importer
  limitations, so no MB2 dataset, fixture, canonical record, or collation claim was
  added and Architecture v12 remains unchanged.

- Phase 77.1 repository documentation reconciliation: current session state, executive
  dashboard, handoff, next task, documentation hierarchy, startup workflow, historical
  status labels, and implementation-versus-vision wording now describe one consistent
  baseline through Phase 77. Historical plans remain retained. No runtime behavior,
  tests, schemas, models, public APIs, or canonical data changed.

- Phase 77 repository-wide Architecture v12 review, including subsystem maturity
  ratings, dependency direction, technical debt and risk register, documented defects,
  non-breaking consolidation sequence, future scaling considerations, and reconciled
  inventory and roadmap. This milestone changes no runtime behavior, canonical data,
  public API, or user-facing feature.

- Documentation reconciliation for the merged first artifact-bearing Phase 67
  evidence handoff and its successful Evidence Review Engine run. The handoff's
  re-delivered official product-title capture supports only MB2 identity; frozen
  Tier 0, the evidence-insufficient rule assessment, and the prohibition on
  canonical promotion remain unchanged.
- An executive `docs/PROJECT_STATUS.md` dashboard that records verified repository
  counts, documentation authority, Phase 66 entry and exit gates, mandatory stop
  conditions, debt categories, critical path, risks, and bounded estimates.
- Documentation recovery that reconciles the PR #18 empty-artifact research
  handoff into the Phase 66 evidence-waiting state without beginning Phase 66,
  changing canonical data, or authorizing downstream product layers.
- A post-Phase 65 architectural assessment and complete dependency plan for the
  first evidence-backed Mystery Booster 2 booster, including a bounded proposed
  evidence-acquisition milestone; no implementation or canonical data changed.
- A documentation-only Phase 66 Evidence Acquisition Packet, controlled raw
  handoff layout, source/claim checklist, stop conditions, and machine-readable
  external intake manifest template for network-restricted operation.
- A retained, schema-validated Mystery Booster 2 Rule Claim Matrix with stable claims, evidence classifications, Source Record and bundle references, precise locators, Tier 0 entity mappings, and explicit uncertainty.
- A deterministic Evidence Sufficiency Report separating known, partial, and unknown claims, blockers for canonical rules, pack generation, and probability, plus a no-redesign architectural sufficiency assessment.
- A content-verified archive of the controlled official Mystery Booster 2 product-title capture and cross-validation for non-canonical rule research artifacts.
- Scalable evidence-backed Card and Printing batches of up to twenty-five complete records, with oversized-input rejection and manifest-declared record-count and Printing-identity boundaries.
- Versioned deterministic pre-promotion review reports retained alongside intermediate artifacts, summarizing new and reused Cards, new Printings, duplicates, conflicts, rejected records, and expected repository count changes.
- Evidence-repository-exclusive Mystery Booster 2 Card and Printing Wave 2,
  adding one verified pair with deterministic intermediate artifacts, declared
  embedded sources, controlled dependency-order promotion, and immutable audits.
- A verified-wave application boundary that selects one archived JSON artifact,
  validates its embedded source identifiers, and identifies existing Cards that
  must not be promoted again.
- Canonical evidence archive foundation under `data/sources/`, including a
  versioned evidence-manifest schema, content-verified archived bundle loading,
  provenance validation against canonical Source Records, and an archive of the
  existing Mystery Booster 2 Wave 1 evidence without additional card population.
- Deterministic multi-source Mystery Booster 2 Card and Printing ingestion,
  demonstrated by three evidence-supported pairs promoted in dependency order
  with retained raw, parsed, candidate, canonical, and immutable audit records.
- Canonical Print Sheet and Slot repository foundation with minimally aligned
  provenance and game-scoped contracts, stable paths, deterministic snapshots,
  complete dependency validation, controlled promotion, immutable audits, and
  dependency-safe rollback verified only with temporary synthetic fixtures.
- Approved Tier 0 Rules Engine Specification and the minimal canonical
  repository-layer boundaries needed to support future Print Sheet and Slot
  records without introducing implementation behavior.
- Approved Tier 0 Data Model Specification as the canonical architectural
  contract for entity identities, relationships, provenance, and validation.
- Initial repository foundation for Mystery Booster 2 analysis.
- Canonical project layout for data, source modules, tests, scripts, notebooks, and documentation.
- Versioned schemas and validation infrastructure for canonical records.
- Mystery Booster 2 canonical product foundation with source provenance and no inferred collation data.
- Generic source registry and acquisition manifests with validated source-target references.
- Evidence-preserving ingestion foundation with deterministic SHA-256 hashing, immutable filesystem evidence storage, parser contracts, and a non-canonical pipeline.
- Parsed-record and normalized-candidate artifact schemas, immutable models, field-level provenance, cross-artifact validation, and hash-safe intermediate storage.
- Controlled Mystery Booster 2 official product-page title evidence, a deterministic product-specific HTML parser, and provenance-complete non-canonical product normalization.
- Explicitly approved canonical product promotion with validation gates, complete provenance snapshots, immutable decision audits, idempotency, conflict detection, rejection, and audited rollback.
- Canonical Card and Printing repository foundation with deterministic stable
  identifiers and snapshots, official source evidence, field-level provenance,
  structural validation, identity-path validation, and Printing-to-Card
  referential validation.
- Entity-agnostic candidate review and canonical promotion, enabled for Card and
  Printing candidates with explicit approval and rejection, immutable audits,
  idempotent and conflict-safe writes, source and provenance validation,
  Printing-to-Card enforcement, and dependency-safe rollback.
- A fixed Phase 58 increment of ten official-source-attributed Limited Edition
  Alpha Cards and Printings, including retained candidate artifacts, canonical
  records, and twenty immutable approval audits.

[Unreleased]: https://github.com/IDontFeelNone/MTG-Lab/compare/v0.0.0...HEAD

## Historical — Phase 80 Canonical Card, Printing, Evidence, and Uncertainty Contract (2026-07-30)

Phase 80 adds the compatible v3 Card/Printing and assertion-level evidence contract,
explicit partial-knowledge semantics, deterministic promotion, legacy projections,
and fail-closed simulation readiness. Historical canonical records remain unchanged;
full Mystery Booster 2 population remains out of scope. See
`docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`. Its former pull-request merge gate
is satisfied and is not active guidance.
