"""PR #210 corrections exercised through the offline CLI and actual files."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from proposed_spell_packets import validation as design


ROOT = Path(__file__).resolve().parents[1]


class ProposedSpellPacketAuthoringCorrectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example_name = design.PACKET_NAMES[0]
        cls.example_raw = (design.PACKAGE_ROOT / cls.example_name).read_bytes()
        cls.example = json.loads(cls.example_raw)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "pilot"
        self.workspace.mkdir()
        self.serial = 0

    def path(self, label="input"):
        self.serial += 1
        return self.root / (label + str(self.serial) + ".json")

    def write(self, value, *, canonical=False):
        path = self.path()
        path.write_bytes(design._canonical_candidate(value) if canonical else
            (json.dumps(value, indent=2, ensure_ascii=False) + "\n").encode())
        return path

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

    def records(self, workspace=None):
        directory = (workspace or self.workspace) / "packets"
        return {p.name: p.read_bytes() for p in directory.glob("*.json")} if directory.exists() else {}

    def record_path(self, identity, workspace=None):
        return (workspace or self.workspace) / "packets" / (identity[7:] + ".json")

    def draft(self, *, example=None, base=None):
        path = self.path("draft")
        selection = ("--example", example) if example else ("--base", base)
        self.cli("draft", *selection, "--output", path)
        return path, json.loads(path.read_bytes())

    def record(self, envelope):
        result = self.cli("record", "--draft", self.write(envelope))
        identity = json.loads(result.stdout)["packet_id"]
        raw = self.record_path(identity).read_bytes()
        packet = json.loads(raw)
        self.assertEqual(raw, design._canonical_candidate(packet))
        self.assertEqual(packet["packet_id"], identity)
        return packet

    def import_example(self):
        self.cli("record", "--sealed", self.write(self.example, canonical=True))
        self.assertEqual(self.record_path(self.example["packet_id"]).read_bytes(), self.example_raw)
        return deepcopy(self.example)

    @staticmethod
    def envelope(packet, base=None):
        body = deepcopy(packet)
        del body["packet_id"]
        return {"draft_version": 1, "base_packet_id": base, "packet": body}

    def test_copied_review_cannot_be_retargeted_through_any_root_entry_point(self):
        original_observation = deepcopy(self.example["history"]["review_observations"])
        for entry in ("template", "manual", "sealed", "ancestor"):
            with self.subTest(entry=entry):
                workspace = self.root / entry
                workspace.mkdir()
                candidate = deepcopy(self.example)
                candidate["reasoning"][0]["explanation"] += " Authored changed fictional explanation."
                self.assertEqual(candidate["history"]["review_observations"], original_observation)
                if entry == "template":
                    path = self.path("template")
                    self.cli("draft", "--example", self.example_name, "--output", path,
                        workspace=workspace)
                    envelope = json.loads(path.read_bytes())
                    envelope["packet"]["reasoning"] = deepcopy(candidate["reasoning"])
                    path.write_text(json.dumps(envelope, indent=2) + "\n")
                    args = ("record", "--draft", path)
                elif entry == "manual":
                    args = ("record", "--draft", self.write(self.envelope(candidate)))
                else:
                    design.seal_packet(candidate)
                    if entry == "ancestor":
                        # An externally placed canonical root must not authorize
                        # a child merely because its own ID and schema verify.
                        bad_root = deepcopy(candidate)
                        destination = self.record_path(bad_root["packet_id"], workspace)
                        destination.parent.mkdir()
                        destination.write_bytes(design._canonical_candidate(bad_root))
                        candidate["revision"] = 2
                        candidate["history"]["supersedes_packet_ids"] = [bad_root["packet_id"]]
                        design.seal_packet(candidate)
                    args = ("record", "--sealed", self.write(candidate, canonical=True))
                before = self.records(workspace)
                result = self.cli(*args, success=False, workspace=workspace)
                self.assertIn("PILOT_EDITED_ROOT_REQUIRES_EXPLICIT_PARENT", result.stdout + result.stderr)
                self.assertEqual(self.records(workspace), before)

    def test_exact_template_and_explicit_parent_corrections_keep_review_origins(self):
        _, envelope = self.draft(example=self.example_name)
        original = self.record(envelope)
        self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), self.example_raw)
        _, correction = self.draft(base=original["packet_id"])
        correction["packet"]["reasoning"][0]["explanation"] += " Authored fictional correction."
        correction["packet"]["history"]["review_observations"] = []
        corrected = self.record(correction)
        _, reviewed_draft = self.draft(base=corrected["packet_id"])
        fresh = deepcopy(original["history"]["review_observations"][0])
        fresh.update(observation_id="review-corrected-material",
            reviewer_id="fictional:a:second-reviewer",
            text="Authored fictional review of the corrected explanation; no real approval or authority.")
        reviewed_draft["packet"]["history"]["review_observations"] = [fresh]
        reviewed = self.record(reviewed_draft)
        history = self.cli("history", reviewed["packet_id"]).stdout
        for packet in (original, corrected, reviewed):
            self.assertIn(packet["packet_id"], history)
        view = self.cli("inspect", reviewed["packet_id"]).stdout
        self.assertIn("originating packet " + reviewed["packet_id"], view)
        self.assertNotIn(original["history"]["review_observations"][0]["text"], view)
        self.assertIn(original["history"]["review_observations"][0]["text"], history)

        # Review-only correction carries both local observations and unchanged
        # material; supersession does not invent an ancestor-only reference.
        _, review_only = self.draft(base=original["packet_id"])
        replacement = deepcopy(fresh)
        replacement.update(observation_id="review-only-correction",
            supersedes_observation_ids=["review-1"])
        review_only["packet"]["history"]["review_observations"].append(replacement)
        revised = self.record(review_only)
        view = self.cli("inspect", revised["packet_id"]).stdout
        self.assertIn("originating packet " + original["packet_id"], view)
        self.assertIn("originating packet " + revised["packet_id"], view)
        self.assertEqual(self.record_path(original["packet_id"]).read_bytes(), self.example_raw)

    def test_generated_near_limit_draft_round_trips_and_oversized_packet_is_rejected(self):
        original = self.import_example()
        parent = deepcopy(original)
        parent["revision"] = 2
        parent["history"]["supersedes_packet_ids"] = [original["packet_id"]]
        design.seal_packet(parent)
        parent["conclusion"]["text"] += "x" * (127059 - len(design._canonical_candidate(parent)))
        design.seal_packet(parent)
        parent_raw = design._canonical_candidate(parent)
        self.assertEqual(len(parent_raw), 127059)
        self.cli("record", "--sealed", self.write(parent, canonical=True))
        self.assertEqual(self.record_path(parent["packet_id"]).read_bytes(), parent_raw)
        generated_path, generated = self.draft(base=parent["packet_id"])
        expected = deepcopy(generated["packet"])
        design.seal_packet(expected)
        expected_raw = design._canonical_candidate(expected)
        self.assertLessEqual(len(expected_raw), 128000)
        print("CLI draft boundary sizes: " + json.dumps({"parent": len(parent_raw),
            "generated_draft": generated_path.stat().st_size,
            "canonical_child": len(expected_raw)}, sort_keys=True), flush=True)
        before = self.records()
        with self.subTest(boundary="generated-draft"):
            result = self.cli("record", "--draft", generated_path)
            self.assertEqual(json.loads(result.stdout)["packet_id"], expected["packet_id"])
            self.assertEqual(self.record_path(expected["packet_id"]).read_bytes(), expected_raw)
            self.cli("inspect", expected["packet_id"])
            self.assertEqual({name: self.records()[name] for name in before}, before)

        with self.subTest(boundary="canonical-oversize"):
            oversized = deepcopy(generated)
            oversized["packet"]["conclusion"]["text"] += "x" * (128001 - len(expected_raw))
            sealed_oversized = deepcopy(oversized["packet"])
            design.seal_packet(sealed_oversized)
            self.assertEqual(len(design._canonical_candidate(sealed_oversized)), 128001)
            before = self.records()
            result = self.cli("record", "--draft", self.write(oversized), success=False)
            self.assertIn("PACKET_EXCEEDS_BOUNDED_READ_SIZE", result.stdout + result.stderr)
            self.assertEqual(self.records(), before)
            self.assertFalse(self.record_path(sealed_oversized["packet_id"]).exists())

    def test_draft_reader_remains_strict_bounded_and_refuses_links(self):
        self.import_example()
        envelope = self.envelope(self.example)
        raw = json.dumps(envelope)
        malformed = {
            "duplicate": raw.replace('"draft_version": 1', '"draft_version": 1, "draft_version": 1'),
            "nonfinite": raw.replace('"draft_version": 1', '"draft_version": NaN'),
            "bounded": " " * 2_000_000 + raw,
        }
        before = self.records()
        for label, contents in malformed.items():
            with self.subTest(input=label):
                path = self.path(label)
                path.write_text(contents)
                self.cli("record", "--draft", path, success=False)
                self.assertEqual(self.records(), before)
        source = self.write(envelope)
        for label in ("symlink", "hardlink"):
            with self.subTest(input=label):
                linked = self.path(label)
                if label == "symlink":
                    linked.symlink_to(source)
                else:
                    linked.hardlink_to(source)
                self.cli("record", "--draft", linked, success=False)
                self.assertEqual(self.records(), before)
                linked.unlink()


if __name__ == "__main__":
    unittest.main()
