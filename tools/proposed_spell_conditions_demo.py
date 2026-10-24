"""Reproduce the fictional conditional pilot through the real offline CLI.

The condition and successor assertions below are explicitly authored fixtures.
They are evidence corrections/alternatives, never simulated state transitions.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

from proposed_spell_packets.conditions import MODEL_VERSION, seal_model


ROOT = Path(__file__).resolve().parents[1]


def authored_beacon(draft, value):
    """Supply an exact fictional Boolean; retain packet classifications as authored."""
    packet = draft["packet"]
    packet["history"]["review_observations"] = []
    beacon = next(row for row in packet["claims"] if row["claim_id"] == "beacon")
    beacon.update(condition="PRESENT", value=value, limitation_refs=[], attribution={
        "actor_id": "fictional:b:condition-demo-author",
        "statement_id": "statement-beacon-" + str(value).lower(),
    })
    packet["reasoning"][0]["explanation"] = (
        "This author retains an UNKNOWN packet-level reasoning classification without "
        "a revised authored explanation. Beacon is now an explicitly supplied fictional "
        "Boolean assertion. A separate condition model may compute its named test; "
        "that computation does not rewrite this packet's authored classification."
    )
    packet["limitations"][0].update(claim_refs=[], description=(
        "The packet-level reasoning explanation remains author-classified UNKNOWN. "
        "This limitation concerns that authored explanation; the beacon assertion is "
        "supplied separately. The condition model does not resolve packet-level limits."
    ))
    packet["conclusion"]["text"] = (
        "The author retains this packet-level explanation as INDETERMINATE_MISSING "
        "because no revised authored reasoning explanation is supplied. The separate "
        "named condition result neither adopts nor resolves this authored conclusion. "
        "Overall permission, legality, compatibility, payment, completion and execution "
        "remain unestablished; execution BLOCKED."
    )


def authored_model(packet):
    """Bind one fixed explicit test to an exact packet, without parsing packet prose."""
    return seal_model({
        "model_version": MODEL_VERSION,
        "authority": "AUTHORED_FICTIONAL_CONDITION",
        "condition_id": "premise-and-lit-beacon",
        "condition_name": "Fictional premise and lit beacon",
        "packet": {key: packet[key] for key in (
            "packet_id", "contract_id", "schema_version", "lineage_id", "revision")},
        "scope": {"context_id": "ctx", "context_version": 1, "alternative_id": None},
        "operator": "ALL_OF",
        "operands": [
            {"operand_id": "explicit-premise", "claim_refs": ["premise"], "expected": True},
            {"operand_id": "lit-beacon", "claim_refs": ["beacon"], "expected": True},
        ],
    })


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", required=True, type=Path,
                        help="existing empty disposable directory outside the repository")
    args = parser.parse_args()
    workspace = args.workspace.absolute()
    if (not workspace.is_dir() or any(path.is_symlink() for path in (workspace, *workspace.parents))
            or any(workspace.iterdir()) or workspace == ROOT or ROOT in workspace.parents):
        parser.error("workspace must be an existing empty directory outside the repository without symlinks")
    drafts = workspace / "drafts"
    drafts.mkdir()
    models = workspace / "models"
    models.mkdir()
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

    draft_path = drafts / "retained-b.json"
    cli("draft", "--example", "packet-b-missing.json", "--output", draft_path)
    original = json.loads(cli("record", "--draft", draft_path))["packet_id"]
    original_packet = packet(original)
    retained_path = ROOT / "reference-reviews" / "gameplay-rules-proposed-spell-evidence-packet-design" / "packet-b-missing.json"
    original_path = workspace / "packets" / (original[7:] + ".json")
    if original_path.read_bytes() != retained_path.read_bytes():
        raise RuntimeError("retained B bytes changed")
    premise = next(row for row in original_packet["claims"] if row["claim_id"] == "premise")
    if premise["condition"] != "PRESENT" or premise["value"] is not True:
        raise RuntimeError("demonstration requires the existing explicitly authored Boolean premise")

    selections = {"missing": original}
    for label, value in (("true", True), ("false", False)):
        path = drafts / ("beacon-" + label + ".json")
        cli("draft", "--base", original, "--output", path)
        draft = json.loads(path.read_bytes())
        authored_beacon(draft, value)
        save(path, draft)
        selections[label] = json.loads(cli("record", "--draft", path))["packet_id"]

    expected = {"missing": "INDETERMINATE", "true": "SATISFIED_UNDER_ASSERTIONS",
                "false": "NOT_SATISFIED_UNDER_ASSERTIONS"}
    # Author models before the read-only phase; evaluation must not persist reports.
    for label, identity in selections.items():
        save(models / (label + ".json"), authored_model(packet(identity)))
    before = {path.relative_to(workspace).as_posix(): path.read_bytes()
              for path in workspace.rglob("*") if path.is_file()}
    outputs = {}
    for label, identity in selections.items():
        model_path = models / (label + ".json")
        readable = cli("evaluate", identity, "--model", model_path)
        print("Readable CLI excerpt (the command above provides the complete explanation):", flush=True)
        print("\n".join(line for line in readable.splitlines() if line.startswith((
            "Computed condition result:", "Condition:", "Scope:", "Result:", "Packet:",
            "Model:", "Execution authority:", "Operand ", "Assertion:", "Comparison:",
            "Selected-input finding:", "Authored packet conclusion (separate):"))), flush=True)
        raw = cli("evaluate", identity, "--model", model_path, "--json")
        result = json.loads(raw)
        if result["computed_result"] != expected[label]:
            raise RuntimeError("unexpected computed result for " + label)
        outputs[label] = {"packet_id": identity, "model_id": json.loads(model_path.read_bytes())["model_id"],
            "result_id": result["result_id"], "computed_result": result["computed_result"]}
    after = {path.relative_to(workspace).as_posix(): path.read_bytes()
             for path in workspace.rglob("*") if path.is_file()}
    if before != after:
        raise RuntimeError("evaluation changed workspace, packet, history or model bytes")
    print(json.dumps({"condition_id": "premise-and-lit-beacon", "results": outputs,
        "evaluation_read_only": True, "all_input_and_history_bytes_unchanged": True,
        "execution_authority": "BLOCKED"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
