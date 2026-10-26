"""Bounded missing-input hypotheses over one actual admitted fictional condition.

Hypotheses are calculation values, never evidence packets or factual results.
The ordinary result retains all original selected evidence once; cases refer to it.
"""
from __future__ import annotations

from dataclasses import dataclass
import json

from . import conditions as c
from . import validation as v


REPORT_VERSION = "fictional-condition-sensitivity-report-v1"
POLICY_VERSION = "fictional-condition-sensitivity-policy-v1"
AUTHORITY = "HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY"
MAX_CASES = 2 * c.MAX_OPERANDS
CASE_VALUES = (True, False)
LIMITATIONS = (
    "A hypothesis is an assumed Boolean used to examine a consequence, not a verified fact, corrected record, reviewer decision or executed game event.",
    "Each case starts independently from the original validated baseline and uniformly assigns every actual UNKNOWN claim in one complete eligible group. Other assertions and all model requirements remain fixed.",
    "True then false is the deterministic case order within model operand order. No combinations across groups or mixed assignments within a group are enumerated; the cases do not establish every possible real-world outcome.",
    "If neither tested case satisfies this condition, the reported unresolved or unmet requirements still apply under these cases. No claim is made that broader future evidence combinations cannot matter.",
    "Zero cases means no selected UNKNOWN claims, not complete knowledge, sufficient evidence or execution readiness.",
    *c.LIMITATIONS,
)


@dataclass(frozen=True, init=False)
class SensitivityReport:
    """Output-only immutable canonical content; decoded views are fresh copies.

    There is deliberately no raw-result admission API. Only analyze() computes
    a report from actual packet/model inputs and creates this output wrapper.
    """

    canonical_bytes: bytes

    def __init__(self, *args, **kwargs):
        c._error("SENSITIVITY_REPORT_IS_COMPUTED_OUTPUT_ONLY")

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def report_id(self):
        return self.to_dict()["report_id"]


def _report(value):
    value["report_id"] = v.identity(REPORT_VERSION, value, "report_id")
    result = object.__new__(SensitivityReport)
    object.__setattr__(result, "canonical_bytes", v._canonical_candidate(value))
    return result


def _mismatches(operands, field="known_mismatch_claim_refs"):
    return [{"operand_id": row["operand_id"], "claim_refs": row[field]}
            for row in operands if row[field]]


def _affected_explanation(selected, unknown, assumed, before, affected):
    reason = ("For calculation only, uniformly assume " + json.dumps(assumed) +
              " for actual UNKNOWN claims " + ", ".join(unknown) +
              "; keep every other assertion fixed. Operand " + selected["operand_id"] +
              " has baseline status " + before["status"] +
              " and hypothetical status " + affected["status"] + ". ")
    if affected["findings"]:
        reason += "Remaining operand barriers: " + "; ".join(
            finding["kind"] + " (" + ", ".join(finding["claim_refs"]) + ")"
            for finding in affected["findings"]) + ". "
    else:
        reason += "No unresolved barrier remains within this operand under this hypothesis. "
    if affected["known_mismatch_claim_refs"]:
        reason += ("Effective comparisons mismatch expected " + json.dumps(selected["expected"]) +
                   " for: " + ", ".join(affected["known_mismatch_claim_refs"]) + ".")
    else:
        reason += "Every evaluable comparison in this operand matches its fixed expectation."
    return reason


def _aggregate_explanation(baseline, outcome, unresolved, mismatches):
    if unresolved:
        reason = "Remaining unresolved selected operands keep the aggregate indeterminate: " + ", ".join(unresolved) + "."
    elif mismatches:
        reason = "All selected operands are resolved under this hypothesis, but Boolean requirements remain unmet: " + ", ".join(row["operand_id"] for row in mismatches) + "."
    else:
        reason = "All selected Boolean comparisons match their fixed model expectations under this hypothesis."
    if mismatches and unresolved:
        reason += " Computed mismatches remain visible in: " + ", ".join(row["operand_id"] for row in mismatches) + "."
    return ("Actual baseline " + baseline["computed_result"] + "; hypothetical aggregate " + outcome + ". " + reason)


def analyze(workspace, packet_id, model):
    """Validate actual inputs once and compute at most 64 independent cases.

    Reuses the sole operand/aggregate semantics from the ordinary evaluator.
    No packet, history or model is mutated and no synthetic packet is admitted.
    """
    from . import conditions_v2 as c2, sensitivity_v2 as v2
    if type(model) is c2.ConditionModel or (type(model) is dict and model.get("model_version") == c2.MODEL_VERSION):
        return v2.analyze(workspace, packet_id, model)
    snapshot = c._prepare(workspace, packet_id, model)
    packet, history, definition, context, groups = snapshot
    baseline = c._evaluate_snapshot(*snapshot).to_dict()
    original = {row["operand_id"]: row for row in baseline["operands"]}
    known_mismatches = _mismatches(baseline["operands"])
    cases = []
    outcomes = {
        "INDETERMINATE": "INDETERMINATE_UNDER_HYPOTHESIS",
        "SATISFIED_UNDER_ASSERTIONS": "SATISFIED_UNDER_HYPOTHESIS",
        "NOT_SATISFIED_UNDER_ASSERTIONS": "NOT_SATISFIED_UNDER_HYPOTHESIS",
    }
    for selected, selected_rows in groups:
        unknown = [row["claim_id"] for row in selected_rows if row["condition"] == "UNKNOWN"]
        if not unknown:
            continue
        before = original[selected["operand_id"]]
        for assumed in CASE_VALUES:
            assumptions = {claim_id: assumed for claim_id in unknown}
            calculated = [c._operand(operand, rows, assumptions if operand is selected else {})
                          for operand, rows in groups]
            outcome = outcomes[c._aggregate(calculated)]
            affected = next(row for row in calculated if row["operand_id"] == selected["operand_id"])
            unresolved = [row["operand_id"] for row in calculated if row["status"] == "UNRESOLVED"]
            mismatches = _mismatches(calculated)
            operands = []
            for row in calculated:
                operands.append({
                    "operand_id": row["operand_id"], "leaf_kind": row["leaf_kind"],
                    "evidence_ref": {"baseline_result_id": baseline["result_id"], "operand_id": row["operand_id"]},
                    "expected": row["expected"], "claim_refs": row["claim_refs"],
                    "assertion_evaluations": [{key: evaluation[key] for key in
                        ("claim_id", "effective_value", "hypothesized", "boolean_match")}
                        for evaluation in row["assertion_evaluations"]],
                    "findings": row["findings"], "status": row["status"],
                    "mismatch_claim_refs": row["known_mismatch_claim_refs"],
                })
            cases.append({
                "sequence": len(cases) + 1, "selected_operand_id": selected["operand_id"],
                "unknown_claim_ids": unknown, "assumed_value": assumed,
                "assumptions": [{"claim_id": claim_id, "value": assumed} for claim_id in unknown],
                "evidence_ref": {"baseline_result_id": baseline["result_id"], "operand_id": selected["operand_id"]},
                "operands": operands, "hypothetical_result": outcome,
                "remaining_unresolved_operands": unresolved,
                "known_mismatches": known_mismatches, "computed_mismatches": mismatches,
                "affected_operand_change": {
                    "baseline_status": before["status"], "hypothetical_status": affected["status"],
                    "baseline_findings": before["findings"], "hypothetical_findings": affected["findings"],
                    "explanation": _affected_explanation(selected, unknown, assumed, before, affected),
                },
                "aggregate_explanation": _aggregate_explanation(baseline, outcome, unresolved, mismatches),
            })
    # The model's closed operand bound makes this finite by construction.
    assert len(cases) <= MAX_CASES
    return _report({
        "report_version": REPORT_VERSION, "sensitivity_policy_version": POLICY_VERSION,
        "authority": AUTHORITY, "execution_authority": "BLOCKED",
        "model_version": c.MODEL_VERSION, "evaluator_policy_version": c.POLICY_VERSION,
        "baseline_result_version": c.RESULT_VERSION,
        "packet": c._binding(packet), "model_id": definition["model_id"],
        "baseline_result_id": baseline["result_id"],
        "condition_id": definition["condition_id"], "condition_name": definition["condition_name"],
        "scope": definition["scope"], "baseline": baseline,
        "sensitivity": {
            "status": "APPLICABLE" if cases else "NOT_APPLICABLE_NO_SELECTED_UNKNOWN_CLAIMS",
            "case_count": len(cases), "cases": cases,
        },
        "limitations": list(LIMITATIONS),
    })


def render(report):
    from . import sensitivity_v2 as v2
    if type(report) is v2.SensitivityReport:
        return v2.render(report)
    value = report.to_dict()
    # The ordinary renderer presents the exact actual result separately.
    baseline = c.ConditionResult(v._canonical_candidate(value["baseline"]))
    lines = ["Actual baseline (unchanged; no hypotheses):", c.render(baseline),
             "Hypothetical sensitivity authority: " + value["authority"],
             "Sensitivity report: " + value["report_id"],
             "Sensitivity: " + value["sensitivity"]["status"] +
             " | cases=" + str(value["sensitivity"]["case_count"])]
    for case in value["sensitivity"]["cases"]:
        lines.append("Hypothesis " + str(case["sequence"]) + ": " + case["selected_operand_id"] +
                     " | assume " + json.dumps(case["assumed_value"]) + " for " +
                     ", ".join(case["unknown_claim_ids"]) + " -> " + case["hypothetical_result"])
        lines.append("Affected operand: " + case["affected_operand_change"]["explanation"])
        lines.append("Aggregate: " + case["aggregate_explanation"])
        for operand in case["operands"]:
            lines.append("Hypothetical operand: " + json.dumps(operand, ensure_ascii=False, sort_keys=True))
        lines.append("Remaining unresolved operands: " + json.dumps(case["remaining_unresolved_operands"]))
        lines.append("Actual known mismatches retained: " + json.dumps(case["known_mismatches"], sort_keys=True))
    lines.extend("Sensitivity limitation: " + text for text in value["limitations"])
    lines.append("Execution authority: BLOCKED")
    return "\n".join(lines)
