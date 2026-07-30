# Analytics Engine v1

The analytics engine is the deterministic boundary between stored domain data
and consumers such as applications or a future reasoning layer. It accepts
snapshots supplied by a caller and never fetches, mutates, or persists data.

## Reports

`AnalyticsService` exposes seven report computations:

- `collection_summary` — totals, finish distribution, and printing frequency;
- `duplicate_report` — duplicate printings and extra-copy counts;
- `acquisition_report` — acquisition types, products, and cumulative growth;
- `inventory_report` — location totals and deck-assignment utilization; and
- `observation_report` — opening, finish, and observed-card frequencies.
- `distribution_report` — finish and language ownership distributions, plus
  rarity and treatment distributions when a canonical repository is supplied;
- `product_report` — observed opening and card totals by product.

Every result is an immutable `AnalyticsReport`. Its envelope records the report
type, UTC generation timestamp, input identifiers, and `analytics-report-v1`
schema version. Nested input and result values are recursively frozen. Calling
`to_dict()` produces a detached JSON-compatible representation, while
`to_json()` produces stable, key-sorted JSON. Report inputs include a SHA-256
fingerprint of the complete relevant snapshot rather than relying on a mutable
repository path or collection identifier alone.

## Repository relationships and lifecycle

Repositories retain ownership of all source data. Callers load and validate a
canonical, observation, collection, or future market-snapshot repository and
pass its immutable snapshot into `AnalyticsService`. The service neither calls
repository save/append methods nor retains references after computation.
Canonical enrichment is optional for dimensions that cannot be known from an
owned-card record; when enabled, an unknown printing is rejected instead of
being silently classified.

A report is generated from one bounded input snapshot, validated against the
`analytics-report-v1` envelope, consumed or persisted by the caller, and never
updated in place. Re-running with the same snapshot and injected clock produces
the same serialized document. Market snapshots can be added as immutable input
to later fact reports without introducing live pricing or repository writes.
The future AI reasoning layer may consume reports, but reasoning,
recommendations, simulation, and expected-value calculations remain outside
this engine.

These reports describe supplied facts only. They do not calculate prices,
expected value, probabilities, deck optimization, recommendations, or AI
interpretations. The generation timestamp can be controlled by injecting a
clock, which makes complete report documents reproducible in tests and batch
jobs.

## CLI

Run the CLI with `PYTHONPATH=src` from the repository root:

```bash
python -m mtglab.analytics collection
python -m mtglab.analytics duplicates
python -m mtglab.analytics acquisitions
python -m mtglab.analytics inventory
python -m mtglab.analytics observations
python -m mtglab.analytics distributions
python -m mtglab.analytics products
python -m mtglab.analytics report --format json
```

Collection commands read `data/collections/default.json` unless
`--collection-file` is supplied. Observation analytics recursively reads raw
observation JSON beneath `data/observations` unless `--observations-dir` is
supplied. Output is JSON on standard output; the engine itself performs no I/O.
