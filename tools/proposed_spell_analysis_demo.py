"""Exercise read-only analysis over the existing fictional authoring demonstration.

The extra descendant below is explicit authored fixture input. Analysis never
authors, changes, seals or records a packet; those remain separate CLI operations.
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


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="existing empty disposable directory outside the repository")
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    seed_command = [sys.executable, "tools/proposed_spell_packet_demo.py", "--workspace", str(workspace)]
    print("$ " + shlex.join(seed_command), flush=True)
    seed = subprocess.run(seed_command, cwd=ROOT, env=env, capture_output=True, text=True)
    if seed.returncode:
        raise RuntimeError(seed.stdout + seed.stderr)
    established = json.loads(seed.stdout.splitlines()[-1])
    print(json.dumps({"established_authoring_demonstration": established}, sort_keys=True), flush=True)

    def cli(*arguments):
        command = [sys.executable, "-m", "proposed_spell_packets", "--workspace", str(workspace), *map(str, arguments)]
        print("$ " + shlex.join(command), flush=True)
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        return result.stdout

    def records():
        return {path.name: path.read_bytes() for path in (workspace / "packets").iterdir()}

    original_bytes = records()
    reports = {}
    for name, identity in established["examples"].items():
        # Print the actual readable report's compact front section. The complete
        # typed node/edge listing remains available through the printed command.
        readable = cli("analyze", identity)
        print(readable.split("Typed nodes (", 1)[0].rstrip(), flush=True)
        value = json.loads(cli("analyze", identity, "--json"))
        view = value["analyses"][0]
        reports[name] = {"report_id": value["report_id"],
            "condition_findings": [{"node": row["node"], "condition": row["condition"]}
                for row in view["condition_findings"]],
            "limitation_kinds": [row["limitation"]["kind"] for row in view["declared_limitations"]],
            "branches": view["branches"]}
    comparisons = {}
    for label, left, right in (
            ("revision_1_to_2", established["original_revision_1"], established["correction_revision_2"]),
            ("revision_2_to_3", established["correction_revision_2"], established["review_revision_3"])):
        value = json.loads(cli("compare", left, right, "--json"))
        comparisons[label] = {"report_id": value["report_id"],
            "reviewed_material_changed": value["reviewed_material_changed"],
            "review_only_change": value["review_only_change"],
            "claim_changes": value["changes"]["claims"],
            "authored_conclusion_changes": value["changes"]["authored_conclusion"],
            "review_observations": value["changes"]["review_observations"]}
        print(json.dumps({label: comparisons[label]}, ensure_ascii=False, sort_keys=True), flush=True)

    original = established["original_revision_1"]
    draft_path = workspace / "drafts" / "declared-transitive.json"
    cli("draft", "--base", original, "--output", draft_path)
    draft = json.loads(draft_path.read_bytes())
    packet = draft["packet"]
    packet["history"]["review_observations"] = []
    packet["reasoning"].append({**deepcopy(packet["reasoning"][0]),
        "step_id": "bounded-followup", "claim_refs": ["premise"],
        "depends_on_steps": ["condition"],
        "explanation": "This fictional authored followup explicitly depends on condition. It supplies no new assertion or evaluation."})
    packet["conclusion"]["step_refs"] = ["bounded-followup"]
    packet["conclusion"]["text"] += " This authored demonstration follows the explicitly named transitive dependency."
    draft_path.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    transitive_id = json.loads(cli("record", "--draft", draft_path))["packet_id"]
    before_analysis = records()
    transitive = json.loads(cli("analyze", transitive_id, "--json"))
    view = transitive["analyses"][0]
    if (view["branches"][0]["direct_step_refs"] != ["bounded-followup"] or
            view["branches"][0]["transitive_step_refs"] != ["condition"] or
            not any(row["node"] == "claim:beacon" and any(witness["nodes"] ==
                ["conclusion", "step:bounded-followup", "step:condition", "claim:beacon"]
                for witness in row["witness_paths"]) for row in view["condition_findings"])):
        raise RuntimeError("analysis omitted the explicitly authored transitive dependency")
    if records() != before_analysis or any((workspace / "packets" / name).read_bytes() != raw
            for name, raw in original_bytes.items()):
        raise RuntimeError("analysis or comparison changed original packet/history bytes")
    print(json.dumps({"acceptance_matrix": reports, "comparisons": comparisons,
        "transitive_descendant": {"packet_id": transitive_id, "report_id": transitive["report_id"],
            "branches": view["branches"], "condition_findings": view["condition_findings"]},
        "original_packet_history_bytes_unchanged": True, "analysis_read_only": True,
        "execution_authority": "BLOCKED"}, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
