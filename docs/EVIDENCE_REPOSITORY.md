# Evidence Repository

**Status:** Implemented foundation

## Purpose

The evidence repository preserves acquired files as reviewable, content-identified
inputs. It complements the existing raw acquisition layer: `data/raw/` may retain
pipeline-specific acquisition destinations, while `data/sources/` is the stable
repository archive through which later ingestion milestones load evidence.
Neither location is canonical domain data, and archived evidence cannot bypass
candidate review or controlled promotion.

## Layout

Evidence bundles are game-scoped and use stable identifiers:

```text
data/sources/<game>/<bundle_id>/manifest.json
data/sources/<game>/<bundle_id>/files/<archived_file>
```

The versioned `evidence-manifest` contract records bundle identity, product
scope, creation time, declared canonical Source Records, and one or more archived
artifacts. Each artifact declares a bundle-relative path, media type, byte size,
SHA-256 digest, and claim-level provenance.

## Loading and validation

`load_evidence_bundle` validates the manifest schema and path identity before
returning any bytes. It rejects paths outside the bundle, missing or unreadable
files, byte-size and SHA-256 mismatches, duplicate artifact identities or paths,
missing canonical Source Records, artifact provenance outside the declared
source set, and declared sources that no artifact actually uses.

Successful loading returns immutable bundle and artifact records containing the
verified bytes and provenance snapshots. Parsing and normalization remain
separate ingestion responsibilities.

## Foundation archive

Phase 62 archives the already-reviewed Mystery Booster 2 Wave 1 controlled
extract as the first evidence bundle. This proves loading and provenance
validation against real repository evidence without adding or changing Cards,
Printings, Print Sheets, Slots, the Product, or any product-rule data.

## Verified ingestion boundary

Phase 63 adds an application-level bridge for bounded Card and Printing waves.
The bridge always calls `load_evidence_bundle`, selects one declared JSON
artifact, and validates every source identifier embedded in its records against
that artifact's provenance before invoking deterministic ingestion. It also
identifies Card candidates whose canonical Cards already exist so review can
skip Card promotion while still promoting a new dependent Printing.

The Wave 2 retained run uses this bridge exclusively. It does not treat an
unchecked raw-file copy as input and does not support Print Sheet, Slot,
collation, probability, or simulation claims.
