"""Read-only verification of the bounded metadata review package.

The fixed inventory contains authored metadata, not source documents. The
manifest never accepts caller-defined exclusions or repairs changed identities.
"""
import hashlib
import json
from pathlib import Path

from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from .contracts import (AUTHORITY_RANKS, EVIDENCE_STATES, PERMISSION_OPERATIONS, PERMISSION_STATES,
                        EvidenceIndex, VersionSelection)
from .selection import select_version


PACKAGE_SCHEMA = "gameplay-rules-source-review-v1"
REVIEW_FILES = frozenset({"source-authority.json", "source-inventory.json",
    "release-candidates.json", "release-lineage.json", "permission-matrix.json",
    "current-selection.json", "readiness.json"})
MAX_METADATA_FILE_BYTES = 64_000
_SCHEMAS = {"source-authority.json": "gameplay-source-authority-v1",
    "release-candidates.json": "gameplay-release-candidate-inventory-v1",
    "release-lineage.json": "gameplay-release-lineage-v1",
    "permission-matrix.json": "gameplay-source-permission-matrix-v1",
    "readiness.json": "gameplay-source-readiness-v1"}


def package_identity(manifest_body):
    return "sha256:" + sha256_identity({"domain": PACKAGE_SCHEMA, "content": manifest_body})


def _fail(reason):
    raise GameplayContractError("source_review_package", reason)


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result: _fail("duplicate review JSON key")
        result[key] = value
    return result


def _nonfinite(_value):
    _fail("non-finite review JSON value")


def _keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail("missing or undeclared metadata fields")


def _summary(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        _fail("a bounded authored metadata summary is required")


def _strings(value):
    if not isinstance(value, list) or len(value) > 64:
        _fail("a bounded metadata string array is required")
    for text in value: _summary(text)


def verify_review_package(root):
    """Verify exact bytes, identities and cross-file readiness without I/O outside root."""
    try:
        root = Path(root)
        if any(path.is_symlink() for path in (root, *root.parents)) or not root.is_dir():
            _fail("an explicit ordinary review directory is required")
        paths = list(root.rglob("*"))
        if any(path.is_symlink() or not path.is_file() for path in paths):
            _fail("review package cannot contain directories, links or special files")
        if {path.name for path in paths} != REVIEW_FILES | {"manifest.json"}:
            _fail("review package inventory differs from its fixed metadata contract")
        documents, raw = {}, {}
        for path in paths:
            if path.stat().st_size > MAX_METADATA_FILE_BYTES:
                _fail("review metadata exceeds bounded size")
            data = path.read_bytes()
            if len(data) > MAX_METADATA_FILE_BYTES: _fail("review metadata exceeds bounded size")
            raw[path.name] = data
            documents[path.name] = json.loads(data.decode("utf-8"), object_pairs_hook=_unique,
                                            parse_constant=_nonfinite)
        manifest = documents["manifest.json"]
        if set(manifest) != {"schema_version", "package_id", "files", "evidence_index_id",
                "version_selection_id", "metadata_only", "raw_source_retained", "projection_authorized"}:
            _fail("manifest fields differ from the metadata-only contract")
        if manifest["schema_version"] != PACKAGE_SCHEMA or manifest["metadata_only"] is not True or manifest["raw_source_retained"] is not False or manifest["projection_authorized"] is not False:
            _fail("review package cannot authorize source retention or rule projection")
        body = {key: value for key, value in manifest.items() if key != "package_id"}
        if manifest["package_id"] != package_identity(body): _fail("review package identity mismatch")
        if set(manifest["files"]) != REVIEW_FILES: _fail("manifest inventory mismatch")
        for name, binding in manifest["files"].items():
            if set(binding) != {"sha256", "bytes"} or type(binding["bytes"]) is not int:
                _fail("invalid metadata file binding")
            if binding["bytes"] != len(raw[name]) or binding["sha256"] != hashlib.sha256(raw[name]).hexdigest():
                _fail("metadata file integrity mismatch")
        index = EvidenceIndex.from_dict(documents["source-inventory.json"])
        selection = VersionSelection.from_dict(documents["current-selection.json"])
        for name, version in _SCHEMAS.items():
            if documents[name].get("schema_version") != version: _fail("unsupported review metadata schema")
        if manifest["evidence_index_id"] != index.identity or manifest["version_selection_id"] != selection.identity or selection.evidence_index_id != index.identity:
            _fail("review index/selection binding mismatch")
        reproduced = select_version(index, scope=selection.scope, as_of_date=selection.as_of_date,
                                    release_id=selection.release_id, review_id=selection.source_review_id)
        if reproduced.to_dict() != selection.to_dict(): _fail("reviewed selection does not reproduce")
        authority = documents["source-authority.json"]
        _keys(authority, {"schema_version", "source_classes", "precedence_rule", "real_rules_executable"})
        _summary(authority["precedence_rule"])
        if authority["source_classes"] != AUTHORITY_RANKS or authority["real_rules_executable"] is not False:
            _fail("source authority or non-execution boundary differs")
        candidates = documents["release-candidates.json"]
        lineage = documents["release-lineage.json"]
        _keys(candidates, {"schema_version", "evidence_index_id", "release_candidates", "unverified_review_leads"})
        if not isinstance(candidates["unverified_review_leads"], list): _fail("review leads must be bounded metadata")
        for lead in candidates["unverified_review_leads"]:
            _keys(lead, {"origin", "topic", "officially_verified"})
            _summary(lead["origin"])
            _summary(lead["topic"])
            if lead["officially_verified"] is not False: _fail("a review lead cannot claim verification")
        _keys(lineage, {"schema_version", "evidence_index_id", "relations", "reality_fracture_check"})
        check = lineage["reality_fracture_check"]
        _keys(check, {"status", "evidence_reference_ids", "reason"})
        if check["status"] not in {"NOT_VERIFIED", "VERIFIED"}: _fail("invalid update incorporation status")
        _strings(check["evidence_reference_ids"])
        _summary(check["reason"])
        if candidates["evidence_index_id"] != index.identity or candidates["release_candidates"] != list(index.to_dict()["release_candidates"]):
            _fail("candidate inventory correspondence mismatch")
        if lineage["evidence_index_id"] != index.identity or lineage["relations"] != index.to_dict()["relations"]:
            _fail("lineage correspondence mismatch")
        permissions = documents["permission-matrix.json"]
        _keys(permissions, {"schema_version", "scope", "operations", "components", "project_authored_metadata"})
        _summary(permissions["scope"])
        own = permissions["project_authored_metadata"]
        _keys(own, {"status", "retention_scope", "does_not_establish_upstream_permissions"})
        _summary(own["retention_scope"])
        if own["status"] != "NOT_APPLICABLE" or own["does_not_establish_upstream_permissions"] is not True:
            _fail("authored metadata cannot grant upstream permission")
        if permissions["operations"] != list(PERMISSION_OPERATIONS): _fail("permission matrix is incomplete")
        components = permissions["components"]
        if not isinstance(components, list) or not components: _fail("permission components required")
        if len({row["component_id"] for row in components}) != len(components): _fail("duplicate permission component")
        sources = {source["source_reference_id"]: source for source in index.to_dict()["source_references"]}
        if not set(check["evidence_reference_ids"]) <= set(sources) or (check["status"] == "VERIFIED" and not check["evidence_reference_ids"]):
            _fail("update incorporation requires retained source evidence")
        if check["status"] == "VERIFIED" and any(sources[reference]["evidence_status"] not in {"VERIFIED_ARTIFACT", "VERIFIED_METADATA_ONLY"} for reference in check["evidence_reference_ids"]):
            _fail("unavailable evidence cannot verify update incorporation")
        for row in components:
            _keys(row, {"component_id", "source_class", "source_reference_id", "evidence_status", "permission_status"})
            _summary(row["component_id"])
            if row["source_class"] not in AUTHORITY_RANKS or row["evidence_status"] not in EVIDENCE_STATES or (row["source_reference_id"] is not None and row["source_reference_id"] not in sources):
                _fail("permission component authority/dependency is unbound")
            if set(row["permission_status"]) != set(PERMISSION_OPERATIONS): _fail("permission operations missing")
            for permission in row["permission_status"].values():
                if set(permission) != {"status", "evidence_references", "conditions"} or permission["status"] not in PERMISSION_STATES:
                    _fail("invalid permission assessment")
                _strings(permission["evidence_references"])
                _strings(permission["conditions"])
                if permission["status"] in {"ESTABLISHED", "ESTABLISHED_WITH_CONDITIONS"} and not permission["evidence_references"]:
                    _fail("established permission requires retained evidence")
                if permission["status"] == "ESTABLISHED_WITH_CONDITIONS" and not permission["conditions"]:
                    _fail("conditional permission requires retained conditions")
                if permission["status"] in {"ESTABLISHED", "ESTABLISHED_WITH_CONDITIONS"} and any(reference not in sources or sources[reference]["evidence_status"] not in {"VERIFIED_ARTIFACT", "VERIFIED_METADATA_ONLY"} for reference in permission["evidence_references"]):
                    _fail("established permission cannot cite unavailable or unretained evidence")
        for source in index.to_dict()["source_references"]:
            rows = [row for row in components if row["source_reference_id"] == source["source_reference_id"]]
            if len(rows) != 1 or rows[0]["permission_status"] != source["permission_status"]:
                _fail("source permission correspondence mismatch")
        readiness = documents["readiness.json"]
        _keys(readiness, {"schema_version", "evidence_index_id", "version_selection_id", "status", "currentness_status", "blocking_reasons", "projection_authorized", "real_rules_executable", "full_source_retained", "source_policy_clearance", "review_observed_at", "research_scope", "future_handoff"})
        _strings(readiness["blocking_reasons"])
        _keys(readiness["research_scope"], {"explicit_url", "bounded_attempts", "origin_http_status", "additional_discovery_attempts", "configured_policy_excludes_wizards_domains"})
        handoff = readiness["future_handoff"]
        _keys(handoff, {"required", "projection_implemented", "gameplay_kernel_remains_fictional_only"})
        _strings(handoff["required"])
        if handoff["projection_implemented"] is not False or handoff["gameplay_kernel_remains_fictional_only"] is not True:
            _fail("future handoff cannot activate real rules")
        if readiness["evidence_index_id"] != index.identity or readiness["version_selection_id"] != selection.identity or readiness["status"] not in {"READY_FOR_RULE_PROJECTION", "NOT_READY_FOR_RULE_PROJECTION"}:
            _fail("readiness identity/status mismatch")
        if selection.status == "NOT_READY_FOR_RULE_PROJECTION" and readiness["status"] != selection.status:
            _fail("package readiness cannot upgrade a blocked selection")
        if readiness["status"] == "READY_FOR_RULE_PROJECTION" and (readiness["blocking_reasons"] or check["status"] != "VERIFIED"):
            _fail("ready package requires complete consistency evidence without blockers")
        if readiness["status"] == "NOT_READY_FOR_RULE_PROJECTION" and not readiness["blocking_reasons"]:
            _fail("blocked package requires explicit blockers")
        if readiness["projection_authorized"] is not False or readiness["real_rules_executable"] is not False or readiness["full_source_retained"] is not False or readiness["source_policy_clearance"] != "not_granted":
            _fail("readiness cannot activate rules or establish permission")
        if not set(selection.blocking_reasons) <= set(readiness["blocking_reasons"]):
            _fail("readiness omits selection blockers")
        if readiness["status"] == "NOT_READY_FOR_RULE_PROJECTION" and readiness["currentness_status"] != "CURRENT_RULES_RELEASE_NOT_VERIFIED":
            _fail("blocked readiness cannot claim verified currentness")
        if not any(row["reviewed_at"] == readiness["review_observed_at"] for row in index.to_dict()["reviews"]):
            _fail("readiness observation must bind a retained review")
        research = readiness["research_scope"]
        if research["explicit_url"] not in {row["authoritative_reference"] for row in sources.values()}:
            _fail("research URL must bind a retained source reference")
        if type(research["bounded_attempts"]) is not int or not 0 <= research["bounded_attempts"] <= 8 or type(research["additional_discovery_attempts"]) is not int or not 0 <= research["additional_discovery_attempts"] <= 8 or type(research["configured_policy_excludes_wizards_domains"]) is not bool:
            _fail("invalid bounded research observation")
        status = research["origin_http_status"]
        if status is not None and (type(status) is not int or not 100 <= status <= 599): _fail("invalid origin HTTP observation")
        if research["configured_policy_excludes_wizards_domains"] and status is not None:
            _fail("environment denial cannot claim an origin HTTP result")
        return {"package_id": manifest["package_id"], "evidence_index_id": index.identity,
                "version_selection_id": selection.identity, "status": readiness["status"],
                "integrity_verified": True, "metadata_only": True,
                "projection_authorized": False}
    except GameplayContractError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError, RecursionError):
        _fail("missing, unreadable or malformed metadata review package")
