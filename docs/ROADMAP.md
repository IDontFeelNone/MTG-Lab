> **Phase 87:** The approved MB2 acquisition pilot stopped at the evidence gate because a reproducible, legally reviewed 25–50-card raw snapshot could not be acquired in the execution environment. No import or promotion occurred.

# MTG Lab Roadmap

> **Phase 86:** The governed canonical dataset import pilot is complete locally. Large-scale imports remain future work and must use the same gates.

> **Status: Current** — Phase 85 is implemented on the current branch and awaits green CI and review.

## Phase 85 — Canonical Promotion Engine v1

Phase 85 implements the only writer for reviewed knowledge: complete fail-closed validation, deterministic provenance-preserving versions, immutable audits (including rejected attempts), supersession chains, compensating rollback, replay, and CLI commands. It imports no MB2 dataset and changes no Architecture v12 contract. Merge requires Project Architect recommendation and green GitHub Actions.

## Current baseline

| Area | State |
| --- | --- |
| Architecture | v12, unchanged |
| Latest completed phase | Phase 84 — Knowledge Acquisition Pipeline v1 |
| Current milestone | Phase 85 — Canonical Promotion Engine v1 (implementation complete; CI pending) |
| Test baseline | 164 passing tests locally |
| Mystery Booster 2 dataset | Evidence-acquisition blocked |
| Simulation | Not implemented |
| Intelligence Engine | Vision only |
| Prior merge gates | None active |
| Merge recommendation | Withheld until GitHub Actions are green |

## Current milestone — Phase 84

Phase 84 composes Phase 82 raw acquisition into validated dataset identities, independent
provider policies, deterministic reports, and integrity-addressed review packages. It
performs no canonical promotion and leaves Architecture v12 frozen.

## Completed milestone — Phase 83

Phase 83 established the Tier 0 [`CONSTITUTION.md`](CONSTITUTION.md),
[`ARCHITECTS_NOTEBOOK.md`](ARCHITECTS_NOTEBOOK.md),
[`FUTURE_VISION.md`](FUTURE_VISION.md), and
[`QUESTIONS_MTG_LAB_SHOULD_ANSWER.md`](QUESTIONS_MTG_LAB_SHOULD_ANSWER.md). The milestone
added institutional memory and project governance only. It did not change runtime
behavior, schemas, canonical data, providers, Simulation, the Intelligence Engine, or
Architecture v12. Its pull request was merged after green GitHub Actions.

## Latest runtime milestone — Phase 82

Phase 82 implemented the generic Raw Data Acquisition Framework: immutable snapshots,
provider abstractions, deterministic normalization, candidate-assertion bridging, change
reports, resumable acquisition runs, security controls, an offline CLI, and tests. It did
not add a live provider, canonical promotion, complete MB2 population, or simulation. Its
pull request is merged; its former merge gate is **Historical and satisfied**.

## Next milestone boundary

The repository is prepared for a separately approved Phase 84, but this roadmap does not
authorize it. A proposal must have a bounded objective and explicit approval. It must
preserve Architecture v12 unless a dedicated architectural decision is separately approved.
MB2 population remains subject to its evidence gate. Simulation and Intelligence Engine
implementation remain out of scope.

## Historical milestone summary

This section is **Historical reference only** and grants no current authorization.

- Phases 56–65 established canonical Card/Printing repositories and population waves,
  evidence and promotion foundations, Print Sheet/Slot repository support, and MB2 rule
  evidence assessment.
- Phases 66–67 established and exercised the controlled evidence-acquisition handoff; the
  evidence obtained did not support complete MB2 collation or rule population.
- Phases 68–76 built bounded observation, import, canonical repository/import, market,
  mapping, collection, analytics, and deterministic decision subsystems.
- Phases 77–77.1 reviewed Architecture v12 and reconciled documentation.
- Phase 79 stopped at pre-implementation contract gaps. Phase 80 subsequently resolved
  those generic Card/Printing, evidence, uncertainty, and importer contract gaps without
  populating MB2.
- Phase 81 confirmed that MB2 population remained evidence-acquisition blocked.

Any old instruction associated with these milestones to await GitHub Actions or recommend
a merge is **superseded**. A future pull request has its own independent review and green-CI
requirement.

## Persistent debt and deferred capabilities

- Complete MB2 topology, pools, weights, replacement, treatments, conditionality,
  correlation, and sequencing lack sufficient preserved evidence.
- Canonical Print Sheets, Slots, product rules, and complete pools remain unpopulated.
- Generic pack generation, exact probability, simulation, and generated-pack validation
  are not implemented.
- Research Log implementation, database-backed persistence, live providers, API, UI, and
  AI/Intelligence implementation remain deferred.
- Repository generations and provenance vocabularies retain the consolidation debt
  documented in [`../ARCHITECTURE_REVIEW_v1.md`](../ARCHITECTURE_REVIEW_v1.md).

## Long-term vision (not authorization)

The Tier 0 [`FUTURE_VISION.md`](FUTURE_VISION.md) describes collection, product, market,
deck, portfolio, research, simulation, and intelligence horizons. These are target-state
ideas only and do not authorize implementation.
