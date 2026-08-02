# Phase 127G streaming gzip JSONL contract

Main includes Phase 127F (`d64b1b2`). Its latest real dry run reached the official metadata endpoint, selected `jsonl_download_uri`, classified JSONL, validated the URI, reached `data.scryfall.io`, and received HTTP 200 with `application/gzip`. Decisive diagnostics were `bulk_payload_download_began: true`, `bytes_downloaded: 0`, `compression_mode: null`, and `failing_stage: payload_content_type`. Thus no provider records were decoded, no MB2 records selected, no observations or canonical bytes written, and no promotion performed; coverage is 0/379.

Phase 127G accepts `application/gzip` (and tested legacy `application/x-gzip`) for JSONL only as gzip. It verifies magic framing independently, streams compressed bytes through gzip and incremental strict UTF-8 decoding, parses exactly one object per nonblank line, and requires successful EOF plus any declared content-length match. Invalid framing, truncation, decompression/UTF-8/JSON failures, non-objects, duplicate identities, unsupported media, ambiguity, or partial streams fail closed. Compressed and decompressed byte counts, line/record/malformed/duplicate/MB2 counts, mapping census, known/missing-price census, stream completion, framing status, and deterministic compressed-source/normalized digests are safe diagnostics. URI values, paths, queries, headers, bodies, and records are never logged. Only at most 1,000 MB2 records are retained; unrelated records are counted then discarded.

After merge, dispatch **Market acquisition** exactly once and inspect the diagnostics plus bounded MB2 projection. Require `persisted`, `canonical_write`, and `promotion_performed` all false. This is the hard stop: Phase 127G has no persistence input and authorizes no subsequent persistence operation.

# Scryfall MB2 Market Acquisition

**Phase 127E status:** provider-descriptor field preservation is explicit. No production
market observation was fabricated or retained by this repair.

The real post-127D dry run reached the official endpoint, decoded a direct `bulk_data`
object, inspected and selected exactly one `default_cards` descriptor, and accepted its
`updated_at`. It then reported `blank_uri` before security validation, began no payload
download, and wrote neither market nor canonical state. It performed no promotion; production
MB2 market coverage remains **0/379**.

Code-level review found that Phase 127D did not actually establish that the provider returned
a blank string: one `selected.get("download_uri")` branch collapsed an absent field, every
non-string value, and a whitespace-only string into the same `blank_uri` result. Selection
used the decoded mapping directly, but this fact was neither represented nor regression-tested,
so the report could not distinguish provider schema from a future projection or sanitization
loss. Phase 127E keeps the exact decoded, validated provider descriptor as the transport
object through URI extraction. A separate value-free diagnostic projection contains only
sorted key names and runtime type names and cannot replace or mutate that transport object.

Diagnostics now distinguish `download_uri_absent`, `download_uri_not_string`,
`download_uri_blank`, and `download_uri_string_preserved`; report top-level and selected key
names, field presence/type/normalized blankness, original-field preservation, and object
separation. URI values, paths, query contents, bodies, headers, and payload contents remain
excluded. URI security policy is unchanged and every extraction/schema/security failure stops
before download.

The latest real Phase 127C GitHub Actions dry run reached Scryfall and parsed one direct
`bulk_data` object, inspected one entry, selected exactly one `default_cards` descriptor,
and validated `updated_at`. It then stopped before payload download with
`Scryfall bulk metadata lacked a permitted secure download URI`; it wrote no market or
canonical data and performed no promotion. Coverage remains **0/379**.

The root cause was Phase 127C's exact `data.scryfall.io` hostname comparison: the official
metadata supplied a different true `scryfall.io` static-file subdomain. Phase 127D does not
record or guess the full returned URI. Because the descriptor comes from the official
metadata endpoint, it derives the static hostname from that selected descriptor and permits
it only when normalized DNS labels form a true subdomain of `scryfall.io`. HTTPS, no
userinfo, effective port 443, a nonempty absolute path, no fragment, and a non-IP,
non-localhost hostname remain mandatory. This rejects suffix lookalikes and does not permit
arbitrary hosts. A query is accepted only when supplied in that official descriptor and is
passed unchanged to the one download; it is never logged or retained in the report.

Safe diagnostics report scheme, normalized hostname, effective port, userinfo/query/fragment
booleans, path presence, hostname-allowlist result, and a stable exact rejection reason code.
They never report the URI, path contents, query contents, payload, headers, or response body.
Successful reports use the stable `scryfall:default_cards` label rather than the transport URI.

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


## Phase 127E post-merge operation

After Phase 127E merges, manually dispatch **Market acquisition** exactly once with
`persist=false`. Confirm `download_uri_string_preserved`, descriptor/diagnostic object
separation, a successful unchanged URI-policy result, exactly one payload download, valid
payload shape, and the MB2-only mapping census. Confirm `canonical_write: false` and
`promotion_performed: false`. Stop on any nonzero status or failed check; `persist=true` is a
hard stop and is not authorized by Phase 127E.

## Phase 127F JSONL provider contract

The latest real Phase 127E Actions dry run reached the official endpoint and selected one
direct `bulk_data` descriptor for `default_cards`. Its retained safe key inventory was
exactly `compressed_size`, `description`, `id`, `jsonl_download_uri`, `name`, `object`,
`type`, `updated_at`, and `uri`; `download_uri_present` was false. Extraction therefore
stopped with `download_uri_absent`. The unchanged provider descriptor and separate safe
diagnostic projection prove that no field was dropped or sanitized. Payload download never
began, no observation or canonical bytes were written, no promotion occurred, and production
coverage remains **0/379**.

The exact defect was the consumer's unsupported `download_uri` assumption. Phase 127F
selects `jsonl_download_uri` as the current JSON Lines transport. It retains `download_uri`
only as unambiguous legacy JSON-array compatibility: neither field, a non-string or blank
selection, or conflicting values fails closed. The metadata `uri` remains API identity and
is never considered a payload location. The existing HTTPS/default-port/no-credentials,
label-aware static `scryfall.io` host, absolute-path, no-fragment policy is unchanged.

The JSONL download occurs exactly once and is decoded incrementally. Blank lines are
permitted; every nonblank line must be valid UTF-8 JSON containing one supported card object.
Malformed JSON, arrays, scalars, unsupported shapes, duplicate provider identities,
unsupported compression, decompression failure, and incomplete streams stop the whole run.
Only MB2 records are retained in the bounded source projection. SHA-256 is accumulated over
the transport bytes while streaming, and provider-neutral normalized output receives its own
deterministic digest. Identity or gzip compression is detected from validated response
metadata and gzip framing, not a filename.

Safe diagnostics contain only the selected field name, format, legacy-use boolean, field
presence/runtime types, exact reason code, response media type, compression mode, byte/line/
record counts, malformed/duplicate counts, and selected MB2 count. They never contain either
URI value, URI path/query, headers, body, or provider record contents.

After merge, dispatch **Market acquisition** exactly once. Phase 127F has no persistence
input and the implementation rejects `persist=true`. Inspect the dry-run artifact and bounded
`market-acquisition-source-mb2.json` projection for the complete decoded/selected/mapping and
known/missing-price census, deterministic digests, `canonical_write: false`,
`promotion_performed: false`, and `persisted: false`. Any failure or unexpected census is a
hard stop before a separately authorized future persistence phase.

## Phase 127I durable successful-run evidence

A temporary Actions artifact is diagnostic transport, not institutional memory: retention expiry
makes a successful acquisition unavailable to later sessions and repository consumers. A
successful run therefore retains only the bounded, verified handoff at
`data/market/acquisitions/<acquisition-run-id>/`. `source-mb2.json` is the MB2-only provider
projection, `dry-run-report.json` is the unchanged acquisition report, and `manifest.json`
binds those two files by SHA-256 and byte length while recording run identity, timestamps,
provider provenance, source/normalized digests, mapping/price censuses, and the exact canonical
snapshot used for identifier mapping. The manifest states `canonical_write: false`,
`promotion_performed: false`, and `observations_persisted: false`.

The complete bulk dataset, normalized observations, and any non-MB2 record are excluded. The
workflow accepts only byte-identical replay, commits only the three evidence files on the
deterministic run branch, never force-pushes, verifies the exact PR base/head/SHA, and fails
closed on collisions or path violations. It requests auto-merge only after branch protection is
present and every required check is green. This is evidence retention, not observation import;
coverage remains 0/379 until a later phase imports retained evidence.
