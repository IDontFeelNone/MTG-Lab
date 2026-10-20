"""Exact successor additions for historical inventory selectors.

Only these named files belong to the bounded three-unit projection. Unknown
future files still reach historical guards and the current independent guard.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/activated_ability_projection/" + name
    for name in ("__init__.py", "__main__.py", "contracts.py", "source.py",
                 "scope.py", "package.py", "reviews.py", "pins.json")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-bounded-activated-ability-procedure-projection/" + name
    for name in ("projection.json", "design-source-correspondence.json",
                 "local-scope.json", "procedure-responsibilities.json",
                 "casting-import.json", "cost-analogy.json",
                 "mana-relationships.json", "consumer-reassessment.json",
                 "composite-coverage.json", "overall-readiness.json",
                 "manifest.json")
)


def is_projection_addition(path):
    """Permit precisely the current milestone's enumerated extension."""
    return path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS
