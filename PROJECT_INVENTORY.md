# MTG Lab Project Inventory

> **Status: Current** — canonical inventory reconciled at Phase 77.1 on 2026-07-30.

## Current state

- **Architecture:** v12 (unchanged)
- **Milestone:** Phase 77.1 repository documentation reconciliation
- **Maturity:** pre-alpha; deterministic local reference implementation
- **Validation baseline:** 137 passing unit/integration-style tests under the CI command
- **Canonical data:** 15 Cards and 15 Printings, including four Mystery Booster 2
  Printings; the MB2 Product is a foundation record; canonical Print Sheets and Slots
  remain unpopulated
- **Review authority:** `ARCHITECTURE_REVIEW_v1.md` records current maturity, debt,
  risks, dependency direction, and non-breaking consolidation recommendations

## Implemented subsystem inventory

| Subsystem | Implementation | Contract / status |
| --- | --- | --- |
| Canonical Repository | Typed game aggregate, specialized schema-backed repositories, deterministic snapshots, relationship validation, staged bulk apply | Operational v1; overlapping repository generations are consolidation debt |
| Canonical Import Pipeline | Reviewed local JSON/CSV adapters, provenance, dry-run/validation-only modes, deterministic report, atomic game-tree replacement | Operational v1; local-only and single-writer |
| Evidence and candidate ingestion | Immutable evidence storage, parsers/normalizers, candidate validation, retained intermediate artifacts, population review | Operational for bounded reviewed workflows |
| Evidence Repository and Review | Content-verified bundles, Source Record validation, external handoff integrity/provenance/completeness/conflict reports | Operational pre-promotion gate |
| Canonical promotion | Explicit entity-agnostic review, immutable audits, conflict protection, idempotency, rollback, dependency safety | Operational for Product, Card, Printing, Print Sheet, and Slot |
| Observation Engine | Immutable pack reports, verification records, descriptive box summaries, dated legacy valuation snapshots | Developing; strictly non-canonical |
| Observation Import Pipeline | Plain-text multi-pack import, create-only allocation, manifest reconciliation, verification and derived summary refresh | Operational v1; single-writer multi-file workflow |
| Market Framework | Provider abstraction, service/cache, normalized immutable snapshots, append-only repository, offline manual provider | Operational v1; no live provider |
| External Mapping Layer | Versioned canonical-to-provider IDs, lifecycle/provenance, exact resolution, append-only mapping sets | Operational v1 |
| Collection Engine | Immutable ownership aggregate, acquisitions, locations, quantity operations, summaries, local repository and CLI | Operational v1 |
| Analytics Engine | Seven immutable deterministic reports, input fingerprints, optional canonical enrichment and CLI | Operational v1 factual analytics |
| Decision Engine | Explicit versioned rules, immutable explainable decisions/reports, stable fact lineage and CLI | Operational v1 deterministic reasoning |
| Probability / simulation | Package placeholder only | Not implemented; canonical rules remain evidence-blocked |
| Research Log | Tier 0 architecture document | Implementation deferred |
| API / UI / AI advisor | Vision only | Not implemented |

## Repository layout

- `data/canonical/` — authoritative game-scoped canonical records
- `data/sources/` and `data/raw/` — archived evidence and controlled handoffs
- `data/intermediate/` — parsed, candidate, review, and research artifacts
- `data/observations/` — immutable non-canonical opening reports
- `data/audit/` — immutable promotion decisions
- `src/canonical`, `src/repository`, `src/canonical_import` — canonical model,
  persistence/validation, and reviewed bulk import
- `src/ingestion`, `src/evidence_review` — evidence-to-candidate and handoff review
- `src/observations`, `src/market`, `src/collection`, `src/analytics`,
  `src/decisions` — downstream domain engines
- `src/mtglab` — command-line application namespaces
- `src/schemas/v1`, `src/validation` — versioned JSON contracts and validation
- `tests/` — 137 deterministic tests collected by the Python validation workflow
- `docs/` — Architecture v12, subsystem contracts, governance, status, and history

## Architecture constraints and known debt

- Canonical identity and evidence provenance remain upstream of observations,
  ownership, analytics, and decisions; downstream results never promote themselves.
- No canonical MB2 rules, complete pools, probability tables, pack generator, or
  simulator are authorized by present evidence.
- Specialized canonical repositories overlap the newer typed aggregate; observation
  analytics and market snapshots overlap newer generic engines.
- Provenance is pervasive but does not yet have one cross-subsystem vocabulary or
  lineage reader.
- Filesystem stores are deterministic and appropriate for current volume, but full-
  tree loading/copying, linear lookup, and single-writer assumptions limit scale.
- The four defects recorded in `ARCHITECTURE_REVIEW_v1.md` are documentation findings;
  Phase 77 intentionally changes no behavior.

## Documentation hierarchy

Documentation status labels have the following consistent meaning:

- **Current** — reports the active repository baseline or authorization.
- **Historical** or **Superseded** — preserves earlier decisions or plans but cannot
  override Current documents.
- **Reference** — retains a reusable contract or context without claiming current
  milestone authority.
- **Vision** — describes target-state capability and does not imply implementation.

Architecture and governance are defined by `docs/ARCHITECTURE.md`,
`docs/DATA_MODEL.md`, `docs/DATA_REPOSITORY.md`, `docs/RULES_ENGINE.md`, and
`docs/AI_CONTRIBUTING.md`. The current implementation assessment is
`ARCHITECTURE_REVIEW_v1.md`. Implemented subsystem contracts include
`docs/CANONICAL_IMPORT_PIPELINE.md`, `docs/MB2_OBSERVATION_INTELLIGENCE.md`,
`docs/MARKET_PROVIDER_FRAMEWORK.md`, `docs/COLLECTION_ENGINE.md`,
`docs/ANALYTICS_ENGINE.md`, and `docs/DECISION_ENGINE.md`. This inventory describes
what exists; the architecture review evaluates it; `docs/ROADMAP.md` controls future
milestones; `CHANGELOG.md` preserves history.

Current operational state is reported by `docs/SESSION_STATE.md`,
`docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and `docs/HANDOFF.md`. Phase-specific
plans explicitly marked Historical, Superseded, or Reference remain retained artifacts.

## Session startup workflow

1. Read this inventory and `ARCHITECTURE_REVIEW_v1.md`.
2. Read `docs/SESSION_STATE.md`, `docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and
   `docs/HANDOFF.md` for the sole current operational state.
3. Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
   `CHANGELOG.md` for architecture, authorization, and history.
4. Treat Historical, Superseded, Reference, and Vision documents according to their
   labels; do not use them to override Current documents.
5. Confirm explicit milestone approval before changing the repository.

## Next-work boundary

Phase 77.1 reconciles documentation and authorizes no refactor. Any code change must be
a separately scoped, non-breaking milestone with characterization tests. Evidence-
blocked MB2 rule or simulation work remains subject to the existing sufficiency and
promotion gates. No next implementation milestone is approved. Do not recommend merge
of Phase 77.1 until GitHub Actions are green.
