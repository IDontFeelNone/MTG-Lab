# Architect's Notebook

> **Tier: Tier 0 (Institutional Memory)**  
> **Status: Current chronological design journal** — Phase 83, 2026-07-30  
> **Architecture:** v12 (unchanged)

## How to read this journal

This notebook preserves why major architectural choices were made. It summarizes accepted
history; it does not replace the authoritative contracts linked from each entry. New major
milestones should append an entry rather than revise earlier reasoning with hindsight.

## 2026-07-28 — Repository vision and data-driven architecture

**Problem.** Product analysis is unreliable when rules are embedded in application code,
source claims are informal, and future contributors depend on chat context.

**Decision.** Make the Git repository the authority; describe products with structured,
versioned data; separate modular engines; favor deterministic, reproducible results.

**Alternatives considered.** A product-specific simulator, a database as primary truth,
and rapid feature development backed by undocumented assumptions.

**Rationale.** Reviewable data and documentation can be versioned, reproduced, audited,
and extended to new products without rewriting generic engines.

**Tradeoffs.** Up-front contracts and validation slow visible feature delivery. Repository
workflows initially favor correctness and a single writer over scale.

**Future implications.** Databases and interfaces must remain generated consumers. New game
or product support should exercise generic contracts rather than add special cases.

**Related documents.** [`ARCHITECTURE.md`](ARCHITECTURE.md),
[`DECISIONS.md`](DECISIONS.md), [`AI_ARCHITECTURE_VISION.md`](AI_ARCHITECTURE_VISION.md),
[`CONSTITUTION.md`](CONSTITUTION.md).

## 2026-07-28 — Hybrid persistence architecture

**Problem.** The project needs durable, queryable state eventually, but early database-first
design would obscure review history and make local reproducibility depend on infrastructure.

**Decision.** Keep version-controlled canonical data authoritative and treat database,
indexes, caches, and other persistence as rebuildable projections. Use deterministic
filesystem repositories for the pre-alpha reference implementation.

**Alternatives considered.** Database-only authority, Git-only persistence forever, or two
peer sources of truth synchronized bidirectionally.

**Rationale.** The hybrid direction combines auditable source control with future query
performance while avoiding split-brain authority.

**Tradeoffs.** Current stores load eagerly, use linear lookups, and assume a single writer.
Projection rebuild and consistency rules must be designed before operational scale.

**Future implications.** Indexes should sit behind stable interfaces; concurrency needs
locks or generation checks; migration must retain provenance and deterministic rebuilds.

**Related documents.** [`DATA_REPOSITORY.md`](DATA_REPOSITORY.md),
[`DATA_MODEL.md`](DATA_MODEL.md), [`../ARCHITECTURE_REVIEW_v1.md`](../ARCHITECTURE_REVIEW_v1.md).

## 2026-07-30 — Canonical contract evolution (Phases 78–80)

**Problem.** Earlier Product, Card, and Printing contracts could not faithfully express
composable products, printing facts, assertion-level provenance, partial knowledge, or
unknown collation without lossy assumptions.

**Decision.** Add compatible v2 composition contracts and v3 Card/Printing assertion and
uncertainty contracts. Preserve v1 bytes and expose compatibility projections rather than
rewriting retained canonical history.

**Alternatives considered.** Mutating v1 records in place, implementing MB2-specific fields,
continuing with incomplete schemas, or allowing consumers to infer missing values.

**Rationale.** Additive versioning preserves history and downstream compatibility while
making uncertainty and evidence eligibility machine-readable and product-agnostic.

**Tradeoffs.** Multiple schema generations and adapters add temporary complexity and
consolidation debt. Consumers must use the canonical boundary rather than storage shapes.

**Future implications.** Contract migrations require explicit review; fail-closed consumers
can distinguish eligible facts from candidates, conflicts, and unknowns.

**Related documents.** [`CANONICAL_CONTRACT_v2.md`](CANONICAL_CONTRACT_v2.md),
[`CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`](CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md),
[`PHASE_79_PREIMPLEMENTATION_REVIEW.md`](PHASE_79_PREIMPLEMENTATION_REVIEW.md).

## 2026-07-30 — Evidence model and controlled promotion (Phases 60–67)

**Problem.** A plausible canonical record is not enough: the project must prove where each
claim came from, preserve delivered bytes, detect conflict, and prevent unreviewed facts
from entering canonical state.

**Decision.** Separate evidence bundles, parsed artifacts, normalized candidates, review
reports, canonical promotion, and immutable audits. Require content integrity, registered
sources, field provenance, validation, and explicit approval.

**Alternatives considered.** Direct import from provider payloads, file-level citations
without field lineage, trust based on provider name, and automatic promotion after schema
validation.

**Rationale.** Explicit stages make insufficiency and disagreement visible and ensure every
promoted fact can be reconstructed from evidence and a human-accountable decision.

**Tradeoffs.** Evidence preparation and promotion are intentionally slower; bounded sources
may leave datasets incomplete for long periods.

**Future implications.** A shared lineage reader can unify provenance without replacing
immutable records. Research and AI must consume evidence-aware facts rather than bypass the
gate.

**Related documents.** [`EVIDENCE_REPOSITORY.md`](EVIDENCE_REPOSITORY.md),
[`EVIDENCE_REVIEW_ENGINE.md`](EVIDENCE_REVIEW_ENGINE.md),
[`CANONICAL_IMPORT_PIPELINE.md`](CANONICAL_IMPORT_PIPELINE.md),
[`RESEARCH_LOG_ARCHITECTURE.md`](RESEARCH_LOG_ARCHITECTURE.md).

## 2026-07-30 — Raw acquisition framework (Phase 82)

**Problem.** Complete datasets require repeatable provider acquisition, but existing raw
artifacts were bounded to particular pipelines and a download could be mistaken for truth.

**Decision.** Introduce a source-neutral upstream framework with immutable checksum-addressed
snapshots, explicit provider adapters and trust policies, deterministic normalized source
records, candidate assertions, change reports, and separately auditable resumable runs.
Keep promotion outside the framework.

**Alternatives considered.** Live-provider code coupled to import, mutable latest snapshots,
one-step download-and-canonize workflows, or repurposing domain-specific evidence formats as
a universal contract.

**Rationale.** Exact bytes and explicit stages provide reproducibility and recovery while
ensuring normalization and provider reputation cannot manufacture canonical authority.

**Tradeoffs.** No live provider or automatic population is delivered; licensing review and
adapter work remain necessary. Duplicate upstream artifact types require clear boundaries.

**Future implications.** Future adapters must be terms-compliant, source-specific only at the
edge, and independently reviewed. Snapshot lineage can support catalog, market, and research
inputs without merging their domain semantics.

**Related documents.** [`RAW_DATA_ACQUISITION_FRAMEWORK.md`](RAW_DATA_ACQUISITION_FRAMEWORK.md),
[`CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`](CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md),
[`MYSTERY_BOOSTER_2_DATASET.md`](MYSTERY_BOOSTER_2_DATASET.md).

## 2026-07-30 — Institutional memory and constitutional guidance (Phase 83)

**Problem.** Contracts describe what exists, but rationale distributed across milestone
documents can be lost or contradicted by future sessions.

**Decision.** Establish a Constitution, this chronological notebook, an architectural future
vision, and a question-led product compass as Tier 0 guidance.

**Alternatives considered.** Expanding the roadmap alone, relying on commit history, or
placing design rationale in AI prompts and handoffs.

**Rationale.** Permanent repository-owned memory lets human and AI contributors understand
both constraints and intent without treating conversation history as authority.

**Tradeoffs.** Tier 0 documents require disciplined maintenance and careful distinction
between constitutional law, architecture, vision, and current authorization.

**Future implications.** Major decisions should append rationale here; proposed capabilities
should trace to user questions and constitutional constraints before implementation.

**Related documents.** [`CONSTITUTION.md`](CONSTITUTION.md),
[`FUTURE_VISION.md`](FUTURE_VISION.md),
[`QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`](QUESTIONS_MTG_LAB_SHOULD_ANSWER.md).
