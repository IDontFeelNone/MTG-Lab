# MTG Lab Roadmap

> **Status: Current — Phase 88 implemented locally; review and green CI pending.**

## Current milestone — Phase 88

The External Dataset Ingestion Framework accepts manifest-governed JSON, CSV, and ZIP
inputs, establishes integrity before registration, and composes supplied bytes into the
unchanged acquisition and Knowledge Review Package stages. It does not promote canonical
facts, import MB2, or change Architecture v12. Merge recommendation remains withheld until
GitHub Actions are green.

## Completed milestone — Phase 87

The Mystery Booster 2 acquisition pilot is merged with an evidence-blocked result. It
correctly stopped because no reproducible, legally reviewed source snapshot was available.
No dataset registration, import, promotion, or canonical mutation occurred.

## Current baseline

| Area | State |
| --- | --- |
| Architecture | v12, unchanged |
| Latest merged phase | Phase 87 — evidence-blocked acquisition pilot |
| Current milestone | Phase 88 — External Dataset Ingestion Framework |
| External formats | JSON, CSV, ZIP containing JSON/CSV |
| Mystery Booster 2 dataset | Evidence-acquisition blocked; not imported |
| Simulation | Not implemented |
| Intelligence Engine | Vision only |
| Merge recommendation | Withheld until GitHub Actions are green |

## Next milestone boundary

Only Phase 88 review and CI are authorized. Future dataset formats or provider extensions
must preserve the manifest, integrity, review, and promotion boundaries. MB2 population
remains subject to its evidence gate. Simulation and Intelligence remain out of scope.

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
