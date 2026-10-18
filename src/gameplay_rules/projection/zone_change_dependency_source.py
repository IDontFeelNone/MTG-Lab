"""Transient verification of the twelve authorized direct dependency lines.

The artifact verifier and exact byte-line locator are reused. Only selected
physical lines are inspected; range expansion is fixed to the two reviewed
citations in this allowlist and never traverses downstream source content.
"""
from __future__ import annotations

import re

from gameplay_rules.errors import GameplayContractError
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _json
from .source import _verified_bytes, _locate_anchors
from .zone_change_dependency_contracts import (
    ZoneChangeDependencyProjection, FOUNDATIONAL_PROJECTION_ID, DEPENDENCY_PROJECTION_ID,
    OBJECT_CONTROL_PROJECTION_ID, ZONE_CHANGE_PROJECTION_ID,
    SOURCE_BINDING, AUTHORIZATION, BOUNDARY_FLAGS, rule_identity,
)
from .zone_change_dependency_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES, NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)


def _fail(field):
    raise GameplayContractError("zone_change_dependency_projection_source", field)


def _selected_explicit_references(reference, selected_line):
    """Inspect citations only within a selected line, with two fixed expansions."""
    try:
        text = selected_line.decode("utf-8")
    except UnicodeError:
        _fail("selected source line must be UTF-8")
    # Remove the two exact reviewed grouped citations after collecting their
    # fixed targets. No general range parser or recursive projection is used.
    grouped = {
        "611.3d": ("rules 611.3a–b", ["611.3a", "611.3b"]),
        "702.35b": ("rules 601.2b and 601.2f–h", ["601.2b", "601.2f", "601.2g", "601.2h"]),
    }
    if reference in grouped:
        citation, targets = grouped[reference]
        if text.count(citation) != 1:
            _fail("selected grouped numbered citation does not match reviewed scope")
        remainder = text.replace(citation, "", 1)
        if re.search(r"\brules?[ \t]+[0-9]{3}(?:\.[0-9]+[a-z]?)?\b", remainder, re.IGNORECASE):
            _fail("unexpected additional selected-line numbered citation")
        return targets
    return re.findall(r"\brules?[ \t]+([0-9]{3}(?:\.[0-9]+[a-z]?)?)\b", text, re.IGNORECASE)


def _locate_zone_change_dependency_anchors(data):
    """Require one physical match per selected ref and its exact direct citations."""
    anchors = [{**anchor, "effective_date": EFFECTIVE_DATE}
               for anchor in _locate_anchors(data, references=SELECTED_REFERENCES)]
    for anchor in anchors:
        selected_line = data[anchor["byte_start"]:anchor["byte_end"]]
        explicit = _selected_explicit_references(anchor["rule_reference"], selected_line)
        expected = list(RULE_CONTENT[anchor["rule_reference"]]["direct_dependency_references"])
        if explicit != expected:
            _fail("selected explicit numbered source references do not match fixed reviewed scope")
    return anchors


def _build_projection(data):
    rules = []
    for anchor in _locate_zone_change_dependency_anchors(data):
        rule = {"rule_reference": anchor["rule_reference"],
                **_json(RULE_CONTENT[anchor["rule_reference"]]), "source_anchor": anchor}
        rule["rule_id"] = rule_identity(rule)
        rules.append(rule)
    return ZoneChangeDependencyProjection.create({
        "game_id": "magic", "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "ZONE_CHANGE_DIRECT_DEPENDENCIES_PROJECTED", "selected_rule_count": len(rules),
        "foundational_projection_id": FOUNDATIONAL_PROJECTION_ID,
        "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "object_control_projection_id": OBJECT_CONTROL_PROJECTION_ID,
        "zone_change_projection_id": ZONE_CHANGE_PROJECTION_ID,
        "source_binding": _json(SOURCE_BINDING), "authorization": _json(AUTHORIZATION),
        "rules": rules, "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "new_boundaries": _json(NEW_BOUNDARIES), "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS),
    })


def build_zone_change_dependency_source(artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Require the exact external source artifact before constructing evidence."""
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
                           source_root=source_root, discovery_root=discovery_root)
    return _build_projection(data)


def build_zone_change_dependency_projection(artifact_path, *, artifact_review_root, source_root, discovery_root):
    return build_zone_change_dependency_source(artifact_path, artifact_review_root=artifact_review_root,
                                              source_root=source_root, discovery_root=discovery_root)


def verify_zone_change_dependency_projection_source(projection, artifact_path, *, artifact_review_root,
                                                    source_root, discovery_root):
    """Reproduce authored records and exact source anchors from the verified bytes."""
    if not isinstance(projection, ZoneChangeDependencyProjection):
        _fail("typed non-executable zone-change dependency projection required")
    projection.verify()
    reproduced = build_zone_change_dependency_source(artifact_path, artifact_review_root=artifact_review_root,
                                                     source_root=source_root, discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("zone-change dependency source anchors or authored records do not reproduce")
    return {
        "status": "VERIFIED_EXACT_SOURCE_SPANS", "projection_id": projection.identity,
        "selected_rule_count": len(SELECTED_REFERENCES), "source_anchor_count": len(SELECTED_REFERENCES),
        "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH, "effective_date": EFFECTIVE_DATE,
        "direct_dependency_targets_represented": ["611.3d", "704.5m", "702.35", "123.5"],
        "semantic_closure_state": "OPEN", "execution_ready": False,
        "source_body_retained": False, "execution_authorized": False, "real_rules_executable": False,
    }
