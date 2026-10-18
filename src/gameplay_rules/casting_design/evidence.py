"""Pinned retained knowledge only; this design never opens a source artifact."""
from pathlib import Path

from .common import _exact, _freeze, _json
from gameplay_rules.projection.dependency_package import _read
from gameplay_rules.projection.zone_change_contracts import ZoneChangeProjection
from gameplay_rules.projection.zone_change_dependency_package import (
    load_zone_change_dependency_package, package_manifest,
)

PACKAGE_IDS = _freeze({
    "foundational": "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea",
    "execution_profile_design": "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687",
    "direct_foundational_dependencies": "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a",
    "object_control_exceptions": "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab",
    "zone_change_exceptions": "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875",
    "zone_change_direct_dependencies": "sha256:d51fab1425f6aa9b82e4621ac8c88d4b83d736c6906a4f4c589c41ff1aeadba4",
})
RETAINED_BINDING = _freeze({
    "authority": "EXISTING_IMMUTABLE_PROJECTED_EVIDENCE_ONLY",
    "projected_real_source_units": 63,
    "prior_package_ids": PACKAGE_IDS,
    "madness_projection_id": "sha256:979d1f829e005664c638424e3613699dc19b0a3af97ceb0bfb68e8a12890ae9a",
    "madness_rules": [
        {"rule_reference": "702.35a", "rule_id": "sha256:48da52c60c006aaae9a752b23155581474244b4a7b3a050b588fb2f51c1b6534"},
        {"rule_reference": "702.35b", "rule_id": "sha256:884e5ecb63b242196785a1d38f8a3014896342a6d4b738e6005430c1ac22d5ae"},
        {"rule_reference": "702.35c", "rule_id": "sha256:79b507ab353539b0d1166876f25c279a2171f860f69ab40b53cc2d942f198fb4"},
    ],
    "zone_change_projection_id": "sha256:0b32e8c16fc2089949d50c0ece4b2afb7b69355f2573f041cfc8b932aa4db141",
    "zone_change_lookup": {"rule_reference": "400.7k", "rule_id": "sha256:5fd728b81834e50cc3555e61fd9cf9f9cb6e3cce172618d23cfcd0649efe21c5"},
    "closure_review_id": "sha256:b8958164e53a1fe4d76888b28e9c164a9615a69bad217bcd18669e808548d2f7",
    "zone_change_readiness_id": "sha256:df7f9ad6c4949f7dec55839a4009c639e0ae6d7e377f076d97788dab8fe3aae3",
    "historical_acquisition_identity": "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53",
})
EXISTING_UNPROJECTED_REFERENCES = (
    "613", "605", "603", "603.7d", "603.7e", "603.7f", "114",
    "901.6", "902.6", "904.7", "905.5", "601.2b", "601.2f", "601.2g", "601.2h",
)


def load_retained_evidence(review_root):
    """Reproduce the latest retained package and its immutable six-package chain."""
    root = Path(review_root)
    roots = {name: root / folder for name, folder in {
        "projection_root": "gameplay-rules-foundational-projection",
        "design_root": "gameplay-rules-execution-profile-design",
        "dependency_root": "gameplay-rules-foundational-dependencies",
        "object_control_root": "gameplay-rules-object-control-exceptions",
        "zone_change_root": "gameplay-rules-zone-change-exceptions",
        "artifact_review_root": "gameplay-rules-artifact-verification",
        "source_root": "gameplay-rules-source-versioning",
        "discovery_root": "gameplay-rules-release-discovery-closure",
    }.items()}
    records = load_zone_change_dependency_package(root / "gameplay-rules-zone-change-direct-dependencies", **roots)
    raw = {name: (record.serialize() + "\n").encode() for name, record in records.items()}
    manifest = package_manifest(records, raw)
    _exact(manifest["package_id"], PACKAGE_IDS["zone_change_direct_dependencies"], "retained_package")
    _exact(records["projection.json"].identity, RETAINED_BINDING["madness_projection_id"], "madness_projection")
    rules = records["projection.json"].to_dict()["rules"]
    _exact([{key: row[key] for key in ("rule_reference", "rule_id")} for row in rules
            if row["rule_reference"] in {"702.35a", "702.35b", "702.35c"}], RETAINED_BINDING["madness_rules"], "madness_rules")
    zone = ZoneChangeProjection.from_json(_read(roots["zone_change_root"] / "projection.json"))
    _exact(zone.identity, RETAINED_BINDING["zone_change_projection_id"], "zone_projection")
    lookup = next(row for row in zone.to_dict()["rules"] if row["rule_reference"] == "400.7k")
    _exact({key: lookup[key] for key in ("rule_reference", "rule_id")}, RETAINED_BINDING["zone_change_lookup"], "zone_lookup")
    _exact(records["closure-review.json"].identity, RETAINED_BINDING["closure_review_id"], "retained_closure")
    _exact(records["zone-change-readiness-reassessment.json"].identity, RETAINED_BINDING["zone_change_readiness_id"], "retained_readiness")
    coverage = records["composite-coverage.json"].to_dict()
    _exact(coverage["total_projected_rule_count"], 63, "retained_coverage")
    _exact(coverage["remaining_unresolved_rules"], EXISTING_UNPROJECTED_REFERENCES, "remaining_references")
    return _json(RETAINED_BINDING)
