# MTG Lab Roadmap

> **Status: Current — Phase 90 evidence-blocked; review and green CI pending.**

## Current milestone — Phase 90

The requested Mystery Booster 2 pilot stopped after source validation: the repository's only
supplied MTGJSON fixture contains synthetic set `TST`, not MB2. Deterministic reports preserve
the checksum, observed contents, zero-import outcome, and evidence limitation. No acquisition,
registration, resolution, promotion, or Architecture v12 change occurred. Merge recommendation
remains withheld until GitHub Actions are green.

## Completed milestone — Phase 89

The MTGJSON Provider Adapter v1 is merged. It validates v5 AllPrintings-style supplied files,
generates provider metadata/manifests, and maps its bounded scope through the unchanged
external acquisition/review boundary without canonical authority.

## Current baseline

| Area | State |
| --- | --- |
| Architecture | v12, unchanged |
| Latest merged phase | Phase 89 — MTGJSON Provider Adapter v1 |
| Current milestone | Phase 90 — MB2 pilot stopped after validation |
| External formats | JSON, CSV, ZIP containing JSON/CSV |
| Mystery Booster 2 dataset | Supplied-data evidence gap; not imported |
| Simulation | Not implemented |
| Intelligence Engine | Vision only |
| Merge recommendation | Withheld until GitHub Actions are green |

## Next milestone boundary

Only Phase 90 review and CI are authorized. A future retry requires supplied, reproducible
MTGJSON v5 bytes containing MB2 and must preserve all manifest, integrity, review, resolution,
and promotion boundaries. Simulation and Intelligence remain out of scope.

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
