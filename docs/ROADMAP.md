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

**Current Phase:** Phase 65 ✅ Complete

**Current Transition:** Phase 66 evidence-waiting; PR #18 handoff structure is
present, contains no acquired artifacts, and has not entered verification

**Current Version:** v0.x

**Repository Status:** Active Development

---

# Completed Milestones

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

# Most Recently Completed Milestone

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

## Phase 66 — MB2 Pack Topology and Selection-Semantics Evidence Verification

**Status:** Evidence-waiting; processing has not begun.

The controlled research handoff structure from PR #18 exists, but its manifest
declares no artifacts and its artifact directory is empty. Verification is
conditionally authorized only after an artifact-bearing, content-complete,
independently reviewed handoff satisfies the entry gate. Phase 66 may then
preserve supported evidence for pack topology, pool mapping, replacement,
treatments, and collation; reconcile the Rule Claim Matrix; and decide whether
Tier 0 can express the supported behavior. It does not authorize canonical
population or engine work. The end-to-end critical path is recorded in
`docs/FIRST_BOOSTER_PLAN.md`.

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

## Evidence Debt

- No artifact-bearing Phase 66 external handoff exists.
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

- Persistence/database, analytics, market intelligence, collection management,
  API, UI, and AI advisor layers remain intentionally deferred. Their absence is
  roadmap scope, not evidence that partially implemented behavior is complete.

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
