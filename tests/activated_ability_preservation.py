"""Exact append-only paths excluded from earlier historical inventory guards.

The successor guard independently pins every byte of the canonical inherited
inventory. Unknown additions remain visible to those historical guards.
"""
from pathlib import Path

from activated_ability_projection_preservation import is_projection_addition
from shared_casting_stage_preservation import is_shared_casting_design_addition
from shared_target_declaration_preservation import is_target_declaration_addition
from shared_target_allocation_preservation import is_target_allocation_addition
from shared_proposal_legality_preservation import is_proposal_legality_addition


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
    """Select historical members, with both exact successor additions excluded."""
    return (path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS
            or is_projection_addition(path) or is_shared_casting_design_addition(path)
            or is_target_declaration_addition(path) or is_target_allocation_addition(path)
            or is_proposal_legality_addition(path))
