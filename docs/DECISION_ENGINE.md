# Decision Engine v1

The Decision Engine is the deterministic, read-only layer between immutable
Analytics Engine reports and future consumers. It evaluates explicit rules; it
does not query or modify repositories, infer product behavior, calculate
expected value, use live prices, simulate outcomes, or perform AI/ML reasoning.

## Model and explainability

Each immutable `Decision` has a stable content-derived identifier, category,
severity, rendered explanation, rule identifier, UTC generation timestamp, and
`decision-v1` schema version. Its supporting analytics contain the exact report
type, fact path and value, plus the analytics input fingerprints. Consequently,
a consumer can follow every recommendation or alert to the immutable snapshot
that established it. A `DecisionReport` deterministically orders decisions and
records every active rule version under `decision-report-v1`.

## Rules and lifecycle

`DecisionRule` configuration declares a rule identifier and version, category,
required analytics report and fact path, comparison operator and threshold,
severity, and explanation template. The generic evaluator contains no
product-specific branches. Named rule types document the supported families:
duplicate thresholds, inventory locations, missing coverage, observation
consistency, and collection growth. Default rules also cover acquisition
opportunities and product-opening summaries.

Rule changes require a version change, independent unit tests, and review of
their severity and explanation. Configuration is validated at construction;
unknown operators, severities, missing facts, duplicate rule identifiers, and
incompatible analytics schemas fail rather than being silently ignored. A rule
matches only its declared `analytics-report-v1` fact. Matching produces one
decision whose identifier hashes the rule version and supporting fact.

## Relationship to Analytics and future reasoning

Callers first create immutable reports with `AnalyticsService`, then supply a
bounded set to `DecisionService`. APIs include `evaluate_collection()`,
`evaluate_inventory()`, `evaluate_observations()`, `evaluate_duplicates()`, and
`generate_decision_report()`. The engine retains no mutable state and performs
no persistence. A future AI reasoning layer may consume decisions and their
explanations, but must remain downstream; it cannot affect deterministic rule
evaluation or its evidence trail.

## CLI

Run from the repository root with `PYTHONPATH=src`:

```bash
python -m mtglab.decisions evaluate
python -m mtglab.decisions report --format json
python -m mtglab.decisions rules
```

The first two commands build analytics from the configured collection file and
observation directory. `rules` prints the complete active configuration. JSON
keys and decision ordering are stable; injecting a fixed clock makes the entire
serialized report reproducible.
