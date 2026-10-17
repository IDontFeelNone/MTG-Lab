"""Exact-source construction of the fixed twelve-rule dependency projection.

Source verification and physical-line locating reuse the original projection
infrastructure. Source data exists only transiently; no official body is kept.
"""
from __future__ import annotations

from gameplay_rules.errors import GameplayContractError
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _json
from .dependency_contracts import (
    DependencyProjection, FOUNDATIONAL_PROJECTION_ID, SOURCE_BINDING, AUTHORIZATION, BOUNDARY_FLAGS,
)
from .dependency_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)
from .source import _verified_bytes, _locate_anchors


def _fail(field):
    raise GameplayContractError("foundational_dependency_projection_source", field)


def _locate_dependency_anchors(data):
    """Use only the immutable dependency allowlist and add its release binding."""
    return [{**anchor, "effective_date": EFFECTIVE_DATE}
            for anchor in _locate_anchors(data, references=SELECTED_REFERENCES)]


def build_dependency_projection(artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Require verified actual source access before creating any projection."""
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    anchors = _locate_dependency_anchors(data)
    return DependencyProjection.create({
        "game_id": "magic", "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "DIRECT_FOUNDATIONAL_DEPENDENCIES_PROJECTED", "selected_rule_count": 12,
        "foundational_projection_id": FOUNDATIONAL_PROJECTION_ID,
        "source_binding": _json(SOURCE_BINDING), "authorization": _json(AUTHORIZATION),
        "rules": [{"rule_reference": anchor["rule_reference"],
                   **_json(RULE_CONTENT[anchor["rule_reference"]]), "source_anchor": anchor}
                  for anchor in anchors],
        "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "new_boundaries": _json(NEW_BOUNDARIES), "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS),
    })


def verify_dependency_projection_source(projection, artifact_path, *, artifact_review_root,
                                        source_root, discovery_root):
    """Reproduce every anchor from verified owner-supplied bytes without retaining them."""
    if not isinstance(projection, DependencyProjection):
        _fail("typed non-executable dependency projection required")
    projection.verify()
    reproduced = build_dependency_projection(artifact_path, artifact_review_root=artifact_review_root,
        source_root=source_root, discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("dependency projection source spans or authored content do not reproduce")
    return {"status": "VERIFIED_EXACT_SOURCE_SPANS", "projection_id": projection.identity,
            "selected_rule_count": 12, "source_anchor_count": 12, "artifact_hash": ARTIFACT_HASH,
            "byte_length": ARTIFACT_BYTE_LENGTH, "effective_date": EFFECTIVE_DATE,
            "source_body_retained": False, "execution_authorized": False, "real_rules_executable": False}
