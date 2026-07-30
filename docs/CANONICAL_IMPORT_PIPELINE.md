# Canonical Import Pipeline v1

## Architecture and authority

The pipeline is the sole write boundary between **reviewed local source data** and the
Canonical Product Repository. `SourceAdapter` separates transport from importing;
v1 includes JSON files and CSV directories, while a future official API adapter can
produce the same in-memory document without changing canonical logic. Adapters do not
make web requests and observations are never accepted as canonical input.

The importer validates the dataset version and review status, required fields,
duplicate identifiers, and the complete prospective relationship graph. It then asks
`CanonicalRepository.apply_import` to stage, load, validate, and atomically replace the
game tree. Validation, dry-run, and validation-only failures leave canonical storage
unchanged. Incremental datasets upsert only the identifiers they contain.

## Dataset and review workflow

A JSON dataset contains `schema_version: v1`, `game`, stable `source` and
`source_version`, `review_status: reviewed`, and preferably a reviewed
`import_timestamp`. Entity arrays are named `cards`, `printings`, `products`,
`treatments`, `finishes`, `rarities`, `product_versions`, `packs`, `slots`, and
`sheets`. Reviewers approve and freeze the local artifact before invoking:

```bash
PYTHONPATH=src python -m mtglab.canonical.import --source reviewed.json --game magic --dry-run
```

Use `--validation-only` for a validation gate and `--report report.json` for a
machine-readable audit report. CSV mode uses a directory containing `dataset.json`
for metadata and optional entity files such as `rarities.csv`.

## Provenance and deterministic guarantees

Every emitted entity has `metadata.import_provenance`: source, source version,
review status, importer version, import timestamp, and SHA-256 hash of the complete
source dataset. Cards and printings also receive field provenance compatible with the
existing repository schemas. The report records created, updated, and unchanged counts.

Records and keys are sorted and serialized with stable formatting. The source hash is
computed from canonical JSON. A dataset-provided import timestamp is part of the
reviewed input; when absent the stable epoch is used rather than wall-clock time.
Therefore replaying identical bytes against identical repository state produces
identical canonical bytes and reports (apart from state-dependent change counts).

## Future official datasets

An official dataset integration should implement `SourceAdapter`, download nothing at
import time, archive its reviewed response locally, and map it to this versioned
contract. Provider-specific names and assumptions belong in that adapter—not in the
pipeline or repository. This preserves support for other games and leaves simulation,
probability, scraping, and print-sheet inference outside the subsystem.
