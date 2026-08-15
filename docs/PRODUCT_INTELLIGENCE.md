# Fixed-Content Product Intelligence Foundation

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

The first useful future vertical should supply reviewed fixed-content manifest/offer/market evidence,
then define a separately approved Decision Intelligence request and policy for sealed-now versus
wait/singles alternatives. It must preserve the three-way distinction among intrinsic component value,
temporary presale scarcity premium, and sealed collectible premium, and fail closed where the latter
concepts lack evidence. This milestone stops before that policy, production data, acquisition, or UI.
