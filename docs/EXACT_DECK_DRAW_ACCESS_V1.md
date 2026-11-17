# Exact Deck Draw-Access Probability V1

This is an exact, non-executing mathematical analysis of caller-declared deck
counts. It calculates access to specified groups, including a declared opposing
answer group. It establishes neither real Card facts nor strategic suitability,
and reads no source-dependent Card data. Architecture v13 and Decision 017,
[governance](GOVERNANCE.md), source-use restrictions and the full-corpus CR HOLD
are unchanged. This is not an implementation of full Deck Intelligence.

## Input contract

`deck-draw-access-input-v1` is a closed JSON object with exactly:

- `schema_version`: that version string.
- `deck_size`: integer 1–120, including all ungrouped cards.
- `groups`: 1–3 objects with distinct `group_id` labels, integer `copies` and
  integer `minimum`. Copies are 0–deck_size; minimum is 0–copies. Group copy
  totals cannot exceed deck_size. A zero minimum imposes no constraint.
- `schedule`: 1–21 objects with distinct `label` strings and cumulative
  `cards_seen` integers from 0 to min(20, deck_size). Counts must be
  nondecreasing; different labels may describe the same count. List order is
  preserved. Labels such as “Turn 3” are assumptions supplied by the caller.
- `assumptions`: exactly `sampling: "uniform-without-replacement"` and
  `group_disjointness: "caller_declared"`.

Each group may also supply `members`, a list of exact, case-sensitive caller
`card_id` strings and positive integer `copies`. Member copies must sum to the
group copies; each identity may appear only once across the entire request.
This distinguishes an individual identity from its analytical group. For example,
two distinct identities with two copies each may constitute one four-copy group.
The caller, not the engine, declares their interchangeability. Names and abilities
are never interpreted. Identifiers are not resolved or admitted as canonical.

When members are omitted, disjointness is an explicit caller assertion that cannot
be independently checked. In mixed requests, supplied identities are checked
against all other supplied identities; unspecified membership stays unverified.
All group populations must still be pairwise disjoint for the mathematical model.
Overlap analysis is unsupported, not approximated.

Group labels are at most 64 characters, member identities 128 and schedule labels
80. Strings must be nonempty, printable and have no surrounding whitespace.
Only integer types are accepted for quantities; booleans, floats and numeric
strings reject. Duplicate JSON keys, unknown fields, nonfinite numbers, invalid
UTF-8 and input over 32,768 bytes reject. Output is bounded to 65,536 bytes.

## Mathematical definition

Let N be deck size, c_i each disjoint group size, m_i its required minimum,
n cards seen and r = N − sum(c_i) the ungrouped population. Every n-element
subset of the physical deck is assumed equally likely. The probability that
**all** requirements hold is:

```text
sum [ product_i C(c_i,k_i) * C(r,n-sum(k_i)) ] / C(N,n)
```

The sum includes k_i from m_i through min(c_i,n), with
0 ≤ n − sum(k_i) ≤ r. Python integer combinations and a reduced rational
`Fraction` give an exact result. Group-access probabilities are dependent;
their individual probabilities are never multiplied. There is no Monte Carlo,
seed, inferred shuffle or gameplay execution.

An event can be impossible even for a valid request: two groups each requiring
two cards have probability zero when only three cards are seen. A minimum greater
than its declared population is rejected as an inconsistent requirement instead.
Drawing all required cards or a zero-threshold event can give certainty.

At most 21³ count tuples are considered per distinct sample size, with at most
21 schedule entries. Repeated sample sizes reuse the calculation within that
assessment. There is no persistent state or cache.

## Public API and CLI

Use the existing probability package; no canonical deck repository is added:

```python
from probability.draw_access import assess_draw_access, canonical_json

request = {
    "schema_version": "deck-draw-access-input-v1",
    "deck_size": 60,
    "groups": [{"group_id": "target", "copies": 4, "minimum": 1,
                "members": [{"card_id": "caller:fictional-target", "copies": 4}]}],
    "schedule": [{"label": "Opening hand", "cards_seen": 7},
                 {"label": "Turn 3", "cards_seen": 9},
                 {"label": "Turn 4", "cards_seen": 10}],
    "assumptions": {"sampling": "uniform-without-replacement",
                    "group_disjointness": "caller_declared"}
}
report = assess_draw_access(request)
print(canonical_json(report))
```

Save a request as UTF-8 JSON and run either:

```console
PYTHONPATH=src python -B -m probability draw-access --input request.json
PYTHONPATH=src python -B -m probability draw-access --input - < request.json
```

This bounded module CLI follows existing Python/argparse/JSON interfaces and keeps
historical `mtglab` entry points unchanged. It reads only the explicit input or
stdin and writes JSON to stdout, not repository data. Invalid input returns exit
2 with `INVALID_DRAW_ACCESS_INPUT`; no partial result or positive report appears.
`DrawAccessError` is the public API's explicit input-validation exception.
`parse_draw_access` performs strict bounded JSON parsing;
`validate_draw_access` returns an independently owned normalized request.

## Results, identities and examples

`deck-draw-access-report-v1` includes the normalized input, method version,
input/report identities, ordered results and limitations. Groups and members
sort by exact identity; schedule order is retained. SHA-256 identities use compact,
sorted-key UTF-8 JSON with a versioned domain plus a NUL separator. The report ID
hashes all report fields except itself. Weights, timestamps, authentication and
source citations are not invented. Hashes establish content identity only.

Each probability contains reduced `numerator` and `denominator` as decimal
**strings**, avoiding JSON client integer-precision loss. `decimal` is a probability
from 0 to 1, rounded to 12 places using ROUND_HALF_EVEN in an isolated 80-digit
decimal context. The rational remains authoritative; presentation is not an
uncertainty estimate. Identical inputs yield identical JSON, without a clock.

- Four targets in 60 cards, at least one in seven:
  `1 − C(56,7)/C(60,7)`, presented as `0.399499625745`.
- Two one-copy groups in four cards, requiring one of each in two cards:
  `1/6`, presented as `0.166666666667`; multiplying the marginal odds would
  incorrectly give `1/4`.
- A declared opposing answer group uses exactly the same mathematics. Access
  does not establish whether the answer can be cast or works against anything.

## Non-goals and preservation

No mulligans, play/draw inference, generic draw effects, mana generation/payment,
casting feasibility, combo execution, matchup win rates, opponent strategy,
format legality, tier classification, synergy detection, real-card execution,
AI integration, source ingestion or CR processing is implemented. Cards seen
are not necessarily still in hand. No permission, admission or execution gate
changes, and no future extension is authorized by this document.

Historical runtime and evidence files remain unchanged. Test-only compatibility
recognizes only the two exact new source files and reverses exact successor
edits to named preservation tests/helpers. Existing hashes and historical
assertions remain intact; unknown files or altered pinned additions fail closed.
