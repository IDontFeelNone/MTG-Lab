# Release-Wide Catalog Reconciliation V1

This private candidate consumer compares one explicitly selected MTGJSON v5
AllPrintings-shaped release across all supplied set partitions. It reuses the
existing incremental decoder, scope-aware validator, identifier policy and
candidate mapper. It never acquires data, invokes the importer/promotion
controller, writes canonical records or activates a snapshot.

## Python API and authorization

Use the existing Python environment (`PYTHONPATH=src`). Linux resource controls
and an importable main module are required by the isolated spawn worker:

```python
from providers.mtgjson.reconciliation import reconcile_release

if __name__ == '__main__':
    report = reconcile_release(
        selected_source_path, dedicated_private_workspace, release_binding,
        authorize_source=trusted_host_source_disposition,
    )
```

The closed release binding contains `provider` (MTGJSON), `release_id`, `version`,
`date`, `artifact_sha256`, `provenance_reference` and `notice_reference`. Hash the
actual compressed or uncompressed artifact, not its filename or URL. Preserve
the original artifact privately under its separately approved retention scope;
the workspace does not duplicate it. Release and provenance labels are caller
declarations bound to verified source bytes, not independently authenticated
provider or legal assertions.

The authorizer is **trusted host code**, outside the imported data. It must
independently establish whole-artifact processing, necessary source retention,
derived source/unknown-field retention and private report use for the exact
release, operation and limits. There is no default real-source authorization,
CLI permission switch or `approved=true` bypass. Refusal precedes source reads
and workspace creation. Each resume requires authorization again. Hashes,
possession and declared license strings are not permission.

Reports, mapped unknown fields and intermediate SQLite rows inherit source
restrictions. Keep the workspace outside repository checkouts, owner-only and
separate from canonical snapshots and collections. No source or private artifacts
belong in public CI. Only original project-authored fixtures are tested publicly.

## Reconciliation and identity

Each physical source row receives exact partition/ordinal coordinates and a
source-record hash. The mapper is invoked on one supported row at a time so its
existing first-Card suppression cannot hide later assertions. Card identity uses
the mapper's explicit Oracle identifier convention. Missing or contradictory
Oracle identifiers remain unresolved; names never supply identity fallbacks.
These are provider Card identities and candidate identifiers, not new canonical
admissions. The existing canonical resolver and admission controllers retain
their authority and are not invoked to manufacture canonical identities.

Every present Card assertion in the documented `CARD_FIELDS` projection is
compared by identity, face discriminator and field. Differing present values
produce conflicts; absence is not silently filled or treated as contradiction.
This bounded projection is not general Oracle interpretation or full schema
support. Complete original row hashes and mapped unknown fields preserve the
evidence for later review. Set-specific Printing fields are not mistaken for
cross-set Card contradictions.

Repeated Printing identifiers are always reported, including identical duplicate
rows. Conflicting Card assertions withhold their dependent Printing candidates.
Strict external identifier collisions also withhold affected Printings. Duplicate
Printings never select an arbitrary winning assertion. Multiface/exceptional rows,
face labels and explicit relationships are preserved, missing referenced faces
are reported, and exceptional candidates require review rather than automatic
assembly into canonical records. Unsupported rows remain explicitly accounted
for. No records are discarded through `INSERT OR IGNORE`.

## Portable reports and completeness

`output/report.json` uses `release-catalog-reconciliation-v1` and the closed
[report schema](../src/schemas/v1/release-catalog-reconciliation-report.schema.json).
It binds the release, partition inventory, counts, limits and byte hashes of eight
streamed JSONL artifacts: all assertions, conflicts, duplicate Printings, external
identifier conflicts, Card candidates, Printing candidates, exceptional records
and unresolved/unsupported rows. Each JSONL stream is ordered deterministically.
The report identity hashes its canonical JSON without `report_id`. No private
paths, timings or process measurements enter the deterministic report.

The immutable source plus compatible public code reconstruct the evidence;
SQLite is a subordinate rebuildable staging index, never canonical authority.
Reports remain private review candidates, not admission-ready canonical bundles.
The existing [set candidate preparation](SET_CANDIDATE_PREPARATION_V1.md) and
separate human admission boundaries remain unchanged. This consumer adds global
comparison that the bounded single-set consumer does not perform.

- **Source coverage:** all parsed rows are accounted for, including unresolved
  and unsupported rows. This does not mean all rows are supported.
- **Catalog population coverage:** `NOT_ESTABLISHED`; this consumer has no
  independent inventory evidence authorizer and cannot assert complete Magic
  membership from provider/file coverage.
- **Canonical admission and activation:** `NOT_PERFORMED`.
- **Mechanical understanding and product collation:** not established.

Release-independent Card/Printing keys, explicit assertions and occurrence
provenance permit a future separately authorized comparison of baselines, new
sets, corrections and provider merges/deletions. V1 implements no update engine
and claims no historical Oracle revision completeness.

## Budgets, interruption and replay

Hard ceilings, individually tighten-able through frozen `ReconciliationLimits`:

| Resource | Ceiling |
| --- | --- |
| Compressed/uncompressed input artifact | 2 GiB |
| Decoded stream | 8 GiB |
| One decoded set partition | 8 MiB |
| One normalized source row | 64 KiB |
| Source rows / partitions | 1,000,000 / 10,000 |
| Private workspace / streamed outputs | 2 GiB / 512 MiB |
| Worker address space | 512 MiB |
| Worker CPU / parent wall deadline | 60 / 70 seconds per invocation |

The decoder retains one bounded partition, not the corpus. SQLite stores global
occurrences and indexed field assertions. Final candidates/findings are written
as streams; the summary retains only a bounded partition inventory. Worker
address-space, CPU and file-size limits, SQLite page/cache limits, SQL progress
checks and workspace checks bound processing. Disk checks include open unlinked
SQLite sort files. Disk checks are periodic rather than filesystem quotas; an
in-progress write can temporarily overshoot the aggregate workspace threshold,
while per-file and SQLite ceilings remain enforced. Use a separately bounded
filesystem if a hard aggregate quota is required. No larger unsafe run is
accepted merely because its row count fits.

Limits apply per call; completing a release in 60 seconds is not guaranteed.
Budget exhaustion is a structured `ReconciliationError` (`RESOURCE_BUDGET`),
never approximate success or zero probability. Invalid source, unsupported
platform, policy refusal, integrity mismatch and workspace contention are
distinct refusals. A process killed by an OS limit produces no successful
result. `last-run.json` holds new timing/peak-memory measurements separately
from deterministic evidence. Peak memory uses the worker's Linux `VmHWM`, not
`ru_maxrss`, which can inherit a launcher's historical peak across `spawn`/exec.

Each partition commits atomically. To deliberately pause after N newly committed
partitions, pass `stop_after_partitions=N`. A pause reports `INCOMPLETE` and does
not create a complete report. Resume with identical bindings and limits. Replay
streams from the source beginning and independently checks each completed
partition, row and assertion against the original source before skipping writes;
it does not trust a coherently rehashed checkpoint. Concurrent runs are refused.
Unexpected checkpoint schema objects, including triggers and views, are refused
before resumed writes can alter previously validated rows.
SQLite recovery handles interrupted transactions. Finalization is repeatable but
not itself checkpointed; a finalization that exceeds budgets requires a smaller
supported scope or future separately approved improvement. Never present a prior
report or partially written JSONL stream as the result of a refused invocation.

## Validation and real-source boundary

The original QRA/QRB fixture demonstrates cross-set reprints and new identities
through the actual mapper and reconciliation report. Tests also cover conflicting
assertions, duplicate/ambiguous IDs, multiface links, malformed sources, checkpoint
tampering, pause/resume, gzip, resource refusals and deterministic replay.

For a reproducible larger original-data demonstration (no provider access), run:

```sh
PYTHONPATH=src python tests/release_reconciliation_benchmark.py --directory /tmp/mtglab-reconciliation-scale
```

The default is 20,000 rows across forty partitions. Use a new directory for each
run. `receipt.json` separates measured duration/memory from source and report
identities. This demonstrates an exercised envelope, not a full-catalog benchmark.

No real AllPrintings release is authorized by this implementation. The real-source
demonstration is **BLOCKED pending operation-specific processing and retention
authorization**. No real-catalog completeness, production activation, public
distribution, external AI export or semantic approval is claimed. Improved
accounting can support later research on new releases; it does not detect releases,
interpret mechanics, discover synergies or notify users autonomously.
