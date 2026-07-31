> **Phase 94 update:** `src/reasoning/` deterministically packages public semantic responses into immutable provenance-backed AI reasoning contexts. It performs no AI inference or language generation and awaits review and green CI.

> **Phase 90 update:** the only supplied MTGJSON fixture was validated as synthetic set
> `TST`, not MB2. The pilot stopped at its evidence gate with deterministic reports and no
> registration, resolution, promotion, or canonical mutation.

> **Phase 89 update:** `src/external_ingestion/mtgjson.py` provides MTGJSON v5 detection,
> metadata/manifest generation, bounded deterministic mappings, and composition into the
> unchanged Phase 88 acquisition/review pipeline. No full corpus or MB2 data was imported.

# MTG Lab Project Inventory

> **Phase 86 update:** `src/dataset_import/` provides the registry, resolver, session orchestrator, and reporter; `src/mtglab/__main__.py` provides dataset/import CLI commands; and `data/fixtures/canonical_import/` contains the reviewed pilot.

> **Phase 84 update:** `src/acquisition/knowledge.py` adds provider policy, dataset
> identity, pre-review validation, reports, and deterministic review packages;
> `data/fixtures/knowledge/` contains test-only reviewed collectible-card inputs;
> `docs/KNOWLEDGE_ACQUISITION_PIPELINE.md` documents the lifecycle. Architecture v12 and
> canonical storage are unchanged.

> **Status: Current** — Phase 99 is implemented and awaits review and
> green GitHub Actions.

## Phase 83 constitutional guidance

Four Tier 0 documents now preserve the project's enduring laws, architectural rationale,
long-term intent, and question-led product compass: `docs/CONSTITUTION.md`,
`docs/ARCHITECTS_NOTEBOOK.md`, `docs/FUTURE_VISION.md`, and
`docs/QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`. They add no runtime behavior, canonical data,
schema, provider, or Architecture v12 change. The Constitution governs why; existing
architecture contracts govern structure; the notebook records rationale; the vision and
questions guide future proposals without authorizing them.

> **Retained baseline:** Phase 82 raw data acquisition framework implemented on 2026-07-30.

## Current state

- **Architecture:** v12 (unchanged)
- **Latest merged milestone:** Phase 98 — Multi-Source Evidence Acquisition Framework v1
- **Current milestone:** Phase 99 — MTGJSON Reference Dataset Provider v1
- **Maturity:** pre-alpha; deterministic local reference implementation
- **Validation baseline:** 194 passing tests locally under the CI command
- **Canonical data:** 15 Cards and 15 Printings, including four Mystery Booster 2
  Printings; the MB2 Product is a foundation record; canonical Print Sheets and Slots
  remain unpopulated
- **Review authority:** `ARCHITECTURE_REVIEW_v1.md` records current maturity, debt,
  risks, dependency direction, and non-breaking consolidation recommendations

## Implemented subsystem inventory

| Subsystem | Implementation | Contract / status |
| --- | --- | --- |
| Canonical Repository | Typed game aggregate, specialized schema-backed repositories, deterministic snapshots, relationship validation, staged bulk apply | Operational v1; overlapping repository generations are consolidation debt |
| Canonical Query Engine | Stable provenance-bearing entity results; relationship, dataset, audit, validation, and deterministic exact search queries; CLI | Operational v1; sole supported read boundary for future consumers |
| Canonical Semantic Query Layer | Immutable structured operations, deterministic Query/Analytics delegation, snapshot identities, provenance, and JSON CLI | Operational v1; no AI reasoning or language generation |
| Canonical Import Pipeline | Reviewed local JSON/CSV adapters, provenance, dry-run/validation-only modes, deterministic report, atomic game-tree replacement | Operational v1; local-only and single-writer |
| Raw data acquisition | Immutable byte snapshots, provider adapters, normalized source records, assertion bridge, acquisition-run reports, offline CLI | Operational v1; no live providers or canonical promotion |
| Multi-source evidence acquisition | Immutable provider/source/dataset/artifact contracts, provider interface, deterministic reference registry, licensing gates, JSON CLI | Framework v1; no live providers, datasets, or promotion |
| MTGJSON Reference Dataset Provider | Local v5 discovery, schema/artifact/dataset validation, deterministic candidate mapping, planning, JSON CLI | Operational v1; reference evidence only, no networking or promotion |
| External dataset ingestion | Canonical supplied-dataset manifest, JSON/CSV/ZIP integrity, MTGJSON v5 provider detection/mapping, registrations, review-package handoff, CLI | Operational v1; stops before human review and promotion |
| Evidence and candidate ingestion | Immutable evidence storage, parsers/normalizers, candidate validation, retained intermediate artifacts, population review | Operational for bounded reviewed workflows |
| Evidence Repository and Review | Content-verified bundles, Source Record validation, external handoff integrity/provenance/completeness/conflict reports | Operational pre-promotion gate |
| Canonical promotion | Legacy entity promotion plus Phase 85 review-package engine, deterministic versions, immutable success/failure audits, supersession, rollback, replay, and CLI | Operational v1; merged before Phase 87 |
| Observation Engine | Immutable pack reports, verification records, descriptive box summaries, dated legacy valuation snapshots | Developing; strictly non-canonical |
| Observation Import Pipeline | Plain-text multi-pack import, create-only allocation, manifest reconciliation, verification and derived summary refresh | Operational v1; single-writer multi-file workflow |
| Market Framework | Provider abstraction, service/cache, normalized immutable snapshots, append-only repository, offline manual provider | Operational v1; no live provider |
| External Mapping Layer | Versioned canonical-to-provider IDs, lifecycle/provenance, exact resolution, append-only mapping sets | Operational v1 |
| Collection Engine | Immutable ownership aggregate, acquisitions, locations, quantity operations, summaries, local repository and CLI | Operational v1 |
| Analytics Engine | Seven immutable deterministic reports, input fingerprints, optional canonical enrichment and CLI | Operational v1 factual analytics |
| Decision Engine | Explicit versioned rules, immutable explainable decisions/reports, stable fact lineage and CLI | Operational v1 deterministic reasoning |
| Probability / simulation | Package placeholder only | Not implemented; canonical rules remain evidence-blocked |
| AI Reasoning Context | Immutable content-addressed evidence packages over Semantic responses | Operational v1; only allowed reasoning input for AI adapters |
| AI Model Adapter | Provider-neutral immutable contracts, abstract interface, explicit registry, lifecycle validation, CLI | Framework v1; no provider implementation or inference |
| Research Log | Tier 0 architecture document | Implementation deferred |
| API / UI / AI advisor | Vision only | Not implemented |

## Repository layout

- `data/canonical/` — authoritative game-scoped canonical records
- `data/raw/<provider>/<dataset>/<snapshot-id>/` — generic immutable source snapshots
- `data/sources/` and retained raw evidence paths — archived evidence and controlled handoffs
- `data/intermediate/` — parsed, candidate, review, and research artifacts
- `data/observations/` — immutable non-canonical opening reports
- `data/audit/` — immutable promotion decisions
- `src/canonical`, `src/repository`, `src/canonical_import` — canonical model,
  persistence/validation, and reviewed bulk import
- `src/query` — provider-neutral canonical read contract and deterministic query facade
- `src/acquisition` — source-agnostic raw snapshots, normalization, and assertion bridge
- `src/external_ingestion` — supplied-file manifests, validation, MTGJSON provider adapter, and governed handoff
- `src/providers/mtgjson` — concrete MTGJSON Reference Dataset provider over Phase 98 contracts
- `src/ingestion`, `src/evidence_review` — evidence-to-candidate and handoff review
- `src/observations`, `src/market`, `src/collection`, `src/analytics`,
  `src/decisions` — downstream domain engines
- `src/reasoning`, `src/ai` — reasoning-context packaging and provider-independent model boundary
- `src/mtglab` — command-line application namespaces
- `src/schemas/v1`, `src/validation` — versioned JSON contracts and validation
- `tests/` — deterministic tests collected by the Python validation workflow
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

Tier 0 purpose and institutional memory are defined by `docs/CONSTITUTION.md`, `docs/ARCHITECTS_NOTEBOOK.md`, `docs/FUTURE_VISION.md`, and `docs/QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`. Architecture and governance are defined by `docs/ARCHITECTURE.md`,
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

1. Read `docs/CONSTITUTION.md`, this inventory, and `ARCHITECTURE_REVIEW_v1.md`.
2. Read `docs/SESSION_STATE.md`, `docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and
   `docs/HANDOFF.md` for the sole current operational state.
3. Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
   `CHANGELOG.md` for architecture, authorization, and history.
4. Treat Historical, Superseded, Reference, and Vision documents according to their
   labels; do not use them to override Current documents.
5. Confirm explicit milestone approval before changing the repository.

## Next-work boundary

Phase 99 review and green CI are the active work. The provider accepts local evidence only and
cannot promote it. Mystery Booster 2 remains evidence-blocked; Simulation and Intelligence
remain unimplemented.

## Phase 80 — Canonical fact and evidence contract

- `src/schemas/v3/`: additive Card, Printing, assertion, and partial-collation schemas.
- `src/canonical/evidence.py`: uncertainty, promotion, and fail-closed consumer API.
- `docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`: authoritative v3 policy.
- No Mystery Booster 2 dataset records were added or rewritten.
> **Phase 96B update:** `src/canonical_import/evidence_package.py` verifies immutable,
> independently reviewed product-identity packages and delegates canonical writes to the
> existing promotion service. The retained MB2 Stage 1 package confirms one foundation
> Product only; all packaging composition and topology remain unresolved.
> **Phase 97 update:** `src/canonical_import/card_list_package.py` is the fail-closed Stage 2
> intake interface. No qualifying MB2 list is retained, so canonical Card/Printing counts
> remain unchanged and no promotion occurred. See `docs/MB2_STAGE_2_CARD_IMPORT.md`.
> **Phase 98 update:** `src/evidence/` provides immutable multi-source acquisition contracts,
> provider capabilities and registration, and a deterministic non-canonical reference dataset
> registry; `mtg-lab evidence` provides JSON inspection and validation. No provider networking,
> dataset population, automatic promotion, canonical contract, or Architecture v12 change exists.
> **Phase 99 update:** `src/providers/mtgjson/` implements the first concrete reference provider,
> with local-only MTGJSON v5 validation, deterministic candidate mapping, planning, and JSON CLI.
> No dataset was bundled, acquired, reviewed, promoted, or written to canonical storage.
