# MTG Lab Architecture

> **Status: Architecture v13 — ACTIVE APPROVED architecture.** Owner-accepted
> Decision 017 governs authority. Architecture v12 is the previous historical baseline.
> This is a documentation/governance transition only; no runtime implementation is authorized.
> The high-level target diagram includes planned layers and is not a claim
> that every component is implemented. `../ARCHITECTURE_REVIEW_v1.md` contains the
> Phase 77 current-implementation dependency diagram and maturity assessment.

Purpose

MTG Lab is designed as a modular research platform for Magic: The Gathering. The architecture emphasizes correctness, extensibility, reproducibility, and maintainability over short-term implementation speed.

The system is designed so that support for new Magic products can be added primarily by importing new product data rather than rewriting application logic.

## Approved v13 authority model

Public Git owns architecture, source code, schemas, policies, validation and
identity rules, transformations, provider adapters, migrations, contracts,
deterministic algorithms, safe/public fixtures and public architecture/version
manifests. Production canonical data may be an explicitly selected, reviewed,
validated immutable operator-managed snapshot, authoritative only for its declared
game, scope, content identity, schema/policy versions, capabilities,
provenance/evidence bindings and approved operation/use scope. Private location
alone grants neither canonical authority nor permission.

Generated SQLite/PostgreSQL databases, caches, indexes and projections remain
subordinate and rebuildable from the exact authorized snapshot plus compatible
public code/contracts. They are not editable fact authorities. Provider/source
evidence is independently governed. Personal collections, holdings, storage,
preferences and assessments remain a separate private trust domain.

The existing runtime still uses its legacy filesystem/Git-bound data roots; no
external loader, activation service or generated SQL runtime is implemented here.
See [Decision 017](DECISIONS.md#decision-017--public-architectural-authority-and-immutable-operator-canonical-snapshots)
and [the accepted direction](EXTERNAL_CARD_DATA_PLANE.md). Implementation, dataset
processing/retention/redistribution/service permission, admission and AI export
remain separate gates. MB2 810 and all nine holds remain pending and unadmitted;
`SOURCE_POLICY_CLEARED_PLANS` is unchanged.

## Core Design Principles

### 1. Data-Driven Design

No product-specific logic should exist in the simulation engine.

Products define themselves through structured data.

Examples include:

- Products
- Cards
- Printings
- Pack definitions
- Slot definitions
- Probability tables

The engine interprets the data rather than containing special-case rules for individual products.

### 2. Modular Architecture

Each major system has a single responsibility.

Long-term modules include:

- Database
- Canonical Import Pipeline and Observation Import Pipeline
- Validation Engine
- Simulation Engine
- Analytics Engine
- Collection Engine
- Market Provider Framework and External Mapping Layer
- Decision Engine
- API
- Web Interface

Each module should remain independently testable.

### 3. Reproducible Results

Every simulation should be reproducible.

Each simulation records:

- Product
- Simulator version
- Database version
- Random seed
- Timestamp
- Configuration

Running the same simulation with identical inputs should produce identical outputs.

### 4. Verification First

Before simulations are trusted, imported data should be validated.

Validation includes:

- Missing cards
- Duplicate identifiers
- Invalid references
- Broken probability tables
- Slot consistency
- Product integrity

The goal is to ensure statistical analyses are built on verified data.

## High-Level Architecture

The following is the long-term target architecture. Web Interface, REST API,
Simulation Engine, and Database Layer are not implemented. The current pre-alpha
implementation uses deterministic filesystem repositories and CLI entry points; its
implemented dependency direction is documented in `../ARCHITECTURE_REVIEW_v1.md`.

```text
                User
                  │
                  ▼
            Web Interface
                 │
          Command Line Interface
                 │
                 ▼
             REST API Layer
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
 Simulation Engine   Analytics Engine
        │                 │
        └────────┬────────┘
                 ▼
          Database Layer
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
 Import Pipeline      Market Data
```

## Engineering Philosophy

MTG Lab favors correctness over convenience, reproducibility over randomness, documentation alongside implementation, modular components over tightly coupled systems, and evidence-based analysis over assumptions.

## Historical v12 preservation and future implementation

[Decision 017](DECISIONS.md#decision-017--public-architectural-authority-and-immutable-operator-canonical-snapshots)
and [the external card-data-plane review](EXTERNAL_CARD_DATA_PLANE.md) record the
approved v13 change to Decision 004's Tier-0 authority invariant. Decision 004/009
historical text, canonical bytes, source evidence and expected replay hashes remain
unchanged. Card Acquisition replay explicitly retains its original Architecture-v12
auxiliary file; it does not read current architecture as a historical dependency.

The next documented milestone, **V13 Stage 1 — Fictional Canonical Snapshot
Attachment**, is NOT AUTHORIZED. It is limited to fictional manifest verification,
read-only attachment through existing query/collection readers and compatibility/
integrity/failure tests, preserving an explicit legacy/public profile. See the
[scope and exclusions](EXTERNAL_CARD_DATA_PLANE_MIGRATION.md#v13-stage-1--fictional-canonical-snapshot-attachment).
