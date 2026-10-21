"""Finite successor selectors for this one review-only design milestone.

The current independent guard pins all 473 inherited source/evidence files.
These selectors preserve older inventory assertions, counts and expected digests;
unknown additions or arbitrary document suffixes remain visible and fail closed.
"""
import hashlib
from pathlib import Path

from shared_target_declaration_preservation import (
    DOCUMENT_APPENDICES as TARGET_DECLARATION_APPENDICES,
    historical_document_before_target_declaration_append,
)

ROOT = Path(__file__).resolve().parents[1]
NEW_REVIEW_PATHS = frozenset(
    "reference-reviews/gameplay-rules-shared-casting-stage-gap-design/" + name
    for name in (
        "source-inspection.json", "gap-matrix.json", "consumer-dependencies.json",
        "scope-recommendation.json", "readiness.json", "manifest.json",
    )
)
NEW_TOOL_PATHS = frozenset({"scripts/shared_casting_stage_gap_design.py"})
# Only the exact appendix of this milestone may be removed before a historical
# assertion. Baseline bytes include the complete PR #200 appendices.
DOCUMENT_APPENDICES = {
    "PROJECT_INVENTORY.md": {
        "baseline_bytes": 72451,
        "baseline_sha256": "07c3dbe96ecc250342636094259d565ecc096fdad9059f440bd1c58fb8daf0e3",
        "appendix_bytes": 1989,
        "appendix_sha256": "5731be6c4763cc1572c3b7246f816c4d54cbd8d0f3de9ae3f936c78f64ac5217",
    },
    "docs/PROJECT_STATUS.md": {
        "baseline_bytes": 91929,
        "baseline_sha256": "cef15bec8b738b569c3f84b902e50e23a8691e1ec1445132be296b7ae72100b9",
        "appendix_bytes": 1894,
        "appendix_sha256": "17ba34493e3a6bfb7f0cbed5de42e255c3e43bf766c2cfcc3ef0115991dbcd05",
    },
    "docs/NEXT_TASK.md": {
        "baseline_bytes": 49075,
        "baseline_sha256": "78042fb0d05f44c2b2a0bda5bdf40fdcc399a62fe1e14d0d1d043e9f71412eff",
        "appendix_bytes": 1883,
        "appendix_sha256": "c5eaa7d089b38217f887ed986d8985d477851daba8ea3f3048a582faed4b87af",
    },
    "docs/HANDOFF.md": {
        "baseline_bytes": 78430,
        "baseline_sha256": "fd6aceb575b076c38ad2ee0a98d30bb02bfaf807bfe0786e767e8259540c5a59",
        "appendix_bytes": 1949,
        "appendix_sha256": "a3e65d7cc9bb7183a0deb2d7e5a84c1be6fe32836a785489e7b998aa9a450b7d",
    },
    "docs/SESSION_STATE.md": {
        "baseline_bytes": 82652,
        "baseline_sha256": "8c5a1e9db6937bcec6285c7b2cad86d2edc0750221488cc75918353531481e71",
        "appendix_bytes": 1978,
        "appendix_sha256": "102a791a7e0b076095bff1209c12158f4da8ca6eca3f34fa174f594e34fcd2ab",
    },
    "CHANGELOG.md": {
        "baseline_bytes": 53271,
        "baseline_sha256": "92014f634f7b357d173ca8068195d7842a446caba1eabeddf3a8cf46ae0a0d7e",
        "appendix_bytes": 1733,
        "appendix_sha256": "0ba1a5d253346d2b248d1345dbbaf7f1fb1a9bd6aca5cb5cec82ba4188139f33",
    },
}


def is_shared_casting_design_addition(path):
    """Exclude only this milestone's named reviews and tool from older inventories."""
    return path.relative_to(ROOT).as_posix() in NEW_REVIEW_PATHS | NEW_TOOL_PATHS


def historical_document_before_shared_casting_append(path, raw):
    """Return exact inherited bytes before the one known review appendix."""
    if type(path) is not str or path not in DOCUMENT_APPENDICES:
        raise AssertionError("Only the named shared casting design documents are adapted")
    if type(raw) is not bytes:
        raise AssertionError("Canonical document input must be bytes")
    if path in TARGET_DECLARATION_APPENDICES:
        raw = historical_document_before_target_declaration_append(path, raw)
    pin = DOCUMENT_APPENDICES[path]
    length = pin["baseline_bytes"]
    if len(raw) != length + pin["appendix_bytes"]:
        raise AssertionError("Only the exact shared casting design appendix is permitted")
    baseline, appendix = raw[:length], raw[length:]
    if (hashlib.sha256(baseline).hexdigest() != pin["baseline_sha256"]
            or hashlib.sha256(appendix).hexdigest() != pin["appendix_sha256"]):
        raise AssertionError("Canonical document or exact shared casting design appendix changed")
    return baseline
