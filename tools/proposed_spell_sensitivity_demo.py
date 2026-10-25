"""Reproduce missing-input sensitivity through the actual offline CLI.

All fixture changes are explicit fictional authored descendants of retained B.
Sensitivity only reads those records; it supplies no new assertion or revision.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from proposed_spell_packets.conditions import seal_model
from proposed_spell_conditions_demo import authored_model


ROOT = Path(__file__).resolve().parents[1]


def add_claim(packet, claim_id, condition, value, *, same_fact=False):
    """Explicit fixture authoring, never inferred from predicate prose."""
    row = deepcopy(next(row for row in packet["claims"] if row["claim_id"] == "beacon"))
    row.update(claim_id=claim_id, condition=condition, value=value, limitation_refs=[])
    row["attribution"] = {"actor_id": "fictional:b:sensitivity-demo-author",
                          "statement_id": "statement-" + claim_id}
    if not same_fact:
        row.update(subject_id="fictional:b:object", predicate="Opaque fictional requirement " + claim_id)
    packet["claims"].append(row)
    if condition in ("UNKNOWN", "UNSUPPORTED"):
        limit_id = claim_id + "-limit"
        row["limitation_refs"] = [limit_id]
        packet["limitations"].append({"limitation_id": limit_id, "kind": condition,
            "context_ids": ["ctx"], "claim_refs": [claim_id], "step_refs": [],
            "description": "Explicit fictional " + condition + " input for the sensitivity demonstration."})
    return row


def fixture(label, packet):
    """Author bounded additions while retaining the original missing beacon."""
    if label == "B-second-unknown":
        add_claim(packet, "other-input", "UNKNOWN", None)
    elif label == "C-known-mismatch":
        add_claim(packet, "other-required", "PRESENT", False)
    elif label == "D-mixed-group":
        add_claim(packet, "beacon-known", "PRESENT", True, same_fact=True)
        add_claim(packet, "beacon-second-unknown", "UNKNOWN", None, same_fact=True)
    elif label == "E-unsupported-conflict":
        add_claim(packet, "unsupported-input", "UNSUPPORTED", None)
        first = add_claim(packet, "dispute-true", "CONFLICTING", True)
        second = add_claim(packet, "dispute-false", "CONFLICTING", False)
        second["predicate"] = first["predicate"]
        first["limitation_refs"] = second["limitation_refs"] = ["declared-dispute"]
        packet["limitations"].append({"limitation_id": "declared-dispute", "kind": "CONFLICT",
            "context_ids": ["ctx"], "claim_refs": ["dispute-true", "dispute-false"], "step_refs": [],
            "description": "Distinct fictional statements disagree. Neither observer is selected as correct."})
    else:
        raise ValueError(label)


def model_for(label, packet):
    model = authored_model(packet)
    model.pop("model_id")
    leaves = model["operands"]
    if label == "B-second-unknown":
        leaves.append({"operand_id": "other-input", "claim_refs": ["other-input"], "expected": True})
    elif label == "C-known-mismatch":
        leaves.append({"operand_id": "other-required", "claim_refs": ["other-required"], "expected": True})
    elif label == "D-mixed-group":
        leaves[1]["claim_refs"] += ["beacon-known", "beacon-second-unknown"]
    elif label == "E-unsupported-conflict":
        leaves.extend([
            {"operand_id": "unsupported-input", "claim_refs": ["unsupported-input"], "expected": True},
            {"operand_id": "declared-dispute", "claim_refs": ["dispute-true", "dispute-false"], "expected": True},
        ])
    return seal_model(model)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="existing empty disposable directory outside the repository")
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    if (not workspace.is_dir() or any(path.is_symlink() for path in (workspace, *workspace.parents))
            or any(workspace.iterdir()) or workspace == ROOT or ROOT in workspace.parents):
        parser.error("workspace must be an existing empty directory outside the repository without symlinks")
    drafts, models = workspace / "drafts", workspace / "models"
    drafts.mkdir(); models.mkdir()
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))

    def save(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def cli(*arguments):
        command = [sys.executable, "-m", "proposed_spell_packets", "--workspace", str(workspace), *map(str, arguments)]
        print("$ " + shlex.join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    def packet(identity):
        return json.loads((workspace / "packets" / (identity[7:] + ".json")).read_bytes())

    original_draft = drafts / "retained-b.json"
    cli("draft", "--example", "packet-b-missing.json", "--output", original_draft)
    original = json.loads(cli("record", "--draft", original_draft))["packet_id"]
    original_path = workspace / "packets" / (original[7:] + ".json")
    retained_path = ROOT / "reference-reviews" / "gameplay-rules-proposed-spell-evidence-packet-design" / "packet-b-missing.json"
    if original_path.read_bytes() != retained_path.read_bytes():
        raise RuntimeError("retained B bytes changed")
    selections = {"A-original-b": original}
    for label in ("B-second-unknown", "C-known-mismatch", "D-mixed-group", "E-unsupported-conflict"):
        path = drafts / (label + ".json")
        cli("draft", "--base", original, "--output", path)
        draft = json.loads(path.read_bytes())
        draft["packet"]["history"]["review_observations"] = []
        fixture(label, draft["packet"])
        save(path, draft)
        selections[label] = json.loads(cli("record", "--draft", path))["packet_id"]
    for label, identity in selections.items():
        actual_beacon = next(row for row in packet(identity)["claims"] if row["claim_id"] == "beacon")
        if actual_beacon["condition"] != "UNKNOWN" or actual_beacon["value"] is not None:
            raise RuntimeError("fixture must retain the actual UNKNOWN beacon")
        save(models / (label + ".json"), model_for(label, packet(identity)))

    before = {path.relative_to(workspace).as_posix(): path.read_bytes()
              for path in workspace.rglob("*") if path.is_file()}
    outputs = {}
    for label, identity in selections.items():
        model_path = models / (label + ".json")
        actual_raw = cli("evaluate", identity, "--model", model_path, "--json")
        readable = cli("sensitivity", identity, "--model", model_path)
        raw = cli("sensitivity", identity, "--model", model_path, "--json")
        report = json.loads(raw)
        if report["baseline"] != json.loads(actual_raw):
            raise RuntimeError("ordinary baseline changed in sensitivity report")
        if json.loads(actual_raw)["computed_result"] != "INDETERMINATE":
            raise RuntimeError("actual baseline must stay INDETERMINATE")
        cases = report["sensitivity"]["cases"]
        beacon_cases = [case for case in cases if case["selected_operand_id"] == "lit-beacon"]
        expected = {
            "A-original-b": ["SATISFIED_UNDER_HYPOTHESIS", "NOT_SATISFIED_UNDER_HYPOTHESIS"],
            "B-second-unknown": ["INDETERMINATE_UNDER_HYPOTHESIS"] * 2,
            "C-known-mismatch": ["NOT_SATISFIED_UNDER_HYPOTHESIS"] * 2,
            "D-mixed-group": ["SATISFIED_UNDER_HYPOTHESIS", "INDETERMINATE_UNDER_HYPOTHESIS"],
            "E-unsupported-conflict": ["INDETERMINATE_UNDER_HYPOTHESIS"] * 2,
        }[label]
        if [case["hypothetical_result"] for case in beacon_cases] != expected:
            raise RuntimeError("unexpected beacon hypotheses for " + label)
        print("Scenario " + label + ": actual baseline INDETERMINATE", flush=True)
        for case in cases:
            print("Hypothesis " + case["selected_operand_id"] + "=" + json.dumps(case["assumed_value"]) +
                  " claims=" + json.dumps(case["unknown_claim_ids"]) + " -> " + case["hypothetical_result"], flush=True)
            print("Affected operand: " + case["affected_operand_change"]["explanation"], flush=True)
            print("Aggregate: " + case["aggregate_explanation"], flush=True)
            print("Remaining unresolved: " + json.dumps(case["remaining_unresolved_operands"]) +
                  "; actual known mismatches: " + json.dumps(case["known_mismatches"]), flush=True)
        if not readable.strip():
            raise RuntimeError("readable sensitivity CLI returned no explanation")
        outputs[label] = {"packet_id": identity, "model_id": report["baseline"]["model_id"],
            "baseline_result_id": report["baseline_result_id"], "report_id": report["report_id"],
            "case_count": len(cases), "hypothetical_results": [case["hypothetical_result"] for case in cases]}
    after = {path.relative_to(workspace).as_posix(): path.read_bytes()
             for path in workspace.rglob("*") if path.is_file()}
    if before != after:
        raise RuntimeError("analysis changed packet, model, history, draft or other workspace bytes")
    print(json.dumps({"results": outputs, "baseline_parity": True,
        "all_input_and_history_bytes_unchanged": True, "sensitivity_read_only": True,
        "actual_beacon_condition": "UNKNOWN", "no_assertions_recorded_by_sensitivity": True,
        "authority": "HYPOTHETICAL_CONDITION_SENSITIVITY_ONLY", "execution_authority": "BLOCKED"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
