# Phase 82 — Raw Data Acquisition Framework

> **Status: Current** — implemented 2026-07-30; Architecture v12 remains frozen.

## Pre-implementation assessment and compatibility finding

The required inventory covered `src/ingestion` (hash-addressed evidence, parser and
normalizer boundaries), `src/evidence_review` and `src/repository/evidence.py`
(content/provenance review), `src/observations` (immutable non-canonical reports),
`src/market` (provider abstraction), `src/canonical/evidence.py` (Phase 80 assertion
classes), `src/canonical_import` and `src/repository/promotion.py` (explicit canonical
gates), and their schemas and tests.

Reusable components and conventions were deterministic SHA-256 identity, canonical
JSON, atomic/create-only writes, safe lowercase identifiers, immutable evidence,
provider isolation, field provenance, and explicit promotion. The older “raw
evidence artifact,” acquisition manifest, observation snapshot, and market snapshot
are bounded domain pipelines, not generic source snapshots. They remain compatible;
this framework deliberately uses **raw snapshot**, **normalized source record**, and
**acquisition run** to avoid claiming they are interchangeable or silently creating
a second canonical importer.

The framework is an additive upstream boundary. It imports no canonical repository
or promotion service and changes no Tier 0 entity, relationship, or authority rule.
No Tier 0 decision was required. Architecture v12 is therefore unchanged.

## Staged flow and boundary

```text
External Source -> Raw Immutable Snapshot -> Normalized Source Record
                -> Evidence Assertions -> [separate reviewed Canonical Promotion]
```

Each arrow is an explicit operation. Acquisition success proves byte receipt only.
Normalization maps provider syntax but does not resolve conflicts. Assertion creation
produces Phase 80 `candidate` assertions. This package contains no promotion command.

## Raw snapshot contract (`raw-snapshot-v1`)

A manifest records snapshot/provider/dataset identity, acquisition and optional
publication timestamps, request parameters, media type and encoding, relative payload
location, byte length, SHA-256, status, license reference, parent snapshot, and schema
version. Provider response, rate-limit and provenance metadata are retained separately.
The full directory is:

```text
data/raw/<provider>/<dataset>/<sha256>/
  payload.bin                 # exact response bytes
  manifest.json               # snapshot contract
  checksum.sha256
  provider-metadata.json
  acquisition-result.json
```

Example manifest (timestamps and parameters are acquisition inputs):

```json
{"schema_version":"raw-snapshot-v1","snapshot_id":"<sha256>","provider_id":"fixture","dataset":"cards","raw_payload_location":"payload.bin","payload_byte_length":64,"checksum":{"algorithm":"sha256","value":"<sha256>"},"acquisition_status":"succeeded"}
```

The content checksum is the snapshot ID. Thus paths are deterministic, identical
content is detected as unchanged, prior content is never overwritten, and runs with
new content create a new directory. Manifests use canonical key ordering. Payload,
manifest and companion artifacts use atomic create-only writes.

## Provider abstraction

`AcquisitionProvider` separates stable provider identity, discovery, request building,
retrieval, response validation, and normalized-record emission. `ProviderResponse`
also carries content encoding, publication time, rate limits, provenance, and provider
metadata. The engine knows no live provider names. `FixtureProvider` is the deterministic
offline JSON implementation. A future live adapter must document its terms, credentials
handling, supported media, pagination, retry policy, and provenance without modifying
the engine. Credentials must be supplied at runtime and must never enter payload
manifests, run reports, fixtures, or repository files.

## Normalized source records (`normalized-source-record-v1`)

Normalization is deterministic and create-only. Each record retains provider ID,
source-record ID, exact raw snapshot ID/path, mapped `source_values`, an intentionally
empty `canonical_values` map, all `unmapped_source_fields`, and validation errors.
Records are sorted by source identity; duplicate source IDs fail rather than collapse.

```json
{"schema_version":"normalized-source-record-v1","provider_id":"fixture","source_record_id":"card-1","raw_snapshot_id":"<sha256>","source_values":{"name":"Alpha"},"canonical_values":{},"unmapped_source_fields":{"id":"card-1","extra":7},"validation_errors":[]}
```

Validation errors belong on records when an adapter can safely emit the original;
malformed containers that cannot be enumerated fail normalization while the raw bytes
remain available for inspection and a corrected retry.

## Evidence bridge and lineage

The bridge converts mapped field paths into schema-v3 assertions with
`status: candidate`. Assertion notes retain both raw snapshot ID and provider source
path. IDs include snapshot identity, so a changed claim creates a new assertion rather
than replacing the old one. `compare_assertions` reports added, removed, changed, and
conflicting values across snapshots. Example lineage:

```text
assertion src-… /name="Alpha" -> normalized card-1 -> raw snapshot <sha256>/payload.bin
```

The output validates against the Phase 80 assertion contract; promotion remains a
separate, reviewed downstream operation.

## Configurable provider trust

`ProviderTrustPolicy` configures evidence class, confidence, verification status,
and source type at bridge invocation. Default trust is `unknown`, confidence `0`, and
`unverified`. Configuration is an evidence classification, never canonical authority.
Policies should be reviewed per provider/dataset: official publisher records may be
`official`; stable structured registries may be `authoritative_structured`; community
or observational inputs require their matching Phase 80 class. A provider name alone
must never infer trust.

## Acquisition-run lifecycle and recovery

Runs (`acquisition-run-v1`) are distinct from snapshots and record requested datasets,
timestamps, status, discovery count, downloaded and unchanged snapshots, failures,
normalization/assertion count placeholders, warnings, resumability, and deterministic
report path. Mixed success is `partial`; successful snapshots remain immutable and
auditable. Recovery consists of inspecting the report, fixing provider/input policy,
and rerunning failed datasets under a new run ID. Checksums deduplicate already-retained
content. A run report is create-only; reuse with different content fails.

Failures remain recoverable as follows:

| Failure | Result | Recovery |
| --- | --- | --- |
| malformed/unsupported/oversized response | no snapshot or no normalized output | correct adapter/policy and retry |
| partial multi-dataset retrieval | successful snapshots retained; run is `partial` | resume failed datasets in a new run |
| checksum/length mismatch | read rejected | restore from source as a new verified acquisition; investigate mutation |
| duplicate ID/provider collision | operation rejected | correct source mapping or registration |
| partial filesystem write | temporary file never becomes snapshot artifact | retry; create-only final paths remain safe |

Safe identifier validation prevents traversal. Raw storage must not be configured in
canonical directories. Supported media are explicit. Schema versions fail closed.

## CLI

The offline reference entry point is `python -m mtglab.acquisition`:

```text
... acquire fixture <dataset> --fixture <json> --timestamp <ISO-8601>
... normalize <snapshot-directory> --output <normalized.json>
... assertions <normalized.json> --output <assertions.json> --timestamp <ISO-8601>
... acquisition-report <run-id>
```

There is intentionally no acquire-and-promote or download-and-canonize operation.

## Licensing and provider policy

Before enabling an adapter, review redistribution, caching, attribution, robots/API
policy, privacy, retention, and commercial-use terms. Record a stable license/policy
reference in the manifest but do not copy secrets into it. This milestone implements
no scraping and no live integration. Retention of bytes does not grant redistribution
rights; excluded/private snapshot storage may be required for a provider's terms.

## MB2 resume and future datasets

To resume Mystery Booster 2: approve a terms-compliant provider adapter and trust
policy; acquire complete source bytes; retain/check the run and checksum; normalize
without canonical mapping; review coverage, unmapped fields, source changes, and
assertion conflicts; generate candidate assertions; then use the existing explicit
canonical review/import boundary. Expected counts and completeness must be independently
established. This phase does not populate MB2.

The contracts are product-agnostic and can likewise retain complete sets, Secret Lair,
Universes Beyond, Marvel, and future releases. Market observations may use the same
raw/run lineage, but price-time semantics and market normalization remain a separate
future adapter/policy concern; this framework implements no history or trend logic.
