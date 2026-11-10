# Fictional single-pack model

All Cards, Printings, product records, weights and source claims beneath this
directory are original synthetic test inputs. None is production-authorized,
real Magic evidence, physical collation evidence, a source-use permission or a
reviewer approval. The fixed source date describes this fixture only.

The complete existing canonical graph is under `data/canonical/games/pack_fixture/`.
The base slot draws twice, with replacement, from Printing 1 (weight 1) and
Printing 2 (weight 3). The accent slot draws once, independently with replacement,
from Printings 2 and 3 (weight 1 each). Explicit pack metadata selects the bounded
model; no probability is supplied by a default.

```sh
PYTHONPATH=src python -B -m mtglab --data-root tests/fixtures/pack_simulation_v0/data pack simulate --game pack_fixture --product-id fictional-pack --definition-id fictional-definition --seed 42 --format text
```

Seed 42 selects base `[pack_fixture.tst.2.en, pack_fixture.tst.2.en]` and accent
`[pack_fixture.tst.3.en]`. Repeating the command produces identical output.
Seed 1 instead selects base `[pack_fixture.tst.1.en, pack_fixture.tst.2.en]`
and accent `[pack_fixture.tst.3.en]`. Different seeds can also produce the same
pack; variation is permitted, not guaranteed.
