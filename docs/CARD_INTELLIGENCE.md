# Card Intelligence

## Phase 132 reviewed pilot

Pilot `phase-132-mb2-reviewed-pilot-v1` contains 90 asserted facts for ten deterministically
selected Mystery Booster 2 Cards: Brainstorm, Command Tower, Counterspell, Goblin Charbelcher,
Goblin King, Sol Ring, Swords to Plowshares, Treasure Cruise, Walking Ballista, and Wishclaw
Talisman. Names are stored in ascending order. Each card was selected before examining price to
exercise a distinct rules-text-supported role where possible: card selection, mana fixing, stack
interaction, damage, tribal synergy, mana acceleration, creature removal, card draw, repeatable
damage, and tutoring.

The supported predicates record retained oracle text, format legalities, MB2 membership, finishes,
USD market-price dimension availability, immutable observation coverage, and one bounded mechanical
role. The Phase 131 contract was extended with narrowly descriptive kinds for product membership,
treatment availability, market-price availability, observation coverage, and evidence gaps; using
an unrelated kind for those assertions would have misrepresented their meaning. Facts preserve
references to the Phase 119 canonical state, the retained Phase 128 Scryfall MB2 projection, or the
Phase 128 observation repository. Confidence remains unknown (`null`), because no separate retained
confidence assessment exists.

Demand and reprint history are explicitly unknown for every pilot card. Empty archetype and market
catalyst queries remain empty rather than producing conclusions. Competitive/Commander staple
status, popularity, supply, scarcity, collectibility, tournament usage, Commander demand, combo
participation, archetype placement, market catalysts, valuation, ranking, and recommendations are
excluded. A format legality is not evidence of play or popularity, a finish is not evidence of
collectibility, and a price observation is not an explanation of value.

Consequently this pilot is not a complete explanation of card value. Future separately retained
and reviewed datasets may append facts about competitive event usage, Commander usage, supply,
printing/reprint history, or dated market catalysts. Those additions must cite their exact retained
evidence, preserve unknowns, and must not be inferred by this repository or an AI consumer.

The deterministic review artifact is
`data/reviews/phase-132/pilot-review.json`. Production facts remain append-only beneath
`data/knowledge/facts/magic/<card-id>/<fact-id>.json`; neither the review artifact nor querying
promotes facts into canonical or market data.
