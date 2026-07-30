# Session State

> **Status: Current** — Phase 83 institutional memory complete; GitHub Actions merge gate pending.

## Phase 83 current state

The documentation-only Institutional Memory and Project Constitution milestone establishes
`CONSTITUTION.md`, `ARCHITECTS_NOTEBOOK.md`, `FUTURE_VISION.md`, and
`QUESTIONS_MTG_LAB_SHOULD_ANSWER.md` as Tier 0 guidance. Together they state enduring laws,
preserve architectural rationale, describe long-term decision-intelligence intent, and orient
future design around user questions. Architecture v12, runtime behavior, schemas, canonical
data, datasets, and acquisition providers are unchanged.

## Current next action

Review the Phase 83 pull request and wait for GitHub Actions. Do not recommend merge until
all Actions checks are green. No subsequent implementation milestone is authorized by the
vision or question catalog; future work requires an explicit bounded approval.

> **Retained baseline:** Phase 82 implemented; its framework remains the latest runtime milestone.

## Phase 82 current state

The generic Raw Data Acquisition Framework is implemented without changing Architecture
v12. It provides immutable checksum-addressed raw snapshots, a source-neutral provider
boundary with an offline fixture provider, deterministic normalized source records, a
Phase 80 candidate-assertion bridge with change/conflict reports, separately auditable
and resumable acquisition runs, security controls, and an explicit-stage offline CLI.
No complete Mystery Booster 2 dataset or canonical record was added. See
`RAW_DATA_ACQUISITION_FRAMEWORK.md`.

## Architectural and operational boundary

Downloaded bytes are not canonical truth. Acquisition, normalization, assertion creation,
and existing reviewed canonical promotion remain separate. Provider trust is explicit
and defaults to unknown/unverified. Architecture v12 remains frozen; the pre-implementation
inventory found no Tier 0 decision was needed.

## Next action and merge gate

Review the Phase 82 pull request and wait for GitHub Actions. Do not recommend merge until
all Actions checks are green. After a green merge, the next separately authorized work may
create a terms-compliant provider adapter and reviewed acquisition run for Mystery Booster
2; full population still requires independent completeness and evidence review. Live market
history, scraping, automatic promotion, probability, simulation, and intelligence features
remain out of scope.

## Retained prior state

Phase 80 resolved the generic canonical contract gaps and Phase 81 established that MB2
population was blocked only by the absence of a reviewed reproducible acquisition workflow.
Phase 82 supplies that workflow; it does not itself satisfy the complete-source evidence gate.

## Prior baseline (retained for history)


> **Status: Current** — Phase 81 stopped at its evidence-acquisition gate.

## Current baseline

| Item | State |
| --- | --- |
| Last updated | 2026-07-30 |
| Version | v0.x (pre-alpha, unreleased) |
| Architecture | v12 (unchanged) |
| Current phase | Phase 81 — MB2 Canonical Dataset v1 (evidence-blocked before import) |
| Last completed implementation phase | Phase 76 — Decision Engine v1 |
| Last completed review phase | Phase 77 — Architecture Consolidation & Technical Debt Review |
| Current change type | Pre-implementation review and machine-readable coverage snapshot |
| Merge gate | GitHub Actions must be green |

Phase 79's mandatory inventory found that the current schemas and importer cannot
faithfully represent required printing facts, assertion classes, or unknown collation.
Implementation therefore stopped. No runtime behavior, public API, schema, model,
fixture, importer, or canonical data changed. See `PHASE_79_PREIMPLEMENTATION_REVIEW.md`.

Phase 80 resolved those architectural gaps with compatible v3 contracts. Phase 81
confirmed that no new architectural decision is needed, but the checkout contains
only four bounded MB2 records and no complete reviewed source fixture. Canonical
promotion stopped rather than fabricating completeness or provenance. See
`MYSTERY_BOOSTER_2_DATASET.md` and the Phase 81 machine-readable coverage snapshot.

## Implemented backend baseline

- Architecture v12, versioned schemas, JSON-schema validation, and deterministic
  filesystem repositories are established.
- Evidence acquisition, immutable storage, parsing, normalization, candidate review,
  promotion, rollback, provenance, and external-handoff review are implemented for
  their bounded workflows.
- The Canonical Repository and reviewed local Canonical Import Pipeline provide the
  typed read aggregate and staged import boundary while older schema-backed loaders
  remain compatibility paths identified as consolidation debt.
- The Observation Engine and Observation Import Pipeline preserve non-canonical pack
  reports, verify identities against canonical data, and produce descriptive summaries.
- The Market Provider Framework and External Mapping Layer provide offline provider,
  mapping, cache, and append-only snapshot foundations; no live provider is implemented.
- The Collection Engine provides immutable ownership operations and local persistence.
- The Analytics Engine provides seven deterministic factual reports.
- The Decision Engine evaluates explicit versioned rules over analytics reports and
  emits immutable, explainable decisions.
- Canonical promotion supports Product, Card, Printing, Print Sheet, and Slot. Canonical
  Mystery Booster 2 Print Sheets and Slots remain unpopulated.
- Probability and simulation are not implemented; `src/probability/` is a placeholder.
- Database-backed persistence, live provider integrations, API, UI, and AI advisor are
  not implemented.

## Verified repository baseline

Counts were re-derived from tracked repository content on 2026-07-30:

| Item | Count |
| --- | ---: |
| Tracked files | 289 |
| Tracked Markdown documents | 40 |
| Python source files under `src/` | 74 |
| Versioned JSON schemas | 16 |
| Top-level test modules | 26 |
| Passing tests | 141 |
| Promotion audits | 28 |
| Canonical Cards | 15 |
| Canonical Printings | 15 |
| Mystery Booster 2 Printings | 4 |
| Canonical Products | 1 |
| Canonical Print Sheets | 0 |
| Canonical Slots | 0 |
| Game-level Source Records | 7 |
| Verified Evidence Repository bundles | 3 |

The test baseline is the result of the same command used by CI:
`PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py" -q`.

## Evidence and canonical-rule boundary

The artifact-bearing Phase 67 handoff passed bounded integrity, provenance,
completeness, duplicate, and explicit-conflict review. Its artifact re-delivers the
already archived official product-title capture and supports only the existing MB2
identity claim. It provides no outcome-affecting rule evidence.

Consequently, complete MB2 topology, pools, weights, replacement, treatment,
conditionality, correlation, sequencing, canonical rules, probability, and simulation
remain unsupported or unimplemented. This evidence gate restricts MB2 rule work; it
does not erase the separately completed Phase 68–76 generic backend foundations.

## Architecture review and debt

`../ARCHITECTURE_REVIEW_v1.md` is the current implementation assessment. It identifies
consolidation rather than redesign as the appropriate architectural direction:

- typed and schema-backed canonical representations overlap;
- observation analytics and snapshot types overlap newer generic engines;
- provenance lacks a shared cross-subsystem vocabulary and lineage reader;
- filesystem repositories rely on eager loading, linear lookup, and single-writer
  assumptions; and
- stable serialization, immutable conversion, identifier, timestamp, and atomic-write
  primitives are duplicated.

The defects documented in that review were not fixed in Phase 77 or 77.1. Any refactor
requires a separately approved, non-breaking milestone with characterization tests.

## Current focus and next authorization

Phase 79 is blocked before implementation. `NEXT_TASK.md` is the sole current
next-action statement: review the blocker, wait for green GitHub Actions, and obtain
explicit approval for a product-agnostic contract/importer resolution. Dataset
population is not authorized while the blocker remains.

## Startup checklist

1. Read `../PROJECT_INVENTORY.md` and `../ARCHITECTURE_REVIEW_v1.md`.
2. Read this file, `PROJECT_STATUS.md`, `NEXT_TASK.md`, and `HANDOFF.md`.
3. Read `ARCHITECTURE.md`, `DECISIONS.md`, `ROADMAP.md`, and `../CHANGELOG.md`.
4. Treat documents marked Historical, Superseded, Reference, or Vision according to
   their status banners; they do not override current-state documents.
5. Verify the checkout, branch, working tree, objective, and acceptance criteria.
6. Run the complete test suite and relevant validation before handing off work.

## Phase 80 — Canonical Card, Printing, Evidence, and Uncertainty Contract (2026-07-30)

Phase 80 adds the compatible v3 Card/Printing and assertion-level evidence contract,
explicit partial-knowledge semantics, deterministic promotion, legacy projections,
and fail-closed simulation readiness. Historical canonical records remain unchanged;
full Mystery Booster 2 population remains out of scope. See
`docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`. Do not recommend merge until
GitHub Actions are green.