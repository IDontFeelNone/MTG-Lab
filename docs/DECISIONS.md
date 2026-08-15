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
