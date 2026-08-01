# Phase 118 inventory update

The active authorization workflow, persistence scripts, authorization production module, Phase 117/117A tests, and current Phase 117 review artifacts are removed. `production_evidence.promotion_readiness` now computes a non-executing plan from trusted immutable evidence and Phase 115/116 review results. Operator signatures do not control readiness; normal PR review and green CI provide oversight. The exact first MB2 batch is technically ready, while promotion remains explicit, audited, rollback capable, and not performed.

Earlier Phase 117/117A inventory entries below are historical and no longer describe active architecture.

# Phase 117A inventory update

`.github/workflows/mb2-operator-authorization.yml` accepts the twelve required operator and immutable-scope inputs; `scripts/mb2_authorization_persistence.py` provides authorization-only durable Git/GitHub persistence; and `verify_authorization_artifact()` independently authenticates a retained result. Tests cover the workflow contract, safe dry run, immutable scope, authorization validation/replay/conflict, canonical isolation, and persistence boundary. Phase 117 remains unauthorized and unpromoted.

# Phase 116 inventory update

`src/production_evidence/identifier_resolution.py` and `tests/test_phase_116_identifier_resolution.py` implement and verify an immutable Phase 116 overlay over the unchanged Phase 115 review. Seven artifacts under `data/reviews/phase-116/mb2-batch-000001-e32022126c07/` retain the 21-candidate resolution ledger, the complete 820-record collision group, updated 1,000-candidate classifications, findings, dependency closure, pending decision, and readiness report. All 1,000 candidates are approved by evidence classification; signature readiness is true, while signature and promotion remain absent and promotion readiness is false.

# Phase 115 inventory update

The repository now retains a reproducible candidate-level review of exactly the first MB2 batch from production evidence revision v2: 1,000 ledger entries, findings, valid dependency closure, an immutable unsigned pending decision, and a not-ready promotion report. Counts are 979 approved, 0 excluded, and 21 requiring additional evidence. Canonical state and Architecture v12 are unchanged.

# Phase 114A inventory update

`src/production_evidence/adapter.py` now emits schema 2 review payloads; `src/production_evidence/repository.py` verifies and stores them under a derived immutable evidence identity. The manual intake workflow targets a dedicated revision branch and reports payload count/bytes. Tests cover exact extraction, isolation, integrity, missing/duplicate payloads, unresolved Card-to-Printing dependencies, immutable collisions, idempotent normalization, and no canonical/promotion authority. The original retained run is unchanged.

# Phase 113A inventory update

Phase 113A makes the retained-evidence gate valid both before and after evidence-intake PR #86.
The historical absence remains accepted on main; the present state validates run `30663562841`,
target-isolated pending MB2/MSH packages, and non-canonical/no-promotion boundaries. Independent
candidate review remains the next gate after #86 merges.

# Phase 112B inventory update

Production-evidence persistence is now a fail-closed Git/GitHub state machine in `scripts/production_evidence_persistence.py`, invoked unconditionally by the manual intake workflow. It reports every durable result, rejects ignored or empty staging and out-of-bound changes, never force-pushes, verifies the PR through GitHub APIs, and can reuse only byte-identical existing evidence. The live run is not claimed until that workflow is rerun successfully. Architecture v12 and all canonical/review/promotion behavior are unchanged.

> **Phase 113:** The independent review was rerun exclusively against the Production Evidence
> Repository. Run `30663562841` is still absent, so no MB2 batch or candidate could be selected,
> classified, or signed; no Marvel review, promotion, or canonical write occurred.

> **Phase 112A:** `src/production_evidence/adapter.py` now deterministically verifies and adapts the
> native nested MTGJSON workflow artifact to the unchanged Phase 111 intake contract. The Phase 112
> operational failure was a native-layout/root-contract mismatch, not corrupt evidence. Dry-run
> intake remains non-canonical and non-promoting; Architecture v12 is unchanged.

> **Phase 112:** A manual GitHub-native workflow securely selects and authenticates a successful
> Actions artifact, invokes Phase 111 intake and verification, confines changes to
> `data/production_runs/`, and opens a dedicated evidence-only PR. No production archive is
> committed yet; Phase 110B remains stopped at its artifact gate.
>
> **Phase 111:** Permanent production evidence storage, verified ZIP intake, deterministic indexes, and evidence CLI lookup are implemented. No production archive is committed; Phase 110B remains stopped at its artifact gate.

> **Phase 110B:** `docs/FIRST_MB2_BATCH_REVIEW.md` records that run `30663562841` and expected batch `mb2-batch-000001-e32022126c07` have no retained artifacts in this checkout. Review and decision counts remain undetermined; canonical state is unchanged.

> **Phase 110A:** the dry-run path now prepares independently verifiable, exact-set `MB2` and `MSH` review batches and retains their payloads, manifests, ID lists, closure evidence, and pending packages. No production rerun artifacts are claimed yet; promotion and merge remain withheld pending green Actions.

> **Phase 110 gate:** merged Phase 109 (`bf696c5`) is confirmed, but the first production canonical promotion failed closed before execution. The repository retains only run `30649546787`'s summary, not its candidate shards or review packages; no reviewer approval or MB2-only batch membership can be verified. Zero entities were promoted and Architecture v12 is unchanged. See `docs/FIRST_CANONICAL_PROMOTION.md`.

> **Phase 109 update:** GitHub Actions run `30649546787` is the first verified successful targeted production dry run. Its retained summary records MB2 and MSH discovery, 10,940 eligible candidates and 11 deterministic batches without writes or promotion. Candidate payload shards and streaming review-index packages were not retained, so the workflow now uploads both; another targeted dry run is required for independently reconstructable review batches. See `docs/MTGJSON_FIRST_SUCCESSFUL_PRODUCTION_RUN.md`.

> **Phase 108B update:** ambiguous same-printing-coordinate `scryfallId` collisions are now fully diagnosed and narrowly quarantined; different-coordinate collisions remain fatal. Unaffected records continue to deterministic planning, while quarantined records cannot be promoted. Official-corpus verification remains pending.

> **Phase 108A update:** `src/providers/mtgjson/validator.py` now applies explicit namespace and
> scope policy. Non-guaranteed external collisions are retained and surfaced for review throughout
> the existing import/delivery path; strict and internal identities remain fail-closed.

> **Phase 107 update:** `src/promotion/delivery.py`, `scripts/mtgjson_delivery.py`, and the manual
> MTGJSON workflow deliver checksum-verified artifacts to the Phase 106 APIs, default to dry-run,
> and bound reviewed promotion to one selected batch. Hosted official-URL access remains HTTP 403;
> Architecture v12 is unchanged.

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

> **Status: Current** — Phase 105 implements official reference dataset acquisition over the
> merged Phase 104 baseline; Architecture v12 remains unchanged.

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
- **Latest merged baseline:** Phase 104 — bounded MTGJSON canonical promotion
- **Current milestone:** Phase 105 — Official Reference Dataset Acquisition
- **Maturity:** pre-alpha; deterministic local reference implementation
- **Validation baseline:** 253 tests passing locally
- **Canonical data:** 15 Cards and 15 Printings, including four Mystery Booster 2
  Printings; the MB2 Product is a foundation record; canonical Print Sheets and Slots
  remain unpopulated
- **Review authority:** `docs/PHASE_101_ARCHITECTURE_REVIEW.md` records current maturity, debt,
  risks, dependency direction, readiness, and roadmap recommendations

## Implemented subsystem inventory

| Subsystem | Implementation | Contract / status |
| --- | --- | --- |
| Canonical Repository | Typed game aggregate, specialized schema-backed repositories, deterministic snapshots, relationship validation, staged bulk apply | Operational v1; overlapping repository generations are consolidation debt |
| Canonical Query Engine | Stable provenance-bearing entity results; relationship, dataset, audit, validation, and deterministic exact search queries; CLI | Operational v1; sole supported read boundary for future consumers |
| Canonical Semantic Query Layer | Immutable structured operations, deterministic Query/Analytics delegation, snapshot identities, provenance, and JSON CLI | Operational v1; no AI reasoning or language generation |
| Canonical Import Pipeline | Reviewed local JSON/CSV adapters, provenance, dry-run/validation-only modes, deterministic report, atomic game-tree replacement | Operational v1; local-only and single-writer |
| Raw data acquisition | Immutable byte snapshots, provider adapters, normalized source records, assertion bridge, acquisition-run reports, offline CLI | Operational v1; no live providers or canonical promotion |
| Multi-source evidence acquisition | Immutable provider/source/dataset/artifact contracts, provider interface, deterministic reference registry, licensing gates, JSON CLI | Framework v1; no live providers, datasets, or promotion |
| Official reference dataset acquisition | Configured official URLs, resumable streaming, checksum/SHA-256 and JSON/schema gates, local registration, JSON CLI | Operational for MTGJSON AllPrintings; acquisition only |
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
- `data/local/reference-datasets/` — Git-ignored official artifacts, partial transfers, manifests, and non-canonical registrations
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
- The Phase 77 review is retained as historical evidence; the Phase 101 review is the
  current assessment and changes no Architecture v12 boundary.

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
`docs/PHASE_101_ARCHITECTURE_REVIEW.md`; `ARCHITECTURE_REVIEW_v1.md` is historical. Implemented subsystem contracts include
`docs/CANONICAL_IMPORT_PIPELINE.md`, `docs/MB2_OBSERVATION_INTELLIGENCE.md`,
`docs/MARKET_PROVIDER_FRAMEWORK.md`, `docs/COLLECTION_ENGINE.md`,
`docs/ANALYTICS_ENGINE.md`, and `docs/DECISION_ENGINE.md`. This inventory describes
what exists; the architecture review evaluates it; `docs/ROADMAP.md` controls future
milestones; `CHANGELOG.md` preserves history.

Current operational state is reported by `docs/SESSION_STATE.md`,
`docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and `docs/HANDOFF.md`. Phase-specific
plans explicitly marked Historical, Superseded, or Reference remain retained artifacts.

## Session startup workflow

1. Read `docs/CONSTITUTION.md`, this inventory, and
   `docs/PHASE_101_ARCHITECTURE_REVIEW.md` (`ARCHITECTURE_REVIEW_v1.md` is historical).
2. Read `docs/SESSION_STATE.md`, `docs/PROJECT_STATUS.md`, `docs/NEXT_TASK.md`, and
   `docs/HANDOFF.md` for the current operational state.
3. Read `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/ROADMAP.md`, and
   `CHANGELOG.md` for architecture, authorization, and history.
4. Treat Historical, Superseded, Reference, and Vision documents according to their
   labels; do not use them to override Current documents.
5. Confirm explicit milestone approval before changing the repository.

## Next-work boundary

Phase 105 was authorized but stopped without implementation because the required caller-supplied
AllPrintings artifact was absent. Phase 104 remains complete. The provider accepts
local evidence only and cannot promote it. Representative validation composes the existing
reviewed promotion boundary; full-corpus mapping and operations remain unproven. Mystery Booster
2 remains evidence-blocked; Simulation and operational AI advice remain unimplemented.

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

> **Phase 100 update:** `src/providers/mtgjson/execution.py` executes local AllPrintings evidence
> through registration and deterministic candidate validation into a pending-only review queue.
> No canonical write, automatic approval, networking, or promotion is available.

## Phase 117 — First MB2 operator-authorization gate (2026-08-01)

Phase 115 reviewed the exact first MB2 batch and Phase 116 resolved its 21 identifier findings,
leaving 1,000 approved candidates (384 Cards, 379 Printings, 235 Identifiers, 2 Finishes) with
valid dependency closure and no MSH candidates. Phase 117 reverified that complete immutable
chain and retained a deterministic signature request, authorization contract, verification, and
promotion-readiness report under `data/reviews/phase-117/mb2-batch-000001-e32022126c07/`.
A human must supply identity, role, durable review reference, RFC 3339 review time, one allowed
decision, notes, and matching request/batch/candidate digests. No authorization exists and
promotion readiness is false. Authorization and promotion remain separate; no canonical write or
promotion occurred. Architecture v12 and canonical contracts are unchanged.
