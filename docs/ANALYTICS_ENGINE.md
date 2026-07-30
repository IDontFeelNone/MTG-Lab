# Analytics Engine v1

The analytics engine is the deterministic boundary between stored domain data
and consumers such as applications or a future reasoning layer. It accepts
snapshots supplied by a caller and never fetches, mutates, or persists data.

## Reports

`AnalyticsService` exposes five report computations:

- `collection_summary` — totals, finish distribution, and printing frequency;
- `duplicate_report` — duplicate printings and extra-copy counts;
- `acquisition_report` — acquisition types, products, and cumulative growth;
- `inventory_report` — location totals and deck-assignment utilization; and
- `observation_report` — opening, finish, and observed-card frequencies.

Every result is an immutable `AnalyticsReport`. Its envelope records the report
type, UTC generation timestamp, input identifiers, and `analytics-report-v1`
schema version. Nested input and result values are recursively frozen. Calling
`to_dict()` produces a detached JSON-compatible representation.

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
python -m mtglab.analytics report --output json
```

Collection commands read `data/collections/default.json` unless
`--collection-file` is supplied. Observation analytics recursively reads raw
observation JSON beneath `data/observations` unless `--observations-dir` is
supplied. Output is JSON on standard output; the engine itself performs no I/O.
