# MTG Lab

> **A decision intelligence platform for collectible card games, powered by structured data, advanced analytics, simulation, and explainable AI.**

MTG Lab is a research and analytics platform designed to help collectors, players, investors, and researchers make better decisions across collectible card games.

Rather than functioning as a traditional card database, MTG Lab transforms large collections of structured card data into explainable, actionable intelligence through statistical analysis, simulation, and AI-assisted reasoning.

---

# Why MTG Lab Exists

Collectible card games generate enormous amounts of information—from product configurations and print sheets to market prices, decklists, and personal collections. While this information is widely available, it is often fragmented across multiple websites and difficult to analyze as a whole.

MTG Lab brings these datasets together into a unified knowledge base that supports probability analysis, market analytics, simulation, and AI reasoning from a single canonical source of truth.

---

# Vision

MTG Lab aims to become a comprehensive decision-support platform capable of analyzing products, collections, decks, markets, and historical trends across multiple collectible card games.

The platform is designed to answer questions such as:

- Which sealed product offers the highest expected value?
- How should I optimize my collection?
- Which cards provide the best upgrade for my deck?
- What is the probability of opening specific cards?
- Which products have historically appreciated the most?
- How close am I to building a competitive deck?
- What purchasing strategy best fits my budget?

---

# Supported Games

MTG Lab is architected as a multi-game platform.

## Current Implementation

- **Magic: The Gathering**
  - Mystery Booster 2 (Reference Implementation)

## Planned Support

- Pokémon Trading Card Game
- Disney Lorcana
- One Piece Card Game
- Yu-Gi-Oh!
- Star Wars: Unlimited
- Flesh and Blood

The architecture is intentionally extensible so additional games can share the same analytics and AI infrastructure.

---

# Architecture

MTG Lab is built around four primary layers.

```text
Repository / Database
        │
        ▼
Analytics Engine
        │
        ▼
AI Reasoning Layer
        │
        ▼
Applications & User Interfaces
```

Each layer has a distinct responsibility.

The Tier 0 [Research Log architecture](docs/RESEARCH_LOG_ARCHITECTURE.md) defines MTG Lab's scientific notebook and institutional memory, preserving versioned hypotheses, experiments, observations, conclusions, and evidence across these layers.

## Repository / Database

The canonical source of structured information including:

- Cards
- Products
- Printings
- Collections
- Market data
- Probability definitions

The first product-specific ingestion path processes controlled official Mystery
Booster 2 product-page title evidence into schema-validated parsed records and
provenance-complete, non-canonical product candidates. It intentionally does not
promote candidates or infer card, slot, sheet, collation, or probability facts.

Validated product candidates can now enter an explicit review workflow. Product
promotion is conflict-safe and idempotent, preserves the complete candidate and
field provenance in immutable audit history, and supports audited rejection and
rollback without silently overwriting canonical data.

The same controlled-review architecture now provides an entity-agnostic
promotion framework, enabled for Card and Printing candidates in the current
milestone. Entity-specific repository definitions preserve schema and
referential boundaries while shared approval, conflict, audit, and rollback
behavior remains reusable for future canonical entity types.

The canonical repository also contains a deliberately small Card and Printing
foundation dataset, now including a three-pair Mystery Booster 2 Wave 1 increment
produced by a deterministic, bounded, multi-source ingestion workflow. Game-scoped loaders validate schemas, stable identity paths,
source-backed field provenance, and every Printing-to-Card reference before
producing deterministic repository snapshots. Identifier and layout rules are
documented in the [Card and Printing Repository](docs/CARD_PRINTING_REPOSITORY.md).

Repository evidence can now be preserved in stable, game-scoped bundles under
`data/sources/`. Versioned manifests identify archived files by byte size and
SHA-256, connect every artifact to canonical Source Records and explicit claims,
and allow ingestion to load only path-safe, content-verified evidence. The
[Evidence Repository](docs/EVIDENCE_REPOSITORY.md) defines this boundary.

## Analytics Engine

Responsible for computing:

- Pull probabilities
- Expected value
- Monte Carlo simulations
- Portfolio metrics
- Collection statistics
- Historical analysis

## AI Reasoning Layer

Retrieves structured information, interprets analytical results, and generates explainable recommendations.

## Applications & User Interfaces

Exposes MTG Lab through:

- Dashboards
- APIs
- Command-line tools
- Conversational AI
- Future desktop and web applications

---

# Core Capabilities

MTG Lab is designed to support:

- Canonical card repositories
- Product databases
- Print sheet reconstruction
- Slot probability analysis
- Expected value (EV) calculations
- Monte Carlo simulation
- Collection management
- Portfolio analytics
- Deck-building analysis
- Market intelligence
- AI-powered decision support

---

# Repository Philosophy

The GitHub repository serves as the canonical source of truth.

Development follows a documentation-first approach:

- Architecture is defined through documentation.
- Implementation follows the documented architecture.
- Every significant decision is recorded.
- Assumptions are documented.
- Milestones are implemented incrementally.
- Documentation and implementation remain synchronized.

---

# Development Workflow

Development sessions are repository-driven. Before making changes, contributors and Codex read the project inventory, current session state, approved next task, architecture, decisions, roadmap, and changelog. Work proceeds one small milestone at a time, with complete tests and synchronized documentation, and stops when the milestone's pull request is ready for review.

See the authoritative [`docs/AI_CONTRIBUTING.md`](docs/AI_CONTRIBUTING.md) guide, reusable [`docs/DEVELOPMENT_PLAYBOOK.md`](docs/DEVELOPMENT_PLAYBOOK.md), engineering context in [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md), required [`docs/CODEX_WORKFLOW.md`](docs/CODEX_WORKFLOW.md), [`docs/HANDOFF.md`](docs/HANDOFF.md), [`docs/SESSION_STATE.md`](docs/SESSION_STATE.md), and [`docs/NEXT_TASK.md`](docs/NEXT_TASK.md). `HANDOFF.md` provides the concise transfer note from the most recent session. The repository—not previous chat history—is the source of truth.

---

# Repository Organization

```text
MTG-Lab/
│
├── README.md
├── ROADMAP.md
├── ARCHITECTURE.md
├── CHANGELOG.md
├── DECISIONS.md
├── TODO.md
│
├── docs/
│   ├── AI_ARCHITECTURE_VISION.md
│   ├── PROJECT_INVENTORY.md
│   └── ...
│
├── games/
│   ├── magic/
│   │   └── mystery_booster_2/
│   ├── pokemon/
│   ├── lorcana/
│   ├── one_piece/
│   ├── yugioh/
│   └── ...
│
├── src/
├── schemas/
├── tests/
└── exports/
```

This organization allows multiple trading card games to share a common analytics platform while maintaining independent datasets.

---

# Project Status

**Architecture:** Version 12

**Status:** Active Development

**Current Focus:** Magic: The Gathering — Mystery Booster 2

Mystery Booster 2 serves as the reference implementation used to validate the platform's data models, analytics engine, simulation framework, and AI reasoning before expanding to additional games.

---

# Long-Term Goal

Build the premier decision intelligence platform for collectible card games by combining high-quality structured data, advanced analytics, simulation, and explainable artificial intelligence.

MTG Lab is designed to become the definitive platform for understanding collectible card games through data rather than intuition.
