# Scryfall MB2 Market Acquisition

**Phase 127B status:** provider acquisition and failure reporting repaired. No production
market observation was fabricated or retained by this repair.

## Selection and access assessment

Scryfall `default_cards` bulk data is the sole selected source. It is publicly accessible
without credentials, explicitly downloadable through the official
`https://api.scryfall.com/bulk-data/default_cards` endpoint, supplies stable card UUIDs,
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

Phase 127/127A used the incorrect path `bulk-data/default-cards` (hyphen). Scryfall's
documented `type` and official endpoint path use `default_cards` (underscore), so the
GitHub-hosted dry run reached Scryfall but received a permanent HTTP 404 before metadata.
The root cause was our implementation, not GitHub Actions and not a Scryfall outage. The
earlier local CONNECT-proxy HTTP 403 was an environment limitation and obscured this path
error; it was not the GitHub-hosted response. No access was fabricated or routed through an
unofficial mirror. Exact retained coverage is **0 priced observations / 379
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
  --data-root data --retrieved-at 2026-08-01T12:00:00Z \
  --run-id scryfall-mb2-example \
  --retain-payload market-acquisition-source.json \
  > market-acquisition-dry-run.json
STATUS=$?
cat market-acquisition-dry-run.json
exit "$STATUS"
```

The report contains only endpoint categories and response-stage facts—never request
secrets, query strings, response bodies, or the provider payload. The Action captures the
exit status, prints this JSON, uploads it under `if: always()`, then exits with the original
status. Consequently a failed fetch cannot enter verification or persistence.

Only after a successful report has been inspected should the manual **Market acquisition**
Action be rerun with
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

## Phase 127A operational audit (2026-08-01)

Phase 127 is merged at `ad0797e`. This checkout contains zero files below
`data/market/observations` and no retained acquisition manifest, so it contains no genuine
Scryfall observation and queryable coverage is still 0/379. The execution environment
rejected both GitHub API and official Scryfall connections at its outbound CONNECT proxy;
therefore the first Actions run's artifacts, dry-run result, branch, PR, checks, and
persistence state could not be independently inspected here. No provider payload was
substituted and no production persistence was attempted.

`market-acquisition-run-v1` now reports the total source records inspected, MB2 source
records selected, unique promoted Printings matched, known-price observations, and explicit
missing-price observations in addition to mapping outcome counts. These fields make a future
retained run sufficient to state exact coverage without deriving it from workflow logs.
Lifecycle tests accept either an empty production store or a store whose retained files pass
content/path verification and the Scryfall/printing/USD boundary.


## Phase 127B retry and stop contract

Redirects are handled by the standard HTTP opener. HTTP 429, 5xx responses, timeouts, and
transport failures receive at most three total attempts with deterministic one- then
 two-second backoff. Other 4xx responses are permanent and receive no retry. Metadata and
payload responses require an accepted JSON/octet-stream content type. The diagnostic reports
the failing stage, endpoint category, status/content type when available, metadata and URI
progress, download start, and byte retention without including response bodies.

A dry run must stop before persistence whenever its process status is nonzero, its report is
invalid, the official metadata lacks a secure `download_uri`, or an integrity/isolation check
fails. Phase 127B performs no live persistence, canonical write, valuation, or promotion.
