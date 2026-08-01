# Phase 123 roadmap update

Phase 123 implemented the generic immutable snapshot-registration seam but the live provider refresh is blocked by HTTP 403 in the execution environment. The immediate roadmap item remains a future trusted provider refresh and exact-one availability rerun. Automatic promotion remains conditional on one complete target and every existing generic gate; Architecture v12 is unchanged.

# Phase 122 roadmap milestone

The first requested real automatic-update target reached its availability gate but no farther. The retained MTGJSON snapshot has only MB2 and MSH and no Hobbit set; Phase 122 therefore adds the reusable availability boundary and report without selecting a code or creating candidates, a descriptor, or a promotion. A future snapshot may advance only after exactly one complete Hobbit target is established. Architecture v12/contracts remain frozen, Phase 119 remains the sole production promotion, and protected required-green-check merge remains mandatory.

# Phase 121 roadmap milestone

**Complete locally; protected merge pending green Actions.** The non-MB2 synthetic `SYN` fixture exercised all sixteen standard stages in an isolated root. Deterministic recovery, replay, conflict rejection, rollback planning, PR reuse/mismatch rejection, green-check gating, and no-force/no-bypass policy are covered. This establishes production readiness of the generic mechanism without authorizing a real-set update.

# Phase 120 roadmap milestone

**Implemented, awaiting protected green merge:** configuration-driven trusted-source updates now run intake through deterministic promotion, automatic PR creation, and auto-merge. Routine flow is signature-free; exceptional safety decisions remain human gates.

# MTG Lab Roadmap through Phase 119


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

The operator-authorization subsystem is retired. Trusted-provider batches become technically ready only after all evidence, schema, membership, isolation, dependency, unknown, duplicate/conflict, quarantine, and canonical-pre-state gates pass. The next task is separately invoked bounded canonical promotion of exactly the first verified MB2 batch, with normal PR review, green CI, audit, and rollback. No promotion or canonical write occurred in Phase 118.

Earlier Phase 117/117A roadmap entries below are historical and no longer impose authorization prerequisites.

# Phase 117A roadmap update

The GitHub-native human authorization submission gate is implemented, but has not been operated. After a green implementation merge, run dry-run first with genuine human values, inspect reports, rerun non-dry, and merge only the authorization artifact PR. Stop before canonical promotion. Another MB2 batch, MSH/Marvel, Architecture v12, canonical contracts, and AI/provider simulation remain out of scope.

# Phase 116 roadmap update

The exact 21 Phase 115 Identifier ambiguities are deterministically resolved as a retained non-unique card-back alias group. The first MB2 batch now has 1,000 approved evidence classifications and valid dependency closure. The immediate separate gate is genuine operator signature metadata; promotion remains false and unauthorized. No second MB2 batch or Marvel review occurred.

# Phase 115 roadmap update

The first true retained-payload MB2 candidate review is complete. Resolve its 21 ambiguous Identifier mappings before operator signature; signature and promotion remain separate gates. No second MB2 batch or Marvel review is authorized.

# Phase 114A roadmap update

Bounded, independently reviewable candidate retention is implemented without duplicating the source corpus. The next gate is a green authenticated intake revision for run `30663562841` and review of its evidence-only PR. Only after that revision is merged may a separately authorized phase inspect one MB2 batch; approval and promotion remain later gates.

# Phase 113A roadmap update

The evidence gate now spans the transition from Phase 113's historically absent retained run to
PR #86's verified present run. Merge this fix before rerunning #86. Once #86 is green and merged,
the next gate is independent review of exactly one indexed MB2 batch; approval and promotion remain
separate and unauthorized.

# Phase 112B roadmap update

Phase 112B reconciles the persistence gap discovered after Phase 113: verified local workflow evidence was mistakenly allowed to end successfully when conditional durable-write stages did not run. The repair makes remote branch/commit/PR confirmation a fail-closed gate. Operational rerun and evidence PR merge follow only after this change is green; review and promotion remain later, separately authorized work.

> **Phase 112A implemented:** The native MTGJSON artifact/root-intake mismatch is bridged by a
> deterministic fail-closed adapter. Phase 111 remains unchanged. The immediate operational gate is
> a green normalized dry run for `30663562841`; merge, review, and promotion remain withheld.

> **Phase 112 complete:** Manually dispatched GitHub-native artifact intake now authenticates a selected successful-run artifact, applies the Phase 111 verification boundary, and proposes only bounded non-canonical evidence on a dedicated PR branch. Run `30663562841` remains absent until dispatch and human merge; review and promotion remain out of scope.
>
> **Phase 111 complete:** Verified production artifact intake and permanent non-canonical evidence retention are implemented. Run `30663562841` is still not present; intake and verification precede the blocked independent review, and promotion remains separately authorized.

> **Phase 110B gate:** Independent review of the first MB2 batch remains blocked before candidate inspection because run `30663562841` is not retained locally. Artifact retention and verification precede review; promotion remains separately authorized.

> **Phase 110A:** exact-set target partitioning and retained pending review packages are implemented. The next gate is a green official-source dry run and independent artifact verification; no approval or promotion has occurred.

> **Phase 110 gate:** The first real canonical promotion remains pending. Phase 110 failed closed because the sole retained successful-run summary cannot reconstruct candidate payloads, review packages, approval, dependency closure, or MB2-only membership. The next operational gate is corrected dry-run retention plus independent one-batch MB2 review; Architecture v12 remains unchanged.

> **Phase 109:** targeted production dry run `30649546787` completed successfully with two discovered sets, 10,940 eligible candidates, 11 deterministic batches, and no write/promotion. Its artifact omitted candidate shards and streaming review-index packages, preventing independent reconstruction. The immediate gate is one new targeted dry run using the corrected retention globs; approval and promotion remain unauthorized.

> **Phase 108B:** preserve global Scryfall printing identity while quarantining evidence-limited same-coordinate collisions. The immediate gate is an official non-promoting rerun and inspection of every colliding source row; no later phase or promotion is authorized.

# MTG Lab Roadmap

> **Phase 108A:** external identifier validation now distinguishes strict global, scoped, and
> non-guaranteed namespaces after the official dry run exposed a valid Deckbox collision. The next
> gate is a green rerun that reaches deterministic full-corpus planning; promotion remains separate.

> **Phase 107:** reproducible checksum-verified local and GitHub Actions delivery now composes the
> Phase 106 production path. Dry-run is default and promotion is limited to one independently
> reviewed deterministic batch. Hosted Codex remains blocked by HTTP 403; automatic full-corpus
> promotion is not authorized.

> **Status: Current — refreshed by Phase 105 Official Reference Dataset Acquisition on 2026-07-31.**

Phase 105 automates acquisition of approved MTGJSON AllPrintings evidence into ignored local
storage. It does not import provider candidates, review, promote, project, or populate targets.
Phase 104 remains the merged baseline and neither target is marked populated.

Phase 104 proves the complete governed pipeline on five MTGJSON-derived entities. The next
scale milestone remains separately authorized work; no unattended full import or automatic
promotion is authorized by this bounded result.
> **Architecture:** v12 unchanged.
> **Authority:** Recommendations only; no milestone below is implementation authorization.

## Current baseline

Phase 100 is merged. Local MTGJSON AllPrintings-style evidence can be validated,
registered, deterministically mapped, and placed in a pending review queue. It cannot
write canonical state or approve itself. The complete local suite passes 248 tests and
17 subtests. Mystery Booster 2 remains evidence-blocked beyond its bounded foundation;
simulation and operational AI advice remain unimplemented.

The current implementation assessment is
[`PHASE_101_ARCHITECTURE_REVIEW.md`](PHASE_101_ARCHITECTURE_REVIEW.md). It supersedes
`../ARCHITECTURE_REVIEW_v1.md` only as a current-state assessment; the Phase 77 report
remains historical architectural evidence.

Phase 102 now validates the small representative path through canonical state, Query,
Analytics, Semantic Query, Reasoning Context, and a non-executed AI request. It does not
establish complete-corpus operational readiness.

## Recommended next boundary

Run a non-promoting full-corpus performance, interruption, resume, quarantine, batching,
and storage rehearsal. Promotion must remain bounded and independently reviewed. The work
must not change Architecture v12 or add provider-shaped canonical entities.

## Top 10 remaining milestones, ranked by value

Ranking reflects expected platform/user value, **not implementation sequence**. Blocked
high-value outcomes may require lower-ranked foundation work first.

1. Evidence-complete product intelligence and reproducible simulation.
2. Complete governed canonical reference population.
3. Collection Intelligence v1.
4. Market Intelligence v1.
5. AI Advisor v1.
6. MB2 evidence closure and canonical topology.
7. Operational persistence, concurrency, and recovery.
8. Unified lineage and provenance reader.
9. Large-corpus performance and reliability program.
10. Boundary, CLI, packaging, terminology, and developer-experience consolidation.

Detailed value, prerequisites, readiness, risks, and constraints are recorded in the
Phase 101 review.

## Persistent gates

- Canonical promotion remains explicit, independently reviewed, provenance-complete, and
  auditable; acquisition success is never promotion eligibility.
- MB2 complete membership, topology, pools, weights, replacement, treatments,
  conditionality, correlation, and sequencing still lack preserved qualifying evidence.
- Simulation must fail closed until every outcome-affecting input is validated.
- AI/model output, analytics, market observations, and collection state remain downstream
  and cannot establish canonical truth.
- Git-owned canonical data remains authoritative; databases and indexes are rebuildable
  projections.
- New live providers require terms, licensing, credential, rate-limit, retry, provenance,
  and failure-policy review.

## Historical summary

Phases 56–100 established canonical repositories and contracts, evidence and acquisition
frameworks, controlled promotion, observation/market/collection/analytics/decision layers,
query and semantic boundaries, reasoning contexts, an AI adapter contract, and local
MTGJSON reference-dataset execution. Historical phase plans and merge-pending statements
do not authorize current work. Consult `CHANGELOG.md` for milestone history.

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
# Phase 124 roadmap update

Collection Intelligence v1 is complete as a deterministic downstream service. The next
recommended milestone hardens import/deck contracts and canonical attribute coverage before
any separately approved pricing or market-intelligence work. Architecture v12 is unchanged.
# Phase 125 roadmap update

The deterministic canonical query layer is complete. A later separately authorized phase
may harden packaging and larger-corpus performance, but must preserve the exact-fact,
provenance, unknown, and snapshot contracts. Market pricing and AI remain separate future work.
