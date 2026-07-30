# Analytics Engines

> **Status: Current — Phase 92 Canonical Analytics Engine v1 implemented.**

## Phase 92 pre-implementation assessment

Architecture v12 already places deterministic analytics downstream of canonical truth and
prohibits derived artifacts from promoting themselves. Phase 91 supplied the missing stable,
provider-neutral read boundary. Phase 92 therefore fits without changing a frozen contract:
the new engine accepts only `CanonicalQueryEngine` snapshots, returns immutable derived
results, and has no repository-storage dependency or write path. Canonical schemas, authority,
promotion, evidence, uncertainty, and filesystem layouts remain unchanged. The work relies on
the constitutional laws that canonical state is the sole truth, unknown is preferable to an
invented value, derived knowledge remains derived, history and provenance are retained, and
product-specific behavior belongs in data. It adds neither AI reasoning nor simulation.

## Canonical Analytics Engine v1

`CanonicalAnalyticsEngine` content-addresses the complete, deterministically ordered query
result snapshot and repeats that `sha256:` identity in every `canonical-analytics-v1` result.
Results are recursively immutable and serialize with sorted JSON keys. The supported views are
`summary`, `entity`, `dataset`, `validation`, and `provenance`.

The summary includes entity counts, cards and printings by set, printings by card, rarity,
color, layout, language and finish distributions, explicit unknown counts, confidence and
validation-state distributions, provenance and dataset coverage, and supersession statistics.
Absent dimensions are reported as `unknown`; they are never inferred. Dataset and provenance
coverage count query-projected lineage only. Validation analytics use the Query Engine's public
validation results so rejected and validation-failure audits are not mistaken for entities.

```bash
PYTHONPATH=src python -m mtglab analytics summary --format json
PYTHONPATH=src python -m mtglab analytics entity --format json
PYTHONPATH=src python -m mtglab analytics dataset --format json
PYTHONPATH=src python -m mtglab analytics validation --format json
PYTHONPATH=src python -m mtglab analytics provenance --format json
```

## Legacy caller-supplied analytics

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
