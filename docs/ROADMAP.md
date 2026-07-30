# MTG Lab Roadmap

> **Living implementation roadmap for MTG Lab.**

---

# Vision

## Mission

Build the world's premier AI-powered decision intelligence platform for collectible card games by combining structured data, advanced analytics, simulation, and explainable artificial intelligence.

## Current Maturity

**Stage:** Pre-Alpha

Current focus is establishing the canonical architecture and reference implementation using Mystery Booster 2.

---

# Current Status

**Current Phase:** Phase 77.1 — Repository Documentation Reconciliation

**Current Transition:** Repository-authoritative documentation reconciled locally;
merge remains contingent on green GitHub Actions. Architecture v12 is unchanged, and
no next implementation milestone is approved.

**Current Version:** v0.x

**Repository Status:** Active Development

---

# Completed Milestones

## Phase 68–76 — Foundational Backend Vertical Slice

- Phase 68–69 established immutable observation verification and the generic
  observation import pipeline.
- Phase 70–71 established the typed Canonical Repository and reviewed local Canonical
  Import Pipeline.
- Phase 72–73 established the Market Provider Framework and versioned External Mapping
  Layer.
- Phase 74 established the immutable Collection Engine.
- Phase 75 established the deterministic Analytics Engine and its seven factual reports.
- Phase 76 established the explicit, explainable Decision Engine.

All remain downstream of evidence-backed canonical identity and introduce no MB2 pack
rules, probability, simulation, or user-facing application feature.

## Phase 77 — Architecture Consolidation & Technical Debt Review

### Objective

Assess all implemented backend subsystems without redesigning Architecture v12 or
changing behavior.

### Success Criteria

- [x] Repository-wide architecture assessment and dependency diagram.
- [x] Responsibilities, coupling, cohesion, APIs, dependency direction, drift,
  duplication, naming, organization, scale, extension, tests, and documentation
  assessed for every requested subsystem.
- [x] Maturity ratings, risks, technical debt, future scale concerns, and a non-
  breaking consolidation sequence recorded in `ARCHITECTURE_REVIEW_v1.md`.
- [x] Defects documented separately and not fixed automatically.
- [x] Inventory, roadmap, and changelog reconciled through Phase 77.
- [ ] GitHub Actions green on the Phase 77 pull request (merge gate).

## Phase 77.1 — Repository Documentation Reconciliation

### Objective

Reconcile current-state, handoff, roadmap, architecture-overview, and historical-plan
documentation with the implementation through Phase 76 and the Phase 77 review.

### Success Criteria

- [x] Current session state, dashboard, handoff, and next task report one Phase 77.1
  baseline with accurate subsystem status, counts, and authorization.
- [x] Phase 65–67 plans remain retained and are explicitly labeled Historical,
  Superseded, or Reference where appropriate.
- [x] README and Architecture v12 distinguish implemented behavior from target vision.
- [x] Documentation status labels and subsystem names are standardized.
- [x] No application code, tests, schemas, models, APIs, or canonical data changed.
- [ ] GitHub Actions green on the Phase 77.1 pull request (merge gate).

## Foundation
- Initial repository
- Architecture principles
- Documentation-first workflow

## Repository Architecture
- Canonical directory structure
- Multi-game design
- Shared analytics architecture

## Documentation
- README
- AI Architecture Vision
- Project Inventory
- Roadmap
- Architectural standards

## Portfolio Intelligence
- Portfolio planning
- Financial analytics vision

## Tournament Command Center
- Initial architecture complete

## Universal Scanner
- (Update when complete)

---

# Earlier Evidence Milestone

## Phase 65 — Mystery Booster 2 Product-Rule Evidence Sufficiency Assessment

### Objective
Preserve and reconcile evidence-backed MB2 rule claims without populating
canonical Product Rules or changing Tier 0.

### Success Criteria
- [x] A deterministic Rule Claim Matrix records stable claims, classifications,
  evidence references, precise locators, affected Tier 0 entities, and uncertainty.
- [x] An Evidence Sufficiency Report separates known, partial, and unknown facts
  and identifies blockers for rule population, pack generation, and probability.
- [x] An Architectural Sufficiency Assessment evaluates the existing Tier 0
  relationship, retains one open question, and makes no redesign.
- [x] Archived evidence, processed research, and canonical data remain separate.
- [x] No Product, Print Sheet, Slot, probability, simulation, or analytics data changed.

---

# Previously Completed Milestone

## Phase 64 — Scalable Evidence-Backed Card and Printing Batch Population

### Objective
Validate complete, verified Card and Printing batches of up to twenty-five
records and retain a deterministic pre-promotion review report.

### Success Criteria
- [x] Complete batches accept one through twenty-five verified Printings.
- [x] Oversized batches fail without silent truncation.
- [x] Optional manifest boundaries enforce expected record counts and Printing IDs.
- [x] Review reports summarize all approved classifications and expected count changes.
- [x] Reports are schema-valid, deterministic, immutable intermediate artifacts.
- [x] No canonical rules or downstream subsystem behavior changed.

---

# Previously Completed Milestone

## Phase 63 — Mystery Booster 2 Card and Printing Population, Wave 2

### Objective
Populate a bounded second wave exclusively from verified Evidence Repository
bytes while enforcing source declaration and existing-Card invariants.

### Success Criteria
- [x] One previously unpopulated Card and Printing pair was supported and promoted.
- [x] Ingestion calls `load_evidence_bundle` and accepts no unchecked raw input.
- [x] Embedded source identifiers are declared by verified artifact provenance.
- [x] Existing canonical Cards are detected and excluded from Card promotion.
- [x] Deterministic artifacts and two immutable promotion audits are retained.
- [x] No Product, Print Sheet, Slot, rule, probability, or simulation data changed.

---

# Previously Completed Milestone

## Phase 62 — Evidence Repository Foundation

### Objective
Establish a stable repository archive for acquired evidence with versioned
manifests, content verification, and provenance validation.

### Success Criteria
- [x] Canonical `data/sources/` layout and evidence-manifest schema exist.
- [x] Archived bundles load only after path, size, and SHA-256 verification.
- [x] Artifact provenance resolves to declared canonical Source Records.
- [x] Existing Wave 1 evidence proves the subsystem without new card population.
- [x] No Product, Print Sheet, Slot, rule, probability, or simulation data changed.

---

# Previously Completed Milestone

## Phase 61 — Mystery Booster 2 Card and Printing Population, Wave 1

### Objective
Validate the complete deterministic ingestion and controlled-promotion workflow
on up to five evidence-supported Mystery Booster 2 Card and Printing pairs.

### Success Criteria
- [x] Three pairs were supported and promoted in dependency order.
- [x] Multiple sources retain field-level attribution.
- [x] Retained artifacts reproduce deterministically and six audits are immutable.
- [x] No Print Sheet, Slot, probability, or simulation work was introduced.

---

# Previously Completed Milestone

## Phase 60 — Canonical Print Sheet and Slot Repository Foundation

### Objective
Implement the approved repository lifecycle for Print Sheet and Slot records
without populating Mystery Booster 2 rules or expanding Tier 0 architecture.

### Success Criteria
- [x] Minimal schema alignment implements provenance and game scoping.
- [x] Generic loaders validate the complete canonical dependency graph.
- [x] Deterministic snapshots, promotion, immutable audits, and rollback work.
- [x] Temporary synthetic fixtures prove behavior without canonical population.

---

# Previously Completed Milestone

## Phase 59 — Rules Engine Architecture Migration

### Objective
Migrate the approved Rules Engine architecture into the Tier 0 repository
documentation without redesigning it or introducing implementation behavior.

### Success Criteria
- [x] The approved Rules Engine architecture is canonical in the repository.
- [x] Tier 0 data-repository layers explicitly support Print Sheets and Slots.
- [x] No schema, canonical data, or application behavior changed.
- [x] Print Sheet and Slot implementation remains unapproved pending review.

---

# Previously Completed Milestone

## Phase 58 — Initial Card and Printing Candidate Population

### Objective
Populate a fixed, official-source-backed increment through controlled promotion.

### Success Criteria
- [x] Ten Card and ten Printing candidates retain official source attribution.
- [x] Explicit approval promotes Cards before their associated Printings.
- [x] Twenty immutable promotion audits preserve the reviewed snapshots.
- [x] The bounded canonical increment is schema-valid and referentially safe.

---

# Earlier Milestones

## Phase 57 — Card and Printing Candidate Ingestion and Controlled Promotion

### Objective
Provide a reusable, entity-agnostic controlled-promotion framework and enable
it for Card and Printing candidates.

### Success Criteria
- [x] Explicitly approved Card and Printing candidates can be promoted.
- [x] Rejection, idempotency, conflict protection, and immutable audits are shared.
- [x] Printing promotion and rollback preserve Card referential integrity.
- [x] Unsupported entity types remain disabled.
- [x] Existing Product promotion remains compatible.

---

## Earlier Milestone

## Phase 56 — Card and Printing Repository Foundation

### Objective
Establish the first canonical Card and Printing records and validate their
identity relationship.

### Deliverables
- Canonical Card, Printing, and supporting Source Record foundation data.
- Stable identifier and repository-layout rules.
- Structural, provenance, identity-path, and referential validation.
- Deterministic validated snapshot output and focused tests.

### Success Criteria
- [x] Canonical Card and Printing records validate.
- [x] Every Printing references an existing Card.
- [x] Source evidence and field-level provenance are retained.
- [x] Invalid and orphaned records are rejected.
- [x] Output is reproducible and the complete suite passes.

### Dependencies
- None

---

# Upcoming Phases

## Post-77 consolidation candidates

No refactor is authorized by this roadmap entry. Separately approved milestones may:

1. publish stable public and provenance protocols;
2. add characterization tests for overlapping canonical, observation analytics, and
   market representations;
3. introduce compatibility adapters and internal ID indexes; and
4. harden single-writer filesystem transactions and recovery.

These changes must remain non-breaking and preserve Architecture v12. Feature work and
evidence-blocked MB2 rules are outside Phase 77.

## MB2 evidence-dependent work

**Status:** Blocked by evidence sufficiency; not authorized by Phase 77.

Phase 66 established the controlled external handoff. The first artifact-bearing
Phase 67 handoff was subsequently integrity/provenance reviewed, but its official
product-title capture supported only the already-known product identity. Preserved
evidence remains insufficient for pack topology, pool mapping, replacement,
treatments, collation, canonical rule population, probability, or simulation. The
end-to-end critical path and stop conditions remain in `docs/FIRST_BOOSTER_PLAN.md`.

---

## Phase 100+
Long-term platform evolution.

---

# Version Roadmap

## v0.x — Foundation
- Repository architecture
- Canonical datasets
- Documentation
- Reference implementation

## v0.5 — Core Analytics
- Probability engine
- Simulation
- Portfolio analytics

## v1.0 — MTG Decision Intelligence Platform
- Complete MTG platform
- REST API
- AI reasoning
- Desktop/Web applications

## v2.0 — Multi-Game Intelligence Platform
- Pokémon
- Lorcana
- One Piece
- Yu-Gi-Oh!
- Cross-game analytics

---

# Debt and Deferred Work

## Technical Debt

- Canonical promotion intentionally requires manual application-workflow
  decisions; batch-level transactional orchestration remains deferred.
- Cross-document status consistency is review-driven rather than enforced by an
  automated documentation validator.
- Research Log Tier 0 architecture is approved, but its implementation is deferred.
- Typed and schema-backed canonical repository representations overlap.
- Observation-specific analytics and market snapshot types overlap the newer generic
  Analytics and Market engines.
- Cross-subsystem provenance is comprehensive but lacks one vocabulary and lineage API.
- Filesystem loaders use eager tree scans, linear lookup, and single-writer assumptions.
- Stable serialization, immutable conversion, identifier, timestamp, and atomic-write
  helpers are duplicated across packages.

## Evidence Debt

- The reviewed Phase 67 artifact-bearing handoff adds no outcome-affecting rule
  evidence beyond the already-known MB2 product identity.
- Complete MB2 pack topology, event pools, weights/frequency semantics,
  replacement, treatments, conditionality, correlation, and sequencing remain
  unsupported by preserved evidence.

## Canonical-Data Debt

- Only 15 Cards and 15 Printings are populated, including four MB2 Printings.
- The MB2 Product remains a foundation record; canonical Print Sheets and Slots
  are empty and no canonical product rules or complete pools exist.

## Implementation Debt

- Generic pack generation, exact probability, simulation, and generated-pack
  validation are not implemented.
- Complete evidence-backed canonical population requires separately approved,
  bounded milestones after Phase 66 sufficiency and architectural-fit decisions.

## Deferred Product Layers

- Database-backed persistence, live market providers, API, UI, simulation, and AI
  advisor layers remain intentionally deferred. Market, collection, analytics, and
  deterministic decisions now have bounded v1 implementations; they are not complete
  product applications.

---

# Future Research

- AI-assisted deck construction
- Market forecasting
- Collection optimization
- Reinforcement learning
- Image recognition
- Automated product reconstruction
- Cross-game analytics
- Advanced simulation
