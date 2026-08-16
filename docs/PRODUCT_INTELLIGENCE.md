# Fixed-Content Product Intelligence Foundation

## Acquisition decision adapter

The first synthetic end-to-end vertical adds a thin Product Intelligence adapter without changing
the descriptive analysis contract. It projects product/game/manifest/offer/analysis identity,
current costs and deltas, coverage and unknown counts, comparability, component contributions,
anchor concentration, evidence/timestamps, assumptions, limitations, unsupported dimensions, and
input snapshots into generic Decision Intelligence requests and alternative envelopes.

Decision Intelligence—not the descriptive analyzer—interprets the explicit objective and applies
versioned current-cost policy `fixed-content-current-acquisition-cost` `1.0.0`. The only evaluated
routes are `BUY_SEALED_NOW` and `BUY_SINGLES_NOW`; singles transaction costs must be supplied.
Selected output includes the exact current cost difference and algebraic break-even thresholds.
Anchor concentration remains descriptive explanatory context and never becomes a price-collapse
forecast. Future `WAIT`, sealed-collectible, and sell/rebuy vocabulary requires new governed evidence
and policy support and currently causes abstention.

## Status and scope

Implemented from baseline `64410189479fc2cc1dae9decf8588c7c115f7613` (merged GitHub PR #157).
This synthetic-only foundation is deterministic, immutable, read-only, versioned, provenance-preserving,
and game-neutral. It does not change frozen Architecture v12 and does not create a production
recommendation.

## Contracts

* `fixed-content-product-manifest-v1` describes canonical game/product identity, category, dates,
  guaranteed typed collectible components, exact quantities and comparable printing/finish/language/
  treatment dimensions, evidence, completeness, explicit unknowns, assumptions, and limitations.
  Components need not be cards.
* `product-acquisition-offer-v1` keeps listed price, shipping, supplied tax, fees, discounts, exact
  effective acquisition cost, currency, time, provider, and evidence separate.
* `component-valuation-input-v1` is a thin binding to Market Intelligence's immutable
  `MarketObservation`; Product Intelligence does not own or copy market history.
* `fixed-content-product-analysis-v1` is a content-identified descriptive result. It exposes exact
  sealed cost, known and (only when complete/comparable) total component cost, both cost deltas,
  item contributions, largest/anchor concentration, top-N concentration, transaction-cost impact,
  valued component/quantity coverage, unpriced counts/quantity, and comparability issues.

Currency, provider, timestamp, price type, printing, finish, language, and treatment mismatches never
produce an exact total or cost delta. Partial evidence retains a known subtotal and explicit incomplete
state rather than treating missing prices as zero. Duplicate identities and conflicting inputs fail
closed. No repository or network writer exists.

## Ownership boundaries

* **Market Intelligence** owns observations, histories, providers, and market dimension semantics.
* **Product Intelligence** owns fixed-content manifests, sealed offers, and descriptive aggregation of
  already supplied evidence.
* **Card Intelligence** owns interpreted card-level evidence; Product Intelligence does not infer it.
* **Collection Intelligence** owns user inventory/state and is not read in this milestone.
* **Decision Intelligence** owns objectives, alternatives, policies, abstention, and recommendations.
  Product Intelligence projects generic metrics through `DomainAnalysisEnvelope` only.
* **AI/ChatGPT** may eventually explain a repository-produced structured recommendation; it does not
  calculate product economics or select an action.

Acquisition objectives—including mechanical ownership, minimum cost, art/treatment collecting,
sealed collecting, deck acquisition, and resale—therefore remain downstream request/policy concerns.

## Explicitly unsupported

Intrinsic component acquisition value is reported only as the literal sum of exact supplied component
observations. Presale scarcity premium and sealed collectible premium are distinct, unevaluated
concepts and are never folded into that sum. Post-release compression risk, supply trajectory,
availability, listing/sales depth, liquidity, playability/demand, collector/IP demand, artwork demand,
reprint risk, and historical comparable-product behavior are also `not_evaluated`. There are no
prediction, fair-value, investment, recommendation, or product-specific formulas.

## Bounded future path

The next useful boundary is one reviewed production evidence packet containing a complete manifest,
sealed offer/effective cost, complete comparable singles observations, explicit transaction costs,
and provenance/snapshot identity. A real evaluation must preserve the distinction among component
acquisition cost, presale scarcity premium, and sealed collectible premium and fail closed where the
latter concepts lack evidence. No production target, acquisition, premium model, forecast, or UI is
authorized by the synthetic vertical.
