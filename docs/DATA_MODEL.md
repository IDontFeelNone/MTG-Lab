# MTG Lab Data Model

**Tier:** Tier 0 (Architectural Constitution)

**Version:** 1.0

**Status:** Approved Architecture

## Purpose

This document defines the approved conceptual data model for MTG Lab. It
establishes entity identities, relationships, provenance expectations, and
validation boundaries without prescribing database tables, ORM models, or a
storage engine.

It is read together with:

- [`ARCHITECTURE.md`](ARCHITECTURE.md), which defines system layers and their
  responsibilities;
- [`DECISIONS.md`](DECISIONS.md), especially the accepted data-driven,
  repository-authority, validation, and canonical-pipeline decisions; and
- [`DATA_REPOSITORY.md`](DATA_REPOSITORY.md), which defines the raw, processed,
  canonical, validation, and derived-data layers.

This migration reconciles the approved model with repository terminology. It
does not expand the model, populate entities, or authorize persistence work.

## Model Principles

- **Repository authority:** Version-controlled canonical data in Git is the
  source of truth. A database is a generated persistence and query layer.
- **Stable identity:** Persistent entities use stable IDs. Relationships refer
  to those IDs rather than file position or collection ordering.
- **Game-agnostic core:** Shared entities do not encode Mystery Booster 2 or
  another product's behavior in application logic.
- **Data-driven products:** Products are defined by structured relationships
  among products, slots, print sheets, printings, and cards.
- **Evidence and provenance:** External claims remain traceable to immutable
  evidence and explicit transformations.
- **Validation before consumption:** Only validated canonical data is eligible
  for persistence, probability, simulation, analytics, or AI reasoning.
- **Versioned contracts:** Serialized records declare a schema version and are
  validated against the matching repository-owned contract.

## Canonical Domain Entities

### Card

A **Card** is the game-level identity of a card, independent of any particular
physical or digital release. It owns a stable ID, game, and name. Game-specific
identity or descriptive attributes may be recorded by the versioned schema,
but do not replace the MTG Lab stable ID.

### Printing

A **Printing** is a specific physical or digital realization of one Card. It
owns a stable ID and references exactly one Card by `card_id`. Set code,
collector number, rarity, language, and treatments describe the realization
rather than the underlying Card identity.

### Print Sheet

A **Print Sheet** is a named, game-scoped weighted collection of Printing
references. Each entry identifies a Printing and a positive integer weight.
Weights describe relative selection data; conclusions about physical printing
or collation require preserved evidence and validation.

### Slot

A **Slot** is a named product selection instruction. It references one Print
Sheet, declares a positive draw count, and records whether draws use
replacement. A Slot contains no product-name conditional behavior.

### Product

A **Product** is a game-scoped sealed-product definition. It owns stable
identity, name, type, lifecycle status, provenance, and an ordered-independent
set of Slot references. Foundation and draft products may be incomplete;
validated products must satisfy the current schema and referential validation.
Deprecated products remain readable for history and auditability.

## Supporting Repository Records

### Source Record

A **Source Record** registers an official, community, inferred, or internal
source and the claims it can support. It records provider, location, access and
publication context when available, verification status, record version, and
content identity or archival location when available.

### Acquisition Manifest

An **Acquisition Manifest** is a structured acquisition plan for a Product. It
references registered Source Records, identifies an immutable raw destination,
and records acquisition and processing state. It does not contain parsed or
canonical domain facts.

### Intermediate Artifacts

**Parsed-record artifacts** preserve deterministic extraction results and
source context. **Normalized-candidate artifacts** contain proposed canonical
entities with field-level provenance, transformation identity, confidence, and
validation state. Both remain non-canonical until controlled promotion.

### Promotion Audit

A **Promotion Audit** is immutable history of an explicit approval, rejection,
promotion, conflict, or rollback decision. It preserves the candidate and its
field provenance. Audit history is not canonical domain data and cannot bypass
canonical validation.

## Relationships

```text
Card 1 <--- many Printing
Printing many <--- Print Sheet entries
Print Sheet 1 <--- many Slot
Slot many <--- Product slot references

Product 1 <--- many Acquisition Manifest
Source Record many <--- Acquisition Manifest source references
Raw evidence -> Parsed artifact -> Normalized candidate -> Controlled promotion
```

All arrows represent stable-ID references. Collection order is not entity
identity. Referential validation must reject missing targets and inappropriate
cross-game relationships before downstream consumption.

## Data Lifecycle and Authority

The repository layers in [`DATA_REPOSITORY.md`](DATA_REPOSITORY.md) apply to
this model as follows:

1. **Raw:** immutable acquired evidence and its content identity.
2. **Processed:** parsed records and normalized candidates with transformation
   lineage; these records are explicitly non-canonical.
3. **Canonical:** reviewed, approved entity definitions stored in the Git
   repository under versioned contracts.
4. **Validation:** structural, referential, domain, and later statistical
   results proving whether canonical data is eligible for consumption.
5. **Derived analytics:** reproducible results calculated from validated
   canonical data; derived output never becomes an untraceable source fact.

Controlled promotion is the only path from a normalized candidate to canonical
data. Promotion must remain explicit, validation-gated, provenance-preserving,
idempotent, conflict-safe, and auditable.

## Validation Boundaries

- **Structural validation** checks a serialized record against its declared
  versioned JSON Schema.
- **Referential validation** verifies stable-ID relationships, including
  Printing-to-Card, Print-Sheet-to-Printing, Slot-to-Print-Sheet, and
  Product-to-Slot references.
- **Domain validation** verifies lifecycle and game-domain rules that cannot be
  expressed completely by structure alone.
- **Statistical validation** verifies probability and collation integrity when
  those approved subsystems are introduced.

Schema validity alone does not make a candidate canonical or make canonical
data eligible for analytics. Approval and every applicable validation boundary
must also succeed.

## Schema and Persistence Boundary

The JSON Schemas under `src/schemas/v1/` are the current serialized contracts
for implemented portions of this conceptual model. They operationalize the
model; they do not redefine architectural ownership or authorize population of
currently empty datasets.

Database tables, SQLAlchemy models, migrations, indexes, and generated database
artifacts are outside this milestone. Any persistence implementation must
follow Decision 010, remain derivable from validated repository data, and be
approved as a separate milestone.

## Scope of This Migration

This milestone migrates architectural documentation only. It does not:

- add or populate Card or Printing records;
- change any JSON Schema or canonical Product record;
- define Mystery Booster 2 card pools, slots, print sheets, collation, or
  probabilities;
- introduce database models, migrations, or persistence behavior; or
- implement simulation, analytics, market, API, or AI behavior.
