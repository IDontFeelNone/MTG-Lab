# DATA_REPOSITORY

Status: Tier 0 (Architectural Constitution)

## Purpose

This document defines the canonical data repository architecture for MTG Lab.

## Objectives

- Establish a single source of truth for datasets.
- Define raw, processed, and canonical data layers.
- Document validation datasets.
- Support probability analysis, Monte Carlo simulation, and market intelligence.
- Ensure reproducible AI workflows.

## Repository Layers

- **Raw Data:** Preserved acquired evidence remains immutable and retains its
  content identity. Stable archived evidence bundles live under `data/sources/`
  with versioned manifests, content hashes, and canonical Source Record
  references; pipeline-specific raw acquisition destinations may remain under
  `data/raw/`.
- **Processed Data:** Parsed records and normalized candidates, including
  proposed Print Sheet and Slot records, retain transformation lineage and are
  explicitly non-canonical.
- **Canonical Repository:** Reviewed and approved Product, Slot, Print Sheet,
  Printing, and Card definitions are version-controlled under repository-owned
  schemas. Relationships use stable IDs.
- **Validation Data:** Structural, referential, domain, and later statistical
  results establish whether canonical definitions are eligible for downstream
  consumption. For Print Sheets and Slots, this includes
  Print-Sheet-to-Printing, Slot-to-Print-Sheet, and Product-to-Slot integrity.
- **Derived Analytics:** Reproducible probability, simulation, and analytical
  output is derived from validated canonical data and does not become an
  untraceable source fact.

Movement from processed candidates into the canonical repository requires
explicit, provenance-preserving, validation-gated, and auditable promotion.
Print Sheets and Slots follow the same repository authority and lifecycle
boundaries as the other canonical domain entities defined in `DATA_MODEL.md`.

This document will be expanded as implementation milestones are completed.
