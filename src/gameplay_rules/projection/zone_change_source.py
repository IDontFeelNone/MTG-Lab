"""Transient verification of the twelve authorized 400.7 exception lines.

This reuses the exact-artifact verifier and bounded byte-line locator. Only
direct 400.7 child identifiers and references in selected lines are inspected;
no downstream source body, parent semantics, or official prose is retained.
"""
from __future__ import annotations

import re

from gameplay_rules.errors import GameplayContractError
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _json
from .source import _verified_bytes, _locate_anchors
from .zone_change_contracts import (
    ZoneChangeProjection, FOUNDATIONAL_PROJECTION_ID, DEPENDENCY_PROJECTION_ID,
    OBJECT_CONTROL_PROJECTION_ID, SOURCE_BINDING, AUTHORIZATION, BOUNDARY_FLAGS, rule_identity,
)
from .zone_change_scope import (
    SELECTED_REFERENCES, RULE_CONTENT, LETTERING_POLICY, GRAPH_NODES, GRAPH_EDGES,
    NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)


def _fail(field):
    raise GameplayContractError("zone_change_projection_source", field)


def _enumerate_direct_family(data):
    """Observe just bounded child identifiers, without extracting rule bodies."""
    pattern = re.compile(rb"^(400\.7[a-z]+)\.?[ \t]+")
    references = []
    for line in data.splitlines():
        match = pattern.match(line)
        if match:
            references.append(match.group(1).decode("ascii"))
    if tuple(references) != SELECTED_REFERENCES:
        _fail("direct exception enumeration must be exactly 400.7a-k/m, uniquely and in source order")
    return tuple(references)


def _locate_zone_change_anchors(data):
    """Bind all selected lines and prove expected lettering and direct refs."""
    _enumerate_direct_family(data)
    anchors = [{**anchor, "effective_date": EFFECTIVE_DATE}
               for anchor in _locate_anchors(data, references=SELECTED_REFERENCES)]
    reference_pattern = re.compile(rb"\brules?[ \t]+([0-9]{3}(?:\.[0-9]+[a-z]?)?)\b", re.IGNORECASE)
    for anchor in anchors:
        # A transient selected-line inspection validates explicit references;
        # neither the selected bytes nor downstream source text is returned.
        selected_line = data[anchor["byte_start"]:anchor["byte_end"]]
        explicit = [match.decode("ascii") for match in reference_pattern.findall(selected_line)]
        expected = list(RULE_CONTENT[anchor["rule_reference"]]["direct_dependency_references"])
        if explicit != expected:
            _fail("selected explicit numbered source references do not match the fixed reviewed scope")
    return anchors


def _build_projection(data):
    rules = []
    for anchor in _locate_zone_change_anchors(data):
        rule = {"rule_reference": anchor["rule_reference"],
                **_json(RULE_CONTENT[anchor["rule_reference"]]), "source_anchor": anchor}
        rule["rule_id"] = rule_identity(rule)
        rules.append(rule)
    return ZoneChangeProjection.create({
        "game_id": "magic", "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "ZONE_CHANGE_EXCEPTION_FAMILY_PROJECTED", "selected_rule_count": len(rules),
        "foundational_projection_id": FOUNDATIONAL_PROJECTION_ID,
        "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "object_control_projection_id": OBJECT_CONTROL_PROJECTION_ID,
        "source_binding": _json(SOURCE_BINDING), "authorization": _json(AUTHORIZATION),
        "lettering_policy": _json(LETTERING_POLICY), "rules": rules,
        "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "new_boundaries": _json(NEW_BOUNDARIES), "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS),
    })


def build_zone_change_source(artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Require the exact external verified artifact before constructing records."""
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
                           source_root=source_root, discovery_root=discovery_root)
    return _build_projection(data)


def build_zone_change_projection(artifact_path, *, artifact_review_root, source_root, discovery_root):
    return build_zone_change_source(artifact_path, artifact_review_root=artifact_review_root,
                                   source_root=source_root, discovery_root=discovery_root)


def verify_zone_change_projection_source(projection, artifact_path, *,
                                         artifact_review_root, source_root, discovery_root):
    """Reproduce authored records, span hashes, and bounded enumeration from bytes."""
    if not isinstance(projection, ZoneChangeProjection):
        _fail("typed non-executable zone-change projection required")
    projection.verify()
    reproduced = build_zone_change_source(artifact_path, artifact_review_root=artifact_review_root,
                                          source_root=source_root, discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict():
        _fail("zone-change source anchors or authored records do not reproduce")
    return {
        "status": "VERIFIED_EXACT_SOURCE_SPANS", "projection_id": projection.identity,
        "selected_rule_count": len(SELECTED_REFERENCES), "source_anchor_count": len(SELECTED_REFERENCES),
        "artifact_hash": ARTIFACT_HASH, "byte_length": ARTIFACT_BYTE_LENGTH, "effective_date": EFFECTIVE_DATE,
        "direct_family_status": "DIRECT_EXCEPTION_FAMILY_REPRESENTED",
        "lettering_classification": "EXPECTED_CR_SUBRULE_LETTERING", "source_anomaly": False,
        "source_body_retained": False, "execution_authorized": False, "real_rules_executable": False,
    }
