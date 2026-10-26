"""Explicit shared requirements over a finite list of fictional alternatives.

Composition is structural only. Each candidate gets its own complete v1 model;
assertions never transfer between alternatives and predicates remain opaque.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from . import conditions as c
from . import validation as v
from .authoring import IDENTITY, read_draft_bytes


DEFINITION_VERSION = "fictional-alternative-requirements-v1"
DEFINITION_AUTHORITY = "AUTHORED_FICTIONAL_REQUIREMENTS"
REPORT_VERSION = "fictional-alternative-requirements-report-v1"
POLICY_VERSION = "fictional-alternative-requirements-policy-v1"
AUTHORITY = "LISTED_FICTIONAL_ALTERNATIVES_UNDER_ASSERTIONS_ONLY"
MAX_CANDIDATES = 16
MAX_REQUIREMENTS = c.MAX_OPERANDS
MAX_CLAIM_REFS = c.MAX_CLAIM_REFS
DEFINITION_BYTE_LIMIT = 1_024_000
# The definition's bounds are cumulative with each composed v1 model's unchanged
# 64,000-byte / 8,192-node / depth-8 bounds. Numeric collection maxima can coexist
# with compact references; sufficiently long references can hit the byte bound.
LIMITATIONS = (
    "A witness means only one explicitly listed declared alternative meeting this particular shared requirement set under its supplied fictional assertions.",
    "The finite candidate list is not established exhaustive. A negative result says nothing about omitted or possible future alternatives.",
    "Requirements are evaluated independently within each exact alternative scope. Different alternatives meeting different requirements do not establish a shared witness; no combinations, evidence unions, ranking or preferred option are computed.",
    "An explicit UNKNOWN assertion is valid incomplete evidence. A missing required group is an insufficient authoring binding and is rejected, never converted to false, vacuous success or a fabricated UNKNOWN claim.",
    "All candidate findings remain visible even when another candidate is a witness. Declaring an alternative does not establish its feasibility or compatibility with another choice.",
    *c.LIMITATIONS,
)


def _error(message):
    v.fail("ALTERNATIVES_" + message)


def _object(value, fields, label):
    if type(value) is not dict or set(value) != set(fields):
        _error(label + "_CLOSED_FIELDS_REQUIRED")


def _owned(value):
    """Refuse coercion before privately owning bounded canonical JSON content."""
    budget = [0]
    def inspect(node, depth):
        budget[0] += 1
        if budget[0] > 65_536 or depth > 8:
            _error("DEFINITION_STRUCTURE_LIMIT")
        if type(node) is dict:
            for key, child in node.items():
                if type(key) is not str or len(key) > 128:
                    _error("DEFINITION_BOUNDED_STRING_KEYS_REQUIRED")
                inspect(child, depth + 1)
        elif type(node) is list:
            for child in node:
                inspect(child, depth + 1)
        elif type(node) is str:
            if len(node) > 4096:
                _error("DEFINITION_STRING_LIMIT")
        elif node is not None and type(node) not in (bool, int):
            _error("DEFINITION_JSON_SCALARS_REQUIRED")
    inspect(value, 0)
    raw = v._canonical_candidate(value)
    if len(raw) > DEFINITION_BYTE_LIMIT:
        _error("DEFINITION_BYTE_LIMIT")
    return json.loads(raw)


def _model(definition, candidate):
    bindings = {row["requirement_id"]: row["claim_refs"] for row in candidate["bindings"]}
    return c.seal_model({
        "model_version": c.MODEL_VERSION, "authority": c.MODEL_AUTHORITY,
        "condition_id": "shared-requirements", "condition_name": "Shared fictional requirements",
        "packet": definition["packet"],
        "scope": {**definition["scope"], "alternative_id": candidate["alternative_id"]},
        "operator": "ALL_OF",
        "operands": [{"operand_id": row["requirement_id"],
                      "claim_refs": bindings[row["requirement_id"]], "expected": row["expected"]}
                     for row in definition["requirements"]],
    })


def _validate(value):
    _object(value, ("definition_id", "definition_version", "authority", "packet", "scope",
                    "requirements", "candidates"), "DEFINITION")
    if (value["definition_version"] != DEFINITION_VERSION or
            value["authority"] != DEFINITION_AUTHORITY):
        _error("DEFINITION_VERSION_OR_AUTHORITY_MISMATCH")
    _object(value["scope"], ("context_id", "context_version"), "SCOPE")
    requirements = value["requirements"]
    if type(requirements) is not list or not 1 <= len(requirements) <= MAX_REQUIREMENTS:
        _error("NONEMPTY_BOUNDED_REQUIREMENTS_REQUIRED")
    ids, facts = set(), set()
    for row in requirements:
        _object(row, ("requirement_id", "subject_id", "predicate", "expected"), "REQUIREMENT")
        c._token(row["requirement_id"], "REQUIREMENT_ID")
        if row["requirement_id"] in ids:
            _error("DUPLICATE_REQUIREMENT_ID")
        ids.add(row["requirement_id"])
        if (type(row["subject_id"]) is not str or
                not re.fullmatch(r"fictional:[a-e]:[a-z0-9-]+", row["subject_id"])):
            _error("FICTIONAL_SUBJECT_ID_REQUIRED")
        if type(row["predicate"]) is not str or not row["predicate"]:
            _error("NONEMPTY_OPAQUE_PREDICATE_REQUIRED")
        if type(row["expected"]) is not bool:
            _error("EXACT_BOOLEAN_EXPECTATION_REQUIRED")
        fact = (row["subject_id"], row["predicate"])
        if fact in facts:
            _error("DUPLICATE_REQUIREMENT_FACT_KEY")
        facts.add(fact)
    candidates = value["candidates"]
    if type(candidates) is not list or not 1 <= len(candidates) <= MAX_CANDIDATES:
        _error("NONEMPTY_BOUNDED_CANDIDATES_REQUIRED")
    alternatives = set()
    for candidate in candidates:
        _object(candidate, ("alternative_id", "bindings"), "CANDIDATE")
        c._token(candidate["alternative_id"], "ALTERNATIVE_ID")
        if candidate["alternative_id"] in alternatives:
            _error("DUPLICATE_CANDIDATE")
        alternatives.add(candidate["alternative_id"])
        bindings = candidate["bindings"]
        if type(bindings) is not list or len(bindings) != len(requirements):
            _error("EXACT_SHARED_REQUIREMENT_BINDINGS_REQUIRED")
        bound = set()
        for binding in bindings:
            _object(binding, ("requirement_id", "claim_refs"), "BINDING")
            c._token(binding["requirement_id"], "REQUIREMENT_ID")
            if binding["requirement_id"] in bound:
                _error("DUPLICATE_REQUIREMENT_BINDING")
            bound.add(binding["requirement_id"])
        if bound != ids:
            _error("EXACT_SHARED_REQUIREMENT_BINDINGS_REQUIRED")
        # Reuse every v1 packet/scope/type/reference/operand acceptance check.
        # This is pure model validation, with no workspace or retained reads.
        _model(value, candidate)
    if type(value["definition_id"]) is not str or not IDENTITY.fullmatch(value["definition_id"]):
        _error("DEFINITION_IDENTITY_REQUIRED")
    if value["definition_id"] != v.identity(DEFINITION_VERSION, value, "definition_id"):
        _error("DEFINITION_IDENTITY_MISMATCH")


@dataclass(frozen=True, init=False)
class AlternativesDefinition:
    """Validated immutable canonical input; decoded dictionaries are copies."""

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
    def definition_id(self):
        return self.to_dict()["definition_id"]


def seal_definition(value):
    """Seal explicit authored bindings, never infer requirements or assertions."""
    owned = _owned(value)
    if type(owned) is not dict or "definition_id" in owned:
        _error("UNSEALED_DEFINITION_REQUIRED")
    owned["definition_id"] = v.identity(DEFINITION_VERSION, owned, "definition_id")
    return AlternativesDefinition(owned).to_dict()


def read_definition(path):
    raw = read_draft_bytes(path)
    if len(raw) > DEFINITION_BYTE_LIMIT:
        _error("DEFINITION_BYTE_LIMIT")
    try:
        value = json.loads(raw, object_pairs_hook=v._unique, parse_constant=v._nonfinite)
    except (ValueError, UnicodeError, RecursionError):
        _error("MALFORMED_DEFINITION_JSON")
    return AlternativesDefinition(value)


@dataclass(frozen=True, init=False)
class AlternativesReport:
    """Computed output only, with private immutable bytes and copied views."""

    canonical_bytes: bytes

    def __init__(self, *args, **kwargs):
        _error("REPORT_IS_COMPUTED_OUTPUT_ONLY")

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def report_id(self):
        return self.to_dict()["report_id"]


def evaluate(workspace, packet_id, definition):
    """Freshly admit actual packet/root/history once, then compare owned scopes."""
    from . import alternatives_v2 as v2
    if type(definition) is v2.AlternativesDefinition or (type(definition) is dict and definition.get("definition_version") == v2.DEFINITION_VERSION):
        return v2.evaluate(workspace, packet_id, definition)
    owned = AlternativesDefinition(definition.to_dict()
        if type(definition) is AlternativesDefinition else definition).to_dict()
    packet, history = workspace.read(packet_id)
    packet, history = v.snapshot(packet), v.snapshot(history)
    if packet["packet_id"] != packet_id:
        _error("SELECTED_PACKET_IDENTITY_MISMATCH")
    v.check_identity(packet, v.PACKET_DOMAIN, "packet_id")
    if owned["packet"] != c._binding(packet):
        _error("EXACT_PACKET_REVISION_BINDING_MISMATCH")
    prepared = []
    for candidate in owned["candidates"]:
        model = _model(owned, candidate)
        eligible_keys = {(row["subject_id"], row["predicate"])
                         for row in packet["claims"]
                         if row["context_id"] == owned["scope"]["context_id"] and
                         row["alternative_id"] in (None, candidate["alternative_id"])}
        if any((row["subject_id"], row["predicate"]) not in eligible_keys
               for row in owned["requirements"]):
            _error("INSUFFICIENT_BINDING_MISSING_REQUIRED_GROUP")
        context, groups = c._groups(packet, model)
        for requirement, (_, rows) in zip(owned["requirements"], groups):
            if (rows[0]["subject_id"], rows[0]["predicate"]) != (
                    requirement["subject_id"], requirement["predicate"]):
                _error("EXACT_SHARED_REQUIREMENT_FACT_KEY_REQUIRED")
        prepared.append((candidate, model, context, groups))
    candidates = []
    for candidate, model, context, groups in prepared:
        result = c._evaluate_snapshot(packet, history, model, context, groups).to_dict()
        outcomes = [{**requirement, "status": operand["status"],
                     "claim_refs": operand["claim_refs"],
                     "known_mismatch_claim_refs": operand["known_mismatch_claim_refs"]}
                    for requirement, operand in zip(owned["requirements"], result["operands"])]
        candidates.append({
            "alternative_id": candidate["alternative_id"], "scope": model["scope"],
            "condition_model": model, "model_id": model["model_id"],
            "condition_result": result, "result_id": result["result_id"],
            "computed_result": result["computed_result"], "requirement_outcomes": outcomes,
            "selected_input_findings": result["selected_input_findings"],
            "known_mismatches": [{"requirement_id": row["requirement_id"],
                                  "claim_refs": row["known_mismatch_claim_refs"]}
                                 for row in outcomes if row["known_mismatch_claim_refs"]],
        })
    witnesses = [row["alternative_id"] for row in candidates
                 if row["computed_result"] == "SATISFIED_UNDER_ASSERTIONS"]
    if witnesses:
        aggregate = "LISTED_WITNESS_FOUND_UNDER_ASSERTIONS"
        explanation = "Every shared requirement matches within each listed witness's own eligible assertions: " + ", ".join(witnesses) + ". All other candidate findings remain visible."
    elif any(row["computed_result"] == "INDETERMINATE" for row in candidates):
        aggregate = "INDETERMINATE_NO_LISTED_WITNESS_ESTABLISHED"
        explanation = "No listed alternative satisfies every shared requirement, and at least one has unresolved selected input. Independent known mismatches remain visible."
    else:
        aggregate = "NO_LISTED_WITNESS_UNDER_ASSERTIONS"
        explanation = "Every explicitly listed alternative determinately mismatches at least one shared requirement under its own assertions. Separate favorable requirements cannot be combined across alternatives."
    value = {
        "report_version": REPORT_VERSION, "comparison_policy_version": POLICY_VERSION,
        "definition_version": DEFINITION_VERSION, "definition_id": owned["definition_id"],
        "definition": owned, "authority": AUTHORITY, "execution_authority": "BLOCKED",
        "condition_model_version": c.MODEL_VERSION, "condition_result_version": c.RESULT_VERSION,
        "evaluator_policy_version": c.POLICY_VERSION, "packet": c._binding(packet),
        "scope": owned["scope"], "context": prepared[0][2],
        "requirements": owned["requirements"], "candidates": candidates,
        "computed_result": aggregate, "satisfying_alternative_ids": witnesses,
        "aggregate_explanation": explanation, "limitations": list(LIMITATIONS),
        "retained_rule_context_authority": "RETAINED_VERSIONED_RULE_CONTEXT_ONLY",
    }
    value["report_id"] = v.identity(REPORT_VERSION, value, "report_id")
    report = object.__new__(AlternativesReport)
    object.__setattr__(report, "canonical_bytes", v._canonical_candidate(value))
    return report


def render(report):
    from . import alternatives_v2 as v2
    if type(report) is v2.AlternativesReport:
        return v2.render(report)
    value = report.to_dict()
    lines = ["Computed alternative comparison: " + value["computed_result"],
             "Packet: " + json.dumps(value["packet"], sort_keys=True),
             "Context: " + json.dumps(value["context"], ensure_ascii=False, sort_keys=True),
             "Definition: " + value["definition_id"], "Report: " + value["report_id"],
             "Shared requirements (exact opaque predicates; Boolean expectations):"]
    lines.extend("Requirement: " + json.dumps(row, ensure_ascii=False, sort_keys=True)
                 for row in value["requirements"])
    lines.append("Alternative | candidate result | " + " | ".join(
        row["requirement_id"] for row in value["requirements"]))
    for candidate in value["candidates"]:
        lines.append(candidate["alternative_id"] + " | " + candidate["computed_result"] + " | " +
                     " | ".join(row["status"] for row in candidate["requirement_outcomes"]))
    lines.append("All satisfying alternative IDs: " + json.dumps(value["satisfying_alternative_ids"]))
    lines.append("Bounded aggregate: " + value["aggregate_explanation"])
    for candidate in value["candidates"]:
        lines.append("Candidate " + candidate["alternative_id"] + " actual v1 result: " + candidate["result_id"])
        lines.append("Candidate findings: " + json.dumps(candidate["selected_input_findings"], sort_keys=True))
        lines.append("Candidate known mismatches: " + json.dumps(candidate["known_mismatches"], sort_keys=True))
        result = candidate["condition_result"]
        for operand in result["operands"]:
            lines.append("Actual assertions and comparisons: " + json.dumps(operand, ensure_ascii=False, sort_keys=True))
    context = value["candidates"][0]["condition_result"]["packet_context"]
    lines.append("Authored packet conclusion (separate): " + json.dumps(context["authored_conclusion"], ensure_ascii=False, sort_keys=True))
    lines.append("Authored packet limitations (separate): " + json.dumps(context["authored_limitations"], ensure_ascii=False, sort_keys=True))
    lines.append("Remaining authored packet context (separate): " + json.dumps(context, ensure_ascii=False, sort_keys=True))
    lines.extend("Comparison limitation: " + limitation for limitation in value["limitations"])
    lines.append("Execution authority: BLOCKED")
    return "\n".join(lines)
