# MTG Lab

> **Verified merged baseline:** `e4a99ae6ccffe3e7121337fe28d9127024be3743` (GitHub PR #166).
> The mechanical production-cohort foundation is merged. The current milestone
> prepares a bounded functional-role review pilot for fifteen Cards. Architecture
> v12 is frozen; all proposed roles require human review and production data stays unchanged.

> **A decision intelligence platform for collectible card games, powered by structured data, advanced analytics, simulation, and explainable AI.**

> **Status: Current Overview and Vision.** Statements labeled as vision or planned
> capability describe the target platform, not implemented behavior. The current
> implementation baseline is maintained in `PROJECT_INVENTORY.md` and
> `docs/PROJECT_STATUS.md`.

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

MTGJSON v5 AllPrintings-style supplied datasets can be detected, inspected, and normalized through the governed acquisition pipeline with `mtg-lab adapter`; successful runs stop at human review. See [the provider adapter contract](docs/MTGJSON_PROVIDER_ADAPTER.md).

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

## Long-term vision

The target platform is organized around four primary layers. Database-backed
persistence, simulation, AI Advisor/model integration and graphical/API applications in this diagram
are not implemented in the current pre-alpha repository.

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

## Repository and canonical identity

The implemented filesystem repositories preserve canonical identity and immutable
domain snapshots. The long-term repository vision includes:

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

The earlier Card and Printing foundation included four Mystery Booster 2 pairs populated across
two bounded waves. The current canonical state contains 384 Cards and 913 Printings, including
379 promoted MB2 Printings and 534 retained non-MB2 pilot Printings. The earlier Wave 2 consumed
only content-verified Evidence Repository
bytes and validates embedded source attribution before deterministic ingestion.
Game-scoped loaders validate schemas, stable identity paths,
source-backed field provenance, and every Printing-to-Card reference before
producing deterministic repository snapshots. Identifier and layout rules are
documented in the [Card and Printing Repository](docs/CARD_PRINTING_REPOSITORY.md).

Repository evidence can now be preserved in stable, game-scoped bundles under
`data/sources/`. Versioned manifests identify archived files by byte size and
SHA-256, connect every artifact to canonical Source Records and explicit claims,
and allow ingestion to load only path-safe, content-verified evidence. The
[Evidence Repository](docs/EVIDENCE_REPOSITORY.md) defines this boundary.

Before an external delivery enters that archive or the Rule Claim Matrix
workflow, the product-agnostic [Evidence Review Engine](docs/EVIDENCE_REVIEW_ENGINE.md)
checks metadata, source references, required artifacts, hashes, duplicate
content, explicit claim conflicts, unsupported claims, and orphaned artifacts.
It emits schema-validated deterministic JSON and Markdown reports but performs
no rule inference or canonical promotion.

Phase 65 adds a retained, schema-validated Mystery Booster 2 Rule Claim
Matrix and evidence sufficiency report under the processed research boundary.
The assessment confirms that preserved evidence remains insufficient for
canonical product rules or pack generation and makes no canonical rule changes.
See the [Mystery Booster 2 Rule Research](docs/MB2_RULE_RESEARCH.md) report.

Verified Card and Printing ingestion accepts complete bounded batches of up to
twenty-five records and rejects oversized inputs without truncation. Before
promotion, a deterministic retained review report binds the candidates to the
validated canonical snapshot and summarizes new and reused Cards, new
Printings, duplicates, conflicts, rejected records, and expected count changes.

## Analytics Engine

The long-term analytics vision includes:

- Pull probabilities
- Expected value
- Monte Carlo simulations
- Portfolio metrics
- Collection statistics
- Historical analysis

The implemented game-agnostic Analytics Engine v1 currently produces seven immutable,
versioned factual reports for collections, duplicates, acquisitions, inventory,
observations, distributions, and products. It does not implement probability, expected
value, simulation, portfolio optimization, or recommendations. See
[Analytics Engine v1](docs/ANALYTICS_ENGINE.md) for its bounded contract.

## AI Reasoning Layer

The implemented AI Reasoning Context Layer v1 converts public Semantic Query Layer responses into immutable, deterministic, provenance-backed evidence packages. It does not perform AI reasoning or generate advice. Model integration remains planned. Shared Decision Intelligence now produces deterministic structured recommendations or abstentions for synthetic fixed-content current-cost inputs, with an AI-facing explanation envelope. Real product recommendations have not been generated. The Decision Engine and shared policy layer use explicit deterministic rules rather than AI/ML calculation.

## Applications & User Interfaces — vision

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

See the executive [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) dashboard,
authoritative [`docs/AI_CONTRIBUTING.md`](docs/AI_CONTRIBUTING.md) guide,
reusable [`docs/DEVELOPMENT_PLAYBOOK.md`](docs/DEVELOPMENT_PLAYBOOK.md),
engineering context in [`docs/LESSONS_LEARNED.md`](docs/LESSONS_LEARNED.md),
required [`docs/CODEX_WORKFLOW.md`](docs/CODEX_WORKFLOW.md),
[`docs/HANDOFF.md`](docs/HANDOFF.md), [`docs/SESSION_STATE.md`](docs/SESSION_STATE.md),
and [`docs/NEXT_TASK.md`](docs/NEXT_TASK.md). `PROJECT_STATUS.md` is subordinate
to the Tier 0 constitution and summarizes, rather than replaces, those detailed
authorities. The repository—not previous chat history—is the source of truth.

---

# Repository Organization

```text
MTG-Lab/
│
├── README.md
├── CHANGELOG.md
├── PROJECT_INVENTORY.md
│
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── ENGINEERING_STANDARDS.md
│   ├── PROJECT_STATUS.md
│   ├── ROADMAP.md
│   ├── SESSION_STATE.md
│   ├── NEXT_TASK.md
│   ├── HANDOFF.md
│   ├── AI_ARCHITECTURE_VISION.md
│   └── ...
│
├── data/
├── src/
├── tests/
└── scripts/
```

This organization allows multiple trading card games to share a common analytics platform while maintaining independent datasets.

---

# Project Status

**Architecture:** Version 12

**Status:** Active Development

**Latest merged milestone:** Mechanical Card Intelligence production cohort — GitHub PR #166 (merged; literal provider mechanics, no canonical role admission)

**Verified main baseline (2026-10-12):** `e4a99ae6ccffe3e7121337fe28d9127024be3743`

**Highest numbered project phase:** Phase 147; later named milestones do not imply a new phase number.

**Reference Product:** Magic: The Gathering — Mystery Booster 2

Mystery Booster 2 validates evidence, canonical, and observation boundaries. The
generic Market, External Mapping, Collection, Analytics, Decision, Semantic Query,
Reasoning Context, and AI Adapter foundations are also implemented. The repository does
not yet contain an MB2 simulation framework, probability engine, model provider, or
operational AI Advisor.

The Collection Intelligence foundation (Phase 124), shared Decision Intelligence, fixed-content
Product Intelligence, synthetic sealed-versus-singles vertical, evidence packet v1, and hardened
human-attested review v2 remain implemented. The Commander Collection: Black pilot and pending
identity bundle remain `NOT_READY_FOR_EVALUATION`; no complete production acquisition packet or
recommendation exists. The six missing ordinary Card/Printing pairs and exact token identity remain
unresolved, and the Product candidate requires review.

The merged [two-Card evidence-to-ChatGPT demonstration](docs/TWO_CARD_CHATGPT_DEMO.md) composes retained
canonical identities, Card Intelligence explanations, historical market observations, independent
Scryfall and MTGJSON signals, and existing reasoning-context contracts. It prepares bounded,
deterministic dossiers and explanation examples for manual review. It does not run a model or
provide a live ChatGPT connection. The [mechanical production-cohort foundation](docs/MECHANICAL_CARD_INTELLIGENCE.md)
adds read-only source-attributed dossiers for all 384 independently verified production Cards,
face-aware coverage and correctly denominated cohort statistics. The 385 retained Scryfall rows
map uniquely to those Cards with one excluded emblem; this is not complete MB2 set membership.
The [functional-role review pilot](docs/FUNCTIONAL_ROLE_CARD_INTELLIGENCE.md) prepares exactly fifteen
Cards and thirty source-bound pending proposals with restrictions and uncertainty. It does not
classify the full cohort or admit knowledge facts. Verified rules interactions, synergy, rankings
and deck optimization remain unsupported. Stop after the role pilot's PR handoff; subsequent work requires
separate approval. Competitive Intelligence remains parked; Competitive Card Intelligence and
Deck Intelligence remain planned and unauthorized.

---

# Long-Term Goal

Build the premier decision intelligence platform for collectible card games by combining high-quality structured data, advanced analytics, simulation, and explainable artificial intelligence.

MTG Lab is designed to become the definitive platform for understanding collectible card games through data rather than intuition.
