# Phase 123 — trusted MTGJSON refresh blocked (2026-08-01)

- Added checksum-verifying, immutable, idempotent AllPrintings snapshot registration.
- Recorded the provider refresh attempt; the environment returned HTTP 403 before publication identity or bytes could be acquired.
- Created no evidence identity, Hobbit result, candidates, descriptor, branch, PR, promotion, or canonical write. Phase 119 remains the sole production promotion and Architecture v12/contracts remain unchanged.

# Phase 122 — The Hobbit availability gate stopped fail-closed

Inspected retained trusted MTGJSON snapshot `5.3.0+20260731`: its complete retained target inventory is MB2 and MSH, with zero independently identifiable Hobbit target. Added a generic set-level availability/bounded-extraction gate, immutable structured report, and unittest coverage for zero, ambiguous, unique, incomplete, unsupported, isolation, checksum-addressed identity, and explicit unknown cases. No target code was guessed; evidence intake, candidate review, descriptor creation, plan/verify/execution, promotion, audit, rollback, and target PR were correctly not performed. Canonical digest remains `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`; Phase 119 remains the only promotion. No MB2, MSH/Marvel, or unrelated data was promoted, and Architecture v12 and canonical contracts remain unchanged.

# Phase 121 — synthetic automatic-update production-readiness validation

Validated all sixteen generic stages with isolated set `SYN`: one Set, two Cards, two Printings, one Identifier, and two Finishes, including explicit provenance and unknowns. Added fail-closed payload inventory/checksum/provenance and audit-integrity gates, deterministic protected-branch persistence, full JSON CLI/recovery/replay/rollback coverage, and mocked PR/green-check auto-merge validation. Production canonical state remains exactly Phase 119; no second MB2 batch or MSH/Marvel data was promoted, and Architecture v12/canonical contracts are unchanged.

# Phase 120 — Reusable automatic canonical update pipeline

Added generic sixteen-stage fail-closed orchestration, a versioned descriptor, JSON CLI, atomic recovery, replay/status/rollback planning, a minimum-permission protected PR/auto-merge workflow, reference MB2 configuration, documentation, and unittest coverage. Phase 119 was not repeated; no second MB2 batch or MSH data was promoted; Architecture v12 and canonical contracts are unchanged.

## Phase 118 — Remove operator authorization subsystem


## Phase 119 — first verified MB2 bounded canonical promotion (2026-08-01)

Promotion **succeeded** for exactly evidence `30663562841-review-payload-v2`, batch
`mb2-batch-000001-e32022126c07`, and target MB2 / Mystery Booster 2. The immutable
Phase 115/116 review chain and every Phase 118 readiness gate were independently reverified
immediately before the write. Exact membership is 1,000 approved candidates: 384 Cards,
379 Printings, 235 Identifiers, and 2 Finishes. Candidate digest is
`e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e`. There are zero
unresolved, excluded, quarantined, fatal-conflict, or orphaned candidates. MSH/Marvel, every
other MB2 batch, and every unrelated candidate were excluded.

Canonical pre-state digest was
`0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba`; post-state digest is
`793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Immutable audit
`phase-119-mb2-batch-000001-e32022126c07` records exact membership, source/review lineage,
preflight digest `d0ea6939c6c282647e24f8873f3021430b451173477013ccaca2fff60d6e1aab`,
pre/post-state digests, deterministic dependency order, replay, and rollback metadata.

Replay with `promote(data_root)`; a byte-identical completed promotion returns idempotent
success without another write or audit. Conflicting replay fails closed. Roll back with
`rollback(data_root)`; it verifies the audited post-state, removes only this bounded canonical
state, verifies restoration of the pre-state digest, and retains immutable audit history.
Architecture v12 and canonical contracts are unchanged. Stop after Phase 119; merge remains
withheld until normal pull-request review and GitHub Actions are green.

## Historical state before Phase 119

- Removed the Phase 117/117A authorization workflow, scripts, production module, tests, and current review artifacts; historical records remain available in Git history.
- Replaced human signatures with trusted-provider, validation-gated readiness under normal pull-request review and green GitHub Actions.
- Added deterministic readiness planning for exactly one verified MB2 batch with checksum, membership, isolation, closure, blocker, canonical-pre-state, audit, and rollback gates.
- The 1,000-candidate MB2 batch is technically ready for a separate bounded promotion. No MSH candidate, canonical write, or promotion occurred. Architecture v12 is unchanged.

## Phase 117A — GitHub-native MB2 operator authorization

- Added a manual, least-privilege workflow for genuine human submission of the immutable Phase 117 contract. It validates the Phase 115–117 chain and canonical pre-state, defaults to a non-persistent dry run, and rejects blank, placeholder, AI/automation, malformed, or mismatched input.
- Added independent immutable-artifact verification and fail-closed authorization-only branch/commit/PR persistence. No operator values, authorization artifact, canonical write, promotion, MSH scope, Architecture v12 change, or canonical-contract change is included.

## Phase 116 — Resolve ambiguous MB2 identifiers

- Resolved the exact 21 Phase 115 candidates as non-unique `scryfallCardBackId` aliases after retained collision evidence established one shared card-back reference across 820 distinct UUID-addressed printings.
- Recomputed the batch to 1,000 approved candidates (384 Cards, 379 Printings, 235 Identifiers, 2 Finishes), zero exclusions, unresolved candidates, quarantines, fatal conflicts, or orphaned Printings.
- Retained seven deterministic overlay artifacts and an unsigned `pending_operator_signature` decision. Operator-signature readiness is true, but promotion readiness remains false; no signature, canonical write, Marvel/second-batch review, or promotion occurred. Architecture v12 and canonical contracts are unchanged.

## Phase 115 — Review first Mystery Booster 2 batch

- Verified retained evidence identity `30663562841-review-payload-v2` and reviewed all 1,000 candidates in exactly the first MB2 batch from retained payload bytes.
- Retained a deterministic ledger with 979 approved, 0 excluded, and 21 additional-evidence classifications, plus findings and dependency-closure reports.
- Created an immutable unsigned pending decision and not-ready promotion report; no Marvel review, canonical write, signature, or promotion occurred.

## Phase 114A — Retain reviewable candidate payloads

- Added adapter v2 bounded extraction of exact ordered per-batch candidate payloads, source-shard authentication, deterministic payload identity/mapping, target isolation, dependency resolution, provenance, and complete manifest inventory.
- Added immutable derived evidence identities so the retained v1 run is never overwritten, and updated intake reporting/branch policy. No review, promotion, canonical write, Architecture v12, or canonical-contract change occurred.

## Phase 113A — State-aware retained-evidence gate

- Replaced Phase 113's permanent run-absence assumptions with a dual-state gate: the historical
  absent state remains fail-closed, while PR #86's retained state must prove run identity,
  manifests/indexes, non-canonical flags, MB2/MSH isolation, pending packages, and the absence of
  decisions or approval/promotion audits. No evidence, canonical state, review, or promotion was
  changed.

## Phase 112B — Fail-closed production-evidence persistence

- Reconciled the reported non-dry-run intake: normalization, intake, Phase 111 verification, and the write boundary completed, but durable persistence was never established. The only repository workflow path that can finish successfully without a branch is the pair of `if: ${{ !inputs.dry_run }}` steps being skipped; therefore the effective dispatch context remained dry-run even though the operator intended false. No Git, push, or PR command ran, and skipped steps supplied no command output or exit status.
- Replaced conditional Git/PR steps with an always-invoked persistence state machine. Non-dry-run now fails closed at named stages, verifies GitHub state independently, safely reuses only byte-identical existing evidence and one matching open PR, exposes persistence outputs, and uploads its structured report even on failure. No canonical, review, promotion, ingestion, or Architecture v12 logic changed.

## Phase 113 — retained MB2 review gate

- Re-ran the independent review exclusively against the Production Evidence Repository and
  recorded that run `30663562841` is not retained, so no deterministic MB2 batch exists to select.
- Recorded every requested verification dimension as unavailable, left all classification counts
  undetermined, and created no false review decision, Marvel review, canonical write, or promotion.

## Phase 112A — Native workflow artifact normalization

- Added a deterministic, fail-closed adapter from the nested native MTGJSON Actions artifact to
  the unchanged Phase 111 Production Evidence Repository contract, including complete source
  inventory, lineage and internal-hash verification, target-isolated pending-review bundles, and
  fixed-byte normalized ZIP output.
- Updated GitHub intake to authenticate, normalize, intake, verify, and enforce the write boundary
  in that order. Dry runs upload normalization evidence and never create a branch, commit, or PR.
- Recorded that run `30663562841` failed Phase 111 because native layout has no root intake
  manifest, not because its evidence was corrupt. No canonical write, review, approval, promotion,
  full MTGJSON retention, or Architecture v12 change occurred.

## Phase 112 — GitHub-native production artifact intake

- Added a manually dispatched, least-privilege workflow that validates a successful repository
  workflow run and its exact unexpired artifact before downloading it through the GitHub API.
- Required an independently supplied archive SHA-256, applied the Phase 111 intake and verification
  commands, and failed closed if any path outside `data/production_runs/` changed.
- Added dedicated intake-branch commit and evidence-only pull-request creation; candidate review,
  approval, promotion, and canonical writes remain explicitly out of scope.

## Phase 111 — production artifact intake and evidence repository

- Added a permanent, non-canonical `data/production_runs/` repository with immutable verified run
  directories and deterministic source, target, batch, workflow, and run lookup indexes.
- Added fail-closed ZIP intake with archive SHA-256, workflow identity, exact internal inventory,
  source lineage, bundle completeness, and digest validation; duplicates and modified, missing,
  unsafe, full-dataset, or transient content are rejected before atomic installation.
- Added JSON CLI commands for intake, run listing, inspection, batch lookup, and verification,
  plus unittest coverage. Architecture v12, canonical contracts, review, and promotion are unchanged.

## Phase 110B — independent MB2 review stopped at artifact gate

- Recorded the fail-closed attempt to review run `30663562841` and expected batch `mb2-batch-000001-e32022126c07`: selected-run artifacts are absent, so no candidates were classified, no decision was created, and no canonical write or promotion occurred.
- Added unittest coverage for the absent-evidence boundary and unchanged canonical state.

## Phase 110A — Retained Target-Specific Review Packages

- Partitioned exact MTGJSON `MB2` and `MSH` identities before dependency-closed batching and added fail-closed cross-target verification.
- Retained candidate payloads, ID lists, manifests, closure reports, pending review packages, findings, quarantine evidence, and workflow diagnostics without promotion.
- Documented the independent reviewer boundary and exact non-promoting production rerun.

## Phase 110 — Canonical Promotion Failed-Closed Precondition Gate

- Confirmed the merged Phase 109 baseline at `bf696c5` and inspected the only retained production evidence for run `30649546787`.
- Stopped before selecting or promoting a batch because candidate shards, per-batch review packages, reviewer identity, review reference, and independently verifiable dependency membership are absent. No missing information was inferred and no Marvel candidate was risked.
- Recorded zero promoted Cards and Printings and marked promotion, projection, downstream, AIModelRequest, rollback, and replay measurements as not observed rather than fabricating them. Architecture v12 and canonical state remain unchanged.

## Phase 109 — First Successful Production Dry Run

- Recorded verified evidence from GitHub Actions dry run `30649546787`: two exact target discoveries, 862 cards, 10,940 eligible candidates, 117 review-required identifier findings, 11 bounded batches, zero rejected/unresolved, and no promotion or canonical write.
- Documented that retained hashes and totals are internally consistent but candidate shards and streaming review-index packages were absent, preventing independent batch reconstruction.
- Added the two missing streaming artifact-upload globs. A new targeted dry run is required before independent review; no approval or promotion is authorized.

## Phase 108B — Scryfall Identifier Collision Investigation

- Classified the evidence-limited official `scryfallId` collision as ambiguous/unsupported rather than weakening global uniqueness.
- Added complete deterministic collision inventories, fatal diagnostics, narrow dependency-closure quarantine, review-visible evidence, and unaffected batch continuation.
- Preserved strict MTGJSON UUID and internal identity guarantees, the Phase 108A Deckbox policy, dry-run non-writing behavior, and reviewed promotion boundaries.
- The official artifact is unavailable locally; an official GitHub dry run remains the resolution gate.

## Phase 108A — External Identifier Validation Policy Fix

- Corrected the real-corpus defect that treated every non-Oracle MTGJSON external identifier as
  globally unique after the first official dry run stopped safely on `deckboxId:2676`.
- Added deterministic error/review-required identifier findings with complete affected-record
  provenance; retained strict MTGJSON UUID, global external, candidate, and internal uniqueness.
- Exposed findings through provider inspection, import review queues, production manifests, and
  delivery reports. No canonical write, promotion, Architecture v12 change, or corpus-pass claim.

## Phase 107 — MTGJSON Dataset Delivery and Production Ingestion Run

- Added a fail-closed local delivery command and manually dispatched GitHub Actions workflow for
  checksum-verified, temporary-storage AllPrintings planning and exactly one independently
  reviewed bounded promotion.
- Added deterministic machine-readable delivery reports, rollback instructions, unittest
  coverage, and operator documentation. The approved URL still returned HTTP 403 in hosted Codex;
  no real corpus result or promotion is claimed. Architecture v12 remains unchanged.

## Phase 106 — Production MTGJSON Dataset Ingestion v1

- Added deterministic dependency-closed review batches, explicit rejected/unresolved accounting, governed bounded promotion, typed projection, replay, rollback, downstream verification, and performance measurements.
- Added production-shape unittest coverage and operator documentation. Official acquisition was attempted through the approved subsystem but blocked by HTTP 403 in this environment; no substitute result was claimed. Architecture v12 remains unchanged.

## Phase 105 — Official Reference Dataset Acquisition

- Added configurable, resumable, fail-closed official dataset acquisition with deterministic local
  storage, SHA-256/checksum, JSON/schema verification, and existing evidence registrations.
- Added JSON `dataset download|verify|status mtgjson` and acquisition-aware `dataset list` commands;
  all operations stop before provider import, review, promotion, projection, or canonical writes.
- Added mocked-network unittest coverage and the official dataset operations/licensing contract.
  Architecture v12 and canonical contracts remain unchanged.

## Phase 105 — Targeted MTGJSON Set Population (source-gated)

- Confirmed merged Phase 104 (`79dbfe5`) and unchanged Architecture v12, canonical authority,
  independent-review promotion, and typed-projection boundaries.
- No caller-supplied immutable AllPrintings artifact was available, so the milestone stopped
  before discovery, extraction, review, promotion, or projection and recorded the exact local
  artifact request in `docs/TARGETED_MTGJSON_SET_POPULATION.md`.
- Added no runtime abstraction, fixture substitution, target-specific branch, canonical record,
  automatic approval, or unattended promotion. Neither requested target is marked populated.

## Phase 104 — Bounded MTGJSON Canonical Promotion v1

- Added a frozen five-entity MTGJSON-derived corpus and executed the complete governed
  review, promotion, typed projection, consumer, replay, rollback, and restore workflow.
- Added JSON `promote corpus|inspect|verify` commands, deterministic verification, rejected
  candidate isolation, supersession, and a non-executed `AIModelRequest` demonstration.
- Architecture v12 and canonical contracts remain unchanged; full or automatic promotion
  remains prohibited.

## Phase 103 — Typed Canonical Projection Engine v1

- Added a deterministic, idempotent, versioned projection registry and engine that maps
  approved canonical assertion state into existing typed canonical entities.
- Added fail-closed completeness, conflict/duplicate, lifecycle, supported-combination,
  schema, and repository validation plus immutable content-addressed projection audits.
- Added JSON `projection validate`, `projection project`, and `projection inspect` CLI
  commands and compatibility tests across Query, Analytics, Semantic, and Reasoning.
- Architecture v12 and canonical contracts remain unchanged; projection cannot bypass
  validation, independent review, or promotion.

## Phase 102 — Representative Corpus Validation

- Added a deterministic two-Card, three-Printing corpus spanning sets, rarities, finishes,
  languages, explicit unknowns, conflicts, failures, review, supersession, and rollback.
- Validated the governed acquisition-to-AI-request path without networking, model execution,
  new providers, canonical contract changes, or product-specific behavior.
- Documented methodology, limitations, the existing generic-to-typed projection gap, and
  conditional readiness for bounded imports in `docs/REPRESENTATIVE_CORPUS_VALIDATION.md`.

## Phase 101 — Architecture Review and Roadmap Refresh

- Completed a repository-wide post-Phase-100 review of Tier 0, current-state, subsystem,
  source, dependency, data, test, and documentation boundaries. Architecture v12 remains
  suitable and unchanged; no feature, canonical-data, or schema change was introduced.
- Published the current health, debt, readiness, maturity, testing, documentation, and
  ranked roadmap assessment in `docs/PHASE_101_ARCHITECTURE_REVIEW.md`; refreshed current
  status and roadmap documents.
- Fixed a genuine test-harness portability defect by declaring `tests/` as a package; the
  complete baseline is 246 passing tests and 17 passing subtests.

## Phase 100 — MTGJSON Reference Dataset Import Execution v1

- Executed the approved local-only MTGJSON provider through validation, artifact and dataset
  registration, deterministic candidate generation and hashing, and pending review-queue storage.
- Added JSON `provider mtgjson import|candidates|review` commands, forward-compatible
  AllPrintings-shape validation, fail-closed imports, documentation, and unittest coverage.
- Created no canonical entities and performed no networking, approval, or promotion; Architecture
  v12 and independent-review authority remain unchanged.

## Phase 99 — MTGJSON Reference Dataset Provider v1

- Added the first concrete Phase 98 provider: network-free local MTGJSON v5 discovery,
  validation, deterministic parsing/mapping, planning, capability reporting, and registration
  support for Cards, Printings, Sets, Languages, Rarities, Finishes, and Identifiers.
- Added `mtg-lab provider mtgjson validate|inspect|plan`, explicit retained unknown fields,
  duplicate/hash/schema/licensing gates, provider documentation, and unittest coverage.
- MTGJSON remains non-canonical reference evidence. No download, automatic review, promotion,
  product-specific mapping, canonical mutation, or Architecture v12 change was introduced.

## Phase 98 — Multi-Source Evidence Acquisition Framework v1

- Added immutable provider-neutral evidence, source, dataset, artifact, acquisition, licensing,
  and review contracts with deterministic JSON and SHA-256 identities.
- Added deterministic reference dataset/artifact registration, duplicate detection, fail-closed
  licensing validation, provider capabilities, and JSON evidence CLI commands.
- Added no live provider, download, dataset population, product-specific behavior, or automatic
  promotion; Architecture v12 and all canonical and downstream contracts remain unchanged.

## Phase 97 — Mystery Booster 2 Stage 2 card-list intake

- Confirmed merged Phase 96B (`0c88825`), unchanged Architecture v12, and successful bounded
  Stage 1 Product confirmation.
- Recorded the absence of a complete, terms-compliant immutable MB2 card-list source and
  stopped with zero Card/Printing promotions rather than fabricating membership.
- Added a deterministic, fail-closed Stage 2 package intake interface and unittest coverage;
  it validates provenance, review, identity, completeness, relationships, and audit-plan
  identity but cannot write canonical state.

## Phase 96B — Mystery Booster 2 Stage 1 evidence package

- Retained and registered the narrow official MB2 title capture with hash, terms notes,
  supported fields, explicit unknowns, and an independent review record.
- Added a generic reviewed-product evidence package importer and deterministic replay tests.
- Confirmed the existing foundation Product through controlled promotion without creating
  ProductVersion, PackDefinition, Slot, PrintSheet, Card, or Printing records.

## Phase 96 — Mystery Booster 2 Canonical Product Repository v1 (blocked assessment)

- Confirmed merged Phase 95 as the baseline and Architecture v12 as unchanged.
- Stopped before canonical mutation because no complete reviewed MB2 source is retained and the
  requested entity coverage conflicts with frozen Set/Language and unknown-pack representations.
- Preserved explicit unknowns and documented evidence and architect-clarification resume gates.

## Phase 95 — AI Model Adapter Framework v1

- Added immutable, versioned provider-neutral request, response, capability, provider, and
  execution contracts with deterministic serialization.
- Added an abstract reasoning-context-only provider interface, validated lifecycle, explicit
  deterministic registry, typed failures, and JSON AI CLI.
- Added no provider, SDK, inference, prompt, runtime dependency, or Architecture v12 change.

# Phase 94 — AI Reasoning Context Layer v1 (Unreleased)

- Added immutable, content-addressed reasoning context requests/results, deterministic evidence and provenance maps, mechanical truncation, typed errors, and JSON CLI commands.
- The layer consumes only public semantic contracts and adds no LLM, advice generation, canonical mutation, or Architecture v12 change.
- Merge recommendation remains withheld until GitHub Actions are green.

## Phase 93 — Canonical Semantic Query Layer v1

- Added immutable, schema-versioned semantic requests and responses plus deterministic operations
  over the Canonical Query and Analytics engines, preserving snapshot identities and provenance.
- Added five JSON semantic CLI groups, comprehensive unittest coverage, and architecture and
  integration documentation. Architecture v12 and canonical contracts remain unchanged; AI
  reasoning, language generation, simulation, and product-specific behavior remain out of scope.

## Phase 92 — Canonical Analytics Engine v1

- Added deterministic, immutable, versioned analytics over content-addressed Canonical Query
  Engine snapshots, including entity, dataset, validation, provenance, confidence, unknown,
  distribution, coverage, and supersession statistics plus five JSON CLI commands. No
  Architecture v12 contract, canonical schema, canonical state, AI, or simulation changed.

## Phase 91 — Canonical Query Engine v1

- Added the provider-agnostic, read-only Canonical Query Engine with a stable,
  provenance-bearing result contract; deterministic entity, relationship, provenance,
  audit, dataset, validation, and exact search queries; and five CLI query operations.
- Added comprehensive contract, relationship, state, ordering, repetition, and CLI tests
  plus architecture and integration documentation. Architecture v12 and canonical data are
  unchanged.

## Phase 90 — Mystery Booster 2 MTGJSON Pilot (evidence-blocked)

- Reconciled the project baseline to record Phase 89 as merged, then validated the only
  checked-in MTGJSON dataset as a ten-card synthetic `TST` fixture containing no MB2 records.
- Applied the mandated stop condition before acquisition, registration, resolution, or
  promotion; added deterministic machine-readable and narrative evidence-gap reports plus a
  regression test. No canonical data or Architecture v12 contract changed.

## Phase 89 — MTGJSON Provider Adapter v1

- Added provider-edge-only MTGJSON v5 detection, metadata/manifest generation, strict validation, deterministic bounded Set/Card/Printing mapping, explicit unknowns, and acquisition integration.
- Added `adapter detect`, `adapter inspect`, and `adapter normalize`, a ten-card synthetic fixture, provider-specific tests, and adapter documentation. Architecture v12 and promotion authority remain unchanged; no full corpus or MB2 data was imported.

## Phase 88 — External Dataset Ingestion Framework

- Added provider-agnostic JSON, CSV, and ZIP ingestion with a canonical external dataset
  manifest, checksum and structure validation, safe archive handling, deterministic
  registration, duplicate detection, and extensible format adapters.
- Composed verified supplied bytes into the unchanged raw acquisition and Knowledge Review
  Package pipeline. Ingestion stops at human review and never invokes canonical promotion.
- Added `ingest`, `ingest validate`, `ingest inspect`, and `ingest list` CLI operations,
  comprehensive failure/idempotence tests, and the ingestion contract documentation.
- Reconciled current-state documents to record Phase 87 as merged and evidence-blocked
  before establishing Phase 88. Architecture v12 remains unchanged; no MB2 data was imported.

## Phase 87 — Mystery Booster 2 Acquisition Pilot (evidence-blocked)

- Completed the pre-implementation source and Architecture v12 compatibility assessment.
- Stopped before acquisition because no retrievable, immutable, legally reviewed 25–50-card raw source was available; no dataset was registered and no canonical data was promoted.
- Added `docs/MYSTERY_BOOSTER_2_ACQUISITION_PILOT.md` with source inventory, evidence gap, limitations, and reproduction requirements.

# Changelog

## Phase 96A — Mystery Booster 2 import contract resolution

- Confirmed the Phase 96 blocker assessment is merged and classified its Set/Language and
  uniform-governance expectations as prompt-assumption errors rather than architecture defects.
- Selected omission of PackDefinition until topology evidence exists, preserving unknown-versus-
  absent semantics without changing frozen contracts.
- Documented the governance metadata inventory, staged evidence acquisition plan, and exact
  evidence/review/promotion gates for resuming bounded MB2 population.
- Added no MB2 records and changed no runtime or Architecture v12 contract.

## Phase 86 — Canonical Dataset Import Framework (Pilot)

- Added first-class dataset registration, deterministic entity resolution, governed import sessions, reporting, unified CLI commands, and a reviewed non-MB2 pilot.
- Composed the existing acquisition, review, and promotion engines without changing Architecture v12.

## Unreleased

- Phase 85 Canonical Promotion Engine v1: fail-closed Knowledge Review Package validation, deterministic provenance-preserving canonical versions, immutable success/failure audits, supersession chains, compensating rollback, replay verification, acquisition CLI commands, and comprehensive tests. Architecture v12 remains unchanged and no MB2 data was imported.

## Evidence Review Engine

- Added a product-agnostic pre-promotion engine for external evidence handoffs.
- Added versioned handoff and review-report schemas, deterministic JSON and
  Markdown renderers, integrity/provenance/completeness checks, duplicate and
  explicit-claim conflict detection, and comprehensive unit coverage.
- Preserved the Phase 66 evidence-waiting boundary: no product-specific logic,
  canonical data, rules, generators, probabilities, or simulations were added.

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0/).

## [Unreleased]

### Added

- Phase 84 Knowledge Acquisition Pipeline v1: deterministic dataset identities, independent
  provider policies, pre-review validation, machine-readable reports, review packages,
  offline collectible-card fixtures, CLI stages, documentation, and tests. No canonical
  promotion or Mystery Booster 2 population was performed; Architecture v12 is unchanged.

### Changed

- Phase 83.1 reconciled authoritative project-state documentation after the successful
  Phase 83 merge: Phase 83 is complete, Phase 82 remains the latest runtime milestone,
  Architecture v12 is unchanged, the active baseline is 154 passing tests, and no prior
  pull-request merge gate or follow-on implementation authorization remains active.

### Added

- Phase 83 Tier 0 institutional memory: a Project Constitution and amendment process, a
  chronological Architect's Notebook, an architectural Future Vision, and a user-question
  compass. Project-state documents now cross-reference their roles. This documentation-only
  milestone leaves Architecture v12, runtime behavior, schemas, canonical data, providers,
  simulation, and intelligence implementation unchanged.


### Added

- Phase 82 generic raw data acquisition framework: immutable checksum-addressed snapshots, provider abstraction and offline fixture, normalized source records, Phase 80 candidate-assertion bridge and change reports, auditable resumable acquisition runs, security controls, explicit-stage CLI, documentation, and comprehensive tests. No canonical records or MB2 population were added; Architecture v12 remains unchanged.

- Phase 79 pre-implementation inventory and architectural-fit review. The review found
  blocking Card/Printing field, assertion-provenance, unknown-collation, and v2 importer
  limitations, so no MB2 dataset, fixture, canonical record, or collation claim was
  added and Architecture v12 remains unchanged.

- Phase 77.1 repository documentation reconciliation: current session state, executive
  dashboard, handoff, next task, documentation hierarchy, startup workflow, historical
  status labels, and implementation-versus-vision wording now describe one consistent
  baseline through Phase 77. Historical plans remain retained. No runtime behavior,
  tests, schemas, models, public APIs, or canonical data changed.

- Phase 77 repository-wide Architecture v12 review, including subsystem maturity
  ratings, dependency direction, technical debt and risk register, documented defects,
  non-breaking consolidation sequence, future scaling considerations, and reconciled
  inventory and roadmap. This milestone changes no runtime behavior, canonical data,
  public API, or user-facing feature.

- Documentation reconciliation for the merged first artifact-bearing Phase 67
  evidence handoff and its successful Evidence Review Engine run. The handoff's
  re-delivered official product-title capture supports only MB2 identity; frozen
  Tier 0, the evidence-insufficient rule assessment, and the prohibition on
  canonical promotion remain unchanged.
- An executive `docs/PROJECT_STATUS.md` dashboard that records verified repository
  counts, documentation authority, Phase 66 entry and exit gates, mandatory stop
  conditions, debt categories, critical path, risks, and bounded estimates.
- Documentation recovery that reconciles the PR #18 empty-artifact research
  handoff into the Phase 66 evidence-waiting state without beginning Phase 66,
  changing canonical data, or authorizing downstream product layers.
- A post-Phase 65 architectural assessment and complete dependency plan for the
  first evidence-backed Mystery Booster 2 booster, including a bounded proposed
  evidence-acquisition milestone; no implementation or canonical data changed.
- A documentation-only Phase 66 Evidence Acquisition Packet, controlled raw
  handoff layout, source/claim checklist, stop conditions, and machine-readable
  external intake manifest template for network-restricted operation.
- A retained, schema-validated Mystery Booster 2 Rule Claim Matrix with stable claims, evidence classifications, Source Record and bundle references, precise locators, Tier 0 entity mappings, and explicit uncertainty.
- A deterministic Evidence Sufficiency Report separating known, partial, and unknown claims, blockers for canonical rules, pack generation, and probability, plus a no-redesign architectural sufficiency assessment.
- A content-verified archive of the controlled official Mystery Booster 2 product-title capture and cross-validation for non-canonical rule research artifacts.
- Scalable evidence-backed Card and Printing batches of up to twenty-five complete records, with oversized-input rejection and manifest-declared record-count and Printing-identity boundaries.
- Versioned deterministic pre-promotion review reports retained alongside intermediate artifacts, summarizing new and reused Cards, new Printings, duplicates, conflicts, rejected records, and expected repository count changes.
- Evidence-repository-exclusive Mystery Booster 2 Card and Printing Wave 2,
  adding one verified pair with deterministic intermediate artifacts, declared
  embedded sources, controlled dependency-order promotion, and immutable audits.
- A verified-wave application boundary that selects one archived JSON artifact,
  validates its embedded source identifiers, and identifies existing Cards that
  must not be promoted again.
- Canonical evidence archive foundation under `data/sources/`, including a
  versioned evidence-manifest schema, content-verified archived bundle loading,
  provenance validation against canonical Source Records, and an archive of the
  existing Mystery Booster 2 Wave 1 evidence without additional card population.
- Deterministic multi-source Mystery Booster 2 Card and Printing ingestion,
  demonstrated by three evidence-supported pairs promoted in dependency order
  with retained raw, parsed, candidate, canonical, and immutable audit records.
- Canonical Print Sheet and Slot repository foundation with minimally aligned
  provenance and game-scoped contracts, stable paths, deterministic snapshots,
  complete dependency validation, controlled promotion, immutable audits, and
  dependency-safe rollback verified only with temporary synthetic fixtures.
- Approved Tier 0 Rules Engine Specification and the minimal canonical
  repository-layer boundaries needed to support future Print Sheet and Slot
  records without introducing implementation behavior.
- Approved Tier 0 Data Model Specification as the canonical architectural
  contract for entity identities, relationships, provenance, and validation.
- Initial repository foundation for Mystery Booster 2 analysis.
- Canonical project layout for data, source modules, tests, scripts, notebooks, and documentation.
- Versioned schemas and validation infrastructure for canonical records.
- Mystery Booster 2 canonical product foundation with source provenance and no inferred collation data.
- Generic source registry and acquisition manifests with validated source-target references.
- Evidence-preserving ingestion foundation with deterministic SHA-256 hashing, immutable filesystem evidence storage, parser contracts, and a non-canonical pipeline.
- Parsed-record and normalized-candidate artifact schemas, immutable models, field-level provenance, cross-artifact validation, and hash-safe intermediate storage.
- Controlled Mystery Booster 2 official product-page title evidence, a deterministic product-specific HTML parser, and provenance-complete non-canonical product normalization.
- Explicitly approved canonical product promotion with validation gates, complete provenance snapshots, immutable decision audits, idempotency, conflict detection, rejection, and audited rollback.
- Canonical Card and Printing repository foundation with deterministic stable
  identifiers and snapshots, official source evidence, field-level provenance,
  structural validation, identity-path validation, and Printing-to-Card
  referential validation.
- Entity-agnostic candidate review and canonical promotion, enabled for Card and
  Printing candidates with explicit approval and rejection, immutable audits,
  idempotent and conflict-safe writes, source and provenance validation,
  Printing-to-Card enforcement, and dependency-safe rollback.
- A fixed Phase 58 increment of ten official-source-attributed Limited Edition
  Alpha Cards and Printings, including retained candidate artifacts, canonical
  records, and twenty immutable approval audits.

[Unreleased]: https://github.com/IDontFeelNone/MTG-Lab/compare/v0.0.0...HEAD

## Historical — Phase 80 Canonical Card, Printing, Evidence, and Uncertainty Contract (2026-07-30)

Phase 80 adds the compatible v3 Card/Printing and assertion-level evidence contract,
explicit partial-knowledge semantics, deterministic promotion, legacy projections,
and fail-closed simulation readiness. Historical canonical records remain unchanged;
full Mystery Booster 2 population remains out of scope. See
`docs/CANONICAL_CARD_PRINTING_EVIDENCE_CONTRACT.md`. Its former pull-request merge gate
is satisfied and is not active guidance.

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
