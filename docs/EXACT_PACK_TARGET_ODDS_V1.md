# Exact Pack Target-Odds V1

This read-only capability calculates **at least one target hit** under an admitted,
finite mathematical pack model. It does not establish physical collation, source
rights, authentic MB2 odds or production admission. Architecture v13, Decision 017
and [governance](GOVERNANCE.md) remain unchanged. No source is acquired, and the
full-corpus Comprehensive Rules HOLD remains in effect.

## Shared composition and evidence

The existing [simulator](PACK_SIMULATION_V02.md) owns admission. Its new
`inspect(product_id, pack_definition_id=...)` method exposes an immutable
`ValidatedPackComposition`. Both inspection and generation call the same admission
routine; all variants, including unselected ones, must pass the original rules.
Product/version/component membership, current known identities, explicit positive
weights, exact schema/model combinations, source correspondence, provenance and
finish eligibility remain required. The 32-slot, 1,024-card, 10,000-entry and
64-bit weight bounds are unchanged. Draws must be independent with replacement.
Other collation, sequencing, conditional slots and depletion refuse.

The view retains the original generator input identity and adds a separate
composition identity binding target-relevant catalog identities, Printing fields
and retained source records. Its byte-owned snapshot is immutable; `to_dict()`
returns an independently owned detailed view. It is bounded to 4 MiB. No private
query handle crosses into the probability consumer. Fresh inspection revalidates
current input; an existing view continues to describe its exact captured evidence,
not an assertion of current source freshness. No persistent cache or new canonical
authority is added. Fixture confirmations remain fictional declarations.

V0, V0.1 and V0.2 seeded generation, random-counter order, input identities,
report fields and golden JSON/text outputs are unchanged. Deck Draw-Access V1
remains the separate without-replacement calculation and retains its API/output.

## Closed request schema

`pack-target-odds-input-v1` accepts exactly these fields:

| Field | Contract |
| --- | --- |
| `schema_version` | Exactly `pack-target-odds-input-v1`. |
| `target` | Exactly `kind` (`card` or `printing`), exact `id`, optionally `finish_id` and/or `treatment_id`. String values are printable, nonempty, trimmed and at most 128 characters. |
| `pack_counts` | 1–32 distinct ascending integer counts, each 0–10,000. No booleans, floats or numeric-string coercion. |
| `independence` | Exactly `independent-identically-distributed-packs`, an explicit analytical assumption, not evidence of physical box independence. |
| `threshold` | Optional exact decimal string in [0,1], with a leading digit, no exponent/percent syntax and at most 18 decimal places; or exactly `numerator` / `denominator` unsigned decimal **strings**, each at most 128 digits. Denominator must be positive and numerator at most denominator. |
| `box` | Optional, only with a threshold: exactly positive integer `packs_per_box` (1–1,000) and `basis: "HYPOTHETICAL_CALLER_DECLARATION"`. |

No unknown fields are accepted. JSON is strict UTF-8, at most 32,768 bytes, with
duplicate keys, nonfinite numbers, malformed/deep JSON and unsupported types
rejected. Threshold forms normalize to the same reduced rational; no clock or
seed is used. Reports are compact sorted-key UTF-8 JSON and at most 65,536 bytes.
`PackOddsError` returns an explicit refusal code and reason, without partial odds.
Composition admission continues to use the owning `PackSimulationError` contract.

## Targets and limitations

Card targets resolve the union of eligible Printings through exact admitted
identity joins. Each outcome contributes its weight once, including when several
finishes or Printings represent the same Card. Printing targets use their exact
identity. Unknown, ambiguous, superseded or unresolved targets refuse. A known
target absent from a complete admitted pool has model probability zero.

Finish-specific probabilities require finish-aware outcomes and existing explicit
finish evidence; legacy Printing-only models cannot supply them. Treatment
restrictions require an explicitly retained, source-bound, confirmed/promoted
Printing treatment field. V1 accepts at most one fixed treatment property per
relevant Printing, or an explicitly evidenced empty list. Missing fields, unknown
values, unreviewed assertions and multiple treatment declarations refuse instead
of inventing allocation weights. This conservative limit also excludes multiple
traits whose joint interpretation has not been modeled. Sheet names, rarity,
frames and product names never infer finish/treatment eligibility.

Field-source and exact-identity validation remain independent of permission,
authentication and semantic authority. These reports are non-production model
analysis, not source-use clearance or real-card gameplay understanding.

## Exact mathematics

For variant v and slot s, let t_vs be matching outcome weight divided by total
pool weight, and d_vs the slot draw count. The admitted model gives:

```text
slot_miss       = (1 − t_vs)^d_vs
variant_miss    = product_s slot_miss
single_pack_hit = 1 − sum_v (variant_weight_v / total_weight) × variant_miss
P(N packs)      = 1 − (1 − single_pack_hit)^N
```

Complete variant probabilities are mixed **after** computing their slot products.
Pools are not averaged across variants; marginal variant probabilities are not
multiplied. The final formula is conditional on independently drawing a new pack
and variant from the same model each time. A caller declaration cannot override
unsupported dependent collation. Zero packs always give zero, even for certain
single-pack hits. No SHA-ticket enumeration, sampling or Monte Carlo is used.

Integer weights and `Fraction` arithmetic remain exact. Each retained rational
numerator/denominator is bounded to 1,000,000 bits; estimated exponentiation work is capped at 4,000,000
bits cumulatively, with repeated sample sizes cached only within one assessment.
The search bound is 10,000 packs. Computation or output budget exhaustion yields
`RESOURCE_LIMIT`; it is never labeled a mathematical impossibility.

Exact fractions use versioned `hexadecimal-integers` strings (for example, 1/10
is numerator `0x1`, denominator `0xa`), avoiding JavaScript precision loss and
Python's decimal integer-string length restriction without changing process-wide
settings. Presentation uses 12 decimal places, ROUND_HALF_EVEN, implemented with
integer quotient/remainder arithmetic. It does not rely on a fixed decimal
precision. `is_zero` and `is_certain` describe the **exact** result: a tiny nonzero
fraction may display `0.000000000000` while `is_zero` remains false.

## Minimum packs and boxes

The solver compares exact rationals, doubles a bracket up to 10,000 and then
uses binary search. A `REACHED` result supplies N and exact probabilities proving
P(N) ≥ threshold and, for N > 0, P(N−1) < threshold.

- Threshold zero: N = 0.
- p = 0 with a positive threshold: `IMPOSSIBLE_ZERO_PROBABILITY`.
- p = 1 with a positive threshold: N = 1.
- 0 < p < 1 with threshold one: `NO_FINITE_SOLUTION`.
- A threshold still unmet at 10,000: `NOT_REACHED_WITHIN_BOUND`, not impossible.
- No supplied threshold: `NOT_REQUESTED`.

Optional box arithmetic returns ceil(N / packs_per_box), corresponding packs and
surplus, under the **hypothetical** count only. It does not calculate box odds,
correlations, guarantees or mixed compositions. A caller `verified=true` flag is
rejected; evidence-based verified box-count admission is intentionally omitted.

## Public API and CLI

```python
from pathlib import Path
from simulation import load_pack_simulator
from probability.pack_odds import assess_pack_target

view = load_pack_simulator(
    'pack_fixture', data_root=Path('tests/fixtures/pack_simulation_v02/data')
).inspect('fictional-pack', pack_definition_id='fictional-variants')
request = {
    'schema_version': 'pack-target-odds-input-v1',
    'target': {'kind': 'printing', 'id': 'pack_fixture.tst.1.en', 'finish_id': 'foil'},
    'pack_counts': [0, 1, 7],
    'threshold': '0.5',
    'independence': 'independent-identically-distributed-packs'
}
report = assess_pack_target(view, request)
```

Save that request as JSON and run:

```console
PYTHONPATH=src python -B -m probability pack-target-odds --input request.json --game pack_fixture --data-root tests/fixtures/pack_simulation_v02/data --product-id fictional-pack --definition-id fictional-variants
```

`--input -` reads bounded stdin. Valid output is JSON, exit 0; refusal is JSON
with `status: "REFUSED"`, exit 2. No repository files are written.

The existing **fictional** 90/8/2 model gives the example foil target exactly
79/800 = `0.098750000000`; seven independently modeled packs reach 50%.
A separate fictional one-slot, 1-to-9 target/non-target benchmark gives p = 1/10:
P(6) = 0.468559 and P(7) = 0.5217031, proving minimum N = 7.
These numbers are not MB2 manufacturing frequencies. Current canonical MB2
remains `NOT_READY_FOR_SIMULATION`; odds admission preserves that refusal.

Reports bind Product/ProductVersion/PackDefinition identities, original simulator
model/input identity, query snapshot, composition and resolved-target identities,
request, assumptions and source references. SHA-256 uses versioned domains plus
a NUL separator and canonical JSON; report identity excludes only itself.
The complete evidence remains inspectable through the immutable view, without a
parallel repository. Checksums do not authenticate a source or reviewer.

Expected copies, multiple-copy distributions, physical box collation, manufacturing
inference, provider ingestion, source permission changes, CR processing, gameplay,
strategic intelligence, AI integration and canonical promotion are excluded.
No follow-on work is authorized by this capability.
