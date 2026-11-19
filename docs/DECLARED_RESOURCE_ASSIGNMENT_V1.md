# Declared Mana-Resource Access and Assignment V1

This is **hypothetical joint-access mathematics**, not Magic casting feasibility.
The API knows no Card facts, Oracle text, mana rules, timing or gameplay state.
It uses no catalog, source evidence, private collection or external service.
Existing [draw access](EXACT_DECK_DRAW_ACCESS_V1.md) and supplied-deck consumers retain
 their own contracts. The full-corpus Comprehensive Rules source-use HOLD remains
unchanged.

## Public interface

```python
from probability.resource_assignment import assess_resource_assignment
report = assess_resource_assignment(request)
```

```sh
PYTHONPATH=src python -B -m probability resource-assignment --input request.json
# --input - reads bounded UTF-8 JSON from stdin
```

The CLI emits canonical, sorted-key JSON plus a newline; successful exit is 0,
refusal is 2. The API raises `ResourceAssignmentError`; `error.as_dict()` returns
the same structured refusal. No partial probability is returned on refusal.
No file is written automatically. Input dictionaries remain unmodified.

## Closed input contract

```json
{
  "schema_version": "declared-resource-assignment-input-v1",
  "population_id": "caller:fixed-example",
  "complete": true,
  "population_size": 60,
  "cards_seen": 9,
  "resource_kinds": ["A", "B"],
  "demands": {"A": 1, "B": 1},
  "target": {"minimum": 1, "mode": "observe"},
  "classes": [
    {"copies": 4, "resources": [], "target": true},
    {"copies": 32, "resources": [], "target": false},
    {"copies": 12, "resources": ["A"], "target": false},
    {"copies": 12, "resources": ["B"], "target": false}
  ],
  "assumptions": {
    "sampling": "uniform-without-replacement",
    "availability": "all-observed-resources-simultaneously-available",
    "output": "one-unit-per-physical-copy",
    "identity_authority": "CALLER_DECLARED"
  }
}
```

All fields shown are required; unknown fields are rejected at every level.
Identifiers are printable, trimmed strings of 1–64 characters. Population size
is 1–120; sample size is 0–20 and cannot exceed population size. Class quantities
are nonnegative integers whose sum must equal the declared population size.
Boolean quantities and floats are rejected. `complete: true` is a caller premise,
not independently verified deck completeness. Omitted filler cards are not added.

There are zero through two distinct resource-kind identifiers; `demands` must
contain exactly those keys. Each demand is an integer from 0 through 3. A target
minimum is 0 through 4. A minimum exceeding available target copies is a valid
impossible event. Zero target minimum and zero demands are vacuous requirements.

There are one through five equivalence classes, including filler classes.
All physical copies in a class have identical resource memberships and target
membership. Duplicate equivalent rows must be explicitly aggregated by the
caller and are rejected, even if one row has zero copies. Zero-copy rows are
allowed and still count toward the class limit. Every resource membership must
be declared and distinct. Resource memberships, kinds and classes normalize
independently of declaration order. These are abstract labels, not canonical
Card identities or actual mana colors.

## Overlap and assignment semantics

Every physical copy contributes **at most one** unit to simultaneous resource
jobs. A flexible A-or-B copy may satisfy A **or** B, never both. Different valid
assignments of the same sample do not multiply that sample's probability.

* `observe`: require the target count in the sample; target observation consumes
  nothing. A target copy may also serve one compatible resource job.
* `reserve`: target copies fill separate target jobs. A physical copy assigned
  to a target job cannot also serve a resource job. Which eligible target copies
  are reserved is decided jointly with resource assignment, not greedily.

Every observed resource is assumed statically and simultaneously available.
Cumulative cards seen in a real game would not establish that availability.
Neither overlap mode is an interpretation of real Magic casting requirements.

## Exact method and safety

The selected reviewed approach streams class-count vectors, each summing to the
sample size. A vector selecting k_i of n_i equivalent copies has integer weight
`product(C(n_i, k_i))`. A bipartite augmenting-path matching decision checks
whether distinct selected copies cover all jobs. Successful weights are summed
once; the denominator is `C(population_size, cards_seen)`. Reduced fractions are
exact. There is no Monte Carlo estimate and no independence assumption between
target access and resources.

This ports the feasibility experiment's streamed vector/matching algorithm into
maintained code, without importing the disposable experiment. The alternative
Hall-signature DP was correct in the experiment but its expanding state table
was less predictable outside the small envelope. The production algorithm
stores only one count vector and matching at a time.

Before enumeration, a bounded DP counts the feasible unweighted vectors V.
With C classes, H observed cards and D assignment jobs (including reserved
target jobs), the deterministic work estimate is:

`V * (2*C + max(1,D)^2 * max(1,H))`.

V must be at most **10,000**, and estimated work at most **5,000,000** units.
The preflight DP uses at most 21 counters per layer and 5×21×21 additions.
D is at most 10; matching uses at most 20 source positions and 10 recursive
job placements; vector recursion depth is at most 5. There are at most 105
precomputed binomial weights, each bounded by C(120,20). No hand collection,
assignment collection or unbounded state cache is retained. The traversal's
prefix bookkeeping is bounded by the class depth per complete vector.
These are deterministic work limits, not a portable wall-clock guarantee.

The static shape bounds do not guarantee acceptance: a 120-card, 20-observation,
five-large-class request has 10,626 vectors and is refused. A smaller vector
count can separately exceed the matching-work budget. Preflight applies even
when an event might otherwise short-circuit to zero. No interrupted or refused
calculation is reported as an impossible event.

Input JSON is limited to 8,192 UTF-8 bytes and reports to 16,384 bytes. Duplicate
JSON keys, malformed UTF-8 and nonfinite numbers are rejected. Only the declared
bounded structures are traversed by the API. No filesystem access occurs in the
analytical module; the CLI reads only its explicitly selected input.

## Report and refusal contract

`declared-resource-assignment-report-v1` has status `CALCULATED`, normalized
`input`, content-derived `input_id` and `report_id`, the method version, integer
`favorable_physical_hands` and `total_physical_hands` strings, and `probability`.
The probability includes reduced integer numerator/denominator strings and a
12-place round-half-even decimal. `nonzero` and `event` preserve the distinction
between a very small nonzero result rounded to zero and an impossible event.
Use fractions for comparison; the decimal is presentation only. Computation
counts and limits are deterministic report fields. All reports explicitly deny
real gameplay authorization and retain limitations.

Refusals have status `REFUSED`, a reason and one of:

* `INVALID_INPUT`: malformed, incomplete or contradictory declarations.
* `UNSUPPORTED_SCOPE`: unsupported version, semantics or numerical scope.
* `RESOURCE_BUDGET_REFUSAL`: deterministic exact-work/output limits exceeded.

A valid zero remains `CALCULATED` / `IMPOSSIBLE` with exact probability 0/1.
No refusal is a probability and no approximate fallback exists.

## Reviewed hypothetical comparison

For 60 cards, nine observed copies, four nonresource targets, 32 fillers,
and simultaneous A=1 / B=1 demands in observe mode:

| Resource composition | Exact joint-access probability | Approximate percentage |
| --- | --- | --- |
| 12 A-only + 12 B-only | 1334229119 / 3695785665 | 36.101366% |
| 8 A-only + 8 B-only + 8 A-or-B | 82162489 / 194515035 | 42.239660% |

The exact difference is **226858172 / 3695785665**, approximately **6.138294
percentage points**. Both configurations have identical target-only access.
This comparison establishes no casting probability, win rate, superior deck or
competitive recommendation. Reproducible input/report examples are in
[the focused fixtures](../tests/fixtures/resource_assignment_v1/).

## Exclusions and research use

A researcher can test how explicit resource-flexibility assumptions change an
exact joint-access hypothesis, or challenge a hypothesis that double-uses a
physical copy. The tool cannot establish the truth of those premises for real
cards. Real-card use would separately require reviewed identity, mechanics,
availability and procedural evidence and the relevant authorization.

No Oracle interpretation, actual mana generation/payment, turns, casting,
strategic classification, deck optimization, AI orchestration, ingestion,
canonical admission or source-use permission is added. Existing analytical,
collection, gameplay and historical evidence contracts are preserved.
