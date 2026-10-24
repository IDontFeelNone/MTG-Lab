"""Read-only dependency analysis through actual commands and changed graphs."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.errors import GameplayContractError
from proposed_spell_packets import analysis
from proposed_spell_packets.authoring import Workspace
from proposed_spell_packets import validation as v


ROOT = Path(__file__).resolve().parents[1]
VERSION = "proposed-spell-dependency-report-v1"


class ProposedSpellPacketAnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reuse the established authoring demonstration, including its exact B
        # correction/review chain. No second permanent packet inventory exists.
        cls.seed = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.seed.cleanup)
        cls.seed_path = Path(cls.seed.name)
        result = subprocess.run([sys.executable, "tools/proposed_spell_packet_demo.py",
            "--workspace", str(cls.seed_path)], cwd=ROOT,
            env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), capture_output=True)
        if result.returncode:
            raise AssertionError(result.stdout.decode() + result.stderr.decode())
        cls.demo = json.loads(result.stdout.splitlines()[-1])
        cls.examples = {name: json.loads((v.PACKAGE_ROOT / name).read_bytes())
            for name in v.PACKET_NAMES}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "pilot"
        shutil.copytree(self.seed_path, self.workspace)
        self.serial = 0

    def cli(self, *args, success=True, workspace=None):
        result = subprocess.run([sys.executable, "-m", "proposed_spell_packets",
            "--workspace", str(workspace or self.workspace), *map(str, args)],
            cwd=ROOT, env=dict(os.environ, PYTHONPATH=str(ROOT / "src")), capture_output=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout.decode() + result.stderr.decode())
            self.assertEqual(json.loads(result.stderr)["execution_authority"], "BLOCKED")
        return result

    def files(self):
        return {p.relative_to(self.workspace).as_posix(): p.read_bytes()
            for p in self.workspace.rglob("*") if p.is_file()}

    def path(self, identity):
        return self.workspace / "packets" / (identity[7:] + ".json")

    def successor(self, base):
        packet = deepcopy(base)
        packet["revision"] += 1
        packet["history"].update(supersedes_packet_ids=[base["packet_id"]], review_observations=[])
        return packet

    def record(self, packet):
        # Fixture construction is explicit authored input. The actual unchanged
        # authoring boundary validates it, including retained roots and history.
        v.seal_packet(packet)
        self.serial += 1
        source = self.root / ("authored-" + str(self.serial) + ".json")
        source.write_bytes(v._canonical_candidate(packet))
        Workspace(self.workspace).record(sealed=source)
        return packet

    def report(self, *args):
        raw = self.cli(*args, "--json").stdout
        value = json.loads(raw)
        self.assertEqual(raw, v._canonical_candidate(value))
        self.assertEqual(value["analysis_version"], VERSION)
        self.assertEqual(value["report_id"], v.identity(VERSION, value, "report_id"))
        self.assertEqual(value["authority"], "DECLARED_DEPENDENCIES_ONLY")
        self.assertEqual(value["execution_authority"], "BLOCKED")
        for view in value["analyses"]:
            links = {(edge["source"], edge["target"]) for edge in view["edges"]}
            for finding in view["condition_findings"] + view["declared_limitations"]:
                self.assertTrue(finding["branches"])
                self.assertEqual(len(finding["witness_paths"]), len(finding["branches"]))
                for witness in finding["witness_paths"]:
                    path = witness["nodes"]
                    self.assertEqual(path[0], "conclusion")
                    self.assertEqual(path[-1], finding["node"])
                    self.assertTrue(all(link in links for link in zip(path, path[1:])))
        return value

    def test_five_retained_examples_keep_authorship_barriers_and_rule_context(self):
        before = self.files()
        reports = {}
        for name, packet in self.examples.items():
            with self.subTest(example=name):
                report = self.report("analyze", packet["packet_id"])
                view = report["analyses"][0]
                reports[name] = view
                self.assertEqual(report["inputs"][0]["packet_id"], packet["packet_id"])
                self.assertEqual(report["inputs"][0]["contract_id"], packet["contract_id"])
                self.assertEqual(view["authored_conclusion"], packet["conclusion"])
                self.assertTrue(all(branch["context_version"] == 1 for branch in view["branches"]))
                self.assertIn("scope", [row["limitation"]["limitation_id"]
                    for row in view["declared_limitations"]])
                nodes = {node["node"]: node for node in view["nodes"]}
                self.assertEqual(nodes["claim:premise"]["authored"]["basis"], "AUTHORED_FICTIONAL_ASSUMPTION")
                cited_rules = [node["authored"] for node in view["nodes"] if node["kind"] == "rule"]
                self.assertTrue(cited_rules)
                self.assertTrue(all(row["authority"] == "RETAINED_VERSIONED_RULE_CONTEXT_ONLY" for row in cited_rules))
                for rule in cited_rules:
                    self.assertIn(rule, packet["rule_evidence"])
                readable = self.cli("analyze", packet["packet_id"]).stdout.decode()
                for text in (packet["packet_id"], packet["conclusion"]["text"], "BLOCKED", "SCOPE"):
                    self.assertIn(text, readable)
        a = reports[v.PACKET_NAMES[0]]
        self.assertFalse(a["condition_findings"])
        self.assertTrue(a["branches"][0]["contextual_choice_refs"])
        b = reports[v.PACKET_NAMES[1]]
        self.assertIn(("claim:beacon", "UNKNOWN"), [(x["node"], x["condition"]) for x in b["condition_findings"]])
        self.assertIn(("step:condition", "UNKNOWN"), [(x["node"], x["condition"]) for x in b["condition_findings"]])
        c = reports[v.PACKET_NAMES[2]]
        self.assertEqual({x["condition"] for x in c["condition_findings"]}, {"UNSUPPORTED"})
        self.assertTrue(all(node["authored"]["condition"] == "PRESENT"
            for node in c["nodes"] if node["kind"] == "claim"))
        d = reports[v.PACKET_NAMES[3]]
        disputed = [node["authored"] for node in d["nodes"]
            if node["node"] in ("claim:lit", "claim:unlit")]
        self.assertEqual({row["value"] for row in disputed}, {True, False})
        self.assertEqual(len({row["attribution"]["actor_id"] for row in disputed}), 2)
        e = reports[v.PACKET_NAMES[4]]
        branches = {row["alternative_id"]: row for row in e["branches"]}
        self.assertEqual(set(branches), {"soften", "brighten"})
        self.assertIn("soften", branches["soften"]["claim_refs"])
        self.assertNotIn("soften", branches["brighten"]["claim_refs"])
        self.assertIn("COMPATIBILITY_GAP", {row["limitation"]["kind"] for row in e["declared_limitations"]})
        self.assertEqual(self.files(), before)

    def test_b_comparisons_distinguish_authored_correction_from_fresh_review(self):
        original, corrected, reviewed = [self.demo[key] for key in (
            "original_revision_1", "correction_revision_2", "review_revision_3")]
        before = self.files()
        changed = self.report("compare", original, corrected)
        review = self.report("compare", corrected, reviewed)
        self.assertEqual([row["packet_id"] for row in changed["inputs"]], [original, corrected])
        self.assertEqual([row["packet_id"] for row in review["inputs"]], [corrected, reviewed])
        self.assertEqual(changed["analyses"][0]["authored_conclusion"]["kind"], "INDETERMINATE_MISSING")
        self.assertEqual(changed["analyses"][1]["authored_conclusion"]["kind"], "CONDITIONAL_SUPPORT")
        self.assertTrue(changed["analyses"][0]["condition_findings"])
        self.assertFalse(changed["analyses"][1]["condition_findings"])
        self.assertTrue(changed["reviewed_material_changed"])
        self.assertFalse(changed["review_only_change"])
        beacon = next(row for row in changed["changes"]["claims"] if row["node"] == "claim:beacon")
        self.assertIn("condition", [row["field"] for row in beacon["changed_fields"]])
        self.assertIn("attribution", [row["field"] for row in beacon["changed_fields"]])
        self.assertIn("value", [row["field"] for row in beacon["changed_fields"]])
        self.assertEqual(beacon["structural_impact"]["descendant"]["dependent_step_refs"], ["condition"])
        self.assertTrue(changed["changes"]["reasoning"])
        self.assertTrue(changed["changes"]["authored_conclusion"])
        omitted = changed["changes"]["review_observations"]["absent_from_successor"]
        self.assertEqual(omitted[0]["origin_packet_id"], original)
        self.assertEqual(omitted[0]["observation"]["observation_id"], "review-1")
        self.assertFalse(review["reviewed_material_changed"])
        self.assertTrue(review["review_only_change"])
        self.assertEqual(review["changes"]["claims"], [])
        self.assertEqual(review["changes"]["reasoning"], [])
        self.assertEqual(review["changes"]["condition_findings"], {"no_longer_reported": [], "newly_reported": []})
        fresh_observation = review["changes"]["review_observations"]["added"][0]
        self.assertEqual(fresh_observation["origin_packet_id"], reviewed)
        self.assertEqual(fresh_observation["observation"]["reviewer_id"], "fictional:b:second-reviewer")
        for value in (changed, review):
            for view in value["analyses"]:
                self.assertIn("scope", [row["limitation"]["limitation_id"] for row in view["declared_limitations"]])
                self.assertIn("EXECUTION", view["authored_conclusion"]["unsupported_stronger_conclusions"])
        # Endpoint dependency material remains equal when only a review changes.
        for key in ("authored_conclusion", "branches", "nodes", "edges", "condition_findings", "declared_limitations"):
            self.assertEqual(review["analyses"][0][key], review["analyses"][1][key])
        readable = self.cli("compare", original, corrected).stdout.decode()
        self.assertIn("beacon", readable)
        self.assertIn("UNKNOWN", readable)
        self.assertIn("review-1", readable)
        self.assertIn(original, readable)
        fresh = self.cli("compare", corrected, reviewed).stdout.decode()
        self.assertIn("review-correction", fresh)
        self.assertIn("fictional:b:second-reviewer", fresh)
        self.assertEqual(self.files(), before)

    def test_changed_graph_traces_transitive_mixed_findings_but_not_uncited_unknown(self):
        original = self.examples[v.PACKET_NAMES[1]]
        packet = self.successor(original)
        # Same retained B names are not required by the analysis: rename all
        # reasoning and author a new dependency, then select only its descendant.
        packet["reasoning"][0]["step_id"] = "supplied-inputs"
        packet["limitations"][0]["step_refs"] = ["supplied-inputs"]
        packet["reasoning"].append({**deepcopy(packet["reasoning"][0]),
            "step_id": "authored-result", "claim_refs": ["premise"],
            "depends_on_steps": ["supplied-inputs"], "explanation": "A declared transitive fictional dependency."})
        packet["conclusion"]["step_refs"] = ["authored-result"]
        unsupported = {"limitation_id": "not-implemented", "kind": "UNSUPPORTED",
            "context_ids": ["ctx"], "claim_refs": ["flash"], "step_refs": ["evaluate-later"],
            "description": "Supplied named assertions do not implement this authored operation."}
        packet["limitations"].append(unsupported)
        packet["reasoning"].insert(1, {**deepcopy(packet["reasoning"][0]),
            "step_id": "evaluate-later", "claim_refs": ["flash"], "condition": "UNSUPPORTED",
            "operation": "UNSUPPORTED_EVALUATION", "limitation_refs": ["not-implemented"]})
        packet["reasoning"][-1]["depends_on_steps"].append("evaluate-later")
        packet["conclusion"]["limitation_refs"].append("not-implemented")
        for source in self.examples[v.PACKET_NAMES[3]]["claims"][1:3]:
            claim = deepcopy(source)
            claim["subject_id"] = "fictional:b:other-beacon"
            claim["attribution"]["actor_id"] = claim["attribution"]["actor_id"].replace("fictional:d:", "fictional:b:")
            packet["claims"].append(claim)
        packet["limitations"].append({"limitation_id": "beacon-conflict", "kind": "CONFLICT",
            "context_ids": ["ctx"], "claim_refs": ["lit", "unlit"], "step_refs": ["authored-result"],
            "description": "Two separately attributed values remain disputed."})
        packet["reasoning"][-1]["claim_refs"].extend(["lit", "unlit"])
        packet["conclusion"]["limitation_refs"].append("beacon-conflict")
        uncited = deepcopy(packet["claims"][1])
        uncited.update(claim_id="uncited-unknown", subject_id="fictional:b:unrelated", limitation_refs=["uncited-limit"])
        uncited["attribution"]["statement_id"] = "statement-uncited"
        packet["claims"].append(uncited)
        packet["limitations"].append({"limitation_id": "uncited-limit", "kind": "UNKNOWN",
            "context_ids": ["ctx"], "claim_refs": ["uncited-unknown"], "step_refs": [],
            "description": "Uncited packet content, outside the selected authored dependencies."})
        self.record(packet)
        before = self.files()
        view = self.report("analyze", packet["packet_id"])["analyses"][0]
        branch = view["branches"][0]
        self.assertEqual(branch["direct_step_refs"], ["authored-result"])
        self.assertEqual(set(branch["transitive_step_refs"]), {"supplied-inputs", "evaluate-later"})
        self.assertEqual({row["condition"] for row in view["condition_findings"]}, {"UNKNOWN", "UNSUPPORTED", "CONFLICTING"})
        self.assertNotIn("claim:uncited-unknown", {row["node"] for row in view["condition_findings"]})
        self.assertNotIn("limitation:uncited-limit", {row["node"] for row in view["declared_limitations"]})
        self.assertIn("uncited-unknown", json.dumps(view["uncited_packet_content"]))
        self.assertIn("step:authored-result", json.dumps(view["condition_findings"]))
        self.assertIn("step:supplied-inputs", json.dumps(view["condition_findings"]))
        relationships = {(edge["source"], edge["target"], edge["relationship"]) for edge in view["edges"]}
        self.assertTrue(any(source == "step:authored-result" and target == "step:supplied-inputs"
            for source, target, _ in relationships))
        supplied = self.successor(packet)
        next(row for row in supplied["claims"] if row["claim_id"] == "beacon").update(
            condition="PRESENT", value=True, limitation_refs=[], attribution={
                "actor_id": "fictional:b:new-author", "statement_id": "statement-supplied-beacon"})
        self.record(supplied)
        supplied_delta = self.report("compare", packet["packet_id"], supplied["packet_id"])
        changed_beacon = next(row for row in supplied_delta["changes"]["claims"] if row["node"] == "claim:beacon")
        self.assertEqual(set(changed_beacon["structural_impact"]["descendant"]["dependent_step_refs"]),
            {"supplied-inputs", "authored-result"})
        self.assertIn("UNKNOWN", {row["condition"] for row in supplied_delta["analyses"][1]["condition_findings"]})
        # Removing only the structured dependency drops the named support node;
        # its wording and packet contents remain present and unchanged.
        detached = self.successor(packet)
        detached["reasoning"][-1]["depends_on_steps"].remove("supplied-inputs")
        detached["reasoning"][-1]["claim_refs"].append("beacon")
        self.record(detached)
        detached_view = self.report("analyze", detached["packet_id"])["analyses"][0]
        self.assertNotIn("supplied-inputs", detached_view["branches"][0]["transitive_step_refs"])
        self.assertNotIn("step:supplied-inputs", {row["node"] for row in detached_view["condition_findings"]})
        delta = self.report("compare", packet["packet_id"], detached["packet_id"])
        self.assertIn("supplied-inputs", json.dumps(delta))
        for name, raw in before.items():
            self.assertEqual((self.workspace / name).read_bytes(), raw)

    def test_alternative_local_claims_and_contextual_choices_stay_separate(self):
        original = self.examples[v.PACKET_NAMES[4]]
        packet = self.successor(original)
        scoped = deepcopy(packet["claims"][-1])
        scoped.update(claim_id="soften-assumption", alternative_id="soften")
        scoped["attribution"]["statement_id"] = "statement-soften-assumption"
        packet["claims"].append(scoped)
        packet["reasoning"][0]["claim_refs"].append("soften-assumption")
        # A contextual choice may reference a supplied assertion without making
        # that assertion a premise of the selected reasoning.
        contextual = deepcopy(packet["claims"][2])
        contextual.update(claim_id="choice-only-detail", condition="UNKNOWN", value=None,
            limitation_refs=["choice-detail-unknown"])
        contextual["attribution"]["statement_id"] = "statement-choice-detail"
        packet["claims"].append(contextual)
        packet["choices"][0]["claim_refs"].append("choice-only-detail")
        packet["limitations"].append({"limitation_id": "choice-detail-unknown", "kind": "UNKNOWN",
            "context_ids": ["ctx"], "claim_refs": ["choice-only-detail"], "step_refs": [],
            "description": "A contextual unknown is not a declared reasoning premise."})
        self.record(packet)
        view = self.report("analyze", packet["packet_id"])["analyses"][0]
        branches = {row["alternative_id"]: row for row in view["branches"]}
        self.assertIn("soften-assumption", branches["soften"]["claim_refs"])
        self.assertNotIn("soften-assumption", branches["brighten"]["claim_refs"])
        self.assertNotIn("choice-only-detail", branches["soften"]["claim_refs"])
        self.assertNotIn("claim:choice-only-detail", {row["node"] for row in view["condition_findings"]})
        self.assertEqual(branches["soften"]["contextual_choice_refs"], ["choice-soften"])
        self.assertEqual(branches["brighten"]["contextual_choice_refs"], ["choice-brighten"])
        reordered = self.successor(packet)
        reordered["claims"].reverse()
        reordered["choices"][0]["description"] += " Separately changed contextual description."
        self.record(reordered)
        delta = self.report("compare", packet["packet_id"], reordered["packet_id"])
        self.assertEqual(delta["changes"]["claims"], [])
        order = next(row for row in delta["changes"]["collection_order"] if row["collection"] == "claims")
        self.assertEqual(order["descendant"], list(reversed(order["ancestor"])))
        impact = delta["changes"]["choices"][0]["structural_impact"]["descendant"]
        self.assertEqual(impact["dependent_step_refs"], [])
        self.assertEqual(impact["branches"], [])
        self.assertEqual({row["alternative_id"] for row in impact["associated_branches"]}, {"soften"})
        self.assertTrue(impact["reference_associations"])
        invalid = self.successor(packet)
        invalid["reasoning"][1]["claim_refs"].append("soften-assumption")
        v.seal_packet(invalid)
        self.path(invalid["packet_id"]).write_bytes(v._canonical_candidate(invalid))
        self.cli("analyze", invalid["packet_id"], "--json", success=False)

    def test_determinism_relocation_identity_and_private_owned_results(self):
        identity = self.demo["correction_revision_2"]
        first = self.cli("analyze", identity, "--json").stdout
        self.assertEqual(self.cli("analyze", identity, "--json").stdout, first)
        relocated = self.root / "relocated"
        shutil.copytree(self.workspace, relocated)
        self.assertEqual(self.cli("analyze", identity, "--json", workspace=relocated).stdout, first)
        workspace = Workspace(self.workspace)
        owned = workspace.read(identity)
        with patch.object(workspace, "read", return_value=owned):
            report = analysis.analyze(workspace, identity)
        owned[0]["claims"][0]["value"] = "Later caller mutation"
        owned[0]["conclusion"]["text"] = "Later caller conclusion"
        next(iter(owned[1].values()))["conclusion"]["text"] = "Later history mutation"
        mutable_output = report.to_dict()
        mutable_output["analyses"][0]["authored_conclusion"]["text"] = "Later output mutation"
        self.assertEqual(report.canonical_bytes, first)
        self.assertNotIn("Later", json.dumps(report.to_dict()))
        packet, _ = workspace.read(identity)
        unchanged = self.record(self.successor(packet))
        second = self.report("analyze", unchanged["packet_id"])
        self.assertNotEqual(json.loads(first)["report_id"], second["report_id"])
        no_change = self.report("compare", identity, identity)
        self.assertEqual(no_change["inputs"][0], no_change["inputs"][1])
        self.assertTrue(no_change["no_change"])
        self.assertFalse(no_change["review_only_change"])

    def test_fresh_file_history_retained_bindings_and_exact_roots_are_required(self):
        original = self.demo["original_revision_1"]
        corrected = self.demo["correction_revision_2"]
        reviewed = self.demo["review_revision_3"]
        self.cli("compare", original, reviewed, "--json")
        before = self.files()
        raw = self.path(original).read_bytes()
        self.path(original).write_bytes(raw + b" ")
        self.cli("analyze", reviewed, "--json", success=False)
        self.cli("compare", corrected, reviewed, "--json", success=False)
        self.assertEqual(self.path(original).read_bytes(), raw + b" ")
        self.path(original).write_bytes(raw)
        self.cli("compare", original, self.examples[v.PACKET_NAMES[0]]["packet_id"], "--json", success=False)
        self.cli("compare", reviewed, original, "--json", success=False)
        sibling = self.successor(self.examples[v.PACKET_NAMES[1]])
        sibling["reasoning"][0]["explanation"] += " A separately authored sibling revision."
        self.record(sibling)
        result = self.cli("compare", corrected, sibling["packet_id"], "--json", success=False)
        self.assertIn("ANALYSIS_EXPLICIT_ANCESTOR_REQUIRED", result.stderr.decode())
        self.path(sibling["packet_id"]).unlink()
        # A freshly resealed edited root cannot bypass PR #210's root policy by
        # being placed directly in the read-only workspace.
        edited = deepcopy(self.examples[v.PACKET_NAMES[1]])
        edited["conclusion"]["text"] += " This edited unparented root is invalid for the pilot."
        v.seal_packet(edited)
        edited_path = self.path(edited["packet_id"])
        edited_path.write_bytes(v._canonical_candidate(edited))
        result = self.cli("analyze", edited["packet_id"], "--json", success=False)
        self.assertIn("PILOT_EDITED_ROOT_REQUIRES_EXPLICIT_PARENT", result.stderr.decode())
        edited_child = self.successor(edited)
        v.seal_packet(edited_child)
        self.path(edited_child["packet_id"]).write_bytes(v._canonical_candidate(edited_child))
        result = self.cli("analyze", edited_child["packet_id"], "--json", success=False)
        self.assertIn("PILOT_EDITED_ROOT_REQUIRES_EXPLICIT_PARENT", result.stderr.decode())
        self.path(edited_child["packet_id"]).unlink()
        edited_path.unlink()
        # Reusing Workspace must still read actual retained files on every call.
        copied = self.root / "retained-design"
        shutil.copytree(v.PACKAGE_ROOT, copied)
        load_package = v.load_package
        workspace = Workspace(self.workspace)
        with patch.object(v, "load_package", side_effect=lambda: load_package(copied)):
            analysis.analyze(workspace, reviewed)
            contract = copied / "contract.json"
            contract.write_bytes(contract.read_bytes() + b" ")
            with self.assertRaises(GameplayContractError):
                analysis.analyze(workspace, reviewed)
        self.assertEqual(self.files(), before)


if __name__ == "__main__":
    unittest.main()
