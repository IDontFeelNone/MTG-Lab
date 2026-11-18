# Supplied Deck Consistency Comparison V1

This read-only workflow derives Card quantities from one or two complete supplied
deck configurations and delegates exact draw-access mathematics to
[Deck Draw-Access V1](EXACT_DECK_DRAW_ACCESS_V1.md). It compares access events, not
mana feasibility, casting, combo success, legality, strategic superiority or win
rates. Architecture v13, [governance](GOVERNANCE.md), permissions and the full-corpus
Comprehensive Rules HOLD are unchanged.

## Input and identity boundary

`supplied-deck-consistency-input-v1` is a closed object with exactly
`schema_version` and `decks` (one or two, in baseline/candidate order). Each deck
contains exactly:

| Field | Contract |
| --- | --- |
| `deck_id` | Unique caller identifier, printable, trimmed, 1–128 characters. |
| `identity_authority` | Exactly `CALLER_DECLARED`. Even a real-looking UUID or canonical ID is not independently verified here. |
| `complete` | Exactly JSON `true`: the caller declares the selected population complete. This is not authenticated evidence or format validation. |
| `draw_population` | Exactly `section` and integer `declared_size` (1–120). The selected row quantities must sum to that size. |
| `entries` | 1–512 objects, each exactly `card_id`, `section`, `quantity`. Quantities are integers 0–120, excluding booleans, floats and numeric strings. |
| `groups` | 1–3 objects, each exactly `group_id`, `members` and `minimum`. Group IDs are distinct, printable/trimmed, 1–64 characters. Members are 1–120 exact Card identity strings; minima are integers 0–120. |
| `schedule` | 1–21 observations, each exactly `label` and `cards_seen`. Labels are unique, printable/trimmed, 1–80 characters. Counts are cumulative, nondecreasing, from 0 through min(20, selected size). |
| `assumptions` | Exactly `sampling: "uniform-without-replacement"`, `group_disjointness: "caller_declared"`. |

Card identity strings are printable, trimmed and 1–128 characters. No names,
aliases, display text, Printing joins or external data are interpreted. Unknown
fields, including canonical-verification flags, refuse. No canonical or private
collection reader participates, and no parallel canonical deck database is added.
This reuses the existing Card-quantity/section conventions without silently
reinterpreting `deck-requirement-v1`, its Printing policies or ownership reports.

Sections are exactly `main`, `sideboard`, `commander`, `companion`, or a named
`other:...` section, at most 48 characters. Exactly one declared section is
selected. No default, union, implicit sideboarding, commander inclusion or other
automatic population is supported. Explicitly selecting another section is only
a caller-defined analytical experiment, not permission to draw it in Magic.

Repeated rows aggregate by exact `(section, card_id)`. Each resulting quantity
must remain at most 120. Entries sort by section/identity; splitting or reordering
rows without changing quantities preserves report identities. Zero rows remain
explicit known identities with no copies. Rows in other sections never supply
group copies. Every group member must be declared in the selected population,
and membership must be disjoint, including zero-copy members.

`complete=true` plus a consistent size detects declared contradictions; it cannot
prove that a caller has truthfully listed an actual physical deck. Incomplete
declarations refuse rather than creating an unspecified remainder.

## Derivation and mathematical boundary

The selected quantities determine deck size and every group population. The
caller cannot supply a conflicting group-copy total. Nonzero member quantities,
group minima and the observation schedule form an ordinary `assess_draw_access`
request; the returned exact report is embedded unchanged.

A minimum can exceed the available group population in a valid supplied deck.
The event is then logically empty: each observation has exact probability 0/1,
status `IMPOSSIBLE_POPULATION_REQUIREMENT`, and the impossible groups are named.
`draw_access_report` is null in this case. The workflow does not clip minima,
invent copies or fabricate a successful V1 engine admission. This explicit empty
event boundary adds no independent combinatorial algorithm. All remaining exact
probabilities use the existing hypergeometric engine, including joint events
that are impossible because too few cards are seen. The older engine's strict
input validation and public reports remain unchanged.

## Comparison equivalence

The joint event is the sorted set of `(exact member identities, minimum)` group
definitions. Group labels alone are never evidence of equivalence. A direct
candidate-minus-baseline delta requires:

1. Identical event definitions, ignoring group labels/declaration order.
2. Identical selected section.
3. Identical full observation schedule, including labels and counts.
4. Identical supported sampling assumptions.

Deck sizes and quantities may differ: those are the configurations being compared.
Schedule-label mismatches conservatively abstain, even when numeric counts match.
There is no cross-configuration mapping in V1. Different targets, minima,
sections or schedules return both valid individual analyses and `ABSTAINED`,
explicit reasons and an empty differences array. One configuration returns
`NOT_REQUESTED`; equivalent configurations return `COMPARABLE`. No ranking follows.

Differences use exact rational subtraction, never rounded percentages. Fractions
are reduced decimal integer strings, with 12-place integer ROUND_HALF_EVEN display.
Signed deltas can be negative; a displayed rounded zero need not be exact zero.
Reports and inputs use sorted compact UTF-8 JSON and content-derived SHA-256 IDs.
No timestamp, randomness or mutable persistent state participates.

## API and working example

```python
from probability.supplied_deck import assess_supplied_decks, parse_supplied_decks

report = assess_supplied_decks(parse_supplied_decks(raw_utf8_json))
```

The complete fictional request and golden API report are retained in
[`tests/fixtures/supplied_deck_consistency_v1`](../tests/fixtures/supplied_deck_consistency_v1/).
They compare three versus four `caller:target` copies, filling the rest of each
60-card main population with `caller:other`; sideboard, commander and companion
rows are declared separately and excluded from main-deck sampling.

| Observation assumption | Three copies | Four copies |
| --- | --- | --- |
| Seven cards seen | 5397/17110 = 0.315429573349 | 38962/97527 = 0.399499625745 |
| Nine cards seen | 2679/6844 = 0.391437755698 | 15849/32509 = 0.487526531114 |

The report supplies exact differences and the normalized evidence for comparison.
Neither an observation label nor a positive difference establishes game timing,
casting feasibility or a stronger deck.

```console
PYTHONPATH=src python -B -m probability deck-consistency --input tests/fixtures/supplied_deck_consistency_v1/example-input.json
PYTHONPATH=src python -B -m probability deck-consistency --input tests/fixtures/supplied_deck_consistency_v1/example-input.json --format text
```

`--input -` reads stdin. JSON is the default; readable output shows deck sizes,
selected sections, exact probabilities, comparison/refusal reasons and limitations.
The API raises `SuppliedDeckError`; the CLI emits its closed structured refusal
and exits 2 without partial analyses. Success exits 0. Existing draw-access and
pack-target-odds commands remain unchanged.

## Schemas, bounds and preservation

The packaged closed contracts are
[`supplied-deck-consistency-input.schema.json`](../src/schemas/v1/supplied-deck-consistency-input.schema.json)
and [`supplied-deck-consistency-report.schema.json`](../src/schemas/v1/supplied-deck-consistency-report.schema.json).
They can be checked directly with the existing JSON Schema dependency. These
analytical contracts do not register a new canonical record kind. Runtime
validation additionally checks quantities, identity membership, sums, schedule
consistency and comparison equivalence.

Output contains exactly version/status, normalized input and identity,
configuration analyses, comparison, bounds, authority/scope flags, limitations
and report identity. Configurations expose selected quantities, derived groups,
exact observations, impossible groups and the unchanged engine report or null.
Refusals expose exactly version, status, reason and a false gameplay-authority flag.

Raw and normalized inputs are bounded to 131,072 bytes; final JSON to 262,144
bytes including its newline. Duplicate JSON keys, invalid UTF-8/nonfinite values,
excessive nesting, arrays, quantities or output size refuse. No bound of the
original engine is enlarged. API inputs and prior reports remain detached.

An exact test-only successor adapter preserves original ledgers, historical
source bytes and older CLI reports. No source policy, admission gate, canonical
data, architecture, gameplay, pack simulation or ownership behavior is changed.
Mulligans, mana feasibility, automatic groups, strategic inference, external
source processing and AI integration remain excluded.
