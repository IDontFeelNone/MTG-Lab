# MTG Lab Engineering Decisions

This document records significant architectural and engineering decisions made throughout the development of MTG Lab.

Each decision should include the reasoning behind it so future development remains consistent.

---

## Decision 001 — MTG Lab is a Platform

**Status:** Accepted

MTG Lab will be developed as a general-purpose Magic: The Gathering research platform rather than a simulator for a single product.

Mystery Booster 2 (MB2) will serve as the first supported product, but the architecture should accommodate future products without requiring changes to the core engine.

### Reasoning

Building a generic platform avoids product-specific code and makes future expansion significantly easier.

---

## Decision 002 — Data-Driven Product Definitions

**Status:** Accepted

The simulation engine must not contain hard-coded logic for specific Magic products.

Each product should be defined through structured data describing:

- Card pools
- Pack composition
- Slot definitions
- Probability rules

The simulation engine interprets these definitions rather than containing product-specific behavior.

### Reasoning

Separating data from logic makes the simulator easier to test, maintain, and extend.

---

## Decision 003 — Reproducible Simulations

**Status:** Accepted

Every simulation must support deterministic execution through configurable random seeds.

Simulation metadata should include:

- Product
- Simulator version
- Database version
- Random seed
- Timestamp

### Reasoning

Reproducible simulations simplify testing, debugging, and research.

---

## Decision 004 — Database as the Source of Truth

**Status:** Accepted

All validated product data should be stored in the database.

The application should not rely on duplicated definitions scattered throughout the codebase.

### Reasoning

Maintaining a single authoritative source reduces inconsistency and simplifies maintenance.

---

## Decision 005 — Validation Before Simulation

**Status:** Accepted

Product data must successfully pass validation before it can be used for simulation.

Validation includes checks for missing data, invalid references, duplicate identifiers, inconsistent slot definitions, and probability integrity.

### Reasoning

Reliable simulations depend on reliable input data.

---

## Decision 006 — Documentation Evolves With the Code

**Status:** Accepted

Significant architectural or behavioral changes should be reflected in the project's documentation as part of the same development effort.

### Reasoning

Keeping documentation current reduces confusion and makes the project easier to maintain over time.

---

## Future Decisions

Additional decisions will be recorded here as MTG Lab evolves.

Examples may include:

- Database technology
- API design
- Plugin architecture
- Market data providers
- Performance optimizations
- Versioning strategy
- Testing standards
