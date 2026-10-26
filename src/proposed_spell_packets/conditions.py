"""Closed fictional Boolean condition pilot, separate from authored v1 packets.

Only exact Boolean assertion comparisons and a bounded flat ALL_OF are computed.
Predicate and explanation strings are opaque; retained rules are context only.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from . import validation as v
from .authoring import IDENTITY, read_draft_bytes


MODEL_VERSION = "fictional-condition-model-v1"
POLICY_VERSION = "fictional-condition-evaluator-policy-v1"
RESULT_VERSION = "fictional-condition-result-v1"
MODEL_AUTHORITY = "AUTHORED_FICTIONAL_CONDITION"
MAX_OPERANDS = 32
MAX_CLAIM_REFS = 64
MODEL_BYTE_LIMIT = 64_000
TOKEN = re.compile(r"[a-z][a-z0-9-]{0,63}\Z")
PACKET_FIELDS = ("packet_id", "contract_id", "schema_version", "lineage_id", "revision")
LIMITATIONS = (
    "Only the named fictional condition under supplied assertions is computed; assertions are unverified.",
    "Exact context/subject/predicate keys check only assertions represented in this packet. No complete fact/effect inventory or semantic equivalence of differently worded predicates is established.",
    "The conservative evidence policy is specific to this pilot, not a general Boolean or multivalued logic system. Any missing, unsupported or conflicting selected input makes ALL_OF indeterminate, while independent mismatches remain visible.",
    "PRESENT means supplied content. Predicate and explanation prose and authored conclusions are not executable semantics. Existing review observations do not approve this condition model.",
    "Neither satisfaction nor an empty finding list establishes truth, soundness of arbitrary prose, complete dependencies/effects, absence of prohibitions, evidence sufficiency, overall casting permission, proposal legality, joint choice compatibility, payment, completion or gameplay execution.",
    "Unselected claims, steps and limitations remain authored packet context; satisfaction of this selected condition does not resolve them.",
)


def _error(message):
    v.fail("CONDITION_" + message)


def _object(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        _error(label + "_CLOSED_FIELDS_REQUIRED")


def _token(value, label):
    if type(value) is not str or not TOKEN.fullmatch(value):
        _error(label + "_TOKEN_REQUIRED")


def _positive_integer(value, label):
    if type(value) is not int or not 1 <= value <= 2_147_483_647:
        _error(label + "_BOUNDED_INTEGER_REQUIRED")


def _owned(value):
    # Refuse coercions (tuple/list, integer/string keys, floats, custom objects)
    # before established canonicalization takes private immutable ownership.
    budget = [0]
    def inspect(node, depth):
        budget[0] += 1
        if budget[0] > 8192 or depth > 8:
            _error("MODEL_STRUCTURE_LIMIT")
        if type(node) is dict:
            if any(type(key) is not str for key in node):
                _error("MODEL_STRING_KEYS_REQUIRED")
            for key, child in node.items():
                if len(key) > 128:
                    _error("MODEL_KEY_LIMIT")
                inspect(child, depth + 1)
        elif type(node) is list:
            for child in node:
                inspect(child, depth + 1)
        elif type(node) is str:
            if len(node) > 4096:
                _error("MODEL_STRING_LIMIT")
        elif node is not None and type(node) not in (bool, int):
            _error("MODEL_JSON_SCALARS_REQUIRED")
    inspect(value, 0)
    raw = v._canonical_candidate(value)
    if len(raw) > MODEL_BYTE_LIMIT:
        _error("MODEL_BYTE_LIMIT")
    return json.loads(raw)


def _validate(value):
    _object(value, ("model_id", "model_version", "authority", "condition_id", "condition_name",
                    "packet", "scope", "operator", "operands"), "MODEL")
    if value["model_version"] != MODEL_VERSION or value["authority"] != MODEL_AUTHORITY:
        _error("MODEL_VERSION_OR_FICTIONAL_AUTHORITY_MISMATCH")
    if value["operator"] != "ALL_OF":
        _error("ONLY_FLAT_ALL_OF_SUPPORTED")
    _token(value["condition_id"], "CONDITION_ID")
    if type(value["condition_name"]) is not str or not 1 <= len(value["condition_name"]) <= 256:
        _error("CONDITION_NAME_REQUIRED")
    _object(value["packet"], PACKET_FIELDS, "PACKET_BINDING")
    packet = value["packet"]
    for field in ("packet_id", "contract_id"):
        if type(packet[field]) is not str or not IDENTITY.fullmatch(packet[field]):
            _error("PACKET_BINDING_IDENTITY_REQUIRED")
    if packet["schema_version"] != v.PACKET_DOMAIN:
        _error("PACKET_VERSION_MISMATCH")
    if (type(packet["lineage_id"]) is not str or
            not re.fullmatch(r"fictional:[a-e]:[a-z0-9-]{1,64}", packet["lineage_id"])):
        _error("FICTIONAL_LINEAGE_REQUIRED")
    _positive_integer(packet["revision"], "REVISION")
    scope = value["scope"]
    _object(scope, ("context_id", "context_version", "alternative_id"), "SCOPE")
    _token(scope["context_id"], "CONTEXT_ID")
    _positive_integer(scope["context_version"], "CONTEXT_VERSION")
    if scope["alternative_id"] is not None:
        _token(scope["alternative_id"], "ALTERNATIVE_ID")
    operands = value["operands"]
    if type(operands) is not list or not 1 <= len(operands) <= MAX_OPERANDS:
        _error("NONEMPTY_BOUNDED_OPERANDS_REQUIRED")
    ids, refs = set(), set()
    for operand in operands:
        _object(operand, ("operand_id", "claim_refs", "expected"), "OPERAND")
        _token(operand["operand_id"], "OPERAND_ID")
        if operand["operand_id"] in ids:
            _error("DUPLICATE_OPERAND_ID")
        ids.add(operand["operand_id"])
        if type(operand["expected"]) is not bool:
            _error("EXACT_BOOLEAN_EXPECTATION_REQUIRED")
        selected = operand["claim_refs"]
        if type(selected) is not list or not 1 <= len(selected) <= MAX_CLAIM_REFS:
            _error("NONEMPTY_BOUNDED_CLAIM_REFS_REQUIRED")
        for ref in selected:
            _token(ref, "CLAIM_REFERENCE")
            if ref in refs:
                _error("DUPLICATE_CLAIM_REFERENCE")
            refs.add(ref)
    if type(value["model_id"]) is not str or not IDENTITY.fullmatch(value["model_id"]):
        _error("MODEL_IDENTITY_REQUIRED")
    if value["model_id"] != v.identity(MODEL_VERSION, value, "model_id"):
        _error("MODEL_IDENTITY_MISMATCH")


@dataclass(frozen=True, init=False)
class ConditionModel:
    """Validated privately owned canonical bytes; decoded dictionaries are copies."""

    canonical_bytes: bytes

    def __init__(self, value):
        owned = _owned(value)
        _validate(owned)
        object.__setattr__(self, "canonical_bytes", v._canonical_candidate(owned))

    @classmethod
    def from_dict(cls, value):
        return cls(value)

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def model_id(self):
        return self.to_dict()["model_id"]


def seal_model(value):
    """Explicit authoring helper: own a supplied definition and derive its identity.

    This does not derive a definition from packet prose or supply assertion facts.
    The returned dictionary is independent of the caller's definition.
    """
    owned = _owned(value)
    if type(owned) is not dict or "model_id" in owned:
        _error("UNSEALED_MODEL_DEFINITION_REQUIRED")
    owned["model_id"] = v.identity(MODEL_VERSION, owned, "model_id")
    return ConditionModel.from_dict(owned).to_dict()


def read_model(path):
    raw = read_draft_bytes(path)
    if len(raw) > MODEL_BYTE_LIMIT:
        _error("MODEL_BYTE_LIMIT")
    try:
        value = json.loads(raw, object_pairs_hook=v._unique, parse_constant=v._nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        _error("MALFORMED_MODEL_JSON")
    return ConditionModel.from_dict(value)


@dataclass(frozen=True)
class ConditionResult:
    """Derived immutable canonical content; callers receive fresh decoded copies."""

    canonical_bytes: bytes

    def __post_init__(self):
        # A public constructor must not retain a caller-owned bytearray or allow
        # canonical bytes to carry a stale identity after external mutation.
        if type(self.canonical_bytes) is not bytes:
            _error("IMMUTABLE_RESULT_BYTES_REQUIRED")
        try:
            value = json.loads(self.canonical_bytes, object_pairs_hook=v._unique,
                               parse_constant=v._nonfinite)
        except (ValueError, UnicodeError, RecursionError):
            _error("MALFORMED_RESULT_JSON")
        if self.canonical_bytes != v._canonical_candidate(value):
            _error("CANONICAL_RESULT_BYTES_REQUIRED")
        _object(value, ("result_id", "result_version", "evaluator_policy_version", "model_version",
                        "authority", "execution_authority", "packet", "model_id", "condition_model",
                        "condition_id", "condition_name", "scope", "context", "operands",
                        "selected_input_findings", "computed_result", "explanation_trace", "limitations",
                        "retained_rule_context_authority", "retained_rule_context", "packet_context"), "RESULT")
        if (value["result_version"] != RESULT_VERSION or
                value["evaluator_policy_version"] != POLICY_VERSION or
                value["model_version"] != MODEL_VERSION or
                value["authority"] != "NAMED_FICTIONAL_CONDITION_UNDER_ASSERTIONS_ONLY" or
                value["execution_authority"] != "BLOCKED"):
            _error("RESULT_VERSION_OR_AUTHORITY_MISMATCH")
        v.check_identity(value, RESULT_VERSION, "result_id")

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def result_id(self):
        return self.to_dict()["result_id"]


def _binding(packet):
    return {field: packet[field] for field in PACKET_FIELDS}


def _groups(packet, model):
    if model["packet"] != _binding(packet):
        _error("EXACT_PACKET_REVISION_BINDING_MISMATCH")
    scope = model["scope"]
    contexts = {row["context_id"]: row for row in packet["contexts"]}
    context = contexts.get(scope["context_id"])
    if context is None or context["version"] != scope["context_version"]:
        _error("EXACT_CONTEXT_VERSION_REQUIRED")
    alternative = scope["alternative_id"]
    if alternative is not None and not any(
            row["context_id"] == scope["context_id"] and row["alternative_id"] == alternative
            for row in packet["choices"]):
        _error("DANGLING_ALTERNATIVE_REFERENCE")
    claims = {row["claim_id"]: row for row in packet["claims"]}
    eligible = {}
    key = lambda row: (row["context_id"], row["subject_id"], row["predicate"])
    for row in packet["claims"]:
        if row["context_id"] == scope["context_id"] and row["alternative_id"] in (None, alternative):
            eligible.setdefault(key(row), []).append(row)
    groups, seen = [], set()
    for operand in model["operands"]:
        refs = operand["claim_refs"]
        if any(ref not in claims for ref in refs):
            _error("DANGLING_CLAIM_REFERENCE")
        rows = [claims[ref] for ref in refs]
        group_key = key(rows[0])
        if any(key(row) != group_key for row in rows):
            _error("ONE_EXACT_FACT_PER_OPERAND_REQUIRED")
        expected = eligible.get(group_key, [])
        if set(refs) != {row["claim_id"] for row in expected}:
            _error("COMPLETE_ELIGIBLE_ASSERTION_GROUP_REQUIRED")
        if group_key in seen:
            _error("DUPLICATE_FACT_OPERAND")
        seen.add(group_key)
        # Model reference order is explicit and contributes to content identity.
        groups.append((operand, rows))
    return context, groups


def _operand(operand, rows, assumptions=None):
    """One comparison policy for actual and private hypothetical calculations.

    Overrides affect calculation values only; original rows are never changed.
    Only actual UNKNOWN claims may receive exact Boolean hypotheses.
    """
    if assumptions is not None:
        allowed = {row["claim_id"] for row in rows if row["condition"] == "UNKNOWN"}
        if (type(assumptions) is not dict or not set(assumptions) <= allowed or
                any(type(value) is not bool for value in assumptions.values())):
            _error("ONLY_UNKNOWN_BOOLEAN_HYPOTHESES_ALLOWED")
    findings, evaluations, effective_booleans = [], [], []
    for row in rows:
        condition = row["condition"]
        hypothesized = assumptions is not None and row["claim_id"] in assumptions
        value = assumptions[row["claim_id"]] if hypothesized else row["value"]
        match = None
        if condition == "UNKNOWN" and not hypothesized:
            finding = "MISSING_ASSERTION"
        elif condition == "UNSUPPORTED":
            finding = "UNSUPPORTED_ASSERTION"
        elif condition == "CONFLICTING":
            finding = "DECLARED_CONFLICT"
        else:
            finding = None
        if finding:
            findings.append({"kind": finding, "claim_refs": [row["claim_id"]]})
        if condition in ("PRESENT", "CONFLICTING") and type(value) is not bool:
            findings.append({"kind": "UNSUPPORTED_BOOLEAN_INPUT", "claim_refs": [row["claim_id"]]})
        if (condition == "PRESENT" or hypothesized) and type(value) is bool:
            match = value == operand["expected"]
        evaluation = {"claim_id": row["claim_id"], "original_value": row["value"],
                      "original_condition": condition, "boolean_match": match}
        if assumptions is not None:
            evaluation.update(effective_value=value, hypothesized=hypothesized)
        evaluations.append(evaluation)
        if type(value) is bool:
            effective_booleans.append((row["claim_id"], value))
    if {value for _, value in effective_booleans} == {True, False}:
        findings.append({"kind": "OPPOSING_BOOLEAN_ASSERTIONS",
                         "claim_refs": [claim_id for claim_id, _ in effective_booleans]})
    matches = [row["boolean_match"] for row in evaluations]
    status = ("UNRESOLVED" if findings else "MATCH" if all(matches) else "MISMATCH")
    return {"operand_id": operand["operand_id"], "leaf_kind": "BOOLEAN_ASSERTIONS_EQUAL",
            "expected": operand["expected"], "claim_refs": operand["claim_refs"],
            "assertions": rows, "assertion_evaluations": evaluations,
            "findings": findings, "status": status,
            "known_mismatch_claim_refs": [row["claim_id"] for row in evaluations
                                          if row["boolean_match"] is False]}


def _prepare(workspace, packet_id, model):
    """Own the model and freshly validate/own the actual packet boundary once."""
    owned_model = ConditionModel.from_dict(model.to_dict() if type(model) is ConditionModel else model)
    definition = owned_model.to_dict()
    packet, history = workspace.read(packet_id)
    packet, history = v.snapshot(packet), v.snapshot(history)
    if packet["packet_id"] != packet_id:
        _error("SELECTED_PACKET_IDENTITY_MISMATCH")
    v.check_identity(packet, v.PACKET_DOMAIN, "packet_id")
    context, groups = _groups(packet, definition)
    return packet, history, definition, context, groups


def _aggregate(operands):
    return ("INDETERMINATE" if any(row["status"] == "UNRESOLVED" for row in operands)
            else "NOT_SATISFIED_UNDER_ASSERTIONS" if any(row["status"] == "MISMATCH" for row in operands)
            else "SATISFIED_UNDER_ASSERTIONS")


def _evaluate_snapshot(packet, history, definition, context, groups):
    """Pure ordinary calculation over an already owned and admitted snapshot."""
    operands = [_operand(operand, rows) for operand, rows in groups]
    computed = _aggregate(operands)
    selected = {ref for row in operands for ref in row["claim_refs"]}
    findings = [{"operand_id": row["operand_id"], **finding}
                for row in operands for finding in row["findings"]]
    trace = [{"sequence": position + 1, "operand_id": row["operand_id"],
              "claim_refs": row["claim_refs"], "expected": row["expected"],
              "assertion_evaluations": row["assertion_evaluations"],
              "findings": row["findings"], "status": row["status"]}
             for position, row in enumerate(operands)]
    trace.append({"sequence": len(trace) + 1, "operator": "ALL_OF",
                  "operand_statuses": [row["status"] for row in operands], "computed_result": computed})
    value = {"result_version": RESULT_VERSION, "evaluator_policy_version": POLICY_VERSION,
        "model_version": MODEL_VERSION, "authority": "NAMED_FICTIONAL_CONDITION_UNDER_ASSERTIONS_ONLY",
        "execution_authority": "BLOCKED", "packet": _binding(packet),
        "model_id": definition["model_id"], "condition_model": definition,
        "condition_id": definition["condition_id"], "condition_name": definition["condition_name"],
        "scope": definition["scope"], "context": context, "operands": operands,
        "selected_input_findings": findings, "computed_result": computed,
        "explanation_trace": trace, "limitations": list(LIMITATIONS),
        "retained_rule_context_authority": "RETAINED_VERSIONED_RULE_CONTEXT_ONLY",
        "retained_rule_context": packet["rule_evidence"],
        "packet_context": {"authored_conclusion": packet["conclusion"],
            "authored_limitations": packet["limitations"],
            "unselected_claims": [row for row in packet["claims"] if row["claim_id"] not in selected],
            "authored_reasoning": packet["reasoning"], "authored_choices": packet["choices"],
            "history": packet["history"], "validated_ancestor_ids": sorted(history),
            "review_authority": "AUTHORED_PACKET_OBSERVATIONS_DO_NOT_APPROVE_CONDITION_MODEL"}}
    value["result_id"] = v.identity(RESULT_VERSION, value, "result_id")
    return ConditionResult(v._canonical_candidate(value))


def evaluate(workspace, packet_id, model):
    """Fresh boundary validation once, then compute solely from owned snapshots."""
    from . import conditions_v2 as v2
    if type(model) is v2.ConditionModel or (type(model) is dict and model.get("model_version") == v2.MODEL_VERSION):
        return v2.evaluate(workspace, packet_id, model)
    return _evaluate_snapshot(*_prepare(workspace, packet_id, model))


def render(result):
    from . import conditions_v2 as v2
    if type(result) is v2.ConditionResult:
        return v2.render(result)
    value = result.to_dict()
    lines = ["Computed condition result: " + value["computed_result"],
        f'Condition: {value["condition_id"]} | {value["condition_name"]}',
        "Scope: " + json.dumps(value["scope"], sort_keys=True),
        "Result: " + value["result_id"], "Packet: " + value["packet"]["packet_id"],
        "Model: " + value["model_id"], "Execution authority: BLOCKED"]
    for row in value["operands"]:
        lines.append(f'Operand {row["operand_id"]}: expected {json.dumps(row["expected"])} -> {row["status"]}')
        lines.extend("Assertion: " + json.dumps(assertion, ensure_ascii=False, sort_keys=True)
                     for assertion in row["assertions"])
        lines.extend("Comparison: " + json.dumps(comparison, sort_keys=True)
                     for comparison in row["assertion_evaluations"])
        lines.extend("Selected-input finding: " + json.dumps(finding, sort_keys=True)
                     for finding in row["findings"])
    lines.append("Authored packet conclusion (separate): " + json.dumps(
        value["packet_context"]["authored_conclusion"], ensure_ascii=False, sort_keys=True))
    lines.append("Remaining authored packet context: " + json.dumps(
        value["packet_context"], ensure_ascii=False, sort_keys=True))
    lines.append("Retained rule context (RETAINED_VERSIONED_RULE_CONTEXT_ONLY): " +
                 json.dumps(value["retained_rule_context"], ensure_ascii=False, sort_keys=True))
    lines.extend("Limitation: " + limitation for limitation in value["limitations"])
    lines.append("Deterministic explanation trace: " + json.dumps(value["explanation_trace"], sort_keys=True))
    return "\n".join(lines)
