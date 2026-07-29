# MTG Lab Rules Engine

**Tier:** Tier 0 (Architectural Constitution)

**Version:** 1.0

**Status:** Approved Architecture

## Purpose

This document records the approved Rules Engine architecture for MTG Lab. It
defines the architectural boundary through which structured product rules are
represented and interpreted. It does not introduce an implementation, extend
the approved data model, or define product-specific collation behavior.

It is read together with:

- [`ARCHITECTURE.md`](ARCHITECTURE.md), which establishes the data-driven,
  modular, reproducible, and verification-first system design;
- [`DECISIONS.md`](DECISIONS.md), especially the accepted data-driven product,
  validation-before-consumption, layered-architecture, and Mystery Booster 2
  reference-implementation decisions;
- [`DATA_MODEL.md`](DATA_MODEL.md), which defines Product, Slot, Print Sheet,
  Printing, and Card identities and relationships; and
- [`DATA_REPOSITORY.md`](DATA_REPOSITORY.md), which defines the authority and
  lifecycle of the structured data interpreted by the Rules Engine.

## Architectural Principles

- **Data-driven behavior:** Product rules are structured data. Reusable engine
  logic must not contain hard-coded knowledge of Mystery Booster 2 or any other
  named product.
- **Generic interpretation:** The same Product, Slot, Print Sheet, Printing,
  Card, and probability abstractions support additional products and games.
- **Stable relationships:** Rule data relates entities through stable IDs, not
  file position or collection ordering.
- **Validation before use:** Only reviewed canonical data that passes every
  applicable structural, referential, domain, and statistical validation may
  be consumed by probability, simulation, analytics, persistence, or AI
  systems.
- **Evidence and provenance:** Product, sheet, slot, probability, and collation
  claims remain traceable to preserved evidence. Confirmed source data must be
  distinguishable from inferred models.
- **Reproducibility:** Probabilistic analysis and simulation must be
  deterministic when supplied identical validated inputs, versions,
  configuration, and random seed.

## Rules Data Model

The approved product-rule relationship is:

```text
Card 1 <--- many Printing
Printing many <--- Print Sheet entries
Print Sheet 1 <--- many Slot
Slot many <--- Product slot references
```

- A **Print Sheet** is a named, game-scoped weighted collection of Printing
  references. Each entry identifies a Printing and a positive integer weight.
- A **Slot** is a named product selection instruction. It references one Print
  Sheet, declares a positive draw count, and records whether draws use
  replacement.
- A **Product** identifies its Slots through stable references. A Slot contains
  no conditional behavior tied to a product name.

Weights express relative selection data. They do not, without preserved
evidence and validation, establish conclusions about physical printing or
collation.

## Engine Boundary

The Rules Engine interprets validated structured product definitions. It does
not own canonical source data, approval decisions, or evidence acquisition.

The surrounding architectural responsibilities remain separate:

- The **Repository** owns version-controlled canonical rule definitions.
- The **Ingestion** layer preserves raw evidence and produces traceable,
  non-canonical parsed and normalized candidates.
- The **Validation** layer establishes structural, referential, domain, and,
  when approved, statistical eligibility for consumption.
- The **Probability** and **Simulation** layers consume validated rules without
  embedding product-specific branches.
- The **Analytics** and **AI reasoning** layers consume validated canonical data
  and reproducible derived results rather than unreviewed claims.

## Validation Boundary

Before rule data is eligible for downstream use, validation includes:

- schema validity under its declared versioned contract;
- stable-identifier and duplicate-identifier checks;
- Printing-to-Card, Print-Sheet-to-Printing, Slot-to-Print-Sheet, and
  Product-to-Slot referential integrity;
- inappropriate cross-game relationship rejection;
- print-sheet, Slot, Product, and probability integrity as applicable; and
- statistical validation of probability and collation integrity when those
  approved subsystems are introduced.

Schema validity alone does not make candidate data canonical or eligible for
Rules Engine consumption. Promotion remains explicit, validation-gated,
provenance-preserving, idempotent, conflict-safe, and auditable.

## Reference Implementation

Mystery Booster 2 is the first complete product implementation used to validate
this architecture. Its product definitions, card pools, Print Sheets,
collation rules, probabilities, validation evidence, and simulations must use
the same generic systems intended for future products. Mystery Booster 2
assumptions must not be embedded in reusable engine logic.

## Scope of This Migration

This document migrates the already approved Rules Engine architecture into the
repository. It does not:

- implement a Rules Engine, probability engine, or simulation engine;
- add or modify JSON Schemas or canonical data;
- define Mystery Booster 2 card pools, Slots, Print Sheets, collation rules, or
  probabilities;
- approve a Print Sheet or Slot implementation milestone;
- introduce persistence, API, analytics, market, collection, or AI behavior;
  or
- add new rule behavior or implementation decisions.
