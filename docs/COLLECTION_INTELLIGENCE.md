# Collection Intelligence Foundation

**Contract versions:** `collection-import-v1`, `collection-snapshot-v1`,
`deck-requirement-v1`. Collection intelligence is deterministic downstream user data;
it reads canonical Cards and Printings but never writes canonical state.

## Import and resolution

JSON imports are objects with `schema_version`, stable `collection_id`, `source`, and an
`entries` array. CSV uses the same entry field names. Each entry may contain
`printing_id`, an `external_identifiers` object (JSON text in CSV), `card_name`, positive
integer `quantity`, `finish`, `language`, `condition`, `acquisition_price`, ISO date
`acquisition_date`, `storage_location`, `notes`, and `provenance`. Blank, `unknown`, and
`null` values become explicit `null` values and are listed in `unknown_fields`.

Resolution priority is: (1) exact canonical Printing ID; (2) the intersection of exact
namespace/value external-Identifier matches; (3) case-insensitive Card-name review
fallback. Name fallback is not silent identity: zero matches are unresolved and multiple
Printings are ambiguous. Every result retains its row, candidates, evidence, reason, and
one of `resolved`, `ambiguous`, `unresolved`, `invalid`, or `duplicate_input_row`.
Reusing identical input produces an `exact_replay` result at snapshot persistence.
Only resolved rows participate in exact-printing calculations.

## Immutable snapshots and summaries

Snapshots bind collection identity, the source-byte SHA-256, canonical repository
digest, resolved and unresolved holdings, source provenance, explicit unknowns, and a
content digest. Canonical compact JSON and stable sorting make identical inputs and
canonical state byte-identical. An existing snapshot ID may be reused only for identical
bytes; conflicts fail closed. Verification recomputes the digest.

Summary reports quantities, unique Cards/Printings, duplicates, finish, language,
condition, set, rarity, unresolved outcomes, acquisition-cost coverage, and missing-value
coverage. Color reports `unknown` when canonical Card data has no color fact. Missing
acquisition prices are counted as missing and never treated as zero. `known_total` therefore
describes only priced holdings and carries no market-value claim.

## Deck requirements and completion

A deck document contains `schema_version`, `deck_id`, `format`, version or snapshot date,
`requirements`, `acceptable_printing_policy`, `substitution_policy`, and `source` provenance.
Each requirement declares a canonical `card_id`, positive quantity, `main` or `sideboard`,
and optionally an exact `printing_id` and policy. `any` allows copies of the Card across
Printings; `exact` allows only the declared Printing. Copies are allocated deterministically
and cannot satisfy both main deck and sideboard requirements.

For each requirement, comparison reports allocated owned, required, missing, excess and
reusable quantities plus complete/partial/missing status. Completion is
`100 * sum(min(available, required)) / sum(required)`. Potentially relevant unresolved
collection evidence is returned rather than hidden.

## Acquisition priorities

Priorities are price-independent. For each missing Card the score is:

`missing copies + completion-percentage points unlocked + 10 × shared decks + 5 × partial-ownership requirements + 3 × playset-completion opportunities − 2 × requirements with unresolved evidence`.

Every report exposes these components and the explanation; ties use canonical Card ID.
The score is a transparent completion aid, not a market or investment recommendation.

## CLI and storage boundary

```console
python -m mtglab --data-root data collection import --input collection.csv
python -m mtglab --data-root data collection verify --snapshot SNAPSHOT_ID
python -m mtglab --data-root data collection summary --snapshot SNAPSHOT_ID
python -m mtglab --data-root data collection duplicates --snapshot SNAPSHOT_ID
python -m mtglab --data-root data deck compare --snapshot SNAPSHOT_ID --deck data/deck_requirements/synthetic-phase-124.json
python -m mtglab --data-root data deck missing --snapshot SNAPSHOT_ID --deck DECK.json
python -m mtglab --data-root data deck acquisition-priorities --snapshot SNAPSHOT_ID --deck DECK.json
```

All output is sorted JSON. Imports, snapshots, and future retained reports belong under
`data/collections/`; requirements belong under `data/deck_requirements/`. None belong in
`data/canonical/`. No price provider, market feed, AI provider, simulation, or live deck
list is consulted.
