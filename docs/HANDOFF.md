# Phase 106 Production MTGJSON Dataset Ingestion handoff

The merged Phase 105 baseline (`43796c0`) was confirmed. Production ingestion orchestration and tests are complete without architecture changes. With official URL access, acquire AllPrintings through `OfficialDatasetAcquisition`, call `ProductionMTGJSONIngestion.prepare()` on the registered path, independently review one batch, promote it, and retain local verification/performance output. Do not approve the full corpus automatically. Merge remains withheld until GitHub Actions are green.

# Phase 105 Official Reference Dataset Acquisition handoff

The acquisition-only subsystem is implemented. Use `dataset download mtgjson`, then `verify` and
explicitly invoke the unchanged provider import only in a separately governed workflow. Local
artifacts and registrations live under ignored `data/local/`. No download was committed, no
canonical state changed, and merge remains withheld until GitHub Actions are green.

Architecture v12, Canonical Repository authority, independent review, promotion, and typed
projection remain unchanged. The prior targeted-population source-gate record below is retained
as historical context; acquisition does not resume or authorize that promotion milestone.

## Prior source-gate record

Phase 105 stopped at its mandatory source gate: no caller-supplied immutable MTGJSON
AllPrintings artifact exists under `/workspace` or `/tmp`. Do not substitute fixtures, download
data, infer set codes, or add importer infrastructure. Supply and validate the artifact exactly
as requested in `TARGETED_MTGJSON_SET_POPULATION.md`, then resume deterministic discovery.

No Phase 105 candidate, review, canonical, projection, or downstream artifact exists. Neither
target is populated. Architecture v12 and the Phase 104 baseline remain unchanged.

## Retained Phase 104 handoff

Phase 104 executes the bounded, governed MTGJSON-derived promotion described in
`BOUNDED_CANONICAL_PROMOTION.md`. Five reviewed entities reach typed canonical storage and
all downstream consumers; one conflicting candidate remains rejected. Replay, rollback,
restore, deterministic identifiers, hashes, lineage, confidence, and unknown lifecycle are
verified. Architecture v12 and canonical contracts are unchanged. Merge remains withheld
until GitHub Actions are green.

Read `PHASE_101_ARCHITECTURE_REVIEW.md`, `REPRESENTATIVE_CORPUS_VALIDATION.md`,
`PROJECT_STATUS.md`, and `ROADMAP.md`. Architecture v12 remains unchanged. Phase 102 proves
the small governed path through a non-executed AI request and records why a full canonical
MTGJSON import is not yet authorized. Any next milestone must be explicitly approved.
