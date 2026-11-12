# Pack Simulation V0.2 — explicit weighted pack variants

V0.2 extends the existing [V0](PACK_SIMULATION_V0.md) /
[V0.1](PACK_SIMULATION_V01.md) single-pack generator. It selects one explicitly
weighted composition and samples that composition's slots. It is generic,
read-only and non-production. It establishes no real MB2 manufacturing odds.
Architecture v13 and Decision 017 remain unchanged.

## Versioned contract

The new native **v3 PackDefinition** is a parent with `variants`, instead of
`slot_ids`. Each reference contains exactly `pack_definition_id` and a positive
integer `weight`. The referenced PackDefinition ID is the stable variant identity;
duplicate references reject even if their weights differ. Existing PackDefinition
and Product identities are reused; `PackVariant` is only an immutable weighted
reference value, not a second Pack, Printing or source model.

The parent must explicitly declare this closed metadata object:

```json
{"simulation_model":"weighted-finish-pack-variants-with-replacement-v1"}
```

Each child is a complete **v2 PackDefinition**, with explicit Slot IDs, using
V0.1's `independent-finish-weighted-with-replacement-v1` model and v3 finish-aware
Sheets. Existing Printing/Finish eligibility, evidence and source validation is
reused unchanged. Children must belong to the parent's exact ProductVersion.
Nested variant parents, V0 Printing-only children, missing weights, unknown
references, unknown metadata and mixed schema/model combinations reject.

Only the parent is a physical component of its ProductVersion. Children are
alternative compositions linked by parent references; they are **not** extra
simultaneous packs in the product's contents. A child used only as an alternative
is not independently selectable as a product component through the public API.
Its entire composition is nevertheless independently validated before selection.

The owning canonical reader admits v3 parents and validates exact child membership,
uniqueness, ownership and non-nesting. The simulator uses public query snapshots
and retained-record readers, exact schema validation and existing provenance
readers. It validates **all** children, their pools, finishes and sources before
calling the sampler. Invalid unselected evidence cannot be hidden by a lucky seed.
No neighboring consumer's private snapshot is accessed.

`PackDefinition.variants` is optional in the typed compatibility model. An absent
legacy value is omitted through the existing query serializer's metadata flag.
V0 and V0.1 retained inputs, exact input identities, output structures, seeded
selections, readable renderings, public API and CLI are unchanged. No old schema
or fixture is migrated. New exports `VARIANT_MODEL` / `VARIANT_VERSION` leave the
existing `MODEL`, `VERSION`, `FINISH_MODEL`, `FINISH_VERSION` values unchanged.

## Exact probability and stream semantics

1. Sort weighted child references lexically by exact PackDefinition ID. Names,
   labels, rarity, product identity and finish appearance infer nothing.
2. Let W be the sum of explicit positive integer weights. Apply the existing
   `sha256-counter-rejection-256-v1` sampler at counter **0** to obtain a uniform
   ticket in `[0,W)`. Contiguous integer intervals select exactly one child.
3. Continue from the counter returned by that call, including every rejected
   SHA-256 block. Sample only the chosen child's slots, preserving declared slot
   order and draw order, using the existing sorted Printing/Finish intervals.
4. Draws inside and across pools remain independent, **with replacement**. There
   are no physical sequencing, conditional slots, correlations or duplicate vetoes.

A fictional 90/8/2 model maps tickets 0–89, 90–97 and 98–99 to its three sorted
children. Tests check **all 100 tickets**, both interval mathematics and actual
engine routing. No floating point, percentage rounding or implicit uniform weight
is involved. Rejection sampling advances correctly before any slot draw. Different
seeds may select different variants but are not guaranteed different outcomes.

Existing local execution bounds remain: 32 slots, 1,024 cards, 10,000 entries per
pool, positive integer weights/pool sums and seeds bounded by 2^64-1. V0.2 also
limits variant count to 32 and conservatively applies 32 slots / 1,024 cards /
10,000 visited pool entries **across all candidate compositions**. Shared slot or
pool visits count in each candidate. Sum of variant weights is bounded by 2^64-1.
No inherited validation bound or timeout is increased.

## Output and provenance

Reports explicitly use `schema_version` / `simulator_version` =
`pack-simulation-v0.2`, model above, and add:

- `selected_variant_id` — exact chosen child PackDefinition ID.
- `selected_variant_weight` and `variant_total_weight` — declared integer weights.
- Existing seed, algorithm, exact Product/ProductVersion/parent identities,
  explicit Printing/Finish `outcomes`, counts and provenance references.

The domain-separated input identity is `pack-simulation-input-v0.2`. It binds the
query snapshot and **all eligible** child definitions, slot/pool/Printing/Finish
evidence, weights and source content. Shared records/sources are deduplicated.
Changing an unselected child's evidence or a weight changes the input identity.
Reordering declaration arrays can change that exact input identity while sorting
keeps the sampling result stable. Existing record/source digest codecs are reused.
No full evidence graph is copied into each output; reports contain exact references.

Source records must exist, pass their existing closed schema and declare confirmed
status; definition provenance must cover every supplied field. Unverified sources,
missing provenance, unknown authentication/permission fields and incompatible
finish assertions refuse. A fixture's `confirmed` / `promoted` labels are supplied
model declarations, not independently authenticated review, source truth, copyright
clearance or production admission. The API never turns a source claim into an
authorization. `production_authorized=false` and the non-production scope remain.

One owning query/catalog admission serves a generated pack. No repeated catalog
load per variant is introduced. Fresh factory calls revalidate current inputs;
returned views are detached and generation writes no canonical files or cache.

## Actual fictional fifteen-card booster

Fixture: `tests/fixtures/pack_simulation_v02/data`, game `pack_fixture`, one
`fictional-pack` Product, parent `fictional-variants`. Every Card, Printing, Finish,
source, timestamp and asserted status is fictional supplied test data outside
production canonical data. The 90/8/2 weights are **not** the retained MB2 model.

| Child | Weight | Declared ordered slot counts | Treatment pool |
|---|---:|---|---|
| variant-a-nonfoil | 90 | base-slot 10; accent-slot 4; nonfoil-slot 1 | Printing1/nonfoil only |
| variant-b-foil | 8 | base-slot 10; accent-slot 4; foil-slot 1 | Printing1/foil only |
| variant-c-mixed | 2 | short-base-slot 9; accent-slot 4; mixed-slot 2 | Printing1/foil weight3, Printing1/nonfoil weight1 |

All three total **15 cards**. Base slots use explicit Printing1/nonfoil weight1
and Printing2/nonfoil weight2; accent uses Printing2/nonfoil weight1 and
Printing3/nonfoil weight3. Thus one admitted fictional Printing is explicitly
eligible in both finishes without inferring finish from its slot's name.

```python
from simulation import load_pack_simulator, render_pack_report
sim = load_pack_simulator('pack_fixture',
    data_root='tests/fixtures/pack_simulation_v02/data')
pack = sim.generate('fictional-pack',
    pack_definition_id='fictional-variants', seed=0)
print(render_pack_report(pack, readable=True), end='')
```

```sh
PYTHONPATH=src python -B -m mtglab --data-root tests/fixtures/pack_simulation_v02/data pack simulate --game pack_fixture --product-id fictional-pack --definition-id fictional-variants --seed 0 --format text
```

Actual public results:

| Seed | Selected child | Cards | Slot counts | Last slot result |
|---:|---|---:|---|---|
| 0 | variant-b-foil | 15 | 10 / 4 / 1 | Printing1/foil |
| 1 | variant-a-nonfoil | 15 | 10 / 4 / 1 | Printing1/nonfoil |
| 97 | variant-c-mixed | 15 | 9 / 4 / 2 | Printing1/foil twice, with replacement |

Identical inputs and seeds reproduce the **entire** report. Complete actual JSON
and readable outputs for these three seeds are in the sibling `examples/`
directory and are tested against live public execution. They are examples of a
supplied mathematical distribution, not evidence of physical booster collation.

## Preservation, validation and stop

The existing canonical MB2 public call still returns `NOT_READY_FOR_SIMULATION`,
CLI exit2 and no invented cards. It lacks an admitted ProductVersion, pack/slot
definitions, validated pools/weights and explicit model, and its Product remains
unvalidated. No authentic MB2 pack, retained 947/45/8 manufacturing assumption,
physical A/B assignment, new source acquisition, admission or permission is added.

Protected canonical datasets, old V0/V0.1 fixtures, reports and schemas, rules,
review decisions, source policies, workflows, timeouts and architecture stay
unchanged. Exact finite source successors are accounted for in
`tests/fixtures/pack_simulation_v02/source-successors.json`; test-only adapters
reverse individually pinned deltas to their exact predecessors and reject unknown
or coherently rehashed substitutes. Historical package identities are not repinned.

Focused regression coverage includes full fifteen-card results, all variant
intervals, random-stream consumption and rejection, unselected invalid evidence,
foreign identities, strict types, source/finish eligibility, aggregate bounds,
read-only public API/CLI, independent ownership and exact old golden outputs.
Final-head full local discovery and both hosted outer/nested writer-publication
receipts belong in the draft PR. This document does not claim tests passed before
those gates execute.

Only one level of finish-aware independent compositions is supported. This does
not model real foil frequencies, correlated slots, physical sheets, boxes, cases,
Monte Carlo batches, valuation or gameplay. No new authentication or authorization
system exists. Stop for independent Senior PM review and owner approval; no merge,
auto-merge or future milestone is authorized.
