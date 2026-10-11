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

## Governed production evidence packet

`fixed-content-acquisition-evidence-v1` is the production input boundary, not an analysis or a
recommendation. It composes `FixedContentProductManifest`, `ProductAcquisitionOffer`, and a complete
partition of every guaranteed component into either `ComponentValuationInput` or an explicit
unpriced ID. `SourceSnapshot` governs provider, source record/document identity, locator when
permitted, canonical references, publication time when known, retrieval time, evidence state, and a
strict SHA-256 digest. Manifest publication/effective time, sealed offer observation/effective time,
each Market observation/recording time, retrieval times, and packet assembly time remain independent.

The sealed wrapper records availability only when actually evidenced and separately marks shipping,
tax, fees, and discounts `known`, `unknown`, `incomplete`, or `not_applicable`; the embedded offer
continues to own exact listed-price-to-effective-cost arithmetic. `SinglesTransactionCosts` records
shipping, acquisition-model marketplace fees, other explicit costs, currency, completeness,
seller/order assumptions, and provenance. Missing values are never converted to zero: a component
without compatible price evidence must be explicitly unpriced, and an unknown required cost remains
unknown.

Canonical JSON uses sorted keys and compact separators. Packet identity is SHA-256 over the complete
logical content including retained input snapshots and timestamps. The replay repository returns the
same bytes for the same packet and rejects identity reuse with different bytes; replay validates the
digest. Construction is immutable and never writes canonical, Market, Card Intelligence, or other
production repositories. The matching JSON Schema rejects additional top-level fields and unsupported
future evidence classes.

### Manual review and readiness

`fixed-content-acquisition-evidence-review-v1` records a human reviewer and review timestamp and has
exactly two outcomes. `READY_FOR_EVALUATION` requires a complete manifest with no decision-critical
unknowns, every guaranteed component valued, exact compatible Printing/finish/language/treatment and
provider/currency/price-type dimensions, acceptable offer and singles timestamps under a
reviewer-supplied currentness threshold, complete sealed effective-cost inputs, complete explicit
singles transaction costs in the same currency, and known digest-bound provenance. Every failed gate
produces `NOT_READY_FOR_EVALUATION` with machine-readable issues. Review never emits
`BUY_SEALED_NOW` or `BUY_SINGLES_NOW`.

Reference-only placeholders exist for presale and post-release observations, supply/availability,
listing depth/liquidity, historical comparables, sealed collectible premium, collector/IP demand, and
reprint risk. They are optional and unevaluated by the current-cost vertical; arbitrary inference
fields fail validation.

### Existing reuse, gaps, and pilot

The packet reuses canonical Card/Printing identities, immutable `MarketObservation` semantics and
retained market history, Decision Intelligence `EvidenceReference`, existing product identity, and
established evidence/source digest conventions. It creates no parallel acquisition subsystem.
Existing production material is insufficient for a READY real packet: retained market observations
cover the bounded MB2 pilot rather than a complete fixed-content product, and no reviewed current
sealed offer/transaction-cost bundle is present.

The provisional later pilot is **Commander Collection: Black (non-premium)**. Repository-retained
MTGJSON deck evidence names an exact product record, its small guaranteed-card scope is manageable,
and it exercises exact Printing resolution without non-card valuation ambiguity. It is preferable to
a large preconstructed deck and is not the motivating named product. Selection remains conditional:
a later authorized assembly must prove complete official contents, exact canonical Printings, a
current sealed offer, complete compatible current singles observations, transaction costs, and source
integrity. No production packet was retained in this milestone.

The exact remaining dependency chain is: assemble that one governed packet from reviewed sources →
human review → if and only if READY, call existing `analyze_fixed_content` → call the existing
sealed-versus-singles Decision Intelligence policy → expose its structured recommendation to ChatGPT.
No additional infrastructure phase is presently indicated.
