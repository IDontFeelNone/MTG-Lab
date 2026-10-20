"""Exact append-only paths excluded from earlier historical inventory guards.

The successor guard independently pins every byte of the canonical inherited
inventory. Unknown additions remain visible to those historical guards.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/activated_ability_design/" + name
    for name in ("__init__.py", "__main__.py", "inspection.py", "package.py",
                 "pins.json", "records.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-activated-ability-procedure-design/" + name
    for name in ("source-correspondence.json", "local-scope.json",
                 "procedure-responsibilities.json", "casting-import.json",
                 "mana-relationships.json", "consumer-bindings.json",
                 "readiness.json", "manifest.json")
)


def is_design_addition(path):
    """Recognize only the reviewed design milestone's exact file extension."""
    return path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS
