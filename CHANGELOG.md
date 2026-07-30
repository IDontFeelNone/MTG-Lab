# Changelog

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
