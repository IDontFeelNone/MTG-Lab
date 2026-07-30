# Future Vision

> **Tier: Tier 0 (Architectural Intent)**  
> **Status: Vision — not implementation authorization**  
> **Architecture:** v12 (unchanged)

## North star

MTG Lab is intended to become an AI-powered decision intelligence platform for collectible
games: a system that turns evidence-backed repository knowledge, observations, market data,
user context, and explicit models into reproducible answers. It should help people understand
what is known, decide under uncertainty, and inspect why an answer was produced.

The platform is not an oracle and AI is not its memory. The canonical repository, immutable
evidence, versioned facts, and auditable derivations remain authoritative. Intelligence
layers reason over those assets and communicate uncertainty. This vision extends
[`AI_ARCHITECTURE_VISION.md`](AI_ARCHITECTURE_VISION.md) and
[`ARCHITECTURE.md`](ARCHITECTURE.md); it changes neither Architecture v12 nor current scope.

## Capability horizons

### Collection Intelligence

Understand what a user owns, where it is, how it was acquired, and how complete or useful it
is. Connect ownership to canonical printing identity while preserving condition, quantity,
location, provenance, and user-entered uncertainty. Recommend actions only from explicit
objectives and explain their factual basis.

### Product Intelligence

Explain sealed product contents, configurations, evidence coverage, and uncertainty. Compare
products using canonical composition rather than product-name logic. Distinguish advertised
facts, observed outcomes, inferred models, and unknown collation.

### Market Intelligence

Build time-aware, provider-aware views of prices, liquidity, spreads, and availability.
Retain raw observations, mappings, currencies, timestamps, and provider terms. Never turn a
single quote into universal market truth; communicate freshness and coverage.

### Deck Intelligence

Relate canonical cards and printings to formats, rules, deck lists, strategies, and collection
constraints. Separate game-rule legality and factual deck composition from strategic opinion.
Recommendations should expose assumptions, evidence, alternatives, and sensitivity.

### Portfolio Intelligence

Treat collections as portfolios only when the user chooses that lens. Analyze concentration,
cost basis, liquidity, scenarios, and risk without promising returns. Preserve the distinction
between observed prices, valuation methods, forecasts, and personal preferences.

### Research Assistant

Help investigators locate sources, compare claims, surface contradictions, identify missing
evidence, and prepare reviewable candidate assertions. It should cite exact repository lineage
and make “not enough evidence” a useful result. It must not bypass research review or canonical
promotion.

### Historical Analysis

Reconstruct what products, markets, collections, and the repository itself looked like at a
given time. Versioned snapshots and immutable history should support temporal comparison
without rewriting earlier knowledge in light of later facts.

### Explainable AI

Produce answers whose sources, transformations, model versions, assumptions, uncertainty, and
counterfactuals can be inspected. Retrieval and inference should be labeled. Users should be
able to ask why, why not, what changed, and what evidence would change the conclusion.

### Intelligence Engine

Coordinate deterministic facts, analytics, explicit decisions, probabilistic models, and AI
reasoning behind stable boundaries. Select the weakest sufficient method: direct lookup before
analytics, analytics before simulation, explicit rules before generative synthesis. Outputs
must be versioned, reproducible where possible, and prohibited when prerequisites are absent.

### Personal Intelligence

Learn user-approved goals, budgets, formats, risk tolerance, collecting interests, and privacy
preferences without confusing personal context with global truth. Personal data needs clear
ownership, export, deletion, provenance, and isolation from canonical records.

### Multi-game support

Generalize evidence, ownership, markets, analytics, decisions, and intelligence across games
while keeping each game's rules and products in versioned data or adapters. Portability must be
demonstrated with real or synthetic second-game contracts, not merely claimed from generic
names.

## Architectural intent

Across all horizons, the enduring flow is:

```text
Evidence and observations -> reviewed canonical facts -> deterministic domain services
                          -> explainable analytics and decisions -> AI-assisted synthesis
```

Not every question requires every layer, and arrows never imply automatic promotion. Future
storage and compute may include databases, indexes, APIs, event streams, or specialized models,
but these remain replaceable implementations behind versioned contracts. The repository must
retain authority, raw inputs remain immutable, and every conclusion must disclose its class:
fact, observation, derivation, simulation, forecast, recommendation, or unknown.

## Success criteria

MTG Lab succeeds when users can make better-informed decisions and independently inspect the
basis of those decisions; when a new product or game is primarily new evidence and data rather
than engine code; when past answers can be reproduced; and when the system refuses unsupported
precision. Capability breadth must never outrun evidence quality, explainability, privacy, or
constitutional governance.
