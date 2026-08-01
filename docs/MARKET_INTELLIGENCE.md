# Market Intelligence Foundation

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
