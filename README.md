# MTG-Lab

A reproducible analysis toolkit for **Magic: The Gathering Mystery Booster 2**. MTG-Lab brings together authoritative card-list data, structured parsing, probability modeling, pack and box simulation, and market analysis so collectors, players, and researchers can answer transparent, testable questions about the product.

## Goals

- Establish a canonical, versioned representation of the Mystery Booster 2 card list and sheet structure.
- Import and validate source data while preserving provenance and reproducibility.
- Model slot, pack, and sealed-product probabilities with clearly stated assumptions.
- Simulate opening experiences and evaluate expected outcomes at scale.
- Analyze market-facing metrics without coupling raw price data to the core card model.
- Provide tested, documented building blocks that can be extended as new information becomes available.

## Repository layout

```text
docs/              Project documentation, methodology, and source notes
data/
  raw/             Immutable source captures
  processed/       Reproducible intermediate datasets
  canonical/       Validated datasets used by the application
  validation/      Validation reports and fixtures
src/
  importer/        Source ingestion and normalization
  parser/          Card-list and print-sheet parsing
  probability/     Probability and expected-value calculations
  simulation/      Pack and product simulation engines
  market/          Market-data adapters and analysis
  models/          Shared domain models and schemas
tests/             Automated tests
scripts/           One-off and operational command-line utilities
notebooks/         Exploratory analysis notebooks
```

## Principles

MTG-Lab favors provenance over convenience: raw inputs remain intact, transformations are repeatable, and published results identify their assumptions. Probability results should distinguish verified product rules from analyst-defined scenarios. The project is designed for Python, with modules kept small, typed, and independently testable.

## Roadmap

1. **Foundation** — establish repository conventions, project documentation, and the canonical module layout.
2. **Data pipeline** — capture Mystery Booster 2 sources, normalize them, and validate a canonical card dataset.
3. **Product modeling** — represent slots, sheets, treatments, and product configurations as explicit domain models.
4. **Probability engine** — calculate exact odds and expected values for individual pulls and sealed products.
5. **Simulation and market analysis** — run reproducible simulations, integrate market snapshots, and publish reports.

## Status

The project foundation is in place. Data acquisition and analytical modules will be added in subsequent milestones.

## License

This project is released under the [MIT License](LICENSE).
