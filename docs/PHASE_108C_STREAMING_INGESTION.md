# Phase 108C — Memory-Bounded Streaming MTGJSON Ingestion

> **Status:** implemented with production-shaped fixtures; official rerun pending. Architecture
> v12 is unchanged. The resource-limit hypothesis is leading but unproven.

## Baseline and retained evidence

The baseline contains merged Phase 108B (`04c974c` via merge `67b61ff`) and the workflow-
diagnostics correction (`ecf46db` via merge `67b61ff`). The retained production evidence proves
download and exact compressed-byte checksum `008d56ab213f665695c27a312d9cf2d3b08a91d12594e80714a2c60656e11bc6`,
then approximately five minutes of planning before GitHub Actions reported cancellation. It does
not contain a Python exception, complete JSON result, or a measured production peak. Memory,
disk, or another runner resource remains a hypothesis rather than a diagnosis.

## Previous scaling assessment

The previous execution called `Path.read_bytes`, decoded the complete document, built the mapped
tuple, split it into eligible/quarantined lists, created a complete candidate tuple, serialized
complete candidate and review-queue documents, read the complete candidate document again,
created eligible rows containing source candidates, dependency groups, batches, assertion
records, review packages, and an aggregate manifest containing every batch report. Identifier
validation also retained an occurrence dictionary and full source-record excerpts across the
corpus. Thus several full or substantial corpus representations could coexist. Candidate,
identifier-occurrence, eligible-row, group, assertion, review-package, quarantine, and JSON
serialization structures were all O(cards + identifiers + candidates). Peak space was O(N),
with a large constant from simultaneous Python object graphs and serialized copies. Fixture
instrumentation can show relative behavior and `ru_maxrss`; no exact official peak is claimed.

## Streaming and storage design

The production dry-run now hashes the exact compressed or uncompressed bytes, streams gzip
decompression when selected, incrementally decodes the top-level object, and validates/maps one
set at a time. Standard-library `JSONDecoder.raw_decode` is fed incrementally because only the
current set value must be materialized; no new dependency is necessary. Per-set candidates are
written atomically to content-addressed, ignored working storage. A SQLite compact index retains
candidate identities, dependency keys, and external identifiers. Collision findings are written
as separate hashed shards; summaries contain only counts and hashed references, not candidate
payloads. Dependency-closed batches are built from the compact index in stable identity order.

The completed-set ledger is updated after every set. Resume verifies every retained shard hash
before trusting a ledger entry, rebuilds/reuses deterministic indexes, and rejects corruption.
Checkpoints precede completion, so runner-level death can leave useful uploadable state without
requiring signal cleanup. Planning reports source size/hash, set/card/Printing and candidate
counts, finding/quarantine summaries, observed peak RSS, disk, throughput, completed/remaining
units, plan digest, and explicit `canonical_write: false` and `promotion_performed: false`.

## Targeting and operations

Targets are generic caller inputs matched case-insensitively against discovered set name or code;
codes are not assumed before discovery. `Mystery Booster 2`, `Marvel Super Heroes`, or arbitrary
names/codes use the same path, and unrelated sets are discovered but never mapped. The workflow
prefers `AllPrintings.json.gz`, verifies its exact compressed checksum, and retains `.json` as a
local supported fallback. Promotion continues to use the established independently reviewed,
bounded promotion API; streaming planning performs no promotion.

Run the official target first:

1. **Actions → MTGJSON production ingestion → Run workflow**.
2. Keep `mode=dry-run`, the default compressed official URL, reviewed compressed SHA-256, and a
   positive batch size; set `target_sets` to `Mystery Booster 2,Marvel Super Heroes`.
3. Require green completion and inspect checksum, provider, summary, batch plan, manifest,
   completed-set ledger, shard inventories, and resource diagnostics.
4. Then rerun with blank `target_sets` for full-corpus planning. Do not select promotion mode.

No official rerun was possible in this environment, so the resource problem is **not claimed
resolved**. Expected space changes from O(total decoded corpus and candidates) to O(largest set
plus decoder buffer), with compact indexes and shard bytes on disk; collision detail for a single
pathological identifier can still scale with that collision group. Merge remains withheld until
all GitHub Actions checks and the official targeted dry run are green.
