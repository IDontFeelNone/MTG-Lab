# Phase 110A handoff

Run the documented targeted production dry run and independently verify its retained exact-set packages. Do not claim artifacts before the green run, do not approve in Phase 110A, and do not promote or merge until GitHub Actions are green. Phase 110 remains failed closed and Architecture v12 is unchanged. See `TARGET_SPECIFIC_REVIEW_ARTIFACTS.md`.

# Phase 110 failed-closed handoff

The merged Phase 109 baseline is `bf696c5`. Do not invoke promotion from retained run `30649546787`: only its evidence summary is present. Candidate shards and per-batch review packages are absent, so candidate hashes, MB2-only membership, dependency closure, and reviewer approval cannot be independently verified. Phase 110 promoted zero Cards and zero Printings and made no canonical write. Obtain a corrected retained dry-run artifact and an independent approval for exactly one demonstrably MB2-only batch before resuming this same milestone. Do not promote Marvel.

---

# Phase 109 handoff

The evidence summary for successful production dry run `30649546787` is validated and documented in `MTGJSON_FIRST_SUCCESSFUL_PRODUCTION_RUN.md`. Both requested sets were discovered and deterministic planning completed without canonical writes or promotion. Do not attempt review from the retained summary: candidate shards and all streaming per-batch review-index packages are missing. After this change is green, rerun the same targeted dry run so the corrected artifact upload retains both families. Inspect and independently verify that artifact in a later authorized phase; do not approve or promote anything as part of Phase 109. Merge remains withheld until GitHub Actions are green.

---

# Phase 108B handoff

Baseline `69b4feb` contains merged Phase 108A. Phase 108B adds generic, deterministic diagnostics and quarantine for ambiguous same-coordinate globally unique Scryfall collisions. The official corpus was not available, so the full inventory (count and record values) remains unknown rather than inferred. Rerun the manual workflow in dry-run with the same URL/SHA-256; inspect the uploaded quarantine and provider reports. Do not merge or promote until CI is green and the official run validates the decision. Stop after Phase 108B.

---

# Phase 108A MTGJSON Identifier Policy handoff

The first official workflow download and checksum verification succeeded, then provider validation
failed closed on `deckboxId:2676`. Phase 108A corrects that policy generally: rerun the manual
workflow in `dry-run`, using the same reviewed URL, SHA-256, and positive batch size. Inspect
identifier findings and confirm deterministic planning before any independent batch review.

Phase 107 composes Phase 105 acquisition/provider validation and Phase 106 ingestion through a
local command and a manual, read-only GitHub workflow. Both require an explicit SHA-256, keep the
corpus out of Git, default to full-corpus planning without canonical writes, and restrict reviewed
promotion to one exact deterministic batch with independent reviewer metadata. See
`MTGJSON_DATASET_DELIVERY.md` for exact commands and workflow instructions.

The official URL was attempted again from hosted Codex and returned HTTP 403. No substitute,
corpus counts, or real promotion is claimed. Trigger the dry-run workflow, independently review
one package, then trigger reviewed promotion only after the dry-run is green. Merge remains
withheld until GitHub Actions are green. Architecture v12 is unchanged.

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
