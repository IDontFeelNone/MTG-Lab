# Pack Simulation V0.1 — explicit finish outcomes

This is a generic, read-only single-pack extension to [V0](PACK_SIMULATION_V0.md).
It does not simulate authentic Mystery Booster 2 collation. All examples below
are fictional supplied models, outside production canonical data. Architecture
v13 and Decision 017 remain unchanged; no source clearance, canonical promotion,
reviewer authentication, physical collation accuracy or gameplay authority follows.

## Compatible model extension

The existing `Printing.finish_ids` and canonical `Finish` identity are reused.
No second Printing identity or foil boolean is introduced. A v3 Print Sheet entry
requires exactly `printing_id`, `finish_id` and a positive integer `weight`.
The v2 sheet schema remains unchanged. Product, ProductVersion, PackDefinition
and Slot stay v2. An explicit PackDefinition metadata value opts in:

```json
{"simulation_model":"independent-finish-weighted-with-replacement-v1"}
```

This model requires v3 sheets and returns `schema_version` and
`simulator_version` = `pack-simulation-v0.1`. Each slot contains `outcomes`,
with explicit Printing/Finish objects, **not** `printing_ids`. The existing
`VERSION`/`MODEL` exports retain their V0 values; new `FINISH_VERSION` and
`FINISH_MODEL` exports identify the opt-in extension. There is no implicit upgrade.
A V0 pack referencing a v3 sheet, or a V0.1 pack referencing a v2 sheet, refuses.

Typed SheetEntry adds optional `finish_id`. An absent legacy value is omitted
from query serialization, preserving existing V0 snapshot/input identities.
Native v3 sheets retain their schema version through the existing compatibility
reader. Canonical relationships validate exact Printing/Finish membership and
reject duplicate pairs. Multiple finishes for one Printing are allowed only when
that Printing explicitly declares those finishes and the Finish records exist.

The simulator additionally requires a native v3 Printing's explicit `finishes`
list and live `/finishes` assertions to match it exactly, refer to that Printing,
be promoted, declare verified/confirmed status, and use a resolved evidence class.
Their existing source records must declare confirmed status. Missing, provisional,
conflicting, foreign or unsupported finish evidence refuses. These checks validate
supplied model evidence; fixture status labels are not authenticated real-world
observations or permission grants. Finish is never inferred from a name, frame,
rarity, sheet or product. Knowledge-object unknown finishes are not eligible.

## Sampling and provenance

V0's SHA-256 counter/rejection algorithm is unchanged. V0.1 sorts entries by
`(printing_id, finish_id)` and assigns exact integer intervals with the supplied
weights. Draws remain independent, **with replacement** across and within slots.
Slot ordering follows the pack; draw ordering follows the counter stream. All
V0 limits remain: 32 slots, 1,024 cards, 10,000 pool entries, weights/total and
seed bounded by 2^64-1. No float probabilities or uniform defaults.

One owning query/catalog admission serves the complete pack. Printing raw records,
Finish query evidence and confirmed finish source records join the deduplicated
input evidence. V0.1 uses domain `pack-simulation-input-v0.1`; the unchanged
record/source canonical codecs retain their `pack-simulation-{record,source}-v0`
domains. Exact source content is included, not merely its identifier. IDs are
checksums, not source authentication. Outputs are detached; generation does not
write definitions, data or snapshots. A fresh factory revalidates current inputs.

## Actual fictional demonstration

Use `tests/fixtures/pack_simulation_v01/data`. It is a complete fictional graph
with source-backed v3 Printings and existing Finish records. In `base-sheet`,
Printing `pack_fixture.tst.1.en` has foil weight 3 and nonfoil weight 1;
`pack_fixture.tst.2.en` has nonfoil weight 2. Two draws are made. `accent-sheet`
has one draw, with Printing 2/nonfoil weight 1 and Printing 3/nonfoil weight 3.
Fictional source timestamps/statuses are supplied fixture content only.

```python
from simulation import load_pack_simulator, render_pack_report
simulator = load_pack_simulator(
    'pack_fixture', data_root='tests/fixtures/pack_simulation_v01/data')
report = simulator.generate('fictional-pack',
    pack_definition_id='fictional-definition', seed=1)
print(render_pack_report(report, readable=True), end='')
```

The existing CLI uses the identical public API (no new command or approval action):

```sh
PYTHONPATH=src python -B -m mtglab --data-root tests/fixtures/pack_simulation_v01/data pack simulate --game pack_fixture --product-id fictional-pack --definition-id fictional-definition --seed 1 --format text
```

Exact V0.1 API/CLI readable output, seed 1:

```text
fictional-pack / fictional-definition: 3 cards
Seed 1; sha256-counter-rejection-256-v1; non-production definition model
pack-simulation-v0.1: explicit Printing + Finish outcomes
base-slot: pack_fixture.tst.1.en [foil], pack_fixture.tst.2.en [nonfoil]
accent-slot: pack_fixture.tst.3.en [nonfoil]
Input: sha256:43177ed777da2d687eeee56a872e3a35d73076777fabb88428a2c157a7a2f0e1
No physical collation or production authority established.
```

With seed 2, the same Printing is selected **nonfoil**:

```text
fictional-pack / fictional-definition: 3 cards
Seed 2; sha256-counter-rejection-256-v1; non-production definition model
pack-simulation-v0.1: explicit Printing + Finish outcomes
base-slot: pack_fixture.tst.2.en [nonfoil], pack_fixture.tst.1.en [nonfoil]
accent-slot: pack_fixture.tst.2.en [nonfoil]
Input: sha256:43177ed777da2d687eeee56a872e3a35d73076777fabb88428a2c157a7a2f0e1
No physical collation or production authority established.
```

For the exact **before** V0 API/CLI output, use the same calls with
`tests/fixtures/pack_simulation_v0/data`, seed 1:

```text
fictional-pack / fictional-definition: 3 cards
Seed 1; sha256-counter-rejection-256-v1; non-production definition model
base-slot: pack_fixture.tst.1.en, pack_fixture.tst.2.en
accent-slot: pack_fixture.tst.3.en
Input: sha256:4cbd3dd8c9d78ecf0a3503840507c0fbd711c96dbe8e07ca1712ef334fb5e8d2
No physical collation or production authority established.
```

`--format json` serializes the full API report. The complete actual JSON and
readable outputs are retained in the sibling fixture's `examples/` directory.
Repeating a seed and identical input reproduces the full result; different seeds
may coincide. Finishes are explicit objects in every V0.1 draw and are rendered
in brackets, so a finish-aware result cannot silently appear Printing-only.

## Refusal and preservation

Current canonical MB2 still returns `NOT_READY_FOR_SIMULATION`: it lacks an
admitted ProductVersion, PackDefinition, Slots, validated pools/weights and
explicit collation model, and its Product is not validated. No MB2 distribution,
947/45/8 frequency, physical sheet assignment or finish eligibility is invented.
The ordinary structured refusal and CLI exit status 2 are unchanged.

Existing V0 fixture bytes, schemas, reports and deterministic selections remain
unchanged. Historical inventory checks use an exact finite successor ledger:
`tests/fixtures/pack_simulation_v01/source-successors.json`. Every adapted runtime
file must match the exact new hash before its reversible deltas yield the exact
old hash; the one added schema is individually pinned. Unknown neighbors,
coherently rehashed replacements and changed evidence still reject. No historical
evidence, inventory, design package, workflow or gate is repinned or weakened.

Tests exercise public execution, exact integer intervals, version mismatches,
malformed/unsupported finish pairs, source-bound assertions, private ownership,
CLI parity, V0 golden identities, MB2 refusal and actual writer-expanded
historical preservation. Full discovery and hosted publication receipts belong
to the draft PR; this document does not claim those have passed in advance.

Remaining limitations: no conditional slots, physical sequencing, correlated
treatments, without-replacement sampling or real MB2 probabilities. The next
bounded recommendation is a source-backed MB2 pool/finish eligibility gap check,
without automatic acquisition, admission or simulation. It is not authorized here.
