# Phase 128 retained-evidence import

Import (or byte-identically verify replay) with:

```bash
PYTHONPATH=src:. python scripts/import_market_observations.py scryfall-mb2-30754638264-1
```

The importer reads only the exact three regular files in the retained evidence directory, verifies the manifest/file/canonical identities and acquisition isolation flags, re-normalizes all MB2 records, and checks the retained normalized digest and censuses before staging. It publishes 478 observation files and the import report transactionally; a pre-publication failure removes staging, and a publication failure rolls back newly published observations. An existing run is accepted only when its report and every observation are byte-identical. The completed run covers 379/379 MB2 printings (previously 0/379), with 478 known and zero missing prices, six unmatched mappings, and no ambiguity, rejection, duplication, unsupported values, canonical write, or promotion.

Post-merge verification:

```bash
PYTHONPATH=src:. python scripts/market_acquisition_evidence.py verify --evidence data/market/acquisitions/scryfall-mb2-30754638264-1 --canonical data/canonical/state.json
PYTHONPATH=src:. python scripts/import_market_observations.py scryfall-mb2-30754638264-1
PYTHONPATH=src:. python -m unittest tests.test_phase_128_market_import
python -m json.tool data/market/imports/scryfall-mb2-30754638264-1/import-report.json >/dev/null
```

# Phase 127M manual evidence-PR completion

Main contains merged Phase 127L at `4d07036`. The latest real Market acquisition reached Scryfall, downloaded and fully validated the official gzip JSONL payload, produced the MB2-only dry-run census, created exactly `dry-run-report.json`, `manifest.json`, and `source-mb2.json`, passed all 415 repository tests, committed `a94288b`, pushed `market-acquisition/scryfall-mb2-30730690426-1` without force, and created the evidence PR. It stopped only because it waited for required checks that do not exist. The exact root cause is repository configuration: there is no branch ruleset and no configured required status-check set.

Phase 127M does not create or change a ruleset. It removes dispatch of `python-validation.yml`, required-check registration and polling, branch-protection API assumptions, and automatic merge. After the existing acquisition and evidence validation, the workflow creates or byte-identically reuses the deterministic branch, stages and commits only the same three durable evidence files, pushes without force, creates or safely reuses exactly one PR, verifies its base branch, head branch, head SHA, and title, records the PR identifier and URL for diagnostics, and exits successfully even while that PR remains open. A user reviews and merges the evidence PR manually. The four transient workflow files remain diagnostic-only; canonical and market-observation paths remain prohibited; conflicting branch or PR state fails closed. No observation import, canonical write, or promotion is authorized, and production MB2 coverage remains 0/379 until a separate later observation-import phase.

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
closed on collisions or path violations. It uses `gh pr checks --required` to wait for the PR's
required checks, independently requires a nonempty all-success result, and then requests
auto-merge, whose eligibility remains governed by repository rules. It does not query the
branch-protection REST endpoint, which is unnecessary for this gate and is unavailable to the
workflow token. This is evidence retention, not observation import; coverage remains 0/379
until a later phase imports retained evidence.

## Phase 127J changed-file verification repair

The repository-validation step checks the complete working-tree status before it creates an
evidence branch. That status intentionally contains the three durable evidence files plus these
four exact untracked (`??`) paths: `market-acquisition-dry-run.json`,
`market-acquisition-run-id.txt`, `market-acquisition-source-mb2.json`, and
`market-acquisition-stamp.txt`. Phase 127I's initial assertion listed only the durable files, so
its three-path expectation could not equal the real seven-path status.

`scripts/verify_market_evidence_boundary.py` parses NUL-delimited porcelain v1 rather than
whitespace-oriented display output. Its `market-evidence-changed-file-verification-v1` JSON
contains `expected_durable_paths`, `permitted_transient_paths`, `actual_changed_paths`,
`path_statuses` (each with `path`, `status`, and, for renames, `original_path`),
`missing_durable_paths`, `unexpected_paths`, `canonical_paths`,
`market_observation_paths`, `unsafe_paths`, `staged_paths`, `failure_reason_codes`, and
`valid`. A valid pre-commit example has seven path statuses, all `??`, no failure reasons, and
`valid: true`. A valid commit-boundary example has the same four transient `??` statuses and
exactly three durable `A ` statuses/staged paths.

The verifier also checks safe run identity, exact non-symlink regular-file placement, manifest
run identity, deletion/rename/status semantics, and explicit canonical/observation isolation.
The workflow prints ordinary status and the JSON report before propagating failure, and its
always-run diagnostic upload retains both reports. Only the three durable files below
`data/market/acquisitions/<acquisition-run-id>/` may enter the evidence commit.


## Phase 127K unsupported branch-protection API removal

Main contains merged Phase 127J. The real acquisition run
`scryfall-mb2-30730690426-1` acquired and validated the official payload, retained exactly the
three durable evidence files, passed the changed-file boundary and all 415 repository tests,
created commit `a94288b`, pushed its deterministic branch, and created the evidence PR. It wrote
no market observations or canonical data and performed no promotion. The workflow failed only
when its token attempted to read the branch-protection REST endpoint.

That endpoint probe supplied no safety property beyond the existing PR-specific required-check
commands. The workflow now waits on `gh pr checks --required --watch --fail-fast`, then requires
the returned required-check set to be nonempty and entirely successful before requesting
auto-merge. Repository rules still decide merge eligibility; there is no admin bypass, force
merge, direct base-branch write, or weakening of the evidence boundary.

## Phase 127L required-check registration and auto-merge gate

GitHub deliberately prevents pushes and pull requests authenticated by the workflow's
`GITHUB_TOKEN` from recursively starting ordinary `push` or `pull_request` workflow runs. The
evidence workflow therefore created the correct immutable branch and PR but reached finalization
before any required check suite existed, producing `no checks reported`.

The workflow now has narrowly scoped `actions: write` permission and explicitly dispatches
`python-validation.yml` on the already-validated evidence branch. It polls only for registration
of a nonempty PR-required check set; after registration, the existing fail-fast watch still waits
for completion and the independent query still requires every required state to be `SUCCESS`.
The recorded PR head SHA is checked after registration and again immediately before the
auto-merge request. Dispatch does not bypass branch protection, manufacture a successful status,
or merge directly: the required workflow executes the repository suite and repository rules
remain the final merge authority.

## Phase 139 — multi-snapshot readiness

Phase 139 preserves the Architecture v12 acquisition/import boundary while making later MB2 snapshots operationally safe. A repository owner manually dispatches `market-acquisition.yml`; the GitHub run ID and attempt produce a unique `scryfall-mb2-<run>-<attempt>` identity. The job makes the existing single provider-corpus request, projects MB2 only, retains exactly `manifest.json`, `dry-run-report.json`, and `source-mb2.json`, and creates or reuses one deterministic evidence branch and at most one exactly verified PR. It neither schedules runs nor merges PRs.

After human review and manual evidence-PR merge, an owner imports that run with `PYTHONPATH=src:. python scripts/import_market_observations.py <acquisition-run-id>`. Verification binds source/normalized digests, byte counts, timestamps, provider, canonical snapshot, scope, census, and non-write flags. Import is append-only, publishes its report last, rolls back partial publication, accepts byte-identical replay, rejects conflicts, preserves acquisition lineage, and records a deterministic observation inventory digest. Previous observations are never overwritten.

Readiness compares only the exact tuple canonical Printing ID, provider, finish, language, currency, and price type. States are `no_observations`, `single_snapshot_only`, `insufficient_comparable_dimensions`, and `multiple_snapshots_descriptive_only`. Missing prices remain explicit. Two priced source timestamps in the same exact dimension may yield Decimal first/latest amounts, absolute/percentage change, elapsed seconds, and count labelled **descriptive historical movement**. This is not statistical trend reliability, momentum, prediction, valuation, ranking, or recommendation.

Production still contains only acquisition `scryfall-mb2-30754638264-1` and therefore remains `single_snapshot_only`: one snapshot is not a trend and no descriptive movement can be established. The hard stop remains in force before prediction or recommendation work. To acquire the next real snapshot after merge: open GitHub Actions, choose **Market acquisition**, click **Run workflow** once, review the three-file evidence PR and checks, merge it manually, then separately run the importer for the displayed run identity and review that import change before merge.
