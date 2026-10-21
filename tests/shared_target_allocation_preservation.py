"""Finite successors for exactly the bounded 601.2d allocation milestone.

This helper supplies no rules authority. Historical views exclude only the
enumerated additions, and document adapters validate every inherited byte and
the exact authored suffix before selecting their earlier snapshots.
"""
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = "d0331139ae10d6709bd448ac83b28ea4e2b45969"
TREE = "a1a4eb4c2f857b50cb3ac0f63162773596eabd8d"
FIXTURE = ROOT / "tests/fixtures/shared-target-allocation-protected-state.json"
FIXTURE_SHA256 = "9185b77c73b22e21944df4d0f9aba2885b4da1e83e38a5e7a8e88348e0f0145b"
PROTECTED_INVENTORY_SHA256 = "731267c1ca4c8f04e07529656c10e85a0bcecc7a555364a5132e43c7eef84c30"
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/shared_target_allocation/" + name
    for name in ("__init__.py", "__main__.py", "source.py", "scope.py",
                 "contracts.py", "package.py", "reviews.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-bounded-shared-target-allocation/" + name
    for name in ("projection.json", "design-source-correspondence.json",
                 "casting-parent-reassessment.json", "activated-import-reassessment.json",
                 "consumer-semantic-boundaries.json", "composite-coverage.json",
                 "preservation-readiness.json", "subsequent-recommendation.json",
                 "manifest.json")
)
NEW_TOOL_PATHS = frozenset()

# Suffix pins are measured from the authored appendices after the complete
# inherited document has been compared to the canonical Git baseline.
DOCUMENT_APPENDICES = {
    "PROJECT_INVENTORY.md": {
        "baseline_bytes": 77840,
        "baseline_sha256": "38bd420591dd2554b1f061994c674fc1a38ab3c3cf425ab21b60545dfcc99cdb",
        "appendix_bytes": 5240,
        "appendix_sha256": "cabae999a6af9e7e54ad681109346460f89fd8b5cd34a0bdd6edebd23ea39d10",
    },
    "docs/PROJECT_STATUS.md": {
        "baseline_bytes": 97080,
        "baseline_sha256": "dd9a0ba8eb2bf053049c56eb30038ce4f1b1c24e2179e5498c6f2c9f2763ba2c",
        "appendix_bytes": 5226,
        "appendix_sha256": "f92b6f2f114102ff1114abd3347b067ce275bcfeb68b1b824e1a7d032354b134",
    },
    "docs/NEXT_TASK.md": {
        "baseline_bytes": 54269,
        "baseline_sha256": "2e1e0c061525a1a989193a54b2c61eedd865f2fb63fb0d114a03446a7c1d5f29",
        "appendix_bytes": 5153,
        "appendix_sha256": "60a4fc12427eb9c44e21329ea77114fee8a8b293694287788de14842ad6ae4aa",
    },
    "docs/HANDOFF.md": {
        "baseline_bytes": 83762,
        "baseline_sha256": "5c8fa34bed8d679245e002de3692e7f59a4401ba25a11b01b26616fb02055476",
        "appendix_bytes": 5168,
        "appendix_sha256": "282dd130f20d1dae02a048150074dd222f502c749572c73fccc8bc583bb38904",
    },
}


def is_target_allocation_addition(path):
    """Select exactly this milestone's seven modules and nine evidence files."""
    return path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS | NEW_TOOL_PATHS


def historical_document_before_target_allocation_append(path, raw):
    """Validate the full baseline and remove only the exact allocation suffix.

    The complete baseline is also accepted for historical adapter composition.
    Unknown paths, arbitrary suffixes, changed bytes and non-bytes fail closed.
    """
    if type(path) is not str or path not in DOCUMENT_APPENDICES:
        raise AssertionError("Only the named target-allocation documents are adapted")
    if type(raw) is not bytes:
        raise AssertionError("Canonical document input must be bytes")
    pin = DOCUMENT_APPENDICES[path]
    length = pin["baseline_bytes"]
    if len(raw) not in (length, length + pin["appendix_bytes"]):
        raise AssertionError("Only the exact target-allocation appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Inherited document changed")
    if appendix and hashlib.sha256(appendix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact target-allocation appendix changed")
    return baseline
