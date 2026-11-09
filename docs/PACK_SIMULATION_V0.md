# Executable single-pack simulation v0

This implementation is the separately owner-authorized Pack Simulation V0
milestone, following canonical main `77c99938f48f03e9a3589f83f19444707affdf3a`.
Architecture v13 and Decisions 002, 003, 005 and 017 remain unchanged. Historical
architecture and state documents retain their original implementation inventories;
this guide records the new bounded runtime, not a new architecture decision.

## Existing implementations reused

| Component | Actual use and boundary |
|---|---|
| `canonical.models` | Existing Product, ProductVersion, PackDefinition, PackSlot, Sheet/SheetEntry and Printing types; no second domain model. |
| `repository.canonical.CanonicalRepository` | Owning schema, duplicate and graph validation, reached through the existing query reader. |
| `schemas/v2/{product,product-version,pack-definition,slot,print-sheet}.schema.json` | Unchanged strict source contracts for executable definitions. |
| `repository.rules` | Existing weighted-sheet/slot source/provenance patterns; its whole-repository loader is a v1 product-slot route and is not substituted for the v2 graph reader. |
| `repository.sources.load_source_record` | Existing source-record schema, identity and scoped source lookup. Confirmed fixture declarations remain declarations, not authenticated authority. |
| `query.CanonicalQueryEngine` | Public validated snapshot, exact namespace/ID membership, detached results and provenance. One small `retained_record` accessor exposes independent raw source views so legacy compatibility defaults cannot become explicit weights. Ambiguous namespaces/state-only records refuse. |
| `probability/` and prior `simulation/` | No executable sampler existed: probability was an empty export stub and simulation contained only `.gitkeep`. No probability engine is claimed as reused. |
| `mtglab.__main__.main` | Small lazy `pack simulate` route; other commands unchanged. It returns before import/collection registry creation. |

The new executable code is `simulation.pack`, exported by `simulation`. It is a
single-pack operation, not a general Rules interpreter or simulation service.

## Supported input model

Supply an explicit data root containing a complete existing canonical graph.
The product must be `validated`, own a declared ProductVersion and the explicitly
selected PackDefinition; that version must contain the pack as a component.
Raw definitions must be v2 and pass their existing schemas. Each Slot supplies
an explicit positive integer draw_count, replacement=true and one Sheet. Each
Sheet supplies unique eligible Printing IDs and explicit positive integer weights.
All Printing IDs must be current, known members of the validated query. No missing
weight receives the SheetEntry compatibility default of 1.

The only metadata extension is an explicit, closed interpretation of the existing
PackDefinition metadata object:

```json
{"simulation_model":"independent-weighted-with-replacement-v1"}
```

No schema or typed domain model changes. Product/Version/Slot/Sheet metadata must
be absent or empty in v0; extra Pack metadata, unknown models, replacement=false,
conditional slots, correlations and foil relationships refuse. This narrow scope
does not turn a previously admitted physical collation claim into an independent
sampling model. Relative weights are mathematical model inputs only.

Every source field, including metadata, must have exact top-level provenance
coverage, and referenced source records must exist and declare confirmed status.
This checks supplied record consistency, not reviewer authentication, truthful
source claims, source-use clearance or production eligibility. Every output is
explicitly `EXPLICIT_DEFINITION_MODEL_ONLY_NON_PRODUCTION`, with
`production_authorized=false`.

Finite v0 bounds: 32 slots, 1,024 selected cards, 10,000 entries per pool, and
positive weights/total pool weight at most 2^64-1. Seeds are integers 0..2^64-1;
booleans, fractional quantities and implicit inputs reject. These are new local
execution bounds; no inherited validator limit or timeout is increased.

## Reproducible draws and metadata

Algorithm `sha256-counter-rejection-256-v1` hashes UTF-8 bytes
`algorithm + NUL + decimal(seed) + NUL + decimal(counter)`, starting counter0.
Interpret the digest as an unsigned big-endian integer x. For total weight W,
accept x only if x < 2^256 - (2^256 mod W), otherwise advance the counter and retry.
The accepted ticket is x mod W. Sorted Printing IDs define contiguous weighted
integer intervals. All draws use replacement, across and within pools; each draw
advances the stream. Slots and results follow the PackDefinition's declared order.
This avoids floating-point probabilities, modulo bias and Python random-version
dependencies. It establishes no physical print-sheet sequence or box correlation.

Identical inputs, seed and optional caller timestamp produce identical reports
under v0. Different seeds may collide; they are not guaranteed different packs.
Reports contain seed, algorithm/model/simulator version, exact product/version/pack
IDs, slots and selected Printing IDs, checked card counts, query snapshot ID,
domain-separated canonical structured-input/source identities and exact evidence
references. Inputs include selected retained records and query evidence plus source
record content; a source-content change changes the input identity even if the
query's typed snapshot is unchanged. Evidence is deduplicated across shared pools.
These are content identities, not signatures or legal permissions.

No database is used (`database_version=null`). An optional `recorded_at` UTC-Z
timestamp is explicitly caller-supplied; absence remains null/unspecified rather
than inventing an observed event. Same seed with a different caller timestamp
retains the selections and changes only that annotation. No wall-clock randomness.

## Public API and CLI

```python
from pathlib import Path
from simulation import load_pack_simulator, PackSimulationError, render_pack_report

sim = load_pack_simulator("pack_fixture",
    data_root=Path("tests/fixtures/pack_simulation_v0/data"))
pack = sim.generate("fictional-pack", pack_definition_id="fictional-definition", seed=42)
assert pack == sim.generate("fictional-pack", pack_definition_id="fictional-definition", seed=42)
print(render_pack_report(pack, readable=True))
```

The complete fictional fixture and actual seed42/seed1 outputs are described in
[`tests/fixtures/pack_simulation_v0/README.md`](../tests/fixtures/pack_simulation_v0/README.md).
CLI: `PYTHONPATH=src python -B -m mtglab --data-root DATA pack simulate --game GAME
--product-id ID --definition-id PACK --seed INTEGER --format json|text`.
`--recorded-at` is optional. Success exits0; a structured refusal exits2. JSON and
readable output describe the same result; readable output does not append raw JSON.

The factory performs actual public query admission on every load; no success cache
or provider fallback. Existing attached snapshot profiles have no authorized pack
simulation capability, so explicit attachments are verified then refused, including
Stage1 fictional attachments. Invalid/missing snapshots never select the legacy root.
For legacy explicit roots, an actual Game record is required (no virtual Game
fallback). The loaded definition view is privately held; public record and report
views are independent copies. A fresh load reads current definitions. Source records
are revalidated per generation, once per distinct source, and bound into that result.

## Actual Mystery Booster 2 refusal

```sh
PYTHONPATH=src python -B -m mtglab pack simulate --product-id mystery_booster_2 --seed 42 --format json
```

The current public reader returns `NOT_READY_FOR_SIMULATION`, with no generated
slots or Printing IDs. Actual missing requirements are PRODUCT_NOT_VALIDATED,
ADMITTED_PRODUCT_VERSION_MISSING, ADMITTED_PACK_DEFINITION_MISSING,
ADMITTED_SLOT_DEFINITIONS_MISSING, VALIDATED_PRINTING_POOLS_AND_WEIGHTS_MISSING,
and EXPLICIT_COLLATION_MODEL_MISSING. The same refusal is readable with `--format text`.

Canonical `products/mystery_booster_2/product.json` remains foundation/v1;
`packs.json` and `slots.json` both have empty ID collections. The retained Stage1
package (`docs/MB2_STAGE_1_EVIDENCE_PACKAGE.md`) confirms product identity only:
zero ProductVersions, PackDefinitions, Slots and Sheets. Later MB2 reference and
810 readiness material remains research/pending admission; Card/Printing inventory
alone supplies no pool weights, pack topology, foil frequencies or collation.
No retained observation, inferred model or card-name label is promoted by this engine.
No MB2 sheets, probabilities, Cards or canonical records were created or modified.

## Preservation, tests and exclusions

Focused tests exercise actual API/CLI generation, seed goldens, exact weighted
ticket intervals and rejection sampling, repeated-output ownership, source binding,
strict source-versus-compatibility validation, counts, malformed inputs, missing
references, unsupported rules, snapshot rejection and real MB2 refusal. Synthetic
assertions establish the declared mathematical model, not physical MB2 accuracy.
Historical test views reverse only exact query/CLI insertions and allow exactly two
pinned new simulation source files. Original schemas, fixtures, workflows, timeouts,
Card/Printing data, collection logic, market data, rules and design packages remain
unchanged. Unknown additions and coherently rehashed source substitutions reject.

No box/case/batch/Monte Carlo API, price/EV evaluation, print-run reconstruction,
collation inference, source acquisition, deck or gameplay engine, authentication,
authorization, canonical promotion, database or network service. Source permissions,
Tier A restrictions and gameplay execution blocks remain unchanged.

One bounded next recommendation: after separate owner authorization, add exact
analytical per-slot Printing probabilities for this same explicit independent model,
without Monte Carlo batches, real-product claims, EV or new data acquisition.
It reuses the admitted integer weights and is testable against exact rational values.
That work is not begun or automatically authorized.

Stop at one draft PR for independent Senior PM review and final owner approval.
Future implementation authorized: false. Future authorization work authorized: false.
Future milestone begun: false.
