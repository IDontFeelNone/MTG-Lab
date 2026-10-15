# DATA_REPOSITORY

Status: Tier 0 (Architectural Constitution)

Architecture v13 — ACTIVE APPROVED architecture under accepted Decision 017.
This authority model is approved governance. Separately owner-authorized Stage 1
fictional read-only snapshot attachment is implemented and pending independent
Project Manager review; production external attachment/activation remains
unimplemented. Architecture v12 is the previous historical baseline. See
[Stage 1 implementation and limits](V13_STAGE1_SNAPSHOT_ATTACHMENT.md).

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
  content identity and independent permission/retention scope. In the existing
  legacy/public implementation, stable archived evidence bundles live under `data/sources/`
  with versioned manifests, content hashes, and canonical Source Record
  references; pipeline-specific raw acquisition destinations may remain under
  `data/raw/`.
- **Processed Data:** Parsed records and normalized candidates, including
  proposed Print Sheet and Slot records, retain transformation lineage and are
  explicitly non-canonical. Deterministic pre-promotion review reports compare
  bounded candidates with a validated canonical snapshot and remain processed data.
- **Canonical Authority:** Reviewed and approved Product, Slot, Print Sheet,
  Printing and Card definitions may live in an explicitly selected, validated
  immutable operator-managed snapshot under public repository-owned schemas and
  policies. Its authority is bounded to declared game, scope, content identity,
  schema/policy versions, capabilities, provenance/evidence bindings and approved
  operation/use scope. Relationships use stable IDs. Private location alone is
  neither authority nor permission. Existing legacy constructors remain Git-bound;
  separately authorized fictional read-only attachment and an explicit legacy/public
  profile do not enable production external-data attachment or admission.
- **Validation Data:** Structural, referential, domain, and later statistical
  results establish whether canonical definitions are eligible for downstream
  consumption. For Print Sheets and Slots, this includes
  Print-Sheet-to-Printing, Slot-to-Print-Sheet, and Product-to-Slot integrity.
- **Derived Analytics:** Reproducible probability, simulation, and analytical
  output is derived from validated canonical data and does not become an
  untraceable source fact.

Movement from processed candidates into the canonical repository requires
explicit, provenance-preserving, validation-gated, and auditable promotion.
Print Sheets and Slots follow the same selected-snapshot authority and lifecycle
boundaries as the other canonical domain entities defined in `DATA_MODEL.md`.

This document will be expanded as implementation milestones are completed.

## Accepted v13 authority boundary

[EXTERNAL_CARD_DATA_PLANE.md](EXTERNAL_CARD_DATA_PLANE.md) and accepted Decision
017 separate public architectural/code authority, immutable operator canonical
snapshots, independently permissioned source evidence, generated persistence and
personal data. Decision 017 prospectively supersedes only Decision 004's public-Git
production data location and rebuild-from-public-Git-alone requirements, preserving
the Raw → Processed → Canonical → Validated lifecycle, stable IDs and explicit
reviewed promotion. Public Git retains code, schemas, policies, rules, contracts,
transformations, adapters, migrations, deterministic algorithms, safe fixtures and
architecture/version manifests. Generated databases, caches, indexes and
projections remain subordinate; rebuild requires compatible public code/contracts
plus the exact authorized retained snapshot/evidence.

Personal collections, holdings, storage, preferences and assessments remain outside
the shared snapshot. Source evidence has its own governance. Governance acceptance
alone authorized no runtime implementation; the subsequent separate Stage 1
authorization is limited to fictional read-only attachment and the explicit
legacy/public profile. No data migration, processing/retention/redistribution/
application permission, protected snapshot, AI export or admission is authorized.
Historical evidence is not rewritten or deleted; MB2 810, the nine holds and
source-policy gates remain unchanged.
