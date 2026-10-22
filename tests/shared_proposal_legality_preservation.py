"""Finite successors for exactly the bounded 601.2e checkpoint milestone.

This helper supplies byte-preservation selectors only. Unknown paths remain
visible; document adaptation verifies the entire canonical prefix and exact
new suffix before older assertions inspect their historical states.
"""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "a21cda0c22092a77ec07097d7b155e7a71bd8de2"
TREE = "6816bbdfbbed9d4ee37e5fe8df98d66bc91763c4"
FIXTURE = ROOT / "tests/fixtures/shared-proposal-legality-protected-state.json"
FIXTURE_SHA256 = "ef2bb3484803d44f9e1ad20e1be1c27b15d3901d3b4e1b86b1476662c0c4e094"
PROTECTED_INVENTORY_SHA256 = "ab6257aa1e9e960a6a81728cb68637a4a7ce5379212dff83a85ce363bbe9defd"
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/shared_proposal_legality/" + name
    for name in ("__init__.py", "__main__.py", "source.py", "scope.py",
                 "contracts.py", "package.py", "reviews.py")
)
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-bounded-shared-proposal-legality/" + name
    for name in ("projection.json", "design-source-correspondence.json",
                 "casting-parent-reassessment.json", "recovery-dependency.json",
                 "activated-import-reassessment.json", "consumer-semantic-boundaries.json",
                 "composite-coverage.json", "preservation-readiness.json",
                 "subsequent-recommendation.json", "manifest.json")
)
NEW_TOOL_PATHS = frozenset()

# Measured from canonical Git and the final authored appendices, independently
# of package records. No suffix other than these exact bytes may be stripped.
DOCUMENT_APPENDICES = {'PROJECT_INVENTORY.md': {'baseline_bytes': 83080,
                          'baseline_sha256': '434a05abdba31305dc8ff917ec530aeb8b08c9fdcfa9054fbaaaf47476ac334d',
                          'appendix_bytes': 6497,
                          'appendix_sha256': '67a093eb06cb238c01b0b95c37ba09e951f9029212dc33a819ac551bcc4663ac'},
 'docs/PROJECT_STATUS.md': {'baseline_bytes': 102306,
                            'baseline_sha256': '1a5b24b4b64af39feb0933699e63950acb8a545860c34049ecb2e18bca4ad4d6',
                            'appendix_bytes': 6492,
                            'appendix_sha256': '0debc4765a600b6bc6c652f82c9ff10cc2bf672f764bca4c7de29422aecfadad'},
 'docs/NEXT_TASK.md': {'baseline_bytes': 59422,
                       'baseline_sha256': 'ac0fdbc60df2b154b7fd90387b3e5550df6d5b33bd29cc94aff405d7ae0591ca',
                       'appendix_bytes': 6492,
                       'appendix_sha256': '0debc4765a600b6bc6c652f82c9ff10cc2bf672f764bca4c7de29422aecfadad'},
 'docs/HANDOFF.md': {'baseline_bytes': 88930,
                     'baseline_sha256': 'af615f5b3c2dfd195a0e6a3cbd8c6dbed51d1a54aa5c9eb4f3a097df291b36c5',
                     'appendix_bytes': 6492,
                     'appendix_sha256': '0debc4765a600b6bc6c652f82c9ff10cc2bf672f764bca4c7de29422aecfadad'}}


def is_proposal_legality_addition(path):
    """Select only the seven modules and ten evidence files enumerated above."""
    return path.relative_to(ROOT).as_posix() in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS | NEW_TOOL_PATHS


def historical_document_before_proposal_legality_append(path, raw):
    """Validate complete current canonical bytes and remove only the e suffix.

    Exact baseline input is accepted to compose older historical adapters.
    Wrong paths, changed prefixes, hidden suffixes and non-bytes fail closed.
    """
    if type(path) is not str or path not in DOCUMENT_APPENDICES:
        raise AssertionError("Only the named proposal-legality documents are adapted")
    if type(raw) is not bytes:
        raise AssertionError("Canonical document input must be bytes")
    pin = DOCUMENT_APPENDICES[path]
    length = pin["baseline_bytes"]
    if len(raw) not in (length, length + pin["appendix_bytes"]):
        raise AssertionError("Only the exact proposal-legality appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    if hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]:
        raise AssertionError("Complete inherited document changed")
    if appendix and hashlib.sha256(appendix).hexdigest() != pin["appendix_sha256"]:
        raise AssertionError("Exact proposal-legality appendix changed")
    return baseline
