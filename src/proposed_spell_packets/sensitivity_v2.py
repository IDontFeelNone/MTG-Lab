"""Bounded, correlated hypotheses over the v2 compound condition evaluator."""
from __future__ import annotations

from dataclasses import dataclass
import json

from . import conditions_v2 as c
from . import validation as v

REPORT_VERSION = "fictional-condition-sensitivity-report-v2"
POLICY_VERSION = "fictional-condition-sensitivity-policy-v2"
AUTHORITY = "HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY"
MAX_CASES = 64
CASE_VALUES = (True, False)
LIMITATIONS = (
    "A hypothesis is a private calculation assumption, never a recorded assertion, factual ordinary result, review or gameplay event.",
    "Each case starts from the exact actual baseline. Uniformly assign true then false to actual UNKNOWN claims in one complete leaf group, in declared leaf order; keep every other assertion fixed.",
    "Reused leaf references remain correlated: every occurrence uses that one leaf outcome. Occurrences do not add hypotheses or independent unknowns.",
    "No mixed assignments within a group, cross-group combinations, solver or sensitivity of an alternative-comparison aggregate is supplied.",
    "Root stability concerns only this exact authored expression and these bounded cases. An unresolved fact is not thereby universally irrelevant, resolved, false or unnecessary.",
    "Zero cases means no selected UNKNOWN claims, not complete evidence or execution readiness.",
    *c.LIMITATIONS,
)


POLICY_AUTHORITY = "REPOSITORY_DEFINED_FICTIONAL_SENSITIVITY_POLICY"
_policy_content = {
    "policy_version": POLICY_VERSION, "authority": POLICY_AUTHORITY,
    "baseline": "Exact standalone ordinary v2 evaluation; retained separately and unchanged.",
    "case_order": "Declared leaf order; uniformly true then false for all actual UNKNOWN claims in one complete leaf group.",
    "case_baseline": "Every case independently starts from the same actual baseline; only the selected group's actual UNKNOWN effective values change.",
    "preservation": "PRESENT, UNSUPPORTED, CONFLICTING and non-Boolean evidence remains fixed, with findings and independent known mismatches retained.",
    "correlation": "Evaluate each declared leaf once per case and use that outcome for every expression occurrence; repeated references create no cases.",
    "composition": "Recompute every expression node under the exact v2 evaluator policy; no early termination or incomplete-branch validation.",
    "result_states": ["SATISFIED_UNDER_HYPOTHESIS", "NOT_SATISFIED_UNDER_HYPOTHESIS", "INDETERMINATE_UNDER_HYPOTHESIS"],
    "limits": {"max_selected_groups": 32, "max_cases": MAX_CASES, "uniform_values": [True, False]},
    "exclusions": "No mixed assignments within a group, cross-group combinations, solver, derived assertion admission or alternative-aggregate sensitivity.",
}
_policy_content["policy_id"] = v.identity(POLICY_VERSION, _policy_content, "policy_id")
_POLICY_BYTES = v._canonical_candidate(_policy_content)
POLICY_ID = _policy_content["policy_id"]
del _policy_content


def policy():
    """Independent decoded view of the finite repository-owned policy."""
    return json.loads(_POLICY_BYTES)


@dataclass(frozen=True, init=False)
class SensitivityReport:
    """Computed output with immutable bytes and independently decoded views."""

    canonical_bytes: bytes

    def __init__(self, *args, **kwargs):
        c._error("SENSITIVITY_REPORT_IS_COMPUTED_OUTPUT_ONLY")

    def to_dict(self):
        return json.loads(self.canonical_bytes)

    @property
    def report_id(self):
        return self.to_dict()["report_id"]


def _mismatches(leaves):
    return [{"leaf_id": row["leaf_id"], "claim_refs": row["known_mismatch_claim_refs"]}
            for row in leaves if row["known_mismatch_claim_refs"]]


def analyze(workspace, packet_id, model):
    """Validate actual workspace once; recompute complete expressions privately."""
    snapshot = c._prepare(workspace, packet_id, model)
    packet, history, definition, context, groups = snapshot
    baseline = c._evaluate_snapshot(*snapshot).to_dict()
    original = {row["leaf_id"]: row for row in baseline["leaves"]}
    original_nodes = {row["path"]: row for row in baseline["expression_nodes"]}
    known_mismatches = _mismatches(baseline["leaves"])
    outcomes = {
        "SATISFIED_UNDER_ASSERTIONS": "SATISFIED_UNDER_HYPOTHESIS",
        "NOT_SATISFIED_UNDER_ASSERTIONS": "NOT_SATISFIED_UNDER_HYPOTHESIS",
        "INDETERMINATE": "INDETERMINATE_UNDER_HYPOTHESIS",
    }
    cases = []
    for selected, rows in groups:
        leaf_id = selected["operand_id"]
        unknown = [row["claim_id"] for row in rows if row["condition"] == "UNKNOWN"]
        if not unknown:
            continue
        for assumed in CASE_VALUES:
            assumptions = {claim_id: assumed for claim_id in unknown}
            calculated, nodes, computed = c._calculate(groups, definition["expression"], assumptions)
            affected = next(row for row in calculated if row["leaf_id"] == leaf_id)
            unresolved = [row["leaf_id"] for row in calculated if row["status"] == "UNRESOLVED"]
            findings = [{"leaf_id": row["leaf_id"], **finding}
                        for row in calculated for finding in row["findings"]]
            leaves = [{
                "leaf_id": row["leaf_id"], "leaf_kind": row["leaf_kind"],
                "evidence_ref": {"baseline_result_id": baseline["result_id"], "leaf_id": row["leaf_id"]},
                "expected": row["expected"], "claim_refs": row["claim_refs"],
                "assertion_evaluations": [{key: evaluation[key] for key in
                    ("claim_id", "effective_value", "hypothesized", "boolean_match")}
                    for evaluation in row["assertion_evaluations"]],
                "findings": row["findings"], "status": row["status"],
                "mismatch_claim_refs": row["known_mismatch_claim_refs"],
            } for row in calculated]
            changes = [{"path": row["path"],
                        "baseline_status": original_nodes[row["path"]]["status"],
                        "hypothetical_status": row["status"],
                        "changed": original_nodes[row["path"]]["status"] != row["status"]}
                       for row in nodes]
            cases.append({
                "sequence": len(cases) + 1, "selected_leaf_id": leaf_id,
                "unknown_claim_ids": unknown, "assumed_value": assumed,
                "assumptions": [{"claim_id": claim_id, "value": assumed} for claim_id in unknown],
                "evidence_ref": {"baseline_result_id": baseline["result_id"], "leaf_id": leaf_id},
                "leaves": leaves, "expression_nodes": nodes, "expression_node_changes": changes,
                "hypothetical_result": outcomes[computed],
                "root_change": {"baseline_result": baseline["computed_result"],
                                "hypothetical_result": outcomes[computed],
                                "changed": baseline["computed_result"] != computed},
                "remaining_unresolved_leaves": unresolved,
                "remaining_input_findings": findings,
                "known_mismatches": known_mismatches,
                "computed_mismatches": _mismatches(calculated),
                "affected_leaf_change": {
                    "leaf_id": leaf_id, "baseline_status": original[leaf_id]["status"],
                    "hypothetical_status": affected["status"],
                    "baseline_findings": original[leaf_id]["findings"],
                    "hypothetical_findings": affected["findings"],
                    "explanation": "Uniformly assume " + json.dumps(assumed) + " for actual UNKNOWN claims " +
                        ", ".join(unknown) + "; keep other evidence fixed and apply the resulting leaf to every reference. " +
                        original[leaf_id]["status"] + " -> " + affected["status"] + ".",
                },
                "aggregate_explanation": "Actual root " + baseline["computed_result"] + "; hypothetical root " +
                    outcomes[computed] + " using " + c.POLICY_VERSION + ". All expression nodes are recalculated. " +
                    "Remaining unresolved leaves: " + json.dumps(unresolved) + ". Independent known mismatches remain reported. " +
                    "Root stability or decisiveness does not establish complete evidence or universal irrelevance of unresolved facts.",
            })
    assert len(cases) <= MAX_CASES
    value = {
        "report_version": REPORT_VERSION, "sensitivity_policy_version": POLICY_VERSION,
        "sensitivity_policy_id": POLICY_ID, "sensitivity_policy": policy(),
        "authority": AUTHORITY, "execution_authority": "BLOCKED",
        "model_version": c.MODEL_VERSION, "evaluator_policy_version": c.POLICY_VERSION,
        "evaluator_policy_id": c.POLICY_ID,
        "baseline_result_version": c.RESULT_VERSION,
        "packet": c._binding(packet), "model_id": definition["model_id"],
        "baseline_result_id": baseline["result_id"],
        "condition_id": definition["condition_id"], "condition_name": definition["condition_name"],
        "scope": definition["scope"], "baseline": baseline,
        "sensitivity": {"status": "APPLICABLE" if cases else "NOT_APPLICABLE_NO_SELECTED_UNKNOWN_CLAIMS",
                        "case_count": len(cases), "cases": cases},
        "limitations": list(LIMITATIONS),
    }
    value["report_id"] = v.identity(REPORT_VERSION, value, "report_id")
    report = object.__new__(SensitivityReport)
    object.__setattr__(report, "canonical_bytes", v._canonical_candidate(value))
    return report


def render(report):
    value = report.to_dict()
    lines = ["Actual baseline (unchanged; no hypotheses):",
             c._render_value(value["baseline"]),
             "Hypothetical sensitivity authority: " + value["authority"],
             "Sensitivity policy: " + value["sensitivity_policy_version"],
             "Sensitivity report: " + value["report_id"],
             "Sensitivity: " + value["sensitivity"]["status"] + " | cases=" + str(value["sensitivity"]["case_count"])]
    for case in value["sensitivity"]["cases"]:
        lines.append("Hypothesis " + str(case["sequence"]) + ": " + case["selected_leaf_id"] +
                     " | assume " + json.dumps(case["assumed_value"]) + " for " +
                     ", ".join(case["unknown_claim_ids"]) + " -> " + case["hypothetical_result"])
        lines.append("Affected leaf: " + case["affected_leaf_change"]["explanation"])
        lines.append("Root: " + case["aggregate_explanation"])
        lines.append("Complete hypothetical trace: " + json.dumps(case, ensure_ascii=False, sort_keys=True))
    lines.extend("Sensitivity limitation: " + limitation for limitation in value["limitations"])
    lines.append("Execution authority: BLOCKED")
    return "\n".join(lines)
