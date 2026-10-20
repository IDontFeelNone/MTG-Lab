"""Exact successor additions for historical inventory selectors.

Only these named files belong to the bounded three-unit projection. Unknown
future files still reach historical guards and the current independent guard.
"""
import hashlib
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


def historical_inventory_before_projection_append(raw):
    """Select exact canonical inventory before this one known status appendix.

    Earlier governance checks pin a historical suffix within the canonical
    inventory. This finite selector preserves that assertion and its fixture
    digest while the independent guard also protects the whole canonical body.
    A changed body, changed appendix, or any future append fails explicitly.
    """
    original_length = 69051
    original_sha256 = "ebf315219fda9317f99431cea4564d6a364aabb2de0618f30795c1e665a570d5"
    appendix_length = 3400
    appendix_sha256 = "fd7d6c5e65d4bdabba1676972ac693329e8bbfa2d11f2b98f21e1eabd3bb1497"
    if type(raw) is not bytes or len(raw) != original_length + appendix_length:
        raise AssertionError("Only the exact bounded projection inventory appendix is permitted")
    original, appendix = raw[:original_length], raw[original_length:]
    if (hashlib.sha256(original).hexdigest() != original_sha256
            or hashlib.sha256(appendix).hexdigest() != appendix_sha256):
        raise AssertionError("Canonical inventory or exact bounded projection appendix changed")
    return original
