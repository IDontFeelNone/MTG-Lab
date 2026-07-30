# MTG Lab Project Status

> **Status: Current** — executive dashboard at the Phase 81 evidence gate.
> This summary is subordinate to Architecture v12 and the documentation authority
> defined in `../PROJECT_INVENTORY.md`.

## Executive dashboard

| Status item | Current state |
| --- | --- |
| Architecture version | v12; unchanged |
| Current phase | Phase 81 — MB2 Canonical Dataset v1 (evidence-blocked) |
| Latest implementation milestone | Phase 76 — Decision Engine v1 |
| Latest architecture milestone | Phase 77 — Architecture Consolidation & Technical Debt Review |
| Current milestone scope | Mandatory inventory and coverage snapshot; complete source absent |
| Repository maturity | Pre-alpha deterministic local reference implementation |
| Canonical rule status | MB2 rule population remains evidence-blocked and unauthorized |
| Implemented downstream foundations | Observation, Market, External Mapping, Collection, Analytics, and Decision engines |
| Unimplemented product layers | Probability, simulation, live providers, database-backed persistence, API, UI, and AI advisor |
| Next implementation milestone | MB2 import after complete reviewed source acquisition |
| Merge gate | Do not recommend merge until GitHub Actions are green |

## Verified repository statistics

Counts below were derived directly from tracked repository content on 2026-07-30.

| Item | Count |
| --- | ---: |
| Tracked files | 289 |
| Tracked Markdown documents | 40 |
| Python source files under `src/` | 74 |
| Versioned JSON schemas | 16 |
| Top-level test modules | 26 |
| Passing automated tests | 141 |
| Promotion audits | 28 |

### Canonical entities

| Entity | Count |
| --- | ---: |
| Cards | 15 |
| Printings | 15 |
| MB2 Printings | 4 |
| Products | 1 |
| Print Sheets | 0 |
| Slots | 0 |
| Game-level Source Records | 7 |

### Evidence and research artifacts

| Artifact | Count |
| --- | ---: |
| Verified Evidence Repository bundles | 3 |
| Rule Claim Matrices | 1 |
| Evidence Sufficiency Reports | 1 |
| Artifact-bearing Phase 67 handoffs | 1 |
| Phase 67 Evidence Review reports | 1 JSON and 1 Markdown |

## Subsystem maturity

| Subsystem | Current implementation state |
| --- | --- |
| Canonical Repository | Operational v1; overlapping typed and schema-backed representations are known debt |
| Canonical Import Pipeline | Operational reviewed-local-data v1; no network acquisition |
| Evidence ingestion/review and provenance | Operational for bounded reviewed workflows |
| Observation Engine and Import Pipeline | Operational non-canonical foundations; observation-specific analytics remain consolidation debt |
| Verification | Operational evidence-handoff and observation identity gates |
| Market Provider Framework | Operational offline v1; live providers are absent |
| External Mapping Layer | Operational versioned mapping foundation |
| Collection Engine | Operational immutable ownership v1 |
| Analytics Engine | Operational deterministic factual-report v1 |
| Decision Engine | Operational explicit rule-evaluation v1 |
| Probability and simulation | Not implemented |
| Research Log | Architecture approved; implementation deferred |
| Database/API/UI/AI advisor | Not implemented |

Detailed ratings, risks, documented defects, dependency direction, and recommended
non-breaking consolidation are in `../ARCHITECTURE_REVIEW_v1.md`.

## Evidence and data status

The Phase 67 handoff mechanically verified one artifact supporting only the already-
known MB2 product identity. It supplies no outcome-affecting pack-rule evidence.
Complete topology, event pools, weights/frequency semantics, replacement, treatments,
conditionality, correlation, and sequencing remain unsupported. Therefore canonical
MB2 Print Sheets, Slots, complete rules, probability, and simulation remain blocked.

This constraint does not apply retroactively to the generic Phases 68–76 backend
foundations, which are implemented and tested but do not infer MB2 product behavior.

## Technical debt and risks

- Specialized canonical loaders and the typed aggregate overlap.
- Observation-specific summaries and price snapshots overlap generic Analytics and
  Market abstractions.
- Provenance is pervasive but lacks one shared vocabulary and lineage API.
- Filesystem loading/copying, linear lookup, and single-writer assumptions limit scale.
- Canonical and observation multi-file write boundaries need stronger coordination and
  recovery before concurrent operation.
- Only 15 Cards and Printings are canonical; MB2 rule structures are empty.
- Documentation consistency remains manually reviewed; Phase 77.1 is the reconciled
  baseline for a future automated consistency check.

## Approved roadmap and next action

`ROADMAP.md` records completed work through Phase 77 and the documentation-only Phase
77.1 reconciliation. Its post-77 consolidation ideas are candidates, not authorization.
Evidence-dependent MB2 work remains gated by a content-complete, independently reviewed
handoff relevant to unresolved rule claims.

After Phase 77.1, no implementation work may begin without explicit approval.
`NEXT_TASK.md` authorizes only final validation, CI observation, merge handoff, and
requesting the next bounded milestone.

## Documentation authority

1. **Architecture:** `ARCHITECTURE.md`, `DECISIONS.md`, `DATA_MODEL.md`,
   `DATA_REPOSITORY.md`, and `RULES_ENGINE.md`.
2. **Implemented inventory and review:** `../PROJECT_INVENTORY.md` and
   `../ARCHITECTURE_REVIEW_v1.md`.
3. **Roadmap and history:** `ROADMAP.md` and `../CHANGELOG.md`.
4. **Current operational state:** `SESSION_STATE.md`, this dashboard,
   `NEXT_TASK.md`, and `HANDOFF.md`.
5. **Historical/reference documents:** files explicitly bearing Historical,
   Superseded, Reference, or Vision status; these preserve context but do not override
   current documents.

## Phase 80 — Canonical Card, Printing, Evidence, and Uncertainty Contract (2026-07-30)

Phase 80 adds the compatible v3 Card/Printing and assertion-level evidence contract,
explicit partial-knowledge semantics, deterministic promotion, legacy projections,
and fail-closed simulation readiness. Historical canonical records remain unchanged;
full Mystery Booster 2 population remains out of scope. See
`docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`. Do not recommend merge until
GitHub Actions are green.
