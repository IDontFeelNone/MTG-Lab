"""Offline checks for one proposed, fictional evidence-packet design.

This test helper validates representation and bindings. It performs no gameplay
interpretation, inference, admission or execution, and writes no retained files.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, validators
from evidence.contracts import sha256_identity
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.casting_permission_family import package as retained_family
from gameplay_rules.projection.dependency_package import _root, _read, _unique, _nonfinite
from gameplay_rules.projection.mana_stack_exception_package import _canonical_candidate

ROOT = Path(__file__).resolve().parents[1]
REVIEW_ROOT = ROOT / "reference-reviews"
PACKAGE_NAME = "gameplay-rules-proposed-spell-evidence-packet-design"
PACKAGE_ROOT = REVIEW_ROOT / PACKAGE_NAME
PACKET_DOMAIN = "proposed-spell-evidence-packet-v1"
CONTRACT_DOMAIN = "proposed-spell-evidence-packet-contract-v1"
PACKAGE_DOMAIN = "proposed-spell-evidence-packet-design-package-v1"
RECORD_DOMAIN = "proposed-spell-evidence-packet-design-record-v1"


def fail(message):
    raise GameplayContractError("proposed_spell_evidence_packet_design", message)


def identity(domain, value, field):
    return "sha256:" + sha256_identity({"domain": domain,
        "content": {key: child for key, child in value.items() if key != field}})


def seal_packet(value):
    """Test-fixture sealing only; this does not build a gameplay packet."""
    value["packet_id"] = identity(PACKET_DOMAIN, value, "packet_id")
    return value


def snapshot(value):
    return json.loads(_canonical_candidate(value))


def canonical_read(path):
    raw = _read(path)
    try:
        value = json.loads(raw, object_pairs_hook=_unique, parse_constant=_nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        fail("MALFORMED_JSON")
    if raw != _canonical_candidate(value):
        fail("CANONICAL_BYTES_REQUIRED")
    return value


StrictValidator = validators.extend(Draft202012Validator,
    type_checker=Draft202012Validator.TYPE_CHECKER.redefine(
        "integer", lambda checker, value: type(value) is int))


def retained_rules(review_root=REVIEW_ROOT):
    """Freshly validate actual own-schema history, then derive an owned index."""
    root = _root(review_root)
    records = retained_family.load_package(root / retained_family.PACKAGE_NAME,
        review_root=root)
    coverage = retained_family.composite_view(records, review_root=root)
    index = snapshot(coverage["all_prior_rule_bindings"])
    for rule in coverage["new_rule_bindings"]:
        index[rule["rule_reference"]] = {
            **rule, "retained_package": retained_family.PACKAGE_NAME}
    if (len(index) != 100 or len(coverage["projection_components"]) != 15
            or coverage["stage_coverage"] != "9/9"
            or coverage["parent_proposal_range_coverage"] != "4/4"
            or coverage["i_preceding_range_source_coverage"] != "8/8"):
        fail("RETAINED_COVERAGE_CHANGED")
    sources = {}
    for reference, row in index.items():
        if reference.startswith(("601.2", "601.3")):
            name = row["retained_package"]
            if name not in sources:
                sources[name] = canonical_read(root / name / "projection.json")["source_binding"]
            row["artifact_hash"] = sources[name]["artifact_hash"]
            row["effective_date"] = sources[name]["effective_date"]
    return index


def check_identity(value, domain, field):
    if type(value) is not dict or type(value.get(field)) is not str:
        fail("OWN_IDENTITY_REQUIRED")
    if value[field] != identity(domain, value, field):
        fail("OWN_IDENTITY_MISMATCH")


def validate_contract(value):
    value = snapshot(value)
    check_identity(value, CONTRACT_DOMAIN, "contract_id")
    if value["contract_id"] != "sha256:612f6c8a7065795e52066b30bc3b9670aacd6becbb6ae09864e6da3250d0326d":
        fail("EXACT_PROPOSED_V1_CONTRACT_REQUIRED")
    if value.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
        fail("DECLARED_DESIGN_SCHEMA_REQUIRED")
    def local_only(node):
        if type(node) is dict:
            if "$ref" in node and not node["$ref"].startswith("#/$defs/"):
                fail("LOCAL_DESIGN_REFERENCES_ONLY")
            for child in node.values():
                local_only(child)
        elif type(node) is list:
            for child in node:
                local_only(child)
    local_only(value)
    try:
        StrictValidator.check_schema(value)
    except Exception as error:
        fail("MALFORMED_DESIGN_SCHEMA: " + type(error).__name__)
    return value


def unique_index(rows, field):
    result = {}
    for row in rows:
        key = row[field]
        if key in result:
            fail("DUPLICATE_LOCAL_IDENTITY: " + field)
        result[key] = row
    return result


def resolve_many(references, index, label):
    if any(reference not in index for reference in references):
        fail("DANGLING_" + label + "_REFERENCE")


PACKET_NAMES = (
    "packet-a-conditional.json", "packet-b-missing.json", "packet-c-unsupported.json",
    "packet-d-conflict.json", "packet-e-compatibility.json")
EXPECTED_OUTCOMES = (
    "CONDITIONAL_SUPPORT", "INDETERMINATE_MISSING", "INDETERMINATE_UNSUPPORTED",
    "INDETERMINATE_CONFLICT", "INDEPENDENT_CONDITIONALS_ONLY")
RECORD_NAMES = {"contract.json", "design-assessment.json", *PACKET_NAMES}
CANONICAL_BASE = "80c7cee9c1448c97a76f7a9139b405cbcb4c3613"


def observation_material(packet, observation):
    """Bind this design's review targets and their finite reference closure."""
    indexes = {name: unique_index(packet[name], field) for name, field in (
        ("contexts", "context_id"), ("claims", "claim_id"),
        ("choices", "choice_id"), ("reasoning", "step_id"),
        ("limitations", "limitation_id"), ("rule_evidence", "evidence_id"))}
    material = {name: {} for name in indexes}
    pending = [("claims", ref) for ref in observation["claim_refs"]]
    pending.extend(("reasoning", ref) for ref in observation["step_refs"])
    while pending:
        kind, ref = pending.pop()
        if ref in material[kind]:
            continue
        row = indexes[kind][ref]
        material[kind][ref] = row
        if kind in ("claims", "choices", "reasoning"):
            pending.append(("contexts", row["context_id"]))
            if row["alternative_id"] is not None:
                pending.extend(("choices", key) for key, choice in indexes["choices"].items()
                    if (choice["context_id"], choice["alternative_id"]) ==
                    (row["context_id"], row["alternative_id"]))
        if kind == "claims":
            pending.extend(("rule_evidence", key) for key in row["rule_context_refs"])
        if kind in ("choices", "reasoning", "limitations"):
            pending.extend(("claims", key) for key in row["claim_refs"])
        if kind == "reasoning":
            pending.extend(("reasoning", key) for key in row["depends_on_steps"])
            pending.extend(("rule_evidence", key) for key in row["rule_refs"])
        if kind in ("claims", "reasoning"):
            pending.extend(("limitations", key) for key in row["limitation_refs"])
        if kind == "limitations":
            pending.extend(("contexts", key) for key in row["context_ids"])
            pending.extend(("reasoning", key) for key in row["step_refs"])
    return material


def validate_packet(value, *, contract=None, rules=None, history=None, _seen=frozenset()):
    """Return an owned structural snapshot; evidence truth remains unassessed."""
    value = snapshot(value)
    contract = validate_contract(contract if contract is not None else
        canonical_read(PACKAGE_ROOT / "contract.json"))
    try:
        StrictValidator(contract).validate(value)
    except Exception as error:
        fail("PACKET_SCHEMA: " + type(error).__name__)
    check_identity(value, PACKET_DOMAIN, "packet_id")
    if value["packet_id"] in _seen:
        fail("CYCLIC_PACKET_HISTORY")
    _seen = _seen | {value["packet_id"]}
    if value["contract_id"] != contract["contract_id"]:
        fail("CONTRACT_BINDING_MISMATCH")
    rules = retained_rules() if rules is None else snapshot(rules)
    indexes = {name: unique_index(value[name], field) for name, field in (
        ("contexts", "context_id"), ("claims", "claim_id"),
        ("choices", "choice_id"), ("reasoning", "step_id"),
        ("limitations", "limitation_id"), ("rule_evidence", "evidence_id"))}
    contexts, claims, choices, steps, limits, evidence = (
        indexes[key] for key in ("contexts", "claims", "choices", "reasoning", "limitations", "rule_evidence"))
    resolve_many([value["question"]["context_id"]], contexts, "QUESTION_CONTEXT")
    prefix = ":".join(value["lineage_id"].split(":")[:2]) + ":"
    for context in contexts.values():
        if any(not context[key].startswith(prefix) for key in ("proposal_id", "object_id", "player_id")):
            fail("FICTIONAL_SCENARIO_NAMESPACE_MISMATCH")
    for rule in evidence.values():
        actual = rules.get(rule["rule_reference"])
        if actual is None or any(rule[key] != actual.get(key) for key in (
                "retained_package", "package_id", "projection_id", "rule_id", "artifact_hash", "effective_date")):
            fail("RETAINED_RULE_BINDING_MISMATCH")
        if rule["anchor_id"] != actual["anchor_identity"]:
            fail("RETAINED_ANCHOR_BINDING_MISMATCH")
    alternatives = {(choice["context_id"], choice["alternative_id"]) for choice in choices.values()}
    for kind in ("claims", "choices", "reasoning"):
        for row in indexes[kind].values():
            resolve_many([row["context_id"]], contexts, "CONTEXT")
            if row["alternative_id"] is not None and (row["context_id"], row["alternative_id"]) not in alternatives:
                fail("DANGLING_ALTERNATIVE_REFERENCE")
            if kind == "claims":
                if not row["subject_id"].startswith(prefix) or not row["attribution"]["actor_id"].startswith(prefix):
                    fail("FICTIONAL_ASSERTION_NAMESPACE_MISMATCH")
                resolve_many(row["rule_context_refs"], evidence, "RULE_CONTEXT")
                if row["condition"] in ("UNKNOWN", "UNSUPPORTED") and row["value"] is not None:
                    fail("MISSING_OR_UNCOMPUTED_VALUE_MUST_REMAIN_NULL")
                if row["condition"] in ("PRESENT", "CONFLICTING") and row["value"] is None:
                    fail("ATTRIBUTED_VALUE_REQUIRED")
            else:
                resolve_many(row["claim_refs"], claims, "CLAIM")
                for ref in row["claim_refs"]:
                    claim = claims[ref]
                    if claim["context_id"] != row["context_id"] or claim["alternative_id"] not in (None, row["alternative_id"]):
                        fail("CLAIM_CONTEXT_OR_ALTERNATIVE_MISMATCH")
            if kind != "choices":
                resolve_many(row["limitation_refs"], limits, "LIMITATION")
                required_kind = {"UNKNOWN": "UNKNOWN", "UNSUPPORTED": "UNSUPPORTED", "CONFLICTING": "CONFLICT"}.get(row["condition"])
                if required_kind and not any(limits[ref]["kind"] == required_kind for ref in row["limitation_refs"]):
                    fail("CONDITION_REQUIRES_TYPED_LIMITATION")
                for ref in row["limitation_refs"]:
                    if row["context_id"] not in limits[ref]["context_ids"]:
                        fail("LIMITATION_CONTEXT_MISMATCH")
    seen_steps = set()
    for step in value["reasoning"]:
        resolve_many(step["rule_refs"], evidence, "RULE")
        resolve_many(step["depends_on_steps"], seen_steps, "PRECEDING_STEP")
        if (step["operation"] == "UNSUPPORTED_EVALUATION") != (step["condition"] == "UNSUPPORTED"):
            fail("UNSUPPORTED_OPERATION_CANNOT_ESTABLISH_RESULT")
        for ref in step["depends_on_steps"]:
            prior = steps[ref]
            if prior["context_id"] != step["context_id"] or prior["alternative_id"] not in (None, step["alternative_id"]):
                fail("STEP_CONTEXT_OR_ALTERNATIVE_MISMATCH")
        seen_steps.add(step["step_id"])
    for limitation in limits.values():
        resolve_many(limitation["context_ids"], contexts, "LIMITATION_CONTEXT")
        resolve_many(limitation["claim_refs"], claims, "LIMITATION_CLAIM")
        resolve_many(limitation["step_refs"], steps, "LIMITATION_STEP")
        if any(claims[ref]["context_id"] not in limitation["context_ids"] for ref in limitation["claim_refs"]):
            fail("LIMITATION_CLAIM_CONTEXT_MISMATCH")
        if any(steps[ref]["context_id"] not in limitation["context_ids"] for ref in limitation["step_refs"]):
            fail("LIMITATION_STEP_CONTEXT_MISMATCH")
        if limitation["kind"] == "CONFLICT":
            rows = [claims[ref] for ref in limitation["claim_refs"]]
            if len(rows) < 2 or any(row["condition"] != "CONFLICTING" for row in rows):
                fail("CONFLICT_MUST_PRESERVE_MULTIPLE_ASSERTIONS")
            key = lambda row: tuple(row[field] for field in ("context_id", "alternative_id", "subject_id", "predicate"))
            if len({key(row) for row in rows}) != 1 or len({_canonical_candidate(row["value"]) for row in rows}) < 2:
                fail("CONFLICT_MUST_IDENTIFY_SAME_FACT_WITH_DISTINCT_VALUES")
            if len({_canonical_candidate(row["attribution"]) for row in rows}) < 2:
                fail("CONFLICT_ATTRIBUTIONS_MUST_REMAIN_DISTINCT")
    conclusion = value["conclusion"]
    resolve_many(conclusion["step_refs"], steps, "CONCLUSION_STEP")
    resolve_many(conclusion["assumption_refs"], claims, "ASSUMPTION")
    resolve_many(conclusion["limitation_refs"], limits, "CONCLUSION_LIMITATION")
    if any(claims[ref]["role"] != "ASSUMPTION" or claims[ref]["basis"] != "AUTHORED_FICTIONAL_ASSUMPTION"
            for ref in conclusion["assumption_refs"]):
        fail("EXPLICIT_AUTHORED_ASSUMPTION_REQUIRED")
    branches = {(steps[ref]["context_id"], steps[ref]["alternative_id"]) for ref in conclusion["step_refs"]}
    if conclusion["kind"] != "INDEPENDENT_CONDITIONALS_ONLY" and len(branches) != 1:
        fail("DISTINCT_ALTERNATIVES_CANNOT_BECOME_JOINT_CONCLUSION")
    for ref in conclusion["assumption_refs"]:
        assumption = claims[ref]
        if any(assumption["context_id"] != context or assumption["alternative_id"] not in (None, alternative)
                for context, alternative in branches):
            fail("CONCLUSION_ASSUMPTION_SCOPE_MISMATCH")
    required_limit = {"INDETERMINATE_MISSING": "UNKNOWN", "INDETERMINATE_UNSUPPORTED": "UNSUPPORTED",
        "INDETERMINATE_CONFLICT": "CONFLICT", "INDEPENDENT_CONDITIONALS_ONLY": "COMPATIBILITY_GAP"}.get(conclusion["kind"])
    if required_limit and not any(limits[ref]["kind"] == required_limit for ref in conclusion["limitation_refs"]):
        fail("CONCLUSION_REQUIRES_TYPED_LIMITATION")
    cited_steps = set(conclusion["step_refs"])
    pending = list(cited_steps)
    while pending:
        for ref in steps[pending.pop()]["depends_on_steps"]:
            if ref not in cited_steps:
                cited_steps.add(ref)
                pending.append(ref)
    cited_claims = {ref for step in cited_steps for ref in steps[step]["claim_refs"]}
    cited_claims.update(conclusion["assumption_refs"])
    cited_rows = [steps[ref] for ref in cited_steps] + [claims[ref] for ref in cited_claims]
    relevant_limits = {ref for row in cited_rows for ref in row["limitation_refs"]}
    if not relevant_limits.issubset(conclusion["limitation_refs"]):
        fail("CONCLUSION_MUST_RETAIN_DEPENDENCY_LIMITATIONS")
    if any(row["context_id"] != value["question"]["context_id"] for row in cited_rows):
        fail("CONCLUSION_QUESTION_CONTEXT_MISMATCH")
    if any(row["alternative_id"] is not None and (row["context_id"], row["alternative_id"]) not in branches
            for row in cited_rows):
        fail("CONCLUSION_DEPENDENCY_ALTERNATIVE_MISMATCH")
    required_condition = {"INDETERMINATE_MISSING": "UNKNOWN", "INDETERMINATE_UNSUPPORTED": "UNSUPPORTED",
        "INDETERMINATE_CONFLICT": "CONFLICTING"}.get(conclusion["kind"])
    if required_condition and not any(row["condition"] == required_condition for row in cited_rows):
        fail("CONCLUSION_BARRIER_MUST_TRACE_CITED_INPUTS")
    if conclusion["kind"] in ("CONDITIONAL_SUPPORT", "INDEPENDENT_CONDITIONALS_ONLY") and any(
            row["condition"] != "PRESENT" for row in cited_rows):
        fail("UNRESOLVED_INPUT_CANNOT_SUPPORT_POSITIVE_CONCLUSION")
    observations = value["history"]["review_observations"]
    unique_index(observations, "observation_id")
    prior_observations = set()
    for observation in observations:
        resolve_many(observation["claim_refs"], claims, "REVIEW_CLAIM")
        resolve_many(observation["step_refs"], steps, "REVIEW_STEP")
        resolve_many(observation["supersedes_observation_ids"], prior_observations, "PRIOR_OBSERVATION")
        if not observation["reviewer_id"].startswith(prefix):
            fail("FICTIONAL_REVIEW_NAMESPACE_MISMATCH")
        prior_observations.add(observation["observation_id"])
    history = {} if history is None else snapshot(history)
    for ref in value["history"]["supersedes_packet_ids"]:
        if ref not in history or ref == value["packet_id"]:
            fail("DANGLING_OR_SELF_SUPERSESSION")
        prior = validate_packet(history[ref], contract=contract, rules=rules, history=history, _seen=_seen)
        if (prior["packet_id"] != ref or prior["contract_id"] != value["contract_id"]
                or prior["lineage_id"] != value["lineage_id"] or prior["revision"] >= value["revision"]):
            fail("INCOMPATIBLE_SUPERSESSION")
        old_contexts = {row["context_id"]: row for row in prior["contexts"]}
        if any(key not in contexts or _canonical_candidate(contexts[key]) != _canonical_candidate(row)
                for key, row in old_contexts.items()):
            fail("HISTORICAL_CONTEXT_REBINDING_FORBIDDEN")
    current_observations = {row["observation_id"]: row for row in observations}
    pending_ancestors = list(value["history"]["supersedes_packet_ids"])
    checked_ancestors = set()
    while pending_ancestors:
        ref = pending_ancestors.pop()
        if ref in checked_ancestors:
            continue
        checked_ancestors.add(ref)
        prior = history[ref]  # Every reachable ancestor was recursively validated above.
        pending_ancestors.extend(prior["history"]["supersedes_packet_ids"])
        for old_observation in prior["history"]["review_observations"]:
            old_id = old_observation["observation_id"]
            if old_id not in current_observations:
                continue
            if _canonical_candidate(current_observations[old_id]) != _canonical_candidate(old_observation):
                fail("HISTORICAL_OBSERVATION_REWRITE_FORBIDDEN")
            if _canonical_candidate(observation_material(value, current_observations[old_id])) != _canonical_candidate(
                    observation_material(prior, old_observation)):
                fail("HISTORICAL_OBSERVATION_MATERIAL_CHANGED")
    return value


def load_package(root=PACKAGE_ROOT, *, review_root=REVIEW_ROOT):
    """Read-only, fresh canonical validation of the finite authored design package."""
    root = _root(root)
    if {path.name for path in root.iterdir()} != RECORD_NAMES | {"manifest.json"}:
        fail("EXACT_DESIGN_PACKAGE_REQUIRED")
    records = {name: canonical_read(root / name) for name in sorted(RECORD_NAMES | {"manifest.json"})}
    contract = validate_contract(records["contract.json"])
    rules = retained_rules(review_root)
    for name, outcome in zip(PACKET_NAMES, EXPECTED_OUTCOMES):
        packet = validate_packet(records[name], contract=contract, rules=rules)
        if packet["conclusion"]["kind"] != outcome:
            fail("AUTHORED_EXAMPLE_OUTCOME_CHANGED")
    assessment = records["design-assessment.json"]
    check_identity(assessment, RECORD_DOMAIN, "record_id")
    assessment_fields = {"all_ten_activation_responsibilities", "authorization", "canonical_base",
        "execution_authority", "historical_recommendation", "permissions", "recommendations", "record_id",
        "record_kind", "remaining_questions", "schema_version", "semantic_closure", "source_policy_clearance",
        "status", "validation_boundaries"}
    expected_authorization = {"basis": "OWNER_EXPLICIT_CURRENT_TASK", "current_milestone_authorized": True,
        "new_source_projections": 0, "new_source_units": 0, "runtime_authorized": False,
        "scope": "PROPOSED-SPELL EVIDENCE PACKET CONTRACT DESIGN", "source_allowlist": []}
    expected_permissions = {key: "NOT_ESTABLISHED" for key in
        ("ai_export", "commercial_service", "free_service", "private_retention", "redistribution")}
    if (set(assessment) != assessment_fields or assessment["canonical_base"] != CANONICAL_BASE
            or type(assessment["schema_version"]) is not int or assessment["schema_version"] != 1
            or assessment["record_kind"] != "DESIGN_ASSESSMENT" or assessment["status"] != "PROPOSED_NON_EXECUTABLE"
            or assessment["execution_authority"] != "BLOCKED" or assessment["semantic_closure"] != "OPEN"
            or assessment["all_ten_activation_responsibilities"] != "OPEN / EXECUTION_BLOCKED"
            or assessment["source_policy_clearance"] != "not_granted"
            or _canonical_candidate(assessment["permissions"]) != _canonical_candidate(expected_permissions)
            or _canonical_candidate(assessment["authorization"]) != _canonical_candidate(expected_authorization)
            or type(assessment["recommendations"]) is not list or len(assessment["recommendations"]) != 1):
        fail("DESIGN_AUTHORIZATION_BOUNDARY_CHANGED")
    historical = assessment["historical_recommendation"]
    if (set(historical) != {"disposition", "historical_future_milestone_authorized", "historical_future_milestone_begun",
            "package_id", "record_id", "retained_package"}
            or historical["historical_future_milestone_authorized"] is not False
            or historical["historical_future_milestone_begun"] is not False
            or historical["package_id"] != rules["601.3"]["package_id"]
            or historical["record_id"] != "sha256:05ff5d7b7dae1db89973038363ec56aa84e2e970f275685790473bf3ad0be869"
            or historical["retained_package"] != retained_family.PACKAGE_NAME):
        fail("HISTORICAL_RECOMMENDATION_BINDING_CHANGED")
    recommendation = assessment["recommendations"][0]
    if any(recommendation[key] is not False for key in ("future_milestone_authorized", "future_milestone_begun", "future_source_projection_authorized")):
        fail("FUTURE_WORK_REMAINS_UNAUTHORIZED")
    if (recommendation["source_allowlist"] != [] or type(recommendation["new_source_units"]) is not int
            or recommendation["new_source_units"] != 0 or type(recommendation["new_source_projections"]) is not int
            or recommendation["new_source_projections"] != 0):
        fail("ZERO_NEW_SOURCE_SCOPE_REQUIRED")
    manifest = records["manifest.json"]
    check_identity(manifest, PACKAGE_DOMAIN, "package_id")
    if set(manifest) != {"canonical_base", "contract_id", "coverage", "execution_authority", "files",
            "historical_acquisition_identity", "package_id", "package_kind", "retained_package_bindings", "schema_version"}:
        fail("EXACT_MANIFEST_FIELDS_REQUIRED")
    expected_files = {}
    for name in sorted(RECORD_NAMES):
        record = records[name]
        raw = _canonical_candidate(record)
        field = "contract_id" if name == "contract.json" else "record_id" if name == "design-assessment.json" else "packet_id"
        expected_files[name] = {"sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "identity": record[field]}
    if _canonical_candidate(manifest["files"]) != _canonical_candidate(expected_files):
        fail("MANIFEST_FILE_BINDING_MISMATCH")
    expected_bindings = {row["retained_package"]: row["package_id"] for ref, row in rules.items()
        if ref.startswith(("601.2", "601.3"))}
    expected_coverage = {"casting_stages": "9/9", "completion_preceding_range": "8/8", "distinct_real_source_units": 100,
        "new_source_projections": 0, "new_source_units": 0, "parent_proposal_range": "4/4", "projections": 15, "single_activated_import": "8/8"}
    if (manifest["schema_version"] != PACKAGE_DOMAIN or manifest["canonical_base"] != CANONICAL_BASE or manifest["contract_id"] != contract["contract_id"]
            or manifest["package_kind"] != "PROPOSED_NON_EXECUTABLE_DESIGN"
            or manifest["execution_authority"] != "BLOCKED"
            or _canonical_candidate(manifest["coverage"]) != _canonical_candidate(expected_coverage)
            or manifest["retained_package_bindings"] != expected_bindings
            or manifest["historical_acquisition_identity"] != "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"):
        fail("MANIFEST_DESIGN_OR_RETAINED_BINDING_MISMATCH")
    return snapshot(records)


if __name__ == "__main__":
    result = load_package()
    print(json.dumps({"status": "STRUCTURALLY_VALID_DESIGN_ONLY", "packets": len(PACKET_NAMES),
        "package_id": result["manifest.json"]["package_id"], "execution_authority": "BLOCKED"}, sort_keys=True))
