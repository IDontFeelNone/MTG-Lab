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
