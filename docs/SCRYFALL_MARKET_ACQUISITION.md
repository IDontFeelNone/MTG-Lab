# Scryfall MB2 Market Acquisition

**Phase 127 status:** implementation complete; live acquisition blocked before response on
2026-08-01. No production market observation was retained.

## Selection and access assessment

Scryfall `default_cards` bulk data is the sole selected source. It is publicly accessible
without credentials, explicitly downloadable through the official
`https://api.scryfall.com/bulk-data/default-cards` endpoint, supplies stable card UUIDs,
set/collector/language/finish fields, USD price fields, and an `updated_at` timestamp.
Scryfall's API documentation requires clients to use the bulk endpoint for large
downloads, identify their client, avoid excessive requests, link users back to Scryfall,
and preserve required Wizards/Scryfall attribution. Prices are informational third-party
market data, may be absent, and must not be presented as purchase advice. See
<https://scryfall.com/docs/api>, <https://scryfall.com/docs/api/bulk-data>, and
<https://scryfall.com/docs/api/cards>.

Cardmarket was not selected because its API access requires approved credentials.
TCGplayer was not selected because new API access is restricted. MTGJSON price files
were not selected because the repository's approved endpoints are currently returning
HTTP 403 and Scryfall gives a direct exact identifier already present on promoted MB2
Printings. No page scraping is performed.

The current container's outbound proxy rejected the official Scryfall API connection
with HTTP 403 before an origin response. Therefore access was not fabricated or routed
through an unofficial mirror. Exact retained coverage is **0 priced observations / 379
promoted MB2 Printings (0%)**, with zero matched, unmatched, ambiguous, or rejected live
records because no provider payload was received. Collection valuation was not run:
there are insufficient real retained prices. The CLI proofs consequently report
`status: unknown` honestly.

## Adapter and deterministic mapping

`scryfall-market-adapter-v1` validates provider-native cards, uses `Decimal` without
binary floating-point conversion, preserves null prices, enforces USD, and emits only
`market-observation-v1`. Resolution priority is: reviewed mapping; exact canonical
`scryfallId`; exact lowercase set code plus collector number, normalized language, and
finish; explicit unresolved/ambiguous. Conflicts are rejected. Names are never used.
Every resolution carries provider ID, method, confidence, candidates, and provenance.

The acquisition manifest records source and normalized SHA-256 digests, source URL,
retrieval/source timestamps, canonical state SHA-256, all outcome counts, and explicit
`canonical_write: false` / `promotion_performed: false`. Provider-native fields remain
inside the adapter, bounded source artifact, and mapping diagnostics—not analytics.

## Operation, persistence, and recovery

Run a dry run first:

```bash
PYTHONPATH=src python scripts/scryfall_market_acquisition.py \
  --data-root data --retrieved-at 2026-08-01T12:00:00Z --run-id scryfall-mb2-example
```

After inspecting it, rerun through the manual **Market acquisition** Action with
`persist=true`. One fetched payload is reused between dry-run and persistence. The
workflow verifies schema, digests, mappings, MB2/promoted isolation, the complete test
suite, changed-file boundaries, and every written observation. It retains diagnostics
on success or failure, safely creates or reuses `automation/scryfall-mb2-market`, opens
an update PR, and requests auto-merge only after required checks succeed. It never
force-pushes or administratively merges.

No secret is required. One-time repository settings are: allow GitHub Actions to create
pull requests, protect the default branch with required `python-validation` checks, and
enable auto-merge if desired. If auto-merge is disabled, the verified PR remains open.
Future scheduling requires only adding a `schedule` trigger after operational review.

Runs append beneath `data/market/acquisitions/<run-id>` and observations beneath
`data/market/observations`; nothing is written beneath `data/canonical`. An existing run
directory fails closed. Observation replay succeeds only for byte-identical content;
different bytes, path/content disagreement, digest failure, or tampering fails closed.
On transport/rate-limit failure, retain diagnostics and rerun later with a new run ID.

## Query proof (currently unknown)

```bash
python -m mtglab --data-root data market printing 0110702e-0151-574a-af73-7259033dcc4e
python -m mtglab --data-root data market history 0110702e-0151-574a-af73-7259033dcc4e --entity-type printing
python -m mtglab --data-root data market product mystery_booster_2
```

All envelopes expose provider, observation timestamp, currency, confidence, provenance,
canonical snapshot identity, and known/unknown status. Refreshes append new observations;
they never edit history. Full MB2 value coverage must not be claimed until all 379
promoted Printings have valid retained observations for the required finish.
