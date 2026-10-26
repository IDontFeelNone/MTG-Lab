"""Read the pilot's exact retained CR evidence, without reading a source body.

The existing package readers verify actual metadata bytes and historical lineage.
They reproduce authored metadata, not fresh source verification or Card semantics.
No successful check is cached. Paths do not enter the returned content.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from evidence.contracts import deterministic_json, sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.projection import bounded_mana_package as mana
from gameplay_rules.projection import mana_classification_package as classification
from gameplay_rules.projection import mana_stack_exception_package as stack
from gameplay_rules.projection.dependency_package import _read, _root
from gameplay_rules.source_evidence.artifact_review import verify_artifact_review_package
from gameplay_rules.activated_ability_projection import package as activated

MANA_PACKAGE = "gameplay-rules-bounded-mana-ability-projection"
PACKAGE_IDS = {
    MANA_PACKAGE: "sha256:010ab048c504b4da4327dbda4a666a6754f2d41e93b73ea34bc595b39c929990",
    classification.PACKAGE_NAME: "sha256:57c9a21ec6a253ad9bfc3a650ec2edc8a389a456eb555a213c3a3f5c673eea73",
    stack.PACKAGE_NAME: "sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1",
}
ACTIVATED_PACKAGE_ID = "sha256:02667e58da72701b7464275184de452a1ec53f34b7dedc80ca3cde8c595a7ff4"
ARTIFACT = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
VERIFICATION = "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3"
RELEASE = "2026-09-25"


def _fail(message):
    raise GameplayContractError("card_rules_pilot_rules", message)


def _identity(domain, value, own):
    return "sha256:" + sha256_identity({"domain": domain,
        "content": {k: v for k, v in value.items() if k != own}})


def _record(path):
    raw = _read(path)
    # Exact canonical bytes reject duplicate JSON keys, nonfinite values, unknown
    # encodings and numeric substitutions against the pinned enclosing manifest.
    value = json.loads(raw)
    if type(value) is not dict or (deterministic_json(value) + "\n").encode() != raw:
        _fail("canonical retained record required")
    return value, raw


def _manifest(root, expected_id):
    value, _ = _record(root / "manifest.json")
    if (type(value.get("schema_version")) is not str
            or value.get("package_id") != expected_id
            or _identity(value["schema_version"], value, "package_id") != expected_id):
        _fail("retained package own identity mismatch")
    return value


def _activated_review(root):
    """Verify the later append-only assessment, without importing 602 semantics.

    This schema's integer version is intentionally distinct from its hash domain.
    The fixed package identity binds all canonical files; no review body supplies
    an additional pilot rule or an activation engine.
    """
    directory = _root(root / activated.PACKAGE_NAME)
    manifest = _manifest(directory, ACTIVATED_PACKAGE_ID)
    names = set(activated.RECORD_NAMES)
    if {p.name for p in directory.iterdir()} != names | {"manifest.json"}:
        _fail("later dependency package file set changed")
    if set(manifest["files"]) != names or set(manifest["record_ids"]) != names:
        _fail("later dependency package manifest bindings changed")
    reviews = {}
    for filename in sorted(names):
        row, raw = _record(directory / filename)
        own = "projection_id" if filename == "projection.json" else "review_id"
        domain = ("gameplay-cr-bounded-activated-ability-projection-v1"
                  if own == "projection_id" else activated.RECORD_DOMAIN)
        schema = row.get("schema_version")
        if not ((type(schema) is str and schema == domain) if own == "projection_id"
                else (type(schema) is int and schema == 1)):
            _fail("later dependency record schema mismatch")
        if (type(row.get(own)) is not str or row[own] != _identity(domain, row, own)
                or manifest["record_ids"][filename] != row[own]
                or deterministic_json(manifest["files"][filename]) != deterministic_json({
                    "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})):
            _fail("later dependency record own identity or bytes mismatch")
        reviews[filename] = row
    row = reviews["mana-relationships.json"]
    relationships = row["findings"]["preserved_relationships"]
    selected = [r for r in relationships if r.get("origin_reference") == "605.3"
                and r.get("target_reference") == "602.2"]
    if len(selected) != 1 or selected[0]["state"] != "DIRECT_REFERENCE_RESOLVED":
        _fail("exact later 605.3 dependency reassessment required")
    return {"package": activated.PACKAGE_NAME, "package_id": manifest["package_id"],
        "record": "mana-relationships.json", "review_id": row["review_id"],
        "schema_version": 1, "identity_domain": activated.RECORD_DOMAIN,
        "status": "SEPARATELY_BOUND_LATER_APPEND_ONLY_REVIEW",
        "relationship": selected[0], "activation_engine_supplied": False}


def read_rules(review_root):
    """Check current retained metadata once and return an independent JSON view.

    Exactly 17 existing rule units may enter this interpretation context. The
    separately bound later review resolves historical source coverage only.
    """
    try:
        root = _root(review_root)
        artifact = verify_artifact_review_package(
            root / "gameplay-rules-artifact-verification",
            source_root=root / "gameplay-rules-source-versioning",
            discovery_root=root / "gameplay-rules-release-discovery-closure")
        if artifact["verification_result_id"] != VERIFICATION:
            _fail("retained artifact verification identity mismatch")
        loaded = {
            MANA_PACKAGE: {name: row.to_dict() for name, row in
                mana.load_bounded_mana_package(root / MANA_PACKAGE, review_root=root).items()},
            classification.PACKAGE_NAME: classification.load_package(
                root / classification.PACKAGE_NAME, review_root=root),
            stack.PACKAGE_NAME: stack.load_package(root / stack.PACKAGE_NAME, review_root=root),
        }
        packages, rules = [], []
        source = None
        for name, records in loaded.items():
            manifest = _manifest(root / name, PACKAGE_IDS[name])
            projection = records["projection.json"]
            binding = projection["source_binding"]
            if (binding["artifact_hash"] != ARTIFACT or binding["effective_date"] != RELEASE
                    or binding["verification_result_id"] != VERIFICATION
                    or (source is not None and source != binding)):
                _fail("retained CR release or artifact lineage mismatch")
            source = binding
            packages.append({"package": name, "package_id": manifest["package_id"],
                "schema_version": manifest["schema_version"],
                "projection_id": projection["projection_id"],
                "projection_schema_version": projection["schema_version"],
                "record_ids": manifest["record_ids"], "files": manifest["files"],
                "prior_package_ids": manifest["prior_package_ids"]})
            for rule in projection["rules"]:
                anchor = rule["source_anchor"]
                if (anchor["artifact_hash"] != ARTIFACT or anchor["effective_date"] != RELEASE
                        or anchor["rule_reference"] != rule["rule_reference"]):
                    _fail("rule anchor belongs to another retained release")
                # These are existing project-authored representations, never an
                # interpretation of fresh CR prose. Preserve all selected rule
                # metadata and limitations in readable/API context.
                rules.append({"package": name, "package_id": manifest["package_id"],
                    "projection_id": projection["projection_id"],
                    "projection_schema_version": projection["schema_version"],
                    "rule": rule})
        expected = list(mana.SELECTED_REFERENCES) + ["115.6", "606.1", "606.2", "405.6c"]
        if [r["rule"]["rule_reference"] for r in rules] != expected:
            _fail("exact retained seventeen-unit pilot context required")
        current = []
        for name, filename in ((classification.PACKAGE_NAME, "classification-dependency-review.json"),
                               (stack.PACKAGE_NAME, "consumer-reassessment.json")):
            row = loaded[name][filename]
            current.append({"package": name, "package_id": PACKAGE_IDS[name], "record": filename,
                "review_id": row["review_id"], "schema_version": row["schema_version"],
                "identity_domain": row["schema_version"],
                "status": "SEPARATELY_BOUND_LATER_APPEND_ONLY_REVIEW", "findings": row["findings"]})
        current.append(_activated_review(root))
        return json.loads(deterministic_json({"source_binding": source,
            "artifact_lineage": artifact, "packages": packages, "rules": rules,
            "current_dependency_reviews": current,
            "verification_scope": "RETAINED_METADATA_INTEGRITY_NOT_FRESH_SOURCE_VERIFICATION",
            "execution_authority": "BLOCKED"}))
    except GameplayContractError:
        raise
    except (OSError, TypeError, ValueError, KeyError, AttributeError, UnicodeError, RecursionError):
        _fail("invalid retained pilot rules evidence")
