# Phase 134 retained-evidence gap

Phase 134 did not append Card Intelligence facts. The retained reviewed MTGJSON payload boundary
contains the ten pilot MB2 Printings but no non-MB2 Printing identity for any pilot Card; its MSH
records do not match the pilot. Set-membership assertions cannot substitute for printing-level
records, and the unretained source bytes cannot be reconstructed from lineage or conversational
memory. Active queries therefore still return the incomplete Phase 133 aggregate, and full-history
queries still return only the Phase 132 unknown and Phase 133 bounded MB2 assertion.

Printing count remains `max(total distinct canonical printings - 1, 0)` for reprint-count purposes,
and does not measure supply. The retained evidence still cannot establish complete global history,
demand, deck usage, popularity, scarcity, catalysts, historical price movement, valuation, price
predictions, or recommendations. See `data/reviews/phase-134/evidence-gap-report.json`.

# Phase 133 verified printing-history intelligence

Phase 133 uses the same ten-card Phase 132 pilot and appends ten known
`printing.reprint_history` facts. Each aggregate cites the exact Phase 119 canonical Card and MB2
Printing IDs and the matching record in retained acquisition `scryfall-mb2-30754638264-1`. It
reports the canonical Printing count and IDs, canonical set codes, separately asserted historical
set memberships, earliest/latest retained canonical Printing dates, finishes, languages, explicit
treatment and promotional fields, and evidence coverage.

Reprint count means **`max(total distinct canonical printings - 1, 0)`**. The current canonical
snapshot contains one MB2 Printing for each pilot Card, so every bounded count is zero. This does
not contradict the retained source assertion that each MB2 record is a reprint: the canonical
repository does not contain the older Printing identities. Set membership codes are not fabricated
into Printings. Consequently all ten histories are known within their MB2 boundary but incomplete
globally, and confidence remains null because arithmetic success is not evidence completeness.

The Phase 132 unknown remains byte-unchanged and is named in `supersedes`; active printing-history
queries return only the later known fact, while full-history queries return both. Invalid subject,
predicate, reference, or recording chronology fails closed through the Phase 131 repository.
Printing count is not supply quantity. Reprint history alone does not establish scarcity,
collectibility, popularity, demand, deck usage, catalysts, historical price movement, price
direction, investment quality, or value. Unsupported archetype and catalyst queries remain
explicitly empty. The deterministic review is `data/reviews/phase-133/pilot-review.json`.

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
