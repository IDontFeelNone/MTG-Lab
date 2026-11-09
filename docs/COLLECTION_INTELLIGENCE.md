# Collection Intelligence Foundation

## Collection audit and personal review history

Canonical baseline `15e19b84701dd47970a948485683f73a687be9d2` includes merged PR #169's production identity resolver and source-replayed acquisition repair. The [bounded collection audit pilot](COLLECTION_AUDIT_PILOT.md) now projects the existing immutable ownership snapshots, preserving source-byte provenance, exact identities, physical organization, unresolved quantities, and append-only personal Card assessment history. It adds no parallel ownership store and leaves typed Collection Engine operations unchanged.

Organization annotations reuse existing row provenance. Storage classification and location remain independent of review status or strategic suitability. Current and historical assessment subjects must reproduce their retained import sources through the canonical resolver before projection or persistence. Snapshot drift fails closed; old source and history files remain retained for explicit reconciliation. Personal assessments do not approve canonical facts, pending roles, or acquisition advice.

The isolated fixture declares 360 fictional copies, including duplicates and unresolved identities. No complete real collection is retained: six partial unverified opening reports account for 90 positions only. The real import requires an exhaustive source-bound inventory and verifiable prior reviews. Historical acquisition-pilot boundaries below describe that milestone's original scope; the audit adds only the bounded functionality described above.

## Current production identity resolution

The bounded [Card acquisition pilot](CARD_ACQUISITION_PILOT.md), based on merged PR #168 at `3cf6ad35fcb54ed5a4b640e36af6fa2ecf99a747`, repairs `CanonicalCollectionResolver` to consume the existing canonical query projection. Its current census is 384 production Cards and 913 production Printings plus 15 legacy seed Cards/Printings. Exact production Printing resolution preserves dimensions and compact source/audit references; snapshot identity covers promoted canonical state and provenance. Name ambiguity and contradictory production identity/dimension inputs remain explicit.

This repairs the Collection Intelligence import/snapshot resolver available for production identity imports. The acquisition pilot independently validates its direct source-bound ownership declaration against the same canonical query projection. The separate typed `CollectionService` repository path is unchanged. No real user collection was retained by that milestone, and its complete ownership input remains synthetic. Its original exclusions of sorting/reassessment history are superseded only by the bounded audit described above; production collection management and automatic reassessment remain outside the pilot.

The acquisition adapter uses direct acceptable-copy accounting and does not call deck allocation. The separately authorized mixed-Printing repair below corrects deck completion; it does not change that adapter or authorize purchase advice. Collection valuation remains descriptive and does not validate comparable current all-in acquisition offers.

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
Printings; `exact` allows only the declared Printing belonging to that Card.
One shared remaining inventory, indexed by Printing ID, prevents a resolved
physical copy from satisfying more than one requirement in a deck comparison.
All exact requirements allocate before flexible requirements, including exact
sideboard requirements before flexible main-deck requirements. Within each policy,
priority follows report order: section, Card ID, Printing ID, then canonical
requirement JSON bytes to resolve otherwise equal keys. Flexible allocation consumes
eligible remaining Printings in ascending Printing-ID order. This is deterministic
copy accounting, not a general optimizer or a statement of deck legality/value.
Quantities must be positive integers and policies must be `any` or `exact`.
Missing, ambiguous, invalid and duplicate-input rows do not create owned copies.

The regression is one owned copy and two requirements (one flexible, one matching
exact): previously two allocations and `100.00%`; corrected one allocation, one
missing copy and `50.00%`. Exact priority avoids spending a scarce exact match on
a flexible requirement when another Printing can satisfy it. Input row order and
inventory dictionary order do not change the result. Public field names/schema,
snapshot identity/provenance, unresolved warnings and acquisition-priority formula
remain unchanged. Requirements are returned in report order, not allocation order.

For each requirement, comparison reports allocated owned, required, missing, excess and
reusable quantities plus complete/partial/missing status. Completion is
`100 * sum(min(available, required)) / sum(required)`. Potentially relevant unresolved
collection evidence is returned rather than hidden.

`owned_quantity` is allocated to this requirement, and `missing_quantity` is its
remaining need. The formerly ambiguous `excess_copies` and `reusable_owned_copies`
both describe eligible copies left **after the entire deck comparison**, excluding
every copy already allocated to any other requirement. For an exact row that is
the remaining matching Printing; for a flexible row it is the remaining Card pool.
These are overlapping views of shared leftover inventory, not quantities to sum
across rows or copy reservations for another deck. A single valid uniform-policy
requirement retains its previous surplus; repeated/mixed rows no longer claim
copies consumed elsewhere. Separate deck comparisons remain independent views
of the supplied collection, with no persistent reservation or ownership mutation.

Historical design/source packages remain immutable. Their tests use an exact,
test-only reversible adapter for this one authorized function replacement; both
current whole-file and reconstructed historical bytes are pinned. No source file,
permission, report, workflow or arbitrary future edit is exempted. This repair
does not change the separate generic evidence-handoff validator or any gameplay,
market, strategic or reviewer-authorization capability.

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
