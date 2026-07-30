# External Dataset Ingestion Framework

> **Status: Current — Phase 88.** Architecture v12 remains frozen. This boundary
> supplies immutable external bytes to the existing acquisition and review stages; it
> neither approves evidence nor promotes canonical facts.

## Pre-implementation assessment and compatibility review

Phase 87 proved the correct failure mode: network retrieval was unavailable, so the MB2
pilot stopped instead of inventing evidence. The Phase 82 raw snapshot store, Phase 84
Knowledge Acquisition Pipeline, and Phase 85 promotion boundary already express the
governed lifecycle. The missing capability was a deterministic, provider-neutral edge for
bytes supplied outside a network adapter.

Phase 88 is an additive composition point. It preserves the constitutional separation of
acquisition, normalization, review, and promotion; immutable checksummed source bytes;
explicit uncertainty; and human promotion authority. It changes no Tier 0 entity,
canonical contract, writer, provider trust rule, or Architecture v12 dependency direction.
No architectural amendment is required.

## Lifecycle

```text
External file
  -> format detection
  -> manifest and byte-integrity verification
  -> immutable dataset registration
  -> provider-neutral format adapter
  -> Phase 82 raw snapshot
  -> Phase 84 normalized records and Knowledge Review Package
  -> human review
  -> existing Phase 85 promotion boundary (separate and explicit)
```

Successful ingestion ends in `awaiting_human_review`. It creates no canonical path and
does not invoke promotion. An identical retry returns the original registration. A reused
logical identity/version with different content is rejected.

## Manifest format

The manifest is the canonical description of a supplied dataset. A ZIP contains it at
`manifest.json`; JSON and CSV inputs use `--manifest PATH`. `checksum` is the lowercase
SHA-256 of the uncompressed data file, not of the ZIP container.

```json
{
  "manifest_schema": "external-dataset-manifest-v1",
  "dataset_name": "Example card export",
  "logical_identity": "example-card-export",
  "version": "2026.07.1",
  "provider": "Example Provider",
  "publication_date": "2026-07-29",
  "source_attribution": "Example Provider bulk export",
  "license": "CC0-1.0",
  "expected_entity_types": ["card", "printing"],
  "schema_version": "provider-schema-v3",
  "checksum": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "data_file": "records.json",
  "notes": "Optional review context"
}
```

All listed fields except `notes` are required. Dates use ISO 8601 calendar dates;
identities are stable lowercase identifiers; archive paths must be safe and relative.

## Integrity verification

Before registration, the framework deterministically verifies:

1. the manifest schema and every required field;
2. presence of the external file, manifest, and declared ZIP member;
3. archive path safety and supported data-file extension;
4. exact SHA-256 equality between the manifest and supplied payload;
5. successful strict adapter parsing; and
6. uniqueness of the logical identity/version registration.

For example, `mtg-lab ingest validate cards.csv --manifest cards.manifest.json`
returns `valid: true` only after all applicable checks pass. Any ambiguity raises an
`ExternalDatasetError` before registration or acquisition. Partial evidence is never
silently accepted.

## Adapter architecture

`AdapterRegistry` maps extensions to `FormatAdapter` implementations. Adapters only turn
syntax into ordered source mappings; they contain no provider trust or promotion policy.
The ingestion core resolves an adapter through the registry and therefore requires no
format-specific branch when a future adapter is registered.

```python
class NdjsonAdapter(FormatAdapter):
    extensions = (".ndjson",)
    content_type = "application/x-ndjson"

    def records(self, payload):
        return [json.loads(line) for line in payload.splitlines() if line]

registry = AdapterRegistry()
registry.register(NdjsonAdapter())
ingestor = ExternalDatasetIngestor("data", registry)
```

Provider-specific field mapping may be supplied at an adapter boundary or as explicit
input `normalized` mappings, but must not enter the ingestion coordinator. Provider name,
attribution, license, expected entity types, and source schema remain manifest evidence,
not hard-coded behavior.

## Supported formats and CLI

- JSON: an array of objects or an object with a `records` array.
- CSV: UTF-8 with a non-empty header row.
- ZIP: `manifest.json` plus one declared supported JSON or CSV member.

```bash
python -m mtglab ingest validate cards.json --manifest manifest.json
python -m mtglab ingest inspect cards.json --manifest manifest.json
python -m mtglab ingest cards.json --manifest manifest.json --timestamp 2026-07-30T18:00:00+00:00
python -m mtglab ingest list
```

`inspect` adds registration state without writing. `list` reads deterministic external
dataset registrations. ZIP commands omit `--manifest` because the manifest is embedded.

## Relationship to acquisition and promotion

The generic supplied-file provider hands verified bytes to `RawSnapshotStore`; the normal
`AcquisitionEngine`, `normalize_snapshot`, candidate assertion generation, and
`build_review_package` functions then run unchanged. The initial trust policy is deliberately
`unknown` with zero confidence. Reviewers must evaluate attribution, license, schema,
coverage, and evidence quality. Promotion remains a later, separately authorized call to
the existing Canonical Promotion Engine. Ingestion success is never promotion eligibility.

## Future provider and format extensions

New formats implement and register `FormatAdapter`. New acquisition sources can continue
to use existing provider adapters. Neither extension changes the ingestion coordinator,
canonical repositories, or promotion engine. Nested/multi-file datasets, signatures, and
additional checksum algorithms require a future versioned manifest contract; unsupported
forms fail closed today.
