# MTG Lab Engineering Decisions

This document records significant architectural and engineering decisions for MTG Lab.

Its purpose is to explain why major technical decisions were made so future contributors can understand the rationale behind the architecture.

Each accepted decision remains part of the project's architectural history. A decision that changes later should be superseded by a newer decision rather than silently removed or rewritten.

---

## Decision 001 — MTG Lab Is a Platform

**Status:** Accepted

MTG Lab is a research and decision-intelligence platform for collectible trading card games.

Magic: The Gathering is the initial supported game, with Mystery Booster 2 serving as the reference implementation.

The architecture must remain generic enough to support additional Magic products and eventually other collectible trading card games without redesigning the core engine.

### Reasoning

Building a platform instead of a single-product application maximizes long-term flexibility and encourages reusable architecture.

---

## Decision 002 — Data-Driven Product Definitions

**Status:** Accepted

The core engine must not contain hard-coded knowledge of specific products.

Products are described through structured data, including:

- Products
- Card pools
- Printings
- Slots
- Print sheets
- Probability definitions

The engine interprets this data rather than embedding product-specific behavior.

### Reasoning

Separating data from logic makes the platform extensible, testable, and easier to validate.

---

## Decision 003 — Reproducible Analytics and Simulations

**Status:** Accepted

All probabilistic analysis and simulations must support deterministic execution through configurable random seeds.

Simulation metadata should record:

- Product
- Repository version
- Database version, when applicable
- Simulator version
- Random seed
- Timestamp

### Reasoning

Deterministic execution simplifies debugging, validation, benchmarking, and scientific reproducibility.

---

## Decision 004 — Git Repository as the Canonical Source of Truth

**Status:** Accepted

The Git repository is the canonical source of truth for MTG Lab.

The repository owns:

- Architecture
- Schemas
- Canonical datasets
- Validation rules
- Documentation
- Version-controlled product definitions

Databases are generated persistence and query layers derived from the repository's validated canonical data. They improve runtime access and query performance but are not the authoritative source.

### Reasoning

Version-controlled data and definitions are reproducible, reviewable, auditable, and recoverable. Generated databases can be rebuilt from the repository without losing canonical knowledge.

---

## Decision 005 — Validation Before Consumption

**Status:** Accepted

Data must successfully pass validation before it is used by downstream components.

Validation includes:

- Schema validation
- Missing-reference checks
- Duplicate-identifier checks
- Probability integrity
- Print-sheet integrity
- Slot integrity
- Cross-reference validation

Only validated canonical data may be consumed by analytics, simulations, persistence layers, or AI components.

### Reasoning

Every downstream result is only as trustworthy as its input data.

---

## Decision 006 — Documentation Evolves With the Code

**Status:** Accepted

Documentation is part of the software.

Architectural, structural, or behavioral changes should include corresponding documentation updates within the same development effort.

### Reasoning

Keeping documentation synchronized with implementation reduces technical debt and improves maintainability.

---

## Decision 007 — Documentation-First Development

**Status:** Accepted

Major architectural work should be designed, documented, and reviewed before implementation.

Implementation follows approved documentation rather than defining architecture informally as code is written.

### Reasoning

Documentation-first development minimizes architectural drift, reduces expensive refactoring, and provides a stable implementation target.

---

## Decision 008 — Layered Architecture

**Status:** Accepted

MTG Lab follows a layered architecture.

The principal layers include:

- Repository
- Ingestion
- Validation
- Probability
- Analytics
- AI reasoning
- Applications

Each layer has a clearly defined responsibility and communicates through stable interfaces.

### Reasoning

Layer separation reduces coupling, improves testability, and allows subsystems to evolve independently.

---

## Decision 009 — Canonical Data Pipeline

**Status:** Accepted

External data follows the standard lifecycle:

```text
Raw
  ↓
Processed
  ↓
Canonical
  ↓
Validated
```

Raw data preserves acquired source material.

Processed data contains normalized intermediate representations.

Canonical data represents the repository's approved structured definitions.

Validated canonical data is eligible for use by persistence, analytics, simulations, and AI reasoning.

### Reasoning

A standardized pipeline improves traceability, repeatability, auditability, and data quality.

---

## Decision 010 — Hybrid SQLAlchemy 2.0 Persistence Layer

**Status:** Accepted

MTG Lab uses SQLAlchemy 2.0 for its persistence layer, with SQLite as the initial database backend.

The persistence subsystem may use SQLAlchemy ORM models, SQLAlchemy Core operations, and direct database features where appropriate, while keeping domain and business logic independent of a specific database engine.

### Reasoning

This hybrid approach provides strong schema management, maintainable application models, efficient bulk operations, and a practical migration path to more capable database backends.

---

## Decision 011 — AI Reasons Over Structured Knowledge

**Status:** Accepted

AI components reason over structured, validated repository data rather than relying on conversational memory as the primary knowledge store.

AI serves as a retrieval, analysis, comparison, and explanation layer over canonical knowledge and analytical outputs.

### Reasoning

Grounding AI in structured, version-controlled information improves reliability, transparency, reproducibility, and explainability.

---

## Decision 012 — Mystery Booster 2 Is the Reference Implementation

**Status:** Accepted

Mystery Booster 2 is the first complete product implementation used to validate the MTG Lab architecture.

Its product definitions, card pools, print sheets, collation rules, probabilities, validation evidence, and simulations must be represented through the same generic systems intended for future products.

No MB2-specific assumptions may be embedded in the reusable platform engine.

### Reasoning

Mystery Booster 2 is complex enough to rigorously test the architecture while preserving the platform's long-term extensibility.

---

## Decision 013 — Research Log Is a Tier 0 Architectural Subsystem

**Status:** Accepted

The Research Log is established as a Tier 0 architectural subsystem of MTG Lab. Its authoritative specification is `docs/RESEARCH_LOG_ARCHITECTURE.md`.

This decision approves only the Research Log architecture. Implementation, database schema, persistence, migrations, and application code remain future work and require separate design and approval.

### Reasoning

Approving the architecture establishes the Research Log's responsibilities and boundaries without prematurely committing the project to implementation or storage details.

---

## Decision 014 — Deterministic Shared Decision Contracts

**Status:** Accepted

Domain analytics provide opaque, versioned evidence envelopes to one game-neutral deterministic
policy boundary. The shared layer owns explicit requests, alternatives, policy evaluation,
structured recommendations, abstention, provenance, replay identities, and the AI-facing projection;
domains own metric and action semantics. Missing, unsupported, incomplete, contradictory, or tied
required evidence fails closed. An LLM may explain the completed recommendation but may not calculate
or change it. This is an additive refinement within frozen Architecture v12.

### Reasoning

One reproducible substrate prevents domain recommendation silos, preserves unknowns and provenance,
and lets future collectible-game domains evolve without embedding their semantics in shared code.

---

## Decision 015 — Product Intelligence Owns Descriptive Fixed-Content Economics

**Status:** Accepted

Product Intelligence owns immutable fixed-content manifests, sealed acquisition-cost contracts, thin bindings to supplied Market Intelligence observations, and deterministic descriptive aggregation. Exact comparisons fail closed across incomplete contents or incompatible currency, provider, time, price-type, printing, finish, language, or treatment dimensions. Acquisition objectives and action selection remain in Decision Intelligence. Intrinsic component value, presale scarcity premium, and sealed collectible premium remain separate concepts; unsupported premiums or risks are not fabricated.

### Reasoning

This minimum boundary supports reusable collectible-product analysis without duplicating Market, Card, Collection, or Decision Intelligence and without creating an open-ended product infrastructure thread. It is an additive refinement within Architecture v12.

---

## Future Decisions

Future architectural decisions will be added as MTG Lab evolves.

Examples include:

- Plugin architecture
- External data providers
- Public API design
- Market-intelligence integration
- Machine-learning pipelines
- Versioning strategy
- Deployment architecture
- Performance optimization
- Security model
- Multi-game schema boundaries

## Decision 016 — Production Fixed-Content Evaluation Requires a Reviewed Evidence Packet

**Status:** Accepted

Production fixed-content inputs cross a versioned, immutable, deterministic evidence boundary before
Product or Decision Intelligence runs. The packet composes existing Product and Market contracts,
adds retained source identity and integrity, explicit unknown/completeness and transaction-cost
states, and preserves independent evidence timestamps. A separate human review returns only
`READY_FOR_EVALUATION` or `NOT_READY_FOR_EVALUATION`; it never selects an acquisition action.
Production evaluation is prohibited unless the packet is READY.

### Reasoning

This fail-closed admission boundary makes real inputs reconstructable and auditable without
transferring recommendation ownership, duplicating Market history, mutating canonical data, or adding
a named-product acquisition subsystem. It is additive within frozen Architecture v12.

---

## Decision 017 — Public Architectural Authority and Immutable Operator Canonical Snapshots

**Status:** Accepted

**Architecture classification:** Architecture v13 — ACTIVE APPROVED architecture

The owner approved Decision 017 and the v13 direction reviewed at
`3d21656b9f67a3089f32c5613804a1984fb44139` in PR #175. This approval authorizes
the documentation/governance transition only. No runtime implementation is
authorized by that architecture approval alone. Architecture v12 is the previous
historical architecture baseline; its filesystem/Git-bound implementation remains
the explicit legacy/public compatibility route.

MTG Lab retains public Git authority over architecture, source code, schemas,
policies, identity/validation rules, deterministic algorithms, transformations,
migrations, provider adapters, contracts, safe/public fixtures and public
architecture/version manifests. Production canonical data may be an explicitly selected,
reviewed, validated immutable operator-managed snapshot with independently
permissioned source evidence. Generated databases, projections and caches remain
subordinate to that snapshot. Personal collection data and credentials remain
separate trust domains.

A snapshot is authoritative only for its declared game, scope, content identity,
schema/policy versions, capabilities, provenance/evidence bindings and approved
operation/use scope. Private location alone does not make data canonical.
Collections, holdings, storage information, preferences and assessments remain
separate personal data, outside the shared canonical card-data snapshot. Source
evidence is independently governed from both canonical and personal data.

### Relationship to accepted decisions

This decision prospectively **supersedes Decision 004 only where it requires
production canonical datasets to live in public Git and production knowledge to
be rebuildable from public Git alone**.
It preserves Git architectural/code authority and generated-database subordination.
Rebuild requires the exact code plus retained authorized snapshot/evidence, not
public Git alone. This changes the explicit Tier-0 repository-authority invariant
also stated in DATA_MODEL and DATA_REPOSITORY, hence v13 rather than a path-only
additive v12 interpretation.

It **clarifies/refines Decision 009**: Raw → Processed → Canonical → Validated,
explicit reviewed promotion, provenance and validation before use remain. The
approved canonical definitions are bound to the selected immutable authority
snapshot under public repository-owned contracts, not necessarily stored in the
public code repository. The lifecycle is not replaced by startup provider fetches.

Decision 010 remains the generated SQLAlchemy persistence direction; it is not
currently implemented SQL runtime. Decision 011 is clarified from repository-data
location to structured validated selected-snapshot knowledge, preserving the
prohibition on conversation memory as canonical authority. Stable IDs, game-neutral
engines, deterministic results and all other accepted invariants remain.

### Gates and scope

Snapshot integrity, authenticated admission/release authority and permission to
process, privately retain, redistribute, serve or export data are independent.
Private storage or a digest is no permission shortcut. Unavailable/incompatible
required snapshots fail closed; no hidden seed/provider/history fallback. Existing
IDs, historical bytes/expected hashes and immutable audits remain interpretable.

The accepted architecture direction, alternatives, design contracts, compatibility, security and
migration plan are in [EXTERNAL_CARD_DATA_PLANE.md](EXTERNAL_CARD_DATA_PLANE.md).
This entry changes governance authority, not runtime behavior or dataset state.
The pending MB2 810 recommendation remains unadmitted; architecture approval is
not an owner admission decision. It grants no processing, private-retention,
public-redistribution, free/commercial application or protected-data AI-export
permission. It does not resolve the nine held multiface candidates, owner spelling
proposals or physical Printing verification; approve a source-policy plan; change
`SOURCE_POLICY_CLEARED_PLANS`; or authorize acquisition, protected production
snapshots, SQL, Rules Intelligence or simulation implementation.

After this governance acceptance, the owner separately authorized **V13 Stage 1 —
Fictional Canonical Snapshot Attachment**. Its fictional-only read-side implementation
is pending PM review; see [the runtime scope](V13_STAGE1_SNAPSHOT_ATTACHMENT.md).
This later instruction does not grant real-data permission or admission authority.
Stage 1 is now merged in PR #176. The owner separately authorized **V13 Stage 2 —
Legacy/Public Snapshot Profile Review** as review only; see [its findings](V13_STAGE2_LEGACY_PUBLIC_PROFILE_REVIEW.md).
A real legacy profile remains unimplemented and Stage 3 is NOT AUTHORIZED.
See [the migration plan](EXTERNAL_CARD_DATA_PLANE_MIGRATION.md).

### Reasoning

Open code and reproducible intelligence do not require publicly redistributing
every useful provider dataset. An immutable effective snapshot can preserve
structured authority, review, provenance, deterministic identity and replay while
supporting permitted operator-supplied/licensed inputs. Public CI uses fictional
safe fixtures; protected integration tests exact permitted production snapshots.
