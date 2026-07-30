# Collection Engine v1

The Collection Engine is the ownership layer between canonical/observed facts and future analytics. A `Collection` is an immutable aggregate of `OwnedCard`, `Acquisition`, `InventoryLocation`, and future-ready `DeckAssignment` values. Service operations return a new aggregate rather than mutating history in place.

## References and boundaries

Every owned entry uses a canonical printing ID; the service verifies that ID through the canonical repository and never resolves a raw card name. An optional observation ID preserves the route from a pack-opening observation to the owned copy without making observations the source of canonical identity. Acquisitions independently record pack openings, single purchases, trades, gifts, or manual entry, including an optional canonical product ID and extensible metadata.

Locations are logical, user-defined values. Suggested kinds include binder, deck, trade binder, long box, display, sealed product, and unknown, but the model intentionally does not restrict this vocabulary.

## Operations and analytics

`CollectionService` adds, removes, moves, splits, and merges quantities, queries a printing's ownership, and produces deterministic summaries. Summaries include total quantity, unique printings, duplicate copies beyond the first, and finish, acquisition, and location breakdowns. Merging is allowed only when printing, acquisition, location, observation, condition, language, and finish match, preventing provenance loss.

The CLI persists a local JSON aggregate:

```console
python -m mtglab.collection add alpha.printing --quantity 2 --finish foil
python -m mtglab.collection import owned-cards.json
python -m mtglab.collection summary
python -m mtglab.collection move OWNED_CARD_ID trade_binder --quantity 1
```

## Future integration

Market snapshots can later join to owned entries by canonical printing ID and finish, but v1 performs no pricing, valuation, or expected-value calculation. AI reasoning can later consume deterministic collection summaries and explicit provenance. It must remain downstream: AI output does not alter canonical identity or ownership records. Deck assignments reserve an allocation shape only; legality and optimization are outside this engine.
