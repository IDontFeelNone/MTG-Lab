"""Transient exact-source construction of seven fixed exception records.

The existing release verifier and bounded line locator are reused. The only
additional inspection is the parent line's declared count for the anomaly;
neither parent semantics nor downstream rule bodies receive a new projection.
"""
from __future__ import annotations

import re

from gameplay_rules.errors import GameplayContractError
from .contracts import ARTIFACT_HASH, ARTIFACT_BYTE_LENGTH, EFFECTIVE_DATE, _json
from .object_control_contracts import (
    ObjectControlProjection, SourceAnomaly, FOUNDATIONAL_PROJECTION_ID, DEPENDENCY_PROJECTION_ID,
    SOURCE_BINDING, AUTHORIZATION, BOUNDARY_FLAGS, ANOMALY_LIMITATIONS, rule_identity,
)
from .object_control_scope import (
    SELECTED_REFERENCES, PARENT_REFERENCE, RULE_CONTENT, GRAPH_NODES, GRAPH_EDGES,
    NEW_BOUNDARIES, UNSUPPORTED_DIMENSIONS,
)
from .source import _verified_bytes, _locate_anchors


def _fail(field):
    raise GameplayContractError("object_control_projection_source", field)


def _locate_object_control_anchors(data):
    """Inspect only the seven immutable authorized source-line references."""
    return [{**anchor, "effective_date": EFFECTIVE_DATE}
            for anchor in _locate_anchors(data, references=SELECTED_REFERENCES)]


def _build_source_anomaly(data):
    """Observe a bounded literal count and the seven unique selected lines.

    This does not extract a count from arbitrary CR prose or inspect deeper
    rules. The known release's parent assertion is checked transiently and no
    official wording enters the returned observation.
    """
    anchors = _locate_object_control_anchors(data)
    parent = {**_locate_anchors(data, references=(PARENT_REFERENCE,))[0],
              "effective_date": EFFECTIVE_DATE}
    parent_line = data[parent["byte_start"]:parent["byte_end"]]
    if len(re.findall(rb"\bsix\s+exceptions\b", parent_line)) != 1:
        _fail("bounded parent exception-count observation does not match verified release")
    if parent["byte_end"] > anchors[0]["byte_start"] or parent["line_number"] >= anchors[0]["line_number"]:
        _fail("parent exception-count evidence must precede the selected family")
    return SourceAnomaly.create({
        "game_id": "magic", "status": "PROJECTED_FOR_REVIEW",
        "anomaly_type": "DECLARED_ENUMERATED_COUNT_MISMATCH", "parent": PARENT_REFERENCE,
        "parent_declared_count": 6, "enumerated_subrule_count": len(anchors),
        "enumerated_refs": [anchor["rule_reference"] for anchor in anchors],
        "source_release": EFFECTIVE_DATE, "source_binding": _json(SOURCE_BINDING),
        "parent_source_anchor": parent,
        "observation_method": "BOUNDED_PARENT_COUNT_AND_AUTHORIZED_SUBRULE_ENUMERATION",
        "correction_applied": False, "interpretation": "SOURCE_INCONSISTENCY_RETAINED",
        "source_intent_inferred": False, "subrule_invalidity_inferred": False,
        "limitations": list(ANOMALY_LIMITATIONS), "boundary_flags": _json(BOUNDARY_FLAGS),
    })


def _build_projection(data):
    rules = []
    for anchor in _locate_object_control_anchors(data):
        rule = {"rule_reference": anchor["rule_reference"],
                **_json(RULE_CONTENT[anchor["rule_reference"]]), "source_anchor": anchor}
        rule["rule_id"] = rule_identity(rule)
        rules.append(rule)
    return ObjectControlProjection.create({
        "game_id": "magic", "projection_kind": "NON_EXECUTABLE", "status": "PROJECTED_FOR_REVIEW",
        "milestone_status": "OBJECT_CONTROL_EXCEPTION_FAMILY_PROJECTED", "selected_rule_count": 7,
        "foundational_projection_id": FOUNDATIONAL_PROJECTION_ID,
        "dependency_projection_id": DEPENDENCY_PROJECTION_ID,
        "source_binding": _json(SOURCE_BINDING), "authorization": _json(AUTHORIZATION),
        "rules": rules, "graph": {"nodes": _json(GRAPH_NODES), "edges": _json(GRAPH_EDGES)},
        "new_boundaries": _json(NEW_BOUNDARIES), "unsupported_dimensions": list(UNSUPPORTED_DIMENSIONS),
        "boundary_flags": _json(BOUNDARY_FLAGS),
    })


def build_object_control_source(artifact_path, *, artifact_review_root, source_root, discovery_root):
    """Require actual verified source bytes and build both independent records."""
    data = _verified_bytes(artifact_path, artifact_review_root=artifact_review_root,
                           source_root=source_root, discovery_root=discovery_root)
    # Validate the anomaly first so no artifact record is returned if the bounded
    # source observation fails; the parent remains anomaly evidence only.
    anomaly = _build_source_anomaly(data)
    return _build_projection(data), anomaly


def build_object_control_projection(artifact_path, *, artifact_review_root, source_root, discovery_root):
    return build_object_control_source(artifact_path, artifact_review_root=artifact_review_root,
                                      source_root=source_root, discovery_root=discovery_root)[0]


def build_source_anomaly(artifact_path, *, artifact_review_root, source_root, discovery_root):
    return build_object_control_source(artifact_path, artifact_review_root=artifact_review_root,
                                      source_root=source_root, discovery_root=discovery_root)[1]


def verify_object_control_projection_source(projection, anomaly, artifact_path, *,
                                            artifact_review_root, source_root, discovery_root):
    """Reproduce all selected anchors and bounded parent evidence from bytes."""
    if not isinstance(projection, ObjectControlProjection) or not isinstance(anomaly, SourceAnomaly):
        _fail("typed non-executable object-control projection and source anomaly required")
    projection.verify()
    anomaly.verify()
    reproduced, observed = build_object_control_source(artifact_path,
        artifact_review_root=artifact_review_root, source_root=source_root, discovery_root=discovery_root)
    if projection.to_dict() != reproduced.to_dict() or anomaly.to_dict() != observed.to_dict():
        _fail("object-control source anchors, authored records, or anomaly do not reproduce")
    return {
        "status": "VERIFIED_EXACT_SOURCE_SPANS", "projection_id": projection.identity,
        "anomaly_id": anomaly.identity, "selected_rule_count": 7, "source_anchor_count": 7,
        "anomaly_parent_anchor_count": 1, "artifact_hash": ARTIFACT_HASH,
        "byte_length": ARTIFACT_BYTE_LENGTH, "effective_date": EFFECTIVE_DATE,
        "source_body_retained": False, "execution_authorized": False, "real_rules_executable": False,
    }
