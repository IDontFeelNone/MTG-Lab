# Market Provider Framework v1

## Architecture and boundary

The Market Provider Framework is the only boundary through which MTG Lab obtains
market information. It adds no vendor-specific assumptions and performs no network
access in v1:

```text
Canonical Repository -> MarketService -> MarketProvider -> interchangeable sources
                              |
                              `-> append-only MarketSnapshotRepository
```

`MarketProvider` returns a validated `ProviderResponse`. A response can contain any
subset of latest, low-listing, market, and high-listing values. Values can be attached
to the printing generally or to provider-defined finish variants such as `foil` and
`nonfoil`. Providers are not required to populate every field. Currency, a timezone-
aware source update timestamp, and JSON-compatible provider metadata travel with the
response. The included `manual` implementation produces deterministic sample data and
never calls an external service.

No observation, analytics, or AI module may instantiate or call a provider directly.
Those consumers use `MarketService`, whose stable API verifies the canonical printing,
selects a registered provider, validates identity and timestamp consistency, normalizes
the response, and caches it for a configurable duration. Provider additions therefore
do not change downstream interfaces.

## Snapshot lifecycle

Each successful retrieval produces an immutable `MarketSnapshot` containing the
canonical printing ID, provider ID, provider update timestamp, retrieval timestamp,
currency, available price points and variants, and provenance. Provenance retains the
provider metadata plus framework retrieval context. Snapshot timestamps are normalized
to UTC, and a provider update cannot be later than retrieval.

When persistence is requested, `MarketSnapshotRepository.append` creates a new JSON
file using exclusive-create semantics. It never updates or replaces a file. Loading
revalidates the schema, values, timestamps, derived snapshot ID, and content-addressed
directory path. A repeated snapshot identity is rejected rather than overwritten.

## Canonical repository and analytics

The service checks printing existence through `CanonicalRepository.get_printing`.
Snapshots only retain that stable identifier: they do not embed, edit, promote, or
otherwise mutate canonical entities. Market history belongs under the separate
snapshot root (`data/market/snapshots` by default).

Analytics, observations, and future AI components consume normalized snapshots from
`MarketService` or the snapshot repository. They must not depend on provider response
formats. Expected-value and portfolio calculations remain outside this milestone.

## CLI

With `src` on `PYTHONPATH`, deterministic offline data can be captured and inspected:

```bash
PYTHONPATH=src python -m mtglab.market refresh --provider manual
PYTHONPATH=src python -m mtglab.market snapshot
```

Use `--printing <canonical-id>` one or more times to limit refreshes, `--game` to select
the canonical game, and `--root` to select a snapshot directory. JSON output is sorted
for reproducibility.

## Future providers

Cardmarket, CSV, manual-entry, marketplace, and metadata-only adapters can implement
`MarketProvider` later. An adapter may remain partial and may expose provider-specific
details only through metadata. Live credentials, rate limiting, transport, and vendor
mapping belong inside future adapters; scraping and live API integration are explicitly
absent from v1. Registration with `MarketService` is the only integration required.

## External identifier mapping layer

External identities remain separate from canonical entities. A versioned mapping set
associates `canonical_printing_id` and `provider_name` with a required provider product
ID and optional SKU, finish, and language. Each record has an explicit lifecycle status
(`pending`, `active`, `rejected`, or `retired`) and non-empty provenance. The set also
has import-level provenance. Provider IDs are intentionally opaque strings: UUIDs and
vendor-specific case are preserved.

`ExternalMappingRepository.import_document` accepts the
`external-market-mappings-v1` JSON format, validates canonical printing references when
a canonical repository is supplied, sorts records by their complete identity, and
writes canonical, sorted JSON. Versions are append-only at
`data/market/mappings/<provider>/<version>.json`; an existing version is never replaced.
One version contains exactly one provider, so review and rollback boundaries are clear.

Resolution requires the caller to name a version and matches printing, finish, and
language exactly. Only `active` records resolve. A generic request does not silently
select a finish- or language-specific record, and missing or ambiguous mappings fail
validation. `validate` reports every non-active record for review.

Future network adapters should subclass `MappedMarketProvider`. Its final `fetch`
workflow resolves an exact mapping before delegating the opaque identifiers to
`fetch_mapped`; the canonical model and `MarketService` API remain unchanged. Providers
that expose finish-specific products can resolve each requested finish explicitly from
the same repository. The mapping layer itself performs no network requests and stores
no credentials.

Minimal import document:

```json
{
  "schema_version": "external-market-mappings-v1",
  "version": "2026.07.30",
  "provenance": {"source": "reviewed provider export"},
  "mappings": [{
    "canonical_printing_id": "printing.example",
    "provider_name": "example",
    "provider_product_id": "opaque-product-id",
    "provider_sku_id": null,
    "finish": null,
    "language": null,
    "mapping_status": "pending",
    "provenance": {"source_record": "export-row-1"}
  }]
}
```
