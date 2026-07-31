# Phase 109 — First successful MTGJSON production dry run

## Evidence boundary

GitHub Actions run `30649546787` is recorded solely from the retained, verified
`phase109_run_evidence_summary.json`. The summary identifies the downloaded workflow archive as
`mtgjson-ingestion-30649546787.zip`, 1,268,127 bytes, SHA-256
`0e0cf3ddb8d87339d956f54b380b285b699d8afea892fb2e6674f7719ee1945d`. Its artifact inventory
digest is `23bd48025557987442cedf5adb0f59bd811057a97d12e36923fd878f3caf5c42`.

The source lineage is a compressed 170,902,200-byte artifact with verified SHA-256
`b47cc83600341e18663bdb48fe9d1337730976844465a35e75bcde5ac6f00d09`, represented by dataset
identifier `mtgjson-allprintings-5.3.0+20260731-b47cc8360034`. The summary's hashes have valid
64-character lowercase SHA-256 form; the dataset suffix agrees with the source digest; target
shard hashes agree in both summary locations; and card, entity, and batch totals reconcile.
The retained summary does not contain the archive inventory or shard payload bytes, so the
inventory, batch, finding-shard, source, archive, and candidate-shard digests cannot be
independently recomputed from this repository. They are recorded as verified summary facts, not
newly reverified payload hashes.

## Verified result and metrics

The run completed in `dry-run` mode with `canonical_write: false` and
`promotion_performed: false`. It processed two sets and 862 cards. The delivery report records
10,940 candidates, all 10,940 eligible, zero rejected, and zero unresolved. Entity counts are:
665 cards, 813 printings, 2 sets, 1 language, 4 rarities, 2 finishes, and 9,453 identifiers.

There are 117 identifier findings, all `review-required` and none errors. Namespace counts are
5 `cardKingdomId`, 5 `cardsphereId`, 5 `deckboxId`, 24 `mcmId`, 5 `mtgArenaId`, 19 `mtgoId`,
5 `multiverseId`, 1 `scryfallCardBackId`, 24 `scryfallId`, and 24 `tcgplayerProductId`.
Provider validation is recorded as valid.

Planning produced 11 deterministic batches with a maximum size of 1,000: the first contains
999 candidates, batches 2 through 10 contain 1,000 each, and batch 11 contains 941. Each batch's
entity count equals its candidate count, totaling 10,940. The batch-plan digest is
`eaf1892bab8f335f4c865a87d2958d816d542d0dfe684e395c3935c615a449c8`.

Performance was 114.54340190600001 seconds at 7.53 cards/second, 191.88 MiB observed peak
memory, 25,795,418 working-disk bytes, and at most one retained set record. The checkpoint records
61.678 elapsed seconds, the same 191.88 MiB peak, and latest set code `MSH`.

## Exact requested-set discovery

Both requested names were discovered exactly:

* **Mystery Booster 2** — code `MB2`; unit `000334-mb2`; 390 cards; 5,785 candidates in shard
  `000334-mb2.json`; shard SHA-256
  `eb577c638fd74f4b45323370dcc179d925ac53492f29714c058a0f3276461995`; 7,120,316 bytes.
* **Marvel Super Heroes** — code `MSH`; unit `000373-msh`; 472 cards; 5,638 candidates in shard
  `000373-msh.json`; shard SHA-256
  `5bdfbe0a4ee16d8468947976cc2e72aa0ba0429ca81bf0455b5b86144ec311aa`; 8,726,511 bytes.

The two pre-planning shard candidate counts total 11,423, while the eligible deterministic-batch
total is 10,940. The summary does not label or retain a count explaining that difference; it must
not be presented as a quarantine or rejection count.

## Metrics not retained

The summary does **not** retain an actual quarantined source-record count, quarantined candidate
count, quarantined UUID inventory, or per-set eligible/entity/batch counts. It also does not retain
the 117 finding payloads, only their counts and a finding-shard digest. Rejection and unresolved
counts are retained and are both zero. Candidate/entity totals and per-batch counts are retained
as listed above.

## Review-batch reconstruction gate

The bounded review batches cannot be independently reconstructed from the retained evidence.
Batch IDs, sizes, and candidate-ID SHA-256 digests prove a deterministic plan existed, but they do
not supply the candidate payloads or even the candidate-ID lists needed to reproduce each batch.
No candidate or review-package content is inferred or invented.

The exact missing artifacts are:

1. `streaming/<source-sha256>/candidate-shards/000334-mb2.json` and
   `streaming/<source-sha256>/candidate-shards/000373-msh.json`, which contain the bounded source
   candidate payloads referenced by the streaming manifest; and
2. every `streaming/<source-sha256>/review-indexes/<batch-id>/review-package.json`, which contains
   the candidate-ID index for its planned batch.

The workflow previously uploaded streaming manifests, ledgers, and checkpoints but omitted those
two payload families (and its older `production-batches` globs do not match streaming output).
The smallest retention correction adds exactly the streaming candidate-shard and review-index
package globs to the existing 30-day artifact upload. It changes no ingestion, batching, review,
approval, promotion, or canonical-write behavior.

A new targeted dry run is required to produce an independently reviewable retained artifact under
the corrected workflow. That future run remains a dry run: Phase 109 approves and promotes
nothing. Any review and promotion remain separate, independently governed work.
