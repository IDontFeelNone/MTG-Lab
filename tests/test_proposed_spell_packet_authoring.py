"""Offline packet authoring through the real CLI and disposable file boundaries."""
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
from proposed_spell_packets import authoring
from proposed_spell_packets import validation as design


ROOT = Path(__file__).resolve().parents[1]


class ProposedSpellPacketAuthoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.examples = {name: json.loads((design.PACKAGE_ROOT / name).read_bytes())
            for name in design.PACKET_NAMES}

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "pilot"
        self.workspace.mkdir()
        self.serial = 0

    def cli(self, *args, success=True, workspace=None):
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
        result = subprocess.run([sys.executable, "-m", "proposed_spell_packets",
            "--workspace", str(workspace or self.workspace), *map(str, args)],
            cwd=ROOT, env=env, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return result

    def path(self, label="input"):
        self.serial += 1
        return self.root / (label + str(self.serial) + ".json")

    def write(self, value, *, canonical=False):
        path = self.path()
        path.write_bytes(design._canonical_candidate(value) if canonical else
            (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())
        return path

    def records(self):
        directory = self.workspace / "packets"
        return {p.name: p.read_bytes() for p in directory.glob("*.json")} if directory.exists() else {}

    def record_path(self, identity):
        return self.workspace / "packets" / (identity.split(":")[1] + ".json")

    def record(self, envelope):
        result = self.cli("record", "--draft", self.write(envelope))
        identity = json.loads(result.stdout)["packet_id"]
        raw = self.record_path(identity).read_bytes()
        packet = json.loads(raw)
        self.assertEqual(packet["packet_id"], identity)
        self.assertEqual(raw, design._canonical_candidate(packet))
        return packet

    def import_packet(self, packet):
        path = self.write(packet, canonical=True)
        result = self.cli("record", "--sealed", path)
        self.assertEqual(json.loads(result.stdout)["packet_id"], packet["packet_id"])
        self.assertEqual(self.record_path(packet["packet_id"]).read_bytes(), path.read_bytes())
        return packet

    def draft(self, *, example=None, base=None):
        path = self.path("draft")
        args = ("--example", example) if example else ("--base", base)
        self.cli("draft", *args, "--output", path)
        envelope = json.loads(path.read_bytes())
        self.assertEqual(set(envelope), {"draft_version", "base_packet_id", "packet"})
        self.assertNotIn("packet_id", envelope["packet"])
        self.assertEqual(envelope["base_packet_id"], base)
        return envelope

    def rejected(self, envelope, error=None):
        before = self.records()
        result = self.cli("record", "--draft", self.write(envelope), success=False)
        if error:
            self.assertIn(error, result.stdout + result.stderr)
        self.assertEqual(self.records(), before, "Invalid drafts must not write or modify packets")
        return result

    def test_all_five_examples_round_trip_with_original_bytes_and_explanations(self):
        for name, outcome in zip(design.PACKET_NAMES, design.EXPECTED_OUTCOMES):
            with self.subTest(example=name):
                packet = self.record(self.draft(example=name))
                self.assertEqual(packet, self.examples[name])
                self.assertEqual(self.record_path(packet["packet_id"]).read_bytes(),
                    (design.PACKAGE_ROOT / name).read_bytes())
                view = self.cli("inspect", packet["packet_id"]).stdout
                for text in (packet["packet_id"], packet["scenario_label"],
                        packet["question"]["text"], packet["conclusion"]["text"], outcome,
                        "BLOCKED", packet["lineage_id"]):
                    self.assertIn(text, view)
                for step in packet["reasoning"]:
                    self.assertIn(step["explanation"], view)
                    self.assertIn(step["condition"], view)
                for limitation in packet["limitations"]:
                    self.assertIn(limitation["kind"], view)
                    self.assertIn(limitation["description"], view)
                for claim in packet["claims"]:
                    self.assertIn(claim["predicate"], view)
                    self.assertIn(claim["attribution"]["actor_id"], view)
                for evidence in packet["rule_evidence"]:
                    self.assertIn(evidence["rule_reference"], view)
                    self.assertIn(evidence["effective_date"], view)

    def test_sealed_identity_and_canonical_bytes_are_verified_never_resealed(self):
        original = deepcopy(self.examples[design.PACKET_NAMES[0]])
        self.import_packet(original)
        before = self.records()
        for change in ("identity", "material", "format", "lifecycle"):
            packet = deepcopy(original)
            if change == "identity":
                packet["packet_id"] = "sha256:" + "0" * 64
            elif change == "material":
                packet["claims"][-1]["value"] = False
            elif change == "lifecycle":
                packet["revision"] = 2
                design.seal_packet(packet)
            path = self.write(packet, canonical=change != "format")
            with self.subTest(change=change):
                self.cli("record", "--sealed", path, success=False)
                self.assertEqual(self.records(), before)
        # Reimporting exact bytes is explicit and verifies the existing record.
        result = self.cli("record", "--sealed", self.write(original, canonical=True))
        self.assertIn("present", result.stdout.lower())
        self.assertEqual(self.records(), before)

    def test_draft_input_is_closed_strict_and_never_discards_supplied_identity(self):
        good = self.draft(example=design.PACKET_NAMES[0])
        mutations = {
            "envelope unknown": lambda d: d.update(extra=True),
            "supplied identity": lambda d: d["packet"].update(packet_id=self.examples[design.PACKET_NAMES[0]]["packet_id"]),
            "draft boolean": lambda d: d.update(draft_version=True),
            "revision boolean": lambda d: d["packet"].update(revision=True),
            "revision float": lambda d: d["packet"].update(revision=1.0),
            "context float": lambda d: d["packet"]["contexts"][0].update(version=1.0),
            "fictional integer": lambda d: d["packet"].update(fictional=1),
            "claim numeric": lambda d: d["packet"]["claims"][0].update(value=42),
            "nested unknown": lambda d: d["packet"]["claims"][0].update(extra=True),
            "bad base type": lambda d: d.update(base_packet_id=[]),
            "lifecycle reparent": lambda d: d["packet"]["history"].update(supersedes_packet_ids=["sha256:" + "0" * 64]),
            "dangling local": lambda d: d["packet"]["reasoning"][0]["claim_refs"].append("absent"),
            "wrong retained owner": lambda d: d["packet"]["rule_evidence"][0].update(retained_package="gameplay-rules-other"),
            "wrong retained anchor": lambda d: d["packet"]["rule_evidence"][0].update(anchor_id="sha256:" + "0" * 64),
        }
        for label, mutate in mutations.items():
            candidate = deepcopy(good)
            mutate(candidate)
            with self.subTest(label=label):
                self.rejected(candidate)
        raw = json.dumps(good)
        for malformed in (raw.replace('"draft_version": 1', '"draft_version": 1, "draft_version": 1'),
                raw.replace('"draft_version": 1', '"draft_version": NaN'),
                raw.replace('"draft_version": 1', '"draft_version": Infinity')):
            path = self.path()
            path.write_text(malformed)
            before = self.records()
            self.cli("record", "--draft", path, success=False)
            self.assertEqual(self.records(), before)

    def test_direct_transitive_and_independent_assumption_scopes_through_record(self):
        good = self.draft(example=design.PACKET_NAMES[4])
        for derived in (False, True):
            for alternative in (None, "soften", "brighten"):
                candidate = deepcopy(good)
                packet = candidate["packet"]
                premise = deepcopy(packet["claims"][-1])
                premise.update(claim_id="scoped-premise", alternative_id=alternative)
                premise["attribution"]["statement_id"] = "statement-scoped-premise"
                packet["claims"].append(premise)
                step = "address"
                if derived:
                    packet["reasoning"].append({**packet["reasoning"][0],
                        "step_id": "derived", "claim_refs": ["premise"], "depends_on_steps": ["address"]})
                    step = "derived"
                packet["conclusion"].update(kind="CONDITIONAL_SUPPORT", step_refs=[step],
                    assumption_refs=["premise", "scoped-premise"], limitation_refs=["scope"])
                with self.subTest(derived=derived, alternative=alternative):
                    if alternative == "brighten":
                        self.rejected(candidate, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH")
                    else:
                        self.record(candidate)
        candidate = deepcopy(good)
        packet = candidate["packet"]
        premise = deepcopy(packet["claims"][-1])
        premise.update(claim_id="soften-premise", alternative_id="soften")
        premise["attribution"]["statement_id"] = "statement-soften-premise"
        packet["claims"].append(premise)
        packet["reasoning"][0]["claim_refs"].append("soften-premise")
        self.record(candidate)  # A step-local restricted premise is legitimate.
        packet["conclusion"]["assumption_refs"].append("soften-premise")
        self.rejected(candidate, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH")
        packet["conclusion"].update(kind="CONDITIONAL_SUPPORT", step_refs=["general"], limitation_refs=["scope"])
        packet["reasoning"].append({**packet["reasoning"][0], "step_id": "general",
            "alternative_id": None, "claim_refs": ["premise"]})
        self.rejected(candidate, "CONCLUSION_ASSUMPTION_SCOPE_MISMATCH")

    def test_missing_correction_fresh_review_and_history_keep_original_context(self):
        original = self.record(self.draft(example=design.PACKET_NAMES[1]))
        original_raw = self.record_path(original["packet_id"]).read_bytes()
        correction = self.draft(base=original["packet_id"])
        packet = correction["packet"]
        beacon = next(c for c in packet["claims"] if c["claim_id"] == "beacon")
        beacon.update(condition="PRESENT", value=True, limitation_refs=[])
        beacon["attribution"] = {"actor_id": "fictional:b:correction-author", "statement_id": "statement-beacon-correction"}
        packet["limitations"] = [row for row in packet["limitations"] if row["limitation_id"] != "missing-beacon"]
        packet["reasoning"][0].update(condition="PRESENT", limitation_refs=[],
            explanation="Authored fictional correction: the narrator now asserts that the beacon is lit. Under premise, the named conditional-flash condition is supported only for this bounded question; no overall permission follows.")
        packet["conclusion"].update(kind="CONDITIONAL_SUPPORT", limitation_refs=["scope"],
            text="Authored fictional conclusion: conditional support under the newly supplied beacon assertion and premise. Overall permission, legality, payment, completion and execution remain unestablished.")
        self.rejected(correction, "HISTORICAL_OBSERVATION_MATERIAL_CHANGED")
        packet["history"]["review_observations"] = []
        corrected = self.record(correction)
        reviewed_draft = self.draft(base=corrected["packet_id"])
        observation = deepcopy(original["history"]["review_observations"][0])
        observation.update(observation_id="review-correction", reviewer_id="fictional:b:second-reviewer",
            text="Separately authored fictional review: the supplied assertion remains unverified and scope limitations remain. This is no PM or owner approval.")
        reviewed_draft["packet"]["history"]["review_observations"] = [observation]
        reviewed = self.record(reviewed_draft)
        self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), original_raw)
        history = self.cli("history", reviewed["packet_id"]).stdout
        positions = [history.index(p["packet_id"]) for p in (original, corrected, reviewed)]
        self.assertEqual(positions, sorted(positions))
        for text in (original["conclusion"]["text"], corrected["conclusion"]["text"],
                original["history"]["review_observations"][0]["text"], observation["text"],
                "INDETERMINATE_MISSING", "CONDITIONAL_SUPPORT", "fictional:b:second-reviewer"):
            self.assertIn(text, history)
        # Required reachable history is checked from its current actual bytes.
        self.record_path(original["packet_id"]).write_bytes(original_raw + b" ")
        self.cli("inspect", reviewed["packet_id"], success=False)
        self.cli("history", reviewed["packet_id"], success=False)
        self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), original_raw + b" ")
        self.record_path(original["packet_id"]).write_bytes(original_raw)
        # Local supersession cannot point only to an observation left in an ancestor.
        dangling = self.draft(base=corrected["packet_id"])
        fresh = deepcopy(observation)
        fresh["supersedes_observation_ids"] = ["review-1"]
        dangling["packet"]["history"]["review_observations"] = [fresh]
        self.rejected(dangling, "DANGLING_PRIOR_OBSERVATION_REFERENCE")

    def test_historical_observations_bind_claims_transitive_material_choices_and_limits(self):
        for change in ("claim", "step", "transitive", "choice", "added-choice", "limitation", "rule-context", "rule-evidence", "context"):
            original = deepcopy(self.examples[design.PACKET_NAMES[0]])
            original["history"]["review_observations"][0]["claim_refs"] = []
            original["reasoning"][0]["limitation_refs"] = ["scope"]
            if change == "transitive":
                original["reasoning"].insert(0, {**original["reasoning"][0],
                    "step_id": "premise-step", "alternative_id": None,
                    "claim_refs": ["premise"], "limitation_refs": []})
                original["reasoning"][1]["depends_on_steps"] = ["premise-step"]
                original["reasoning"][1]["claim_refs"].remove("premise")
            design.seal_packet(original)
            self.import_packet(original)
            original_raw = self.record_path(original["packet_id"]).read_bytes()
            successor = self.draft(base=original["packet_id"])
            packet = successor["packet"]
            if change in ("claim", "transitive"):
                packet["claims"][-1]["value"] = False
            elif change == "step":
                packet["reasoning"][0]["explanation"] += " Changed authored explanation."
            elif change == "choice":
                packet["choices"][0]["description"] += " Changed fictional choice."
            elif change == "added-choice":
                packet["choices"].append({**packet["choices"][0], "choice_id": "second-soften-choice"})
            elif change == "limitation":
                packet["limitations"][0]["description"] += " Additional scope restriction."
            elif change == "rule-context":
                packet["claims"][0]["rule_context_refs"].append("r601-3a")
            elif change == "rule-evidence":
                replacement = deepcopy(next(row for row in packet["rule_evidence"] if row["evidence_id"] == "r601-3a"))
                replacement["evidence_id"] = "r601-3"
                packet["rule_evidence"] = [replacement if row["evidence_id"] == "r601-3" else row
                    for row in packet["rule_evidence"]]
            else:
                packet["contexts"][0]["description"] += " Changed context."
            with self.subTest(change=change):
                self.rejected(successor, "HISTORICAL_CONTEXT_REBINDING_FORBIDDEN" if change == "context"
                    else "HISTORICAL_OBSERVATION_MATERIAL_CHANGED")
                self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), original_raw)

    def test_omission_and_reintroduction_cannot_erase_observation_binding(self):
        original = self.import_packet(deepcopy(self.examples[design.PACKET_NAMES[0]]))
        for changed in (False, True):
            middle_draft = self.draft(base=original["packet_id"])
            middle_draft["packet"]["history"]["review_observations"] = []
            if changed:
                middle_draft["packet"]["claims"][-1]["value"] = False
            middle = self.record(middle_draft)
            successor = self.draft(base=middle["packet_id"])
            successor["packet"]["history"]["review_observations"] = deepcopy(original["history"]["review_observations"])
            with self.subTest(changed=changed):
                if changed:
                    self.rejected(successor, "HISTORICAL_OBSERVATION_MATERIAL_CHANGED")
                else:
                    restored = self.record(successor)
                    self.assertEqual(restored["history"]["review_observations"], original["history"]["review_observations"])

    def test_unchanged_material_review_correction_keeps_both_local_observations(self):
        original = self.import_packet(deepcopy(self.examples[design.PACKET_NAMES[0]]))
        draft = self.draft(base=original["packet_id"])
        old = deepcopy(original["history"]["review_observations"][0])
        fresh = deepcopy(old)
        fresh.update(observation_id="review-2", reviewer_id="fictional:a:second-reviewer",
            supersedes_observation_ids=[old["observation_id"]],
            text="Authored fictional review-only correction of the earlier observation; material is unchanged. This supplies no approval or gameplay authority.")
        draft["packet"]["history"]["review_observations"].append(fresh)
        reviewed = self.record(draft)
        self.assertEqual(reviewed["history"]["review_observations"], [old, fresh])
        self.assertEqual(reviewed["claims"], original["claims"])
        view = self.cli("history", reviewed["packet_id"]).stdout
        for text in (original["packet_id"], reviewed["packet_id"], old["text"], fresh["text"], fresh["reviewer_id"]):
            self.assertIn(text, view)

    def test_record_and_draft_paths_refuse_links_overwrite_and_fresh_corruption(self):
        original = self.import_packet(deepcopy(self.examples[design.PACKET_NAMES[0]]))
        canonical = self.record_path(original["packet_id"])
        good_raw = canonical.read_bytes()
        draft_path = self.path("existing-draft")
        draft_path.write_text("unrelated local work\n")
        self.cli("draft", "--example", design.PACKET_NAMES[0], "--output", draft_path, success=False)
        self.assertEqual(draft_path.read_text(), "unrelated local work\n")
        source = self.write(original, canonical=True)
        linked = self.path("symlink")
        linked.symlink_to(source)
        self.cli("record", "--sealed", linked, success=False)
        hardlinked = self.path("hardlink")
        hardlinked.hardlink_to(source)
        self.cli("record", "--sealed", hardlinked, success=False)
        hardlinked.unlink()
        draft_link = self.path("draft-link")
        draft_source = self.write(self.draft(example=design.PACKET_NAMES[0]))
        draft_link.symlink_to(draft_source)
        self.cli("record", "--draft", draft_link, success=False)
        alias = self.root / "workspace-link"
        alias.symlink_to(self.workspace, target_is_directory=True)
        self.cli("inspect", original["packet_id"], workspace=alias, success=False)
        # A successful read cannot authorize changed bytes on the next operation.
        self.cli("inspect", original["packet_id"])
        for bad in (good_raw.replace(b'"revision":1', b'"revision":2'), b'{ "corrupt": true }\n'):
            canonical.write_bytes(bad)
            self.cli("inspect", original["packet_id"], success=False)
            self.cli("history", original["packet_id"], success=False)
            self.cli("draft", "--base", original["packet_id"], "--output", self.path(), success=False)
            self.cli("record", "--sealed", source, success=False)
            self.assertEqual(canonical.read_bytes(), bad, "No automatic repair of corrupted records")
        canonical.write_bytes(good_raw)  # Test-controlled restoration, never tool repair.
        renamed = self.workspace / "packets" / ("0" * 64 + ".json")
        canonical.rename(renamed)
        self.cli("inspect", "sha256:" + "0" * 64, success=False)
        self.assertEqual(renamed.read_bytes(), good_raw)

    def test_failed_write_publishes_no_partial_packet_and_record_uses_owned_snapshot(self):
        original = self.import_packet(deepcopy(self.examples[design.PACKET_NAMES[0]]))
        draft = self.draft(base=original["packet_id"])
        draft["packet"]["history"]["review_observations"] = []
        candidate_path = self.write(draft)
        workspace = authoring.Workspace(self.workspace)
        before = self.records()
        # Exercise the real write boundary with failure before atomic publication.
        with patch.object(authoring.os, "fsync", side_effect=OSError("fictional write failure")):
            with self.assertRaisesRegex(OSError, "fictional write failure"):
                workspace.record(draft=candidate_path)
        self.assertEqual(self.records(), before)
        self.assertFalse(list((self.workspace / "packets").glob(".partial-*")))
        # Mutation of the parser's returned draft after validation cannot alter
        # the separately owned bytes returned by the corrected shared checker.
        owned_input = authoring.read_draft(candidate_path)
        validate = workspace.validate
        def validate_then_mutate(value):
            result = validate(value)
            value["claims"][-1]["value"] = "Caller mutation after validation"
            owned_input["packet"]["conclusion"]["text"] = "Caller changed conclusion"
            return result
        with patch.object(authoring, "read_draft", return_value=owned_input), \
                patch.object(workspace, "validate", side_effect=validate_then_mutate):
            recorded = workspace.record(draft=candidate_path)
        raw = self.record_path(recorded["packet_id"]).read_bytes()
        self.assertNotIn(b"Caller mutation", raw)
        self.assertNotIn(b"Caller changed", raw)
        packet = json.loads(raw)
        self.assertEqual(packet["packet_id"], design.identity(design.PACKET_DOMAIN, packet, "packet_id"))
        self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), before[self.record_path(original["packet_id"]).name])

    def test_reused_workspace_rechecks_actual_contract_manifest_and_template_files(self):
        # Only the eight small fictional design files are copied to a disposable
        # fixture. The actual retained rule package validation still runs.
        copied = self.root / "retained-design"
        shutil.copytree(design.PACKAGE_ROOT, copied)
        load_package = design.load_package
        workspace = authoring.Workspace(self.workspace)
        original = deepcopy(self.examples[design.PACKET_NAMES[0]])
        with patch.object(design, "load_package", side_effect=lambda: load_package(copied)):
            workspace.record(sealed=self.write(original, canonical=True))
            draft_path = self.path("fresh-bindings-draft")
            workspace.draft(base=original["packet_id"], output=draft_path)
            before = self.records()
            for name in ("contract.json", "manifest.json", design.PACKET_NAMES[0]):
                path = copied / name
                raw = path.read_bytes()
                path.write_bytes(raw + b" ")
                with self.subTest(changed=name):
                    with self.assertRaises(GameplayContractError):
                        workspace.record(draft=draft_path)
                    with self.assertRaises(GameplayContractError):
                        workspace.read(original["packet_id"])
                    self.assertEqual(self.records(), before)
                path.write_bytes(raw)  # Test restores the disposable fixture.
            workspace.read(original["packet_id"])


if __name__ == "__main__":
    unittest.main()
