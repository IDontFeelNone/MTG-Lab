# Mystery Booster 2 Observation Verification & Market Intelligence

## Data boundary

Pack reports are immutable, non-canonical source observations. The subsystem never
uses a report to update `data/canonical`; a canonical card index is a read-only input
to verification. Corrections are new observations or new verification records, not
edits to history. A verification stores the SHA-256 of the complete normalized JSON
observation so later mutation is detectable.

Raw reports retain the exact `reported_name`, order, and reported treatment.
Verification records separately add a normalized lookup name, status (`verified`,
`ambiguous`, or `unmatched`), verifier and timestamp, and canonical card and printing
identifiers where there is exactly one match. Ambiguities retain candidate IDs and
must not be silently resolved.

## Workflow

1. Load a raw pack JSON without modifying it.
2. Construct `ObservationVerifier` with a reviewed, read-only canonical name index.
3. Call `verify`; write the result under a derived observation directory with
   `VerificationStore.save`. Writes are create-only and refuse replacement.
4. Capture provider prices with `MarketSnapshotStore.capture`. Every snapshot has an
   ISO capture date, provider, currency, canonical identifier-to-price map, and a
   stable snapshot ID. Snapshots are also create-only, allowing analyses to be
   reproduced instead of silently acquiring today's prices.
5. Pass packs, matching verification records, and one snapshot to `analyze_box`.

The report contains each observed pack value, total observed box value, mean observed
pack value, duplicates by normalized name, treatment counts, and identifiers without
a price. Values use decimal arithmetic and the snapshot currency. “EV” here describes
the value of observed contents at that dated snapshot. It is **not** a predicted pack
expectation and makes no claims about slots, population, collation, or probabilities.

## Example

```python
from pathlib import Path
from observations import ObservationVerifier, VerificationStore

verification = ObservationVerifier(canonical_index, verifier="mb2-index-2026-07").verify(pack)
VerificationStore(Path("data/derived/observations/mb2/verifications")).save(verification)
```

Generated records should remain outside both the raw observation tree and the
canonical product repository. Publication should include the snapshot and verification
records needed to reproduce the report.

## Plain-text observation import

The generic importer appends one or more packs to any product observation box. Put
one reported card name on each line and separate packs with a line containing only
`---`. An optional treatment may follow a name in square brackets:

```text
Sol Ring [future_sight_frame]
Lightning Bolt
---
Time Walk [foil]
Ancestral Recall
```

Run the importer from the repository root:

```bash
PYTHONPATH=src python -m observations.importer packs.txt \
  --game magic --product mystery_booster_2 --box box_001 \
  --recorded-on 2026-07-30
```

Each import allocates the next `pack_XXX.json` name, appends the manifest, writes
create-only verification records, and regenerates the box's descriptive
`analytics.json`. The input file's exact UTF-8 text and SHA-256 digest are retained
inside every imported pack. Existing observations are checked against the manifest
and are never overwritten. Missing derived verification records for legacy packs
may be created, but existing verification records must still match their raw pack.

The importer reads the canonical Card/Printing repository only to construct the
existing verifier's lookup index. It never writes canonical data, downloads prices,
or runs simulation, probability, slot, or print-sheet inference. Market valuation
remains a separate explicit workflow using a caller-supplied dated snapshot.
