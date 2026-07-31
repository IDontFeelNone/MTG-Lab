# Phase 101 — Architecture Review and Roadmap Refresh

> **Status:** Complete — 2026-07-31  
> **Scope:** Repository state after merged Phase 100 (`6fb6266`)  
> **Architecture:** v12 reviewed and unchanged  
> **Change class:** Documentation and one test-harness portability defect; no feature, canonical-data, schema, or runtime change

## 1. Executive summary

MTG Lab is a disciplined **pre-alpha reference platform with a beta-ready architectural
shape**, not a beta product. Architecture v12 has **not materially drifted**: canonical
truth remains repository-owned, acquisition and normalization cannot promote, promotion
is explicit and audited, deterministic read/analytics/semantic/reasoning layers point
downstream, and the AI adapter has no authority over upstream state. The implementation
now demonstrates nearly every boundary from local evidence to an AI-provider-neutral
request, but it does so at fixture scale and mostly through filesystem stores.

The strongest qualities are fail-closed contracts, unusually complete provenance,
immutable/content-addressed artifacts, deterministic serialization, controlled promotion,
and broad subsystem tests. The principal risks are no longer missing abstractions. They
are **overlapping generations of abstractions**, a query facade that reads both typed
repository objects and raw storage, repeated persistence/identity machinery, single-writer
filesystem assumptions, and current-state documentation that accumulated contradictory
phase banners.

No architectural redesign is justified. Consolidation should be incremental and preserve
all v1/v2/v3 bytes and public boundaries. Readiness is highest for governed canonical
promotion and lowest for simulation, whose inputs remain evidence-blocked. A local
MTGJSON corpus can now reach a pending review queue, but large-corpus behavior, durable
review operations, and a governed mapping from provider candidates into canonical
contracts are not yet demonstrated.

One genuine defect was found during the review: `tests/test_reasoning_context.py` imports
shared test fakes through `tests.*`, while `tests/` was not a declared package. Collection
failed in this environment. A package marker fixes the portability defect without
changing runtime behavior. The complete suite then passed: **246 tests and 17 subtests**.

## 2. Review method and evidence base

The review read the Tier 0 corpus, current-state documents, Architecture v12, decisions,
roadmap, project inventory, README, subsystem contracts, and Phase 96–100 handoffs. It
then inspected all `src/` packages, schemas, test modules, canonical/data layouts,
repository imports, debt markers, and the merged Phase 100 baseline. The assessment used:

- 116 Python source files, approximately 9,821 source lines, 200 classes, and 572 functions;
- 133 retained data files (about 1.3 MiB), including 51 canonical files;
- 246 executable tests plus 17 unittest subtests after the portability fix;
- repository-wide searches for TODO, FIXME, obsolete, deprecated, incomplete, and
  unimplemented markers; and
- direct dependency inspection plus complete test execution.

Counts describe the reviewed checkout and are not quality scores. Test count means pytest
items; the 17 subtests are reported separately rather than inflated into the item total.

## 3. Architecture review

### 3.1 Repository structure

**Finding: sound, with visible evolutionary layers.** Top-level separation between
canonical data, raw evidence, intermediate artifacts, observations, audits, source,
tests, and documentation matches Architecture v12. Packages broadly correspond to
bounded subsystems and the CLI is isolated under `mtglab`.

The structure also exposes consolidation debt:

- empty placeholders remain at `src/importer`, `src/parser`, `src/models`,
  `src/probability`, `src/simulation`, and `src/market/.gitkeep`;
- root-level subsystem packages and `mtglab/*` command packages follow different
  organizational conventions;
- evidence/acquisition functionality spans `ingestion`, `acquisition`, `evidence`,
  `evidence_review`, `external_ingestion`, and `providers`; and
- three schema generations are valid history, but their location and compatibility
  ownership are not obvious to a new contributor.

These are navigation and maintenance costs, not evidence of an invalid architecture.

### 3.2 Dependency direction

**Finding: correct at the architectural level.** The meaningful flow remains:

```text
external bytes -> acquisition/evidence -> review -> promotion -> canonical repository
  -> query -> analytics/semantic -> reasoning context -> AI adapter / CLI consumers
```

Collection, market, observations, analytics, and decisions consume canonical identity
without gaining canonical write authority. Semantic delegates to Query and Canonical
Analytics; reasoning delegates to Semantic; the AI adapter depends on reasoning contracts.
No reverse dependency from canonical or promotion into AI, semantic, decisions, market,
or collection was found.

There are two coupling qualifications:

1. `CanonicalQueryEngine` constructs `CanonicalRepository` **and** scans canonical JSON
   directly for assertion/provenance fields. That makes query behavior depend on storage
   layout in addition to the advertised typed repository boundary.
2. `repository` imports ingestion models and evidence helpers in several specialized
   paths. This is historical promotion support, but it weakens the ideal that repository
   contracts are ignorant of upstream pipeline implementations.

Neither warrants Architecture v12 change. Both warrant boundary-consolidation tests and
small adapters in future debt milestones.

### 3.3 Canonical Repository

**Strengths.** It is read-only for consumers, validates cross-entity references,
preserves immutable v1 data, exposes v2 compatibility projections, supports v3 evidence
states, and produces deterministic snapshots. Promotion remains the controlled writer.

**Risks.** There are specialized repositories (`cards`, `products`, `rules`, `sources`),
a typed aggregate (`repository.canonical`), compatibility logic, and promotion-specific
repositories. Multiple generations encode similar path, schema, JSON, validation, and
atomic-write concepts. Eager full-tree loading and linear scans are acceptable at current
scale but not validated for a complete AllPrintings-derived repository. A single logical
repository interface is documented more strongly than it is implemented.

**Assessment.** Responsibility remains clean; implementation consolidation is desirable,
not urgent. Do not rewrite retained formats merely to reduce file count.

### 3.4 Acquisition Framework and MTGJSON provider

**Strengths.** Raw bytes are immutable and content-addressed; provider trust is separate;
licenses fail closed; normalization preserves unknown fields; supplied-file, generic
evidence, legacy MTGJSON adapter, and Phase 99/100 provider paths all stop before
promotion. Phase 100 validates the complete document before registration and creates
only validated, pending candidates.

**Risks.** Five related vocabularies—raw snapshots, evidence artifacts, external dataset
registrations, knowledge review packages, and reference provider candidates—are valid at
their boundaries but expensive to understand. MTGJSON has both the Phase 89 external
adapter and Phase 99 provider, with overlapping validation/mapping intent. The new provider
emits Set, Language, Rarity, Finish, and Identifier candidates even though frozen
canonical contracts do not define all of them as first-class promotable entity types.
That is safe because execution stops at review, but the next handoff contract is unresolved.

Large-corpus memory, time, interruption recovery, quarantine, and resumability have not
been measured with an actual AllPrintings corpus. Content-addressed registration is sound;
operational scale is unproven.

### 3.5 Promotion Engine

**Strengths.** Explicit independent review, validation, immutable success and failure
audits, deterministic versions, supersession, compensation, rollback, replay, unknown
preservation, and idempotency are unusually mature for pre-alpha. Promotion owns writes;
acquisition does not call it implicitly.

**Risks.** Legacy candidate promotion and the Phase 85 Knowledge Review Package engine
coexist. Their audit shapes and provenance vocabularies overlap without a single reader.
Filesystem transactions rely on one process and compensation rather than locking or a
durable transaction coordinator. Bulk scale and concurrent reviewers are not tested.

### 3.6 Query, Analytics, Semantic, and Reasoning Context

**Query.** The result envelope is storage-independent and provenance-aware, operations are
deterministic, and the CLI exercises them. Direct raw-tree scanning is the main hidden
coupling. Search is intentionally bounded rather than accidentally fuzzy.

**Analytics.** Two analytics families exist: general `AnalyticsService` reports over
collection/observations/products and `CanonicalAnalyticsEngine` over Query snapshots.
Both are deterministic and read-only, but the shared name “Analytics Engine” hides two
entry points and two report domains. This is naming/conceptual duplication rather than a
behavioral defect. Probability, EV, forecasts, and portfolio analytics remain absent.

**Semantic.** It is correctly a structured operation router rather than natural-language
understanding. Its name can mislead readers, but the contract is explicit. It delegates
rather than reproducing repository logic.

**Reasoning context.** It preserves provenance, uncertainty, limits, omissions, and
content identity. It is an appropriate anti-corruption layer for future model providers.
The context currently depends on specific semantic operation/result shapes; compatibility
fixtures should be retained when either contract evolves.

### 3.7 AI Model Adapter

The provider-neutral registry and immutable request/response lifecycle are correctly
placed downstream and have typed failures, deterministic serialization, and no imported
SDK. There is no model provider, inference, prompting policy, safety/evaluation harness,
or generated advice. Calling this an “AI Model Adapter” is fair as a framework, but project
summaries must not imply an operational AI capability.

### 3.8 CLI

The CLI provides useful JSON seams across most implemented layers and is well covered by
subsystem tests. It is currently assembled in a large central dispatcher plus namespace
modules; command names reflect accumulated milestones (`adapter`, `provider mtgjson`,
`evidence`, `ingest`, `acquisition`, `dataset`). This mirrors real boundaries but presents
a steep user model and overlapping routes. There is no stable CLI compatibility policy,
end-to-end operator guide, packaging metadata, or installed console-script test. Keep
commands until a separately reviewed compatibility plan exists; do not collapse them
casually.

### 3.9 Architecture v12 drift verdict

**No material drift.** Every constitutional authority boundary remains intact. The most
important implementation mismatch is that Query reads raw canonical files beside the
typed repository to recover evidence metadata. The most important complexity risk is
parallel acquisition and repository generations. Both are evolutionary debt already
anticipated by the architecture; neither proves the architecture wrong or requires a
v13 proposal.

## 4. Technical debt inventory

### Critical

None discovered. No path was found that lets unreviewed evidence, analytics, AI output,
market data, or observations silently mutate canonical truth.

### High

| Debt | Evidence / impact | Recommendation |
| --- | --- | --- |
| Full-corpus scale is unproven | Eager parsing/loading, filesystem copies, and linear scans may make large import/review impractical | Establish benchmark corpus, budgets, failure injection, and resumable batch boundaries before population |
| Promotion is single-writer only | No cross-process lock/generation guard; compensation is not concurrency control | Add concurrency contract and generation checks before multi-user operation |
| Provider-to-canonical handoff is incomplete | Phase 100 candidate entity taxonomy exceeds current promotable canonical taxonomy | Define a generic reviewed mapping/resolution package; do not auto-promote or add provider-shaped canonical entities |
| MB2 topology evidence is absent | No complete pools, sheets, slots, weights, conditionality, correlation, or sequence | Continue evidence acquisition; keep simulation blocked |

### Medium

| Debt | Evidence / impact | Recommendation |
| --- | --- | --- |
| Query bypasses one repository boundary | Typed aggregate plus raw JSON scan couples result semantics to paths/storage fields | Move evidence projection behind a repository-owned read adapter, preserving Query results |
| Repository generations overlap | Specialized, aggregate, compatibility, and promotion repositories duplicate validation/path logic | Inventory public callers, converge behind facades incrementally, retain formats |
| Acquisition generations overlap | Legacy ingestion, raw acquisition, external ingestion, generic evidence, and provider framework duplicate identity/storage concepts | Publish one lifecycle map and designate preferred entry points before code consolidation |
| MTGJSON adapters overlap | Phase 89 and Phase 99 independently detect/map AllPrintings-like input | Reuse pure validators/mappers where contracts truly match; keep distinct orchestration semantics |
| Provenance vocabulary is fragmented | Source records, assertions, manifests, review packages, audits, snapshots, and query summaries lack one traversal API | Implement a read-only lineage index/reader before AI explanation or migration work |
| Analytics naming is ambiguous | General factual reports and canonical snapshot analytics share one subsystem label | Document two domains and stable entry points; avoid a disruptive rename |
| CLI surface is milestone-shaped | Several commands describe similar acquisition tasks | Define operator personas, compatibility policy, and command map before simplification |
| Test support crossed modules implicitly | `tests.*` reuse failed without a package declaration | Fixed by explicit package marker; later move reusable fakes into a named support module |

### Low

- Empty placeholder packages and `.gitkeep` files add navigation noise.
- Deprecated v1 typed aliases remain intentionally for compatibility; removal needs usage
  evidence and a version policy.
- Numerous one-line command modules and compact source formatting reduce readability but
  do not compromise correctness.
- Phase-specific retained artifacts are valuable history but need clearer historical labels.

### TODO/FIXME and dead-code result

No literal TODO, FIXME, XXX, HACK, or runtime `NotImplemented` debt marker was found in
`src/` or tests. That is positive, but roadmap prose is the real debt ledger. Static
inspection cannot prove dead code. The strongest candidates are empty placeholders and
compatibility aliases; neither should be removed without import/consumer evidence.

### Inconsistent terminology

- “canonical import” refers both to legacy atomic batch import and reviewed promotion;
- “provider” is used by market, raw acquisition, external ingestion, generic evidence,
  MTGJSON reference data, and AI contracts;
- “analytics engine” names general domain reports and canonical snapshot statistics;
- “semantic” means structured typed operations, not language understanding;
- “review” can mean evidence review, candidate review, knowledge-package review, PR review,
  or pending provider candidate state; and
- “current milestone,” “latest merged phase,” and “merge pending” contradicted one another
  across current documents before this refresh.

A glossary and lifecycle diagram are preferable to renaming stable code immediately.

## 5. Documentation review

### Strengths

Tier 0 principles are explicit and mutually compatible. Major implemented subsystems have
bounded contracts that state exclusions, authority, determinism, and failure behavior.
Historical evidence and phase decisions are retained rather than rewritten. Architecture
v12 clearly distinguishes target diagrams from current implementation.

### Outdated or contradictory material

Before this review, `ROADMAP.md` simultaneously called Phase 100, Phase 93, and Phase 96B
current; `PROJECT_INVENTORY.md` called Phase 100 current but Phase 98 latest merged and
listed a 194-test baseline; README still named Phase 77.1 as current, claimed only a
pre-reasoning platform in one section, and opened with a Phase 96B merge-pending banner.
Several subsystem documents preserve “review/green CI pending” language after their
merges. These are documentation defects, not architectural drift.

This milestone refreshes the authoritative current-state and roadmap documents. Historical
phase documents should be relabeled in a later documentation-only cleanup rather than
silently rewritten.

### Redundancy

`PROJECT_STATUS`, `SESSION_STATE`, `HANDOFF`, `NEXT_TASK`, `PROJECT_INVENTORY`, README,
ROADMAP, CHANGELOG, and phase banners all repeat current phase state. The intended
hierarchy exists but maintenance has not enforced it. Keep:

- `PROJECT_STATUS` as the single concise current dashboard;
- `PROJECT_INVENTORY` as detailed implementation inventory;
- `ROADMAP` as ranked forward-looking recommendations;
- `CHANGELOG` as history; and
- `HANDOFF`/`SESSION_STATE` only for operational context, preferably generated or linked.

`NEXT_TASK` should link to an approved milestone rather than restating a phase narrative.

### Missing documents

1. A dependency and lifecycle map updated after Phase 100.
2. A glossary for evidence/acquisition/review/provider terms.
3. A persistence, locking, and recovery contract for operational scale.
4. A CLI command/reference and compatibility policy.
5. A test strategy/coverage matrix with supported Python versions and performance suites.
6. A lineage traversal contract spanning evidence through derived outputs.
7. A release/maturity checklist distinguishing architectural readiness from operational
   production readiness.

### Documentation disposition

**Mostly healthy contracts, unhealthy status synchronization.** The architecture corpus is
strong. Current-state duplication and stale merge language are the largest documentation
risk. This report supersedes `ARCHITECTURE_REVIEW_v1.md` only as the current implementation
assessment; v1 remains valid historical evidence of the Phase 77 baseline.

## 6. Testing review

### Baseline

- **246 pytest items passed**.
- **17 unittest subtests passed** inside those items.
- Tests are deterministic local tests; no network or external service is required.
- The suite completes in seconds at fixture scale.

### Subsystem coverage

| Area | Test strength | Notes |
| --- | --- | --- |
| Schemas, canonical repositories, relationships | Strong | Invalid structure, duplicates, provenance, orphans, snapshots, v1/v2/v3 compatibility |
| Evidence, ingestion, acquisition, review | Strong | Integrity, path safety, unknowns, conflicts, resumability, deterministic artifacts |
| Promotion and rollback | Strong | Approval/rejection, audit failure compensation, idempotency, replay, supersession |
| Query, canonical analytics, semantic, reasoning, AI adapter | Strong contract coverage | Determinism, immutability, provenance, typed failures, CLI; no real AI provider |
| Market, mapping, collection, decisions | Good foundation coverage | Offline/manual and fixture-scale only |
| MTGJSON provider/execution | Good bounded coverage | Synthetic ten-card fixture; no complete corpus, memory, throughput, or crash recovery |
| MB2 retained data | Good evidence-bound regression coverage | Intentionally incomplete; no topology/simulation assertions |
| CLI | Broad command-level unit coverage | Mostly direct `main()` invocation; no packaged install or shell end-to-end contract |

### Weak or missing coverage

- full AllPrintings import, candidate review, mapping, and promotion at realistic scale;
- concurrent writers/reviewers, locking, interrupted atomic operations, and recovery;
- one end-to-end governed flow from supplied external bytes through independently reviewed
  canonical promotion and downstream query/context;
- performance and memory regression thresholds;
- supported Python version matrix and OS/filesystem portability;
- property/fuzz testing for schemas, archives, identifiers, and path handling;
- live provider contract tests (none exist by design);
- database projection/rebuild tests (database is not implemented);
- simulation/statistical validation (simulation is not implemented); and
- real model-provider conformance, prompt safety, evaluation, and cost controls.

### Deterministic guarantees

Determinism is tested extensively for canonical JSON, hashes, sorted outputs, immutable
models, replay, fixed-clock behavior, reports, snapshots, queries, and repeated imports.
Timestamp-bearing workflows remain deterministic only when timestamps/clocks are explicit.
Filesystem atomicity is tested under ordinary failure injection, not concurrent processes,
power loss, or network filesystems. Therefore deterministic **content behavior is strong**;
operational determinism under concurrency is unproven.

## 7. Platform readiness assessment

| Capability | Rating | Rationale |
| --- | --- | --- |
| Canonical Promotion | **Ready** | Strong validation, explicit independent review, audit, idempotency, rollback, replay, and fail-closed behavior for bounded single-writer workflows. Not yet operationally multi-user. |
| Large dataset imports | **Mostly Ready** | Local MTGJSON validation and pending candidates exist; realistic corpus benchmarks, resumable chunking, durable review, concurrency, and canonical mapping are missing. |
| MB2 repository population | **Not Ready** | Product identity and four bounded printings exist, but no qualifying complete list/topology evidence supports full Cards, Printings, Sheets, Slots, or rules. |
| Simulation | **Not Ready** | Engine absent and outcome-affecting inputs remain unknown. The constitutional fail-closed gate correctly blocks it. |
| AI Advisor | **Not Ready** | Query, analytics, semantic context, reasoning context, and adapter contracts exist, but no model provider, advice policy, evaluation, or safety boundary is operational. |
| Collection Intelligence | **Mostly Ready** | Ownership operations, deterministic summaries, analytics, decisions, and reasoning context exist; valuation, decks, user objectives/privacy, and advisor behavior do not. |
| Market Intelligence | **Mostly Ready** | Provider/service/mapping/snapshot foundations are sound; only manual/offline data exists, with no live history, freshness policy, FX, liquidity, or market analytics. |

“Ready” here means ready for the bounded capability stated, not production-ready as a
hosted service. In particular, Canonical Promotion is ready as a controlled local workflow.

## 8. Updated roadmap recommendation

Roadmap ranking must separate **value** from **implementation order**. The highest-value
outcome is reliable product intelligence and simulation, but it cannot start before
evidence and canonical rule readiness. Foundation milestones below may therefore precede
higher-value capabilities despite ranking lower by direct user value.

The next approved milestone should be a bounded debt/readiness milestone, not a feature:
prove Phase 100 against a realistic local corpus, specify the reviewed provider-to-canonical
handoff, and measure resource behavior without promoting data. New feature authorization
should remain separate.

## 9. Top 10 remaining milestones, ranked by value

1. **Evidence-complete product intelligence and simulation.** Deliver generic,
   reproducible pack generation/probability only after complete evidence and fail-closed
   readiness. Highest user value; presently blocked.
2. **Complete governed canonical reference population.** Convert a terms-compliant,
   reviewed reference dataset into canonical Card/Printing coverage with explicit mapping,
   rejection, lineage, and resumable promotion.
3. **Collection Intelligence v1.** Join ownership, canonical identity, deterministic
   analytics, user objectives, and explainable decisions without AI authority.
4. **Market Intelligence v1.** Add a terms-compliant live provider, temporal snapshots,
   freshness/coverage semantics, currency handling, and factual market analytics.
5. **AI Advisor v1.** Implement one provider behind the adapter with cited reasoning
   contexts, strict no-promotion authority, evaluation, privacy, cost, and failure policy.
6. **MB2 evidence closure and canonical topology.** Acquire/review complete card membership
   and collation evidence; populate only supported generic Sheets, Slots, and rules.
7. **Operational persistence and concurrency.** Add projection/index strategy, locks or
   generation guards, crash recovery, rebuild verification, and retention without changing
   Git canonical authority.
8. **Unified lineage and provenance reader.** Traverse raw bytes, normalized records,
   assertions, reviews, promotions, canonical facts, analytics, decisions, and AI contexts.
9. **Large-corpus performance and reliability program.** Establish representative fixtures,
   benchmarks, memory budgets, chunking, resumability, quarantine, and failure-injection CI.
10. **Boundary and developer-experience consolidation.** Clarify acquisition lifecycle,
    repository facades, analytics domains, CLI taxonomy, packaging, glossary, and test
    strategy while retaining compatibility.

## 10. Project maturity assessment

### Rating: Pre-Alpha, with beta-ready architectural shape

The project is beyond a prototype: it has versioned contracts, retained real evidence,
controlled canonical promotion, deterministic consumers, audits, compatibility layers,
and broad automated tests. “Alpha” would imply a usable end-to-end product capability on
representative data. Today the reference repository is deliberately tiny, MB2 topology is
unknown, live market and AI providers are absent, simulation is absent, and full-corpus
operations are unproven. “Production-ready architecture” would additionally require
security, access control, concurrency, backup/recovery, observability, performance budgets,
release support, privacy, and operational persistence contracts.

Thus **pre-alpha** is the honest overall maturity label. “Beta-ready architecture” describes
the quality of the authority boundaries, not product readiness and should not replace the
overall label.

## 11. Recommended priorities

### Immediate

1. Keep Architecture v12 frozen; record no amendment.
2. Treat the Phase 100 provider-to-canonical review/mapping gap as the next design gate.
3. Run a non-promoting representative-corpus benchmark with explicit time/memory/failure
   budgets and retained reports.
4. Establish one authoritative current-state document and remove stale “merge pending”
   claims from active summaries.
5. Add an end-to-end test that proves external bytes cannot bypass independent review.

### Before canonical scale or multiple operators

6. Specify locking, generation checks, idempotent recovery, and audit consistency.
7. Put raw evidence projection behind the canonical repository/query boundary.
8. Publish a shared lineage reader and vocabulary rather than inventing another provenance
   envelope.
9. Define CLI/package compatibility and supported Python/filesystem matrices.

### Keep blocked

10. Do not implement MB2 simulation, EV, automated promotion, AI advice, or provider-shaped
    canonical entities until their explicit evidence and contract gates are satisfied.

## Final disposition

Architecture v12 remains suitable and unchanged. No feature was added. The single codebase
defect corrected was test-package portability. The roadmap is refreshed around evidence,
scale, lineage, operational safety, and user-value milestones. Implementation should stop
here pending explicit approval of a subsequent milestone.
