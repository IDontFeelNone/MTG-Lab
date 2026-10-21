"""Exact finite successors for the single 601.2c projection milestone.

This helper has no source-verification or gameplay authority. Historical guards
keep their original fixtures, counts and digests; only the named additions and
exact document appendices are selected before those guards run.
"""
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "9953142e6b729f8ca34a008dc5e8fcf5b642ad54"
TREE = "7e283050ca31cf9ca62ead060a94ee5dbd4b4871"
FIXTURE = ROOT / "tests/fixtures/shared-target-declaration-protected-state.json"
FIXTURE_SHA256 = "304a26435fe18bfa9a9e093b43f6186c94d4d1d36d9f5986135f0f08058a3cda"
PROTECTED_INVENTORY_SHA256 = "05b68d15be6c6a5f321b1ba633e163f029211353383cc2add816902203152f68"
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/shared_target_declaration/" + name
    for name in ("__init__.py", "__main__.py", "source.py", "scope.py",
                 "contracts.py", "package.py", "reviews.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-bounded-shared-target-declaration/" + name
    for name in ("projection.json", "design-source-correspondence.json",
                 "casting-parent-reassessment.json", "activated-import-reassessment.json",
                 "consumer-semantic-boundaries.json", "composite-coverage.json",
                 "preservation-readiness.json", "subsequent-recommendation.json",
                 "manifest.json")
)
NEW_TOOL_PATHS = frozenset()

# These whole inherited documents include every earlier appendix. New suffix
# pins are added only after the authored bytes exist and have been measured.
DOCUMENT_APPENDICES = {
    "PROJECT_INVENTORY.md": {
        "baseline_bytes": 74440,
        "baseline_sha256": "4ce7d0cb9654c856e06496cc534c1cfce4558a1feb695d73e0e3675b76d382dd",
        "appendix_bytes": 3400,
        "appendix_sha256": "d9c058e4bbf0ac8bf07ec32916053923660081ef7b293b5d17cd33de13aa4410",
    },
    "docs/PROJECT_STATUS.md": {
        "baseline_bytes": 93823,
        "baseline_sha256": "985352a0ee56792de290dfbb5ef4f2a15c16c274266f039b2197b83823634950",
        "appendix_bytes": 3257,
        "appendix_sha256": "e3a1163a600188f622d879748b14eab165bd5979e93ed249fa214b716ce0dff8",
    },
    "docs/NEXT_TASK.md": {
        "baseline_bytes": 50958,
        "baseline_sha256": "96c1ff9730a23888d08e9767c41145ea3a829afd420e34e801a29ee9d3183df0",
        "appendix_bytes": 3311,
        "appendix_sha256": "641da2ead06f1212eab3acaa54cf08d7cef232a102b5868221e126c4a0ec381d",
    },
    "docs/HANDOFF.md": {
        "baseline_bytes": 80379,
        "baseline_sha256": "9b1a28efee07ca1d5724b3ba507e6a72a4de8221c6602fefcbf004b3c620c28b",
        "appendix_bytes": 3383,
        "appendix_sha256": "544c8ed8073db15a6c715571260d1ca4cf110d5cd9bf79e2a5b0bd7e4e63e2e3",
    },
}


def is_target_declaration_addition(path):
    """Select only the seven modules and nine records of this milestone."""
    return path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS | NEW_TOOL_PATHS


def historical_document_before_target_declaration_append(path, raw):
    """Validate and remove only the exact new suffix before older adapters.

    The exact inherited document is also accepted so historical adapters can
    continue operating on their own complete canonical baseline. Arbitrary
    suffixes, changed inherited bytes and invalid input types fail closed.
    """
    if type(path) is not str or path not in DOCUMENT_APPENDICES:
        raise AssertionError("Only the named target-declaration documents are adapted")
    if type(raw) is not bytes:
        raise AssertionError("Canonical document input must be bytes")
    pin = DOCUMENT_APPENDICES[path]
    length = pin["baseline_bytes"]
    if len(raw) not in (length, length + pin["appendix_bytes"]):
        raise AssertionError("Only the exact target-declaration appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Inherited document changed")
    if appendix and hashlib.sha256(appendix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact target-declaration appendix changed")
    return baseline
