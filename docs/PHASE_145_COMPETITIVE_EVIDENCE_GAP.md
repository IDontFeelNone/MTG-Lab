# Phase 145 — competitive and actual-play evidence gap assessment

## Decision and frozen baseline

Phase 145 is acquisition design only. Architecture v12 is frozen. Repository inspection confirms
exactly ten pilot Cards (Brainstorm, Command Tower, Counterspell, Goblin Charbelcher, Goblin King,
Sol Ring, Swords to Plowshares, Treasure Cruise, Walking Ballista, and Wishclaw Talisman), 140
retained Card Intelligence facts, ten active Phase 136 `printing.reprint_history` facts, ten Phase
142 Scryfall `value_driver.demand` facts, and twenty Phase 144 facts (ten each of
`demand.deck_inclusion` and `format.usage`). It also confirms 956 immutable MB2 observations in two
retained Scryfall acquisitions and active opt-in `card-value-explanation-v4` behavior.

The Phase 143 MTGJSON artifact is immutable. Its 3,004-file denominator describes provider-curated
deck-product files; it is **not** an event, match, player, tournament, or competitive population.
Scryfall EDHREC rank, prices, and printing counts remain separate evidence classes.

## Retained-evidence census

A path, filename, JSON-key, and semantic inspection of `data/` found **zero** retained tournament
decklists, competitive event records, placements, event sizes, match results, or actual-play
competitive usage snapshots. Incidental words such as “event” in product or rules material do not
change that result. Phase 143 contains board membership and literal provider labels only. Therefore
there is no existing competitive evidence to admit and Phase 145 creates no production facts.

## Provider assessment

Network research was attempted on 2026-08-11. Both the browsing service (HTTP 401) and direct HTTPS
requests through the environment proxy (HTTP 403) failed. The assessment consequently fails closed:
the following are candidates, not verified endorsements.

| Candidate | Potential strength | Unresolved blocker |
|---|---|---|
| TopDeck.gg API | Machine-readable tournaments, standings and decklists may provide stable event/deck identities and bounded queries. | Current API contract, attribution, redistribution/retention rights, identity stability, coverage, pagination and denominator semantics could not be verified. |
| Melee | Established tournament platform and provider-supplied event/results/decklist fields. | No verified supported public bulk/API contract or permission to retain and redistribute a projection; completeness and stable identity are unknown. |
| Wizards / Magic.gg | First-party event reporting is authoritative for records it explicitly publishes. | Pages are not known to form a complete stable machine-readable dataset; retention, extraction, revisions and denominator completeness are unverified. |
| MTGTop8 / MTGGoldfish | Established public deck/event presentations. | Machine access, licensing, reproducible snapshot boundaries and population completeness are unverified; displayed percentages must not be imported as valid denominators. |

The one bounded pilot path recommended for post-merge investigation is **TopDeck.gg**, solely because
its advertised API shape is the best prospective fit for deterministic event/deck records. This is a
conditional acquisition design, not authorization. A human must first capture and approve the
then-current API documentation and terms, obtain permission if the terms do not explicitly allow
retention, and verify stable identities, pagination, rate limits, and denominator semantics. If any
gate fails, acquire nothing; do not silently fall back to scraping another provider.

## Minimum evidence contract

`card-competitive-evidence-v1` is an external evidence-envelope contract, not an Architecture v12 or
canonical model change. It requires provider and source-dataset identity; endpoint; dataset and
retrieval timestamps; exact source byte count/digest; licensing review; retention boundary;
completeness and provenance; explicit unknowns; and an exact digest over canonicalized projected
records. Each record binds canonical game/Card identity to a provider source-record/deck identity and
records nullable event identity/date, format, provider-supplied deck/archetype labels, placement,
literal result, mainboard and sideboard copies, and event size. Player identity is deliberately
forbidden in v1: it is unnecessary for Card-level counts and adds privacy/retention risk.

Null means provider-absent or unretained, and the corresponding field must be named in explicit
unknowns. Zero means observed zero and must never substitute for unknown. Provider archetype and deck
names are copied only when explicit; no classifier or inferred archetype is allowed.

## Literal metrics and denominator semantics

After separate manual admission approval, a retained snapshot could literally support only:

* count of distinct retained source deck records containing a Card;
* sum of retained mainboard, sideboard, or combined copies where those counts are known;
* count of distinct retained event identities and dated qualifying events;
* count of retained placements meeting an explicitly stated finish predicate (for example,
  placement 1–8), never the ambiguous phrase “top finish” by itself;
* provider-supplied format, deck-name, or archetype labels; and
* counts or fractions relative to the exact retained provider population only when the provider
  supplies a complete, reproducible denominator under the same filters and snapshot.

The deck denominator means all provider deck records satisfying the recorded query/filter, not all
decks played. The event denominator means distinct provider event identities satisfying the recorded
qualifying-event definition, not all events. An event-size value is a property of one event and is
not either denominator. With an absent or incomplete denominator, no metagame share may be stated.
Deck records are not matches: no win rate is available without complete, linked match/result data.

Unsupported claims include “competitive staple,” “Tier 1 card,” popularity or quality scores,
metagame share without a valid denominator, win rate without adequate matches, comparative ranking,
future demand, expected price movement, valuation, momentum, investment quality, inferred
archetypes, and recommendations.

## Bounded acquisition, replay, rollback, and admission

Once licensing is approved, one operator-selected, immutable TopDeck.gg response window should cover
the ten exact pilot Card UUIDs, one explicitly named format, and one closed date interval. Retain only
the raw response (outside Git if redistribution forbids it), its digest/size and request manifest,
plus the at-most-ten-Card bounded projection. Do not commit a full corpus. Pagination must be
exhausted deterministically and the provider population definition retained. Manual review must
precede any facts, explanations, or production admission.

The validator is intentionally local-only. Exact snapshot ID and byte/digest replay is idempotent;
same identity with different bytes must fail. A failed run removes only files it created before
manifest publication. A reviewed retained snapshot is immutable; rollback removes a newly proposed
snapshot/projection together and never edits canonical data, market evidence, Phase 135/142/143/144
evidence, historical facts, or prior explanations. No workflow or network acquirer is enabled in
Phase 145 because licensing and API behavior could not be verified.

## Post-merge operation

Manually review TopDeck.gg's current official API documentation and legal terms, record dated copies
and provider contact/permission where needed, and complete a denominator/pagination probe without
retaining deck data. Only a separately reviewed phase may enable one snapshot acquisition. Stop
before Phase 146.
