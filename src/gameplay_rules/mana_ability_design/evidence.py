"""Pinned repository evidence for a design that never opens a CR artifact.

The latest retained loader validates its complete eight-package ancestry. Only
stable rule and review identities enter this design; historical source anchors
remain in their original packages and are not copied into new design records.
"""
from __future__ import annotations

import json
from pathlib import Path

from gameplay_rules.casting_design.evidence import (
    PACKAGE_IDS as CASTING_PRIOR_PACKAGE_IDS,
    RETAINED_BINDING as CASTING_RETAINED_BINDING,
)
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection.bounded_casting_package import (
    load_bounded_casting_package,
    package_manifest as bounded_casting_manifest,
)
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.projection.object_control_contracts import ObjectControlProjection

from .common import _exact, _freeze, _json


PACKAGE_IDS = _freeze({
    **_json(CASTING_PRIOR_PACKAGE_IDS),
    "madness_casting_dependency_design": "sha256:06cd012d08d204f10337d834f312bcf19b060a3569ef3cf879c46714d30944c8",
    "bounded_casting_projection": "sha256:d2b1832f170d1bbd6ef21efe3d3452923880cc47c57dad523f7aefff4bc427d7",
})
PACKAGE_FOLDERS = _freeze({
    "foundational": "gameplay-rules-foundational-projection",
    "execution_profile_design": "gameplay-rules-execution-profile-design",
    "direct_foundational_dependencies": "gameplay-rules-foundational-dependencies",
    "object_control_exceptions": "gameplay-rules-object-control-exceptions",
    "zone_change_exceptions": "gameplay-rules-zone-change-exceptions",
    "zone_change_direct_dependencies": "gameplay-rules-zone-change-direct-dependencies",
    "madness_casting_dependency_design": "gameplay-rules-madness-casting-design",
    "bounded_casting_projection": "gameplay-rules-bounded-casting-projection",
})
BOUNDED_CASTING_PROJECTION_ID = "sha256:d2ce6fdca9cd7856658cd2ae0acf184069a375cc01a67cd2f612558835d0c9a6"
OBJECT_CONTROL_PROJECTION_ID = "sha256:f4b75e686bfb5202f54818dc4fc9247a49a6e6ef84e2d57f070e990c25b6cce9"
CASTING_READINESS_ID = "sha256:ea27a6f08ae9dc4696871fdbe5560587dd76f4a7e459ba458d70cb991340b38f"
HISTORICAL_ACQUISITION_ID = CASTING_RETAINED_BINDING["historical_acquisition_identity"]


def _consumer(reference, identity, projection):
    return {
        "rule_reference": reference,
        "rule_id": identity,
        "projection_id": projection,
        "direct_dependency_references": ["605"],
        "coverage_state": "EXISTING_PROJECTED_EVIDENCE_UNCHANGED",
        "dependency_state": "UNRESOLVED",
        "dependency_coverage_state": "UNPROJECTED",
    }


RETAINED_BINDING = _freeze({
    "authority": "EXISTING_IMMUTABLE_PROJECTED_EVIDENCE_ONLY",
    "projected_real_source_units": 68,
    "prior_package_ids": PACKAGE_IDS,
    "consumers": {
        "601.2g": _consumer(
            "601.2g", "sha256:7c01241cb591680e28dd16dd3c97b88b28ebcdaca80af8c153a5891e1363a662",
            BOUNDED_CASTING_PROJECTION_ID),
        "109.4a": _consumer(
            "109.4a", "sha256:7793b14d8f2af5916dd02316ff0ea817d77b0bf656284c0f56d86b3f743fcea1",
            OBJECT_CONTROL_PROJECTION_ID),
    },
    "madness_projection_id": CASTING_RETAINED_BINDING["madness_projection_id"],
    "madness_rules": CASTING_RETAINED_BINDING["madness_rules"],
    "zone_change_lookup": CASTING_RETAINED_BINDING["zone_change_lookup"],
    "bounded_casting_readiness_id": CASTING_READINESS_ID,
    "historical_acquisition_identity": HISTORICAL_ACQUISITION_ID,
})
EXISTING_UNPROJECTED_REFERENCES = (
    "613", "605", "603", "603.7d", "603.7e", "603.7f", "114",
    "901.6", "902.6", "904.7", "905.5", "601.2a", "601.2c", "601.2d",
    "601.3", "733", "700.2", "702.47", "118.8", "118.9", "107.3",
    "601.2e", "601.2i",
)


def _fail(message="invalid retained mana-ability design evidence"):
    raise GameplayContractError("mana_ability_design_evidence", message)


def _find_rule(projection, reference):
    rules = [row for row in projection.to_dict()["rules"]
             if row["rule_reference"] == reference]
    if len(rules) != 1:
        _fail("exactly one retained consumer rule required")
    return rules[0]


def _check_consumer(projection, reference):
    expected = RETAINED_BINDING["consumers"][reference]
    row = _find_rule(projection, reference)
    _exact(projection.identity, expected["projection_id"], "consumer_projection")
    _exact(row["rule_id"], expected["rule_id"], "consumer_rule_id")
    _exact(row["direct_dependency_references"], ["605"], "consumer_direct_dependencies")
    unresolved = [item for item in row["unresolved_dependencies"]
                  if item["reference"] == "605"]
    if len(unresolved) != 1:
        _fail("consumer must retain the unresolved 605 dependency")
    _exact(unresolved[0]["status"], "UNRESOLVED", "consumer_dependency_state")
    if unresolved[0].get("coverage_state", "UNPROJECTED") != "UNPROJECTED":
        _fail("605 must remain unprojected")
    _exact(row["execution_ready"], False, "consumer_execution_ready")


def load_retained_evidence(review_root):
    """Validate eight immutable packages and return anchor-free identity bindings.

    The underlying loader uses only retained canonical package bytes. It never
    requests a source-artifact path or claims that this design reverified CR text.
    """
    try:
        root = _root(review_root)
        records = load_bounded_casting_package(
            root / PACKAGE_FOLDERS["bounded_casting_projection"], review_root=root)
        manifest = bounded_casting_manifest(records)
        _exact(manifest["package_id"], PACKAGE_IDS["bounded_casting_projection"], "retained_package")
        _exact(manifest["prior_package_ids"],
               {key: value for key, value in PACKAGE_IDS.items()
                if key != "bounded_casting_projection"}, "retained_package_ancestry")
        # All eight package loaders have already checked canonical content. Pin
        # their immutable manifest identities independently at this new boundary.
        for name, folder in PACKAGE_FOLDERS.items():
            prior_manifest = json.loads(_read(root / folder / "manifest.json"))
            _exact(prior_manifest["package_id"], PACKAGE_IDS[name], "prior_package_id")
        projection = records["projection.json"]
        _check_consumer(projection, "601.2g")
        object_control = ObjectControlProjection.from_json(_read(
            root / PACKAGE_FOLDERS["object_control_exceptions"] / "projection.json"))
        _check_consumer(object_control, "109.4a")
        _exact(records["casting-readiness-reassessment.json"].identity,
               CASTING_READINESS_ID, "casting_readiness")
        madness = records["madness-readiness-reassessment.json"].to_dict()["findings"]
        _exact(madness["retained_madness_rules"], RETAINED_BINDING["madness_rules"], "madness_rules")
        _exact(madness["retained_zone_change_lookup"], RETAINED_BINDING["zone_change_lookup"], "zone_lookup")
        coverage = records["composite-coverage.json"].to_dict()["findings"]
        _exact(coverage["total_projected_rule_count"], 68, "retained_coverage")
        _exact(coverage["component_rule_counts"], [20, 12, 7, 12, 12, 5], "component_counts")
        references = coverage["projected_references"]
        if (len(references) != 68 or len(set(references)) != 68 or
                any(reference == "605" or reference.startswith("605.") for reference in references)):
            _fail("exactly 68 distinct retained source units and no 605 projection required")
        _exact(coverage["remaining_unresolved_rules"], EXISTING_UNPROJECTED_REFERENCES,
               "remaining_references")
        _exact(coverage["historical_acquisition_identity"], HISTORICAL_ACQUISITION_ID,
               "historical_acquisition_identity")
        return _json(RETAINED_BINDING)
    except GameplayContractError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError,
            UnicodeError, RecursionError):
        _fail()
