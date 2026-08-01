# Canonical Query Layer

**Status:** Phase 125 complete. **Architecture:** v12 unchanged.

## Architecture

`CanonicalQueryService` is a read-only facade over `CanonicalQueryEngine`. The engine
loads the validated canonical repository and content-addresses its deterministic result
set; the service applies exact, normalized, game-agnostic predicates and returns one
stable `canonical-query-v1` envelope. It has no writer, provider, price, simulation,
recommendation, or AI dependency.

Supported Card predicates are canonical identifier, normalized exact name, type, color,
rarity, set, mana value, keyword, and legality. Printing queries support canonical and
promoted external identifiers, all Printings for a Card, and canonical finish, language,
rarity, collector-number, product-membership, release, identifier, and provenance fields
when those fields exist. Product queries expose the canonical Product, explicit promotion
and validation state, canonical membership, Cards, and counts. Collection queries expose
owned, duplicate, missing, unique Card/Printing, acquisition, and unresolved facts from an
immutable collection snapshot. The existing deck comparison exposes completion, owned,
missing, reusable, and excess quantities.

## Explainability and provenance

Every service response contains `answer`, `provenance`, `confidence`,
`canonical_identifiers`, and `snapshot_identity`. Confidence is the minimum explicit
confidence among returned facts; it is `null` when canonical evidence supplies none.
Provenance is copied from canonical evidence/assertion, acquisition, review, dataset, and
promotion lineage without synthesis. Snapshot identity is a SHA-256 content identity of
the complete query projection. Empty matches return `status: not_found`, an empty answer,
empty provenance, and null confidence rather than a guessed value.

## CLI

All commands emit sorted JSON:

```console
python -m mtglab --data-root data query card "Urza's Saga"
python -m mtglab --data-root data query card --set mb2 --rarity rare
python -m mtglab --data-root data query card --identifier magic.sol-ring --printings
python -m mtglab --data-root data query printing magic.mb2.1.en
python -m mtglab --data-root data query product mystery_booster_2
python -m mtglab --data-root data collection owned --snapshot SNAPSHOT_ID
python -m mtglab --data-root data collection unresolved --snapshot SNAPSHOT_ID
python -m mtglab --data-root data deck compare --snapshot SNAPSHOT_ID --deck DECK.json
```

## Limitations

The layer does not fuzzy-match, rank, recommend, infer, or turn `unknown_values` into facts.
Queries for canonical attributes not populated in the repository correctly return no
matches. Product release and printing finish/product fields are returned only where the
canonical record contains them. Collection missing Cards means canonical Cards absent from
the selected snapshot, not a recommendation or product-completion claim. There is no
pricing, market intelligence, network access, AI provider, or simulation.
