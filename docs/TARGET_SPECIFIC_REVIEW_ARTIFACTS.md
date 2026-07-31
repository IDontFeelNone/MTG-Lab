# Phase 110A — Target-specific review artifacts

## Baseline and boundary

Phase 110 is merged at `e759bd1` (implementation record `933f10b`). Its promotion gate failed
closed because run `30649546787` retained only a summary: candidate-shard payloads and per-batch
review packages were absent, MB2-only candidate membership and dependency closure could not be
recomputed, the plan combined both requested targets, and no independent reviewer identity or
durable review reference existed. Zero canonical writes and zero promotions occurred. Architecture
v12 and canonical contracts are unchanged.

Phase 110A changes only the non-promoting dry-run and retained review boundary. It does not claim
production artifacts exist; those exist only after the rerun below completes and its archive is
verified.

## Target partitioning and batches

The planner selects user input only as a discovery request. It then uses each source set's exact
MTGJSON `code` and `name`, indexes those values with every candidate, partitions by that exact
identity, and only then forms dependency-closed batches. A batch whose payload or review package
has any other set code fails verification.

* Mystery Booster 2 batches have exact code `MB2`, exact discovered name `Mystery Booster 2`, and
  contain no MSH or ineligible candidates.
* Marvel Super Heroes batches have exact code `MSH`, exact discovered name `Marvel Super Heroes`,
  and contain no MB2 or ineligible candidates.
* Quarantined source-record dependency closures are deleted before batching. Rejected, unresolved,
  and unsupported candidates are recorded as exclusions and never admitted.

Every batch has a deterministic target-prefixed ID, target-only candidate-ID SHA-256,
dependency-closure SHA-256, entity counts, payload references, and review-package identifier.

## Retained artifact contract

Under the bounded path `streaming/<source-sha256>/`, the workflow retains:

* `candidate-shards/*.json` and `finding-shards/*.json`;
* `review-batches/<set-code>/<batch-id>/manifest.json`, `candidate-ids.json`,
  `dependency-closure.json`, and `review-package.json`;
* `quarantine/*.json`, `batch-index.json`, `manifest.json`, `completed-sets.json`, and resource
  checkpoints;
* delivery checksum verification, dataset summary, validation, batch verification, performance,
  acquisition/provider reports, `run-result.json`, and job resource diagnostics.

Packages include source lineage, exact target identity, counts, exclusions and reasons, identifier
findings, quarantine references, explicit unknowns, validation state, confidence, provenance,
`canonical_write: false`, and `promotion_performed: false`. The full AllPrintings source is not
uploaded.

## Reviewer contract and promotion prerequisites

Every generated package starts with `review_status: pending`; Phase 110A manufactures no approval.
Later approval must populate: independent reviewer identity, immutable review reference, reviewed
timestamp, approved candidate IDs, excluded candidate IDs, approval decision, reviewer notes, and
the reviewed package digest. Before any promotion, an operator must verify the retained payload and
package hashes, exact target identity, candidate membership, dependency closure, exclusions, and
all approval fields. Promotion remains a separate, explicitly reviewed operation and is not run in
this phase.

Local deterministic inspection uses the existing delivery CLI:

```bash
PYTHONPATH=src python scripts/mtgjson_delivery.py --data-root STATE --batch-size 1000 \
  --target MB2 plan --source AllPrintings.json.gz --sha256 SHA256
PYTHONPATH=src python scripts/mtgjson_delivery.py --data-root STATE --batch-size 1000 \
  --target MSH verify-batch --source AllPrintings.json.gz --sha256 SHA256 --batch BATCH_ID
PYTHONPATH=src python scripts/mtgjson_delivery.py --data-root STATE --batch-size 1000 \
  --target MSH review-package --source AllPrintings.json.gz --sha256 SHA256 --batch BATCH_ID
```

## Exact GitHub Actions rerun

1. Open **Actions → MTGJSON production ingestion → Run workflow** on the Phase 110A branch.
2. Set `source_url` to `https://mtgjson.com/api/v5/AllPrintings.json.gz`.
3. Set `expected_sha256` to the current reviewed digest for those exact compressed bytes:
   `b47cc83600341e18663bdb48fe9d1337730976844465a35e75bcde5ac6f00d09`.
4. Set `target_sets` exactly to `Mystery Booster 2,Marvel Super Heroes`.
5. Set `maximum_batch_size` to a positive bounded value (recommended `1000`).
6. Set `mode` to `dry-run`.
7. Leave `selected_batch`, `reviewer`, and `review_reference` blank, then run the workflow.
8. Require a green job; download the `mtgjson-ingestion-<run-id>` archive; verify
   `checksum-verification.json`, `run-result.json`, all target batch manifests/packages/payloads,
   closure reports, inventories, summaries, and diagnostics. Do not merge or promote based merely
   on dispatch. If official bytes changed, stop and obtain a newly reviewed checksum rather than
   substituting an unreviewed digest.
