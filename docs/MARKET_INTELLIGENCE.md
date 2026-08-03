# Phase 131 Card Intelligence boundary

Card Intelligence is a separate knowledge repository, not a market observation store. Its facts may
record asserted supply, demand, scarcity, or market-catalyst knowledge with evidence, confidence,
effective date, explicit unknowns, and supersession, but the engine does not translate those facts
into a price, forecast, EV, or recommendation. It does not copy, alter, promote, or infer from market
observations. Future AI integration is limited to consuming deterministic read-only knowledge query
contracts alongside independently provenance-bearing market reports.

Phase 131 added no production facts and did not touch the retained acquisition, 478 immutable
observations, append-only Phase 129 history, or Phase 130 reporting behavior.

# Phase 128 production snapshot

The first production snapshot is retained acquisition `scryfall-mb2-30754638264-1`. It uses the existing `market-observation-v1` printing-level model and `data/market/observations/<entity-type>/<printing-id>/<provider>/<observation-id>.json` repository. Provider ID, printing ID, finish, language, USD currency, market price type, source/retrieval timestamps, acquisition ID, both source identities, mapping method, and canonical snapshot identity are preserved. Null price remains an explicit observation; this run contains zero null prices. The import report is stored separately under `data/market/imports/<run-id>/import-report.json`. Canonical data is never a market destination.

# Phase 127M evidence-PR completion boundary

The latest real acquisition reached the official Scryfall source, validated and streamed its gzip JSONL payload, completed the MB2-only dry-run census, and retained exactly three durable evidence files without importing observations, changing canonical data, or promoting. Its deterministic branch and evidence PR exist; the run stopped only because it waited for required checks even though this repository has no ruleset or configured required status checks. Phase 127M removes that nonexistent-check and auto-merge orchestration. The workflow now verifies and records the exact PR and succeeds, leaving manual review and merge as the next operation. The hard stop before observation import is unchanged, so production MB2 coverage remains 0/379.

# Phase 127G gzip transport boundary

The latest Phase 127F dry run reached the official metadata endpoint, selected `jsonl_download_uri`, validated the JSONL URI, reached `data.scryfall.io`, and received HTTP 200 `application/gzip`. It stopped before reading payload bytes because gzip was not an accepted payload media type. No provider or MB2 record was decoded, and coverage remains 0/379. Phase 127G treats the response as gzip—not plain JSONL—requires valid framing and complete incremental decompression, validates UTF-8 JSONL line by line, and reports only safe counts/digests. Exactly one post-merge dry run is next; persistence, canonical writes, and promotion remain prohibited.

# Phase 130 read-only historical CLI

Run commands with `PYTHONPATH=src:.`:

```bash
python -m market.cli observations list --provider scryfall --limit 100
python -m market.cli observations latest --printing-id 0110702e-0151-574a-af73-7259033dcc4e
python -m market.cli observations first --acquisition-run-id scryfall-mb2-30754638264-1
python -m market.cli observations count --finish foil --language en --currency USD --price-type market
python -m market.cli printing-history 0110702e-0151-574a-af73-7259033dcc4e
python -m market.cli coverage --product mystery-booster-2
python -m market.cli acquisition-summary scryfall-mb2-30754638264-1
python -m market.cli snapshot --as-of 2026-08-02T09:09:45.851000Z
```

`market-history-report-v1` is the primary deterministic JSON contract. Every success identifies
the report, normalized filters, canonical snapshot where applicable, returned result count,
truncation, ordering keys, explicit empty state, and data with complete observation provenance.
Errors use `market-history-error-v1`, emit `valid: false`, and exit 2. Supported filters are exact
canonical Printing ID, provider, acquisition run ID, finish, language, currency, and price type,
plus inclusive `--observed-from`, `--observed-to`, and `--as-of` source timestamps. Timestamps must
be timezone-aware ISO 8601. Values not supported by retained/canonical data and unknown Printing
IDs are rejected rather than treated as empty.

Lists sort by source timestamp, retrieval timestamp, provider, and observation identity; the
default limit is 100 and maximum is 500. First/latest return one exact retained record or an
explicit empty result. Count is untruncated. Printing history returns the complete selected series.
As-of snapshots select the latest retained record independently for each Printing, provider,
finish, language, currency, and price-type tuple and exclude every newer source observation.
Explicit null prices remain observations.

MB2 coverage compares observed Printing IDs with the 379 promoted canonical records whose set is
MB2, and reports covered/uncovered/total, observations, providers, acquisitions, earliest/latest
source time, and latest retrieval time. Acquisition summary reads the retained manifest and reports
provider/timestamps, observation and Printing counts, dimension counts, known/null price counts,
canonical snapshot, and available provider-source, retained-source, and normalized digests.

The facade has no write method. It does not acquire, import, append, replace, delete, promote,
calculate product EV, recommend, or start a workflow. `data/canonical/`, retained acquisition
evidence, observation history, and import reports are strictly read-only inputs.

# Market Intelligence Foundation

## Phase 127E acquisition status

Phase 127D established that URI extraction produced `blank_uri` before security validation,
but its combined check could not distinguish an absent field, a non-string field, or a blank
string. Phase 127E preserves the full selected decoded provider descriptor for transport and
creates a separate key/type-only diagnostic projection. Exact extraction reason codes and
schema diagnostics remain value-free. The next and only operation is one `persist=false` dry
run; persistence, canonical writes, and promotion remain prohibited, and coverage is 0/379.

## Phase 127D acquisition status

The real post-127C dry run parsed the official direct descriptor and timestamp but rejected
the download before transfer. Its exact-host validator allowed only `data.scryfall.io`, while
the selected official descriptor used another true `scryfall.io` static-file subdomain.
Phase 127D uses a label-aware, official-metadata-derived `scryfall.io` subdomain boundary plus
HTTPS/default-port/no-userinfo/absolute-path/no-fragment constraints and safe property-only
diagnostics. Query presence is permitted only from the selected official descriptor and its
contents are never logged. The next operation is one `persist=false` Action dry run;
production observations, canonical data, promotion, and MB2 coverage remain unchanged at 0/379.

## Phase 127C acquisition status

Phase 127B's endpoint correction reached Scryfall and received JSON metadata, confirming the remaining failure was local response-shape parsing rather than access or authorization. Phase 127C accepts the official direct and list bulk-metadata forms and still fails closed before persistence. No live payload, price observation, canonical write, or promotion has occurred; MB2 coverage remains 0/379. The next operation is one reviewed nonpersistent workflow dry run after merge.

**Status:** Phase 127 acquisition boundary complete; live access blocked. **Architecture:** v12 unchanged. **Contracts:** `market-observation-v1`, `market-analytics-v1`, and `market-query-v1`.

Phase 127 selects only Scryfall default-card bulk data and adds a versioned adapter outside
analytics. The local proxy blocked the official endpoint before response, so no production
observation was retained and promoted MB2 coverage remains exactly 0/379. See
[`SCRYFALL_MARKET_ACQUISITION.md`](SCRYFALL_MARKET_ACQUISITION.md). Query envelopes now
explicitly expose currency and observation timestamp even when their status is unknown.

## Baseline and architecture review

Phase 125 is merged at `b71f961`. Phase 119 remains the only production canonical promotion, with digest `793a364794e12002dd561a47a42333332ae7dd64a958fc18903b0cc2381de27f`. Architecture v12, Canonical Query Layer, Collection Intelligence, and the generic automatic-update pipeline are unchanged. Production canonical facts contain no pricing. Market records live below `data/market/observations`, never `data/canonical`.

## Market and provider model

`MarketObservation` is a provider-neutral immutable assertion for a card, printing, or sealed product. It supports market and buylist amounts, finish, currency, provider provenance, observation and recording timestamps, listing and sales counts, spread, and provider confidence. A null price is an explicit unknown. Multiple providers coexist and may be filtered or compared independently. Adapters remain outside `MarketAnalytics`; it has no provider SDK, field mapping, network behavior, or provider preference.

## Historical storage

`MarketObservationRepository` stores `<entity-type>/<entity-id>/<provider>/<sha256>.json`. The digest covers every semantic field. Exclusive creation rejects replacement, and reads verify both content identity and path. Corrections must be new observations: historical assertions are never rewritten. The repository has no canonical writer dependency.

## Deterministic analytics

Calculations use `Decimal`, UTC ordering, population variance, and round-half-even output at six decimal places. Current value is the latest known price; average is the arithmetic mean. Daily, weekly, and monthly changes compare the latest value with the latest observation at or before 1, 7, or 30 days earlier. Historical trend is the 30-day relative change. Moving averages cover trailing 7, 30, and 90-day windows. Volatility is the population standard deviation of consecutive relative returns.

Liquidity requires listings, sales, and spread and equally weights capped listing depth (`listings / 100`), capped activity (`sales / 30`), and inverse capped spread (`1 - spread`). Confidence requires provider confidence and weights it four parts against one part metric completeness. Missing inputs produce null, never invented numbers.

## Query interface and CLI

The Canonical Query Service optionally accepts the read-only market repository and exposes card, printing, product, history, and provider-comparison queries. Every `market-query-v1` response contains provenance, provider, timestamp, confidence, canonical snapshot identity, and known/unknown status. Historical points retain these fields individually.

```console
python -m mtglab --data-root data market card magic.abzan-falconer
python -m mtglab --data-root data market printing magic.mb2.1.en --provider example
python -m mtglab --data-root data market product mystery_booster_2
python -m mtglab --data-root data market history magic.mb2.1.en --entity-type printing
python -m mtglab --data-root data collection value --snapshot my-collection
```

An empty store returns valid JSON with explicit unknown status and null price/provider/timestamp/confidence.

## Collection integration

Valuation reports total market value, acquisition cost, unrealized gain/loss, and value by set, rarity, finish, and storage location. Each amount retains known amount and missing quantity. Any missing required price or acquisition cost keeps the complete total and dependent gain/loss unknown rather than assuming zero. Existing price-independent acquisition priorities are unchanged.

## Future recommendation engine

This foundation may supply inputs to a separately approved downstream recommendation engine. Phase 126 does **not** recommend purchases or sales, rank investments, analyze portfolios, or add AI reasoning. A future engine must explain policy and uncertainty, use these read-only contracts, and never promote market observations into canonical facts.

## Phase 127A operational state

Provider adapter availability is not a successful dry run, a successful dry run is not
persisted production history, and persisted history is not complete queryable coverage.
At this checkout those states are respectively **available**, **unverified**, **absent**, and
**0/379**. Phase 127A adds explicit acquisition census fields and state-aware verification;
it does not add market facts or change analytics, canonical data, or recommendations.
# Phase 129 append-only historical lifecycle

The production observation root is a multi-run historical database. An observation's
content-derived identity includes its provider assertion, observed/source time, recorded/retrieval
time, printing, finish, currency, price type, and provenance. Import enrichment binds the
acquisition run, provider identifier, language, source digest, normalized digest, resolution,
and source URL. Thus a later acquisition creates new immutable identities rather than updating
prices in place.

An acquisition is validated and normalized completely in a private staging directory. Publication
uses exclusive destinations and verifies every byte before writing the immutable run report, which
acts as its commit marker. Failure before that marker removes only newly published files. Existing
history is not touched. A completed run may be replayed only when its report lineage and all
observation bytes are identical; conflicts fail closed.

`MarketObservationRepository.observations` provides stable chronological history and filters for
acquisition, provider, printing/entity, finish, language-bearing provenance, currency, price type,
UTC date, and as-of timestamp. `first`, `latest`, and `count` use the same filters. Existing Market
Intelligence summaries remain compatible and naturally select the newest priced observation.
Per-run deterministic reports record acquisition summary, observation/coverage growth, total
historical count, append and replay assertions, and import lineage. These are market-only facts:
canonical writes and promotion remain prohibited.
