"""Keep Phase 121 evidence fixed; test the supported repair derivative separately.

A standalone Set is outside the frozen query/projection representation. The
original eight-record packet is explicitly rejected, not silently truncated.
The new seven-record rehearsal declares its different candidate/batch digests.
"""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from production_evidence.automatic_updates import AutomaticCanonicalUpdate, GitHubPersistence, IsolatedAdmissionTestBoundary, STAGES, digest
from production_evidence.promotion_readiness import canonical_state_digest
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase_121_synthetic"
REPAIR_BATCH = "syn-repair-derivative-000001-4f2c"


class SyntheticRepairDerivativeUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(FIXTURE / "data", self.root / "data")
        shutil.copy2(FIXTURE / "config.json", self.root / "config.json")
        self.config = self.root / "config.json"
        # The retained Phase 121 bytes stay untouched. This labeled disposable
        # derivative supplies the explicit language that the old fixture omitted.
        payload = self.payload()
        self.assertEqual(len(payload["candidate_ids"]), 8)
        payload["candidate_ids"] = [identifier for identifier in payload["candidate_ids"] if identifier != "set:syn"]
        payload["candidate_payloads"] = [row for row in payload["candidate_payloads"] if row["candidate_identifier"] != "set:syn"]
        payload["repair_derivative_notice"] = {
            "mode": "SIMULATED_TEST_AUTHORIZATION_ONLY", "original_candidate_count": 8,
            "held_candidate_ids": ["set:syn"], "selected_candidate_count": 7,
            "reason": "Standalone Set admission is unsupported; source set namespace remains on Printings."}
        for row in payload["candidate_payloads"]:
            if row["entity_type"] == "printing":
                row["mapped_fields"]["language"] = "en"
                row.setdefault("unknown_fields", {})["fixture_language_note"] = "TEST ONLY: explicit fictional English Printing"
        self.write_payload(payload, refresh_checksum=True, refresh_digest=True)
        (self.root / "data/canonical/games/magic").mkdir(parents=True)
        (self.root / "data/canonical/games/magic/game.json").write_text(json.dumps({"id": "magic", "name": "Fictional test game"}))
        config = json.loads(self.config.read_text())
        config["integrity"]["canonical_pre_state_digest"] = canonical_state_digest(self.root / "data")
        config["integrity"]["expected_candidate_count"] = 7
        config["target"]["batch_identifier"] = REPAIR_BATCH
        config["target"]["destination_branch"] = "canonical-update/" + REPAIR_BATCH
        config["artifacts"]["promotion_audit"] = "audit/" + REPAIR_BATCH + ".json"
        self.config.write_text(json.dumps(config))
        self.boundary = IsolatedAdmissionTestBoundary(self.temporary)

    def tearDown(self): self.temporary.cleanup()

    def engine(self): return AutomaticCanonicalUpdate(self.root, self.config, review_boundary=self.boundary)

    def payload(self): return json.loads((self.root / "data/evidence/candidates.json").read_text())

    def write_payload(self, value, *, refresh_checksum=False, refresh_digest=False):
        path = self.root / "data/evidence/candidates.json"
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        config = json.loads(self.config.read_text())
        if refresh_checksum: config["integrity"]["candidate_payload_sha256"] = digest(path.read_bytes())
        if refresh_digest: config["target"]["candidate_digest"] = digest(value["candidate_ids"])
        self.config.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    def test_complete_seven_record_derivative_workflow_replay_and_rollback_plan(self):
        engine = self.engine()
        plan = engine.plan()
        self.assertEqual(plan["target"]["target_code"], "SYN")
        self.assertEqual(plan["stages"], list(STAGES))
        result = engine.execute()
        self.assertTrue(result["complete"]); self.assertEqual(result["completed_stages"], list(STAGES))
        verification = engine.verify(); self.assertTrue(verification["verified"]); self.assertTrue(verification["audit_present"])
        self.assertTrue(engine.replay()["idempotent"])
        rollback = engine.rollback_plan(); self.assertFalse(rollback["execute"]); self.assertTrue(rollback["human_decision_required"])
        state = json.loads((self.root / "data/canonical/state.json").read_text())
        self.assertEqual({kind: len(rows) for kind, rows in state.items()}, {"card": 2, "finish": 2, "identifier": 1, "printing": 2, "set": 0})
        self.assertIsNone(state["card"]["syn-alpha"]["values"]["oracle_text"])
        self.assertEqual(state["printing"]["00000000-0000-4000-8000-000000000121"]["values"]["set_id"], "syn")
        self.assertEqual(len(self.payload()["candidate_ids"]), 7)
        self.assertNotEqual(json.loads(self.config.read_text())["target"]["candidate_digest"],
                            json.loads((FIXTURE / "config.json").read_bytes())["target"]["candidate_digest"])

    def test_interrupted_checkpoint_recovers_without_repeating_completed_stages(self):
        engine = self.engine(); engine.execute(stop_after=STAGES[7])
        first = [path.read_bytes() for path in sorted((engine.run_root / "stages").iterdir())]
        engine.execute()
        self.assertEqual(first, [path.read_bytes() for path in sorted((engine.run_root / "stages").iterdir())[:8]])
        self.assertTrue(engine.status()["complete"])

    def test_candidate_and_evidence_failures_close_deterministically(self):
        cases = ("untrusted", "contamination", "missing", "duplicate", "unresolved", "quarantined", "orphan", "checksum")
        for case in cases:
            with self.subTest(case=case):
                self.tearDown(); self.setUp(); payload = self.payload(); config = json.loads(self.config.read_text())
                refresh_checksum = refresh_digest = True
                if case == "untrusted": config["target"]["trusted_provider"] = "untrusted"; self.config.write_text(json.dumps(config)); refresh_checksum = False
                elif case == "contamination": payload["candidate_payloads"][0]["mapped_fields"]["set_code"] = "BAD"
                elif case == "missing": payload["candidate_ids"].pop()
                elif case == "duplicate": payload["candidate_ids"][-1] = payload["candidate_ids"][0]
                elif case == "unresolved": payload["candidate_payloads"][0]["final_classification"] = "unresolved"
                elif case == "quarantined": payload["candidate_payloads"][0]["final_classification"] = "quarantined"
                elif case == "orphan": next(row for row in payload["candidate_payloads"] if row["candidate_identifier"] == "printing:alpha")["mapped_fields"]["card_reference"] = "absent"
                elif case == "checksum": payload["candidate_payloads"][0]["mapped_fields"]["name"] = "tampered"; refresh_checksum = refresh_digest = False
                if case != "untrusted": self.write_payload(payload, refresh_checksum=refresh_checksum, refresh_digest=refresh_digest)
                with self.assertRaises(EvidenceError): self.engine().execute()
                self.assertTrue((self.engine().run_root / "blocked-report.json").is_file())

    def test_conflicting_identity_prestate_drift_checkpoint_audit_and_replay_fail_closed(self):
        # Pre-state drift.
        (self.root / "data/canonical/drift").write_text("drift")
        with self.assertRaisesRegex(EvidenceError, "pre-state drift"): self.engine().execute()
        self.tearDown(); self.setUp()
        # A pre-existing different identity is rejected with a correctly declared pre-state.
        state_path = self.root / "data/canonical/state.json"; state = json.loads(state_path.read_text())
        state["card"]["syn-alpha"] = {"different": True}; state_path.write_text(json.dumps(state))
        config = json.loads(self.config.read_text()); config["integrity"]["canonical_pre_state_digest"] = canonical_state_digest(self.root / "data")
        self.config.write_text(json.dumps(config))
        with self.assertRaisesRegex(EvidenceError, "conflicting canonical card identity"): self.engine().execute()
        self.tearDown(); self.setUp()
        engine = self.engine(); engine.execute(stop_after=STAGES[0]); checkpoint = engine._checkpoint(STAGES[0])
        value = json.loads(checkpoint.read_text()); value["details"]["sha256"] = "altered"; checkpoint.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvidenceError, "checkpoint"): engine.execute()
        self.tearDown(); self.setUp()
        engine = self.engine(); engine.execute(); audit = self.root / "data/audit" / (REPAIR_BATCH + ".json")
        value = json.loads(audit.read_text()); value["promoted_entities"] = []; audit.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvidenceError, "audit digest"): engine.verify()
        # Conflicting replay is detected even if the altered audit is internally re-digested.
        body = {key: item for key, item in value.items() if key != "audit_digest"}; body["batch_id"] = "other"
        audit.write_text(json.dumps({**body, "audit_digest": digest(body)}))
        for stage in STAGES[10:]: engine._checkpoint(stage).unlink(missing_ok=True)
        with self.assertRaisesRegex(EvidenceError, "admission audit scope mismatch"): engine.execute()

    def test_cli_all_commands_return_structured_json_and_stable_identity(self):
        # A subprocess cannot inherit the nonserialized temporary-root test
        # authority. Caller-authored synthetic_fixture_only is not authorization.
        for command in ("execute", "replay"):
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/automatic_canonical_update.py"), command,
                "--config", str(self.config), "--repository-root", str(self.root)], env={**__import__('os').environ, "PYTHONPATH": str(ROOT / "src")},
                text=True, capture_output=True)
            value = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertEqual(value["status"], "blocked")
            self.assertIn("trusted host review boundary", value["error"].lower())
        # The live authority stays in this process. The CLI may inspect the
        # resulting receipt; it never receives this test admission capability.
        self.engine().execute()
        for command in ("plan", "verify", "status", "rollback-plan"):
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/automatic_canonical_update.py"), command,
                "--config", str(self.config), "--repository-root", str(self.root)], env={**__import__('os').environ, "PYTHONPATH": str(ROOT / "src")},
                text=True, capture_output=True)
            self.assertEqual(completed.returncode, 0, completed.stdout)
            value = json.loads(completed.stdout)
            self.assertEqual(value.get("schema_version"), "automatic-canonical-update-v1")
            if "batch_identifier" in value:
                self.assertEqual(value["batch_identifier"], REPAIR_BATCH)

    def test_github_persistence_is_idempotent_and_merge_is_eligibility_gated(self):
        calls = []
        def run(command, **kwargs):
            calls.append(command)
            if command[1:3] == ["pr", "view"]:
                return subprocess.CompletedProcess(command, 0, json.dumps({"headRefName":"canonical-update/syn-batch-000001-4f2c","baseRefName":"main","headRefOid":"abc","statusCheckRollup":[{"conclusion":"SUCCESS"}]}), "")
            return subprocess.CompletedProcess(command, 0, "", "")
        persistence = GitHubPersistence(run)
        result = persistence.enable_auto_merge("pr", "canonical-update/syn-batch-000001-4f2c", "main", "abc")
        self.assertTrue(result["auto_merge_requested"])
        flattened = " ".join(" ".join(call) for call in calls); self.assertIn("--auto", flattened); self.assertNotIn("--force", flattened); self.assertNotIn("--admin", flattened)
        def red(command, **kwargs):
            if command[1:3] == ["pr", "view"]: return subprocess.CompletedProcess(command, 0, json.dumps({"headRefName":"canonical-update/syn-batch-000001-4f2c","baseRefName":"main","headRefOid":"abc","statusCheckRollup":[{"conclusion":"FAILURE"}]}), "")
            self.fail("merge was attempted before checks were green")
        with self.assertRaisesRegex(EvidenceError, "not green"): GitHubPersistence(red).enable_auto_merge("pr", "canonical-update/syn-batch-000001-4f2c", "main", "abc")

    def test_original_eight_record_fixture_is_unchanged_and_explicitly_rejected(self):
        original_config = json.loads((FIXTURE / "config.json").read_bytes())
        original_payload_path = FIXTURE / "data/evidence/candidates.json"
        original = json.loads(original_payload_path.read_bytes())
        self.assertEqual(len(original["candidate_ids"]), 8)
        self.assertEqual(original["candidate_ids"][0], "set:syn")
        self.assertEqual(original_config["integrity"]["candidate_payload_sha256"],
                         "38815793d170e2db08ce5e88f458cf909073b22173b2a5021ec7a5976474ccad")
        self.assertEqual(digest(original_payload_path.read_bytes()),
                         original_config["integrity"]["candidate_payload_sha256"])
        self.assertEqual(original_config["target"]["candidate_digest"],
                         "b5da7553c846a82347f6bbe106aaf6d20fd843e831a883a14eace7c617b93925")
        self.assertEqual(digest(original["candidate_ids"]), original_config["target"]["candidate_digest"])
        # Exercise all eight records with explicit test authorization and valid
        # fictional language fields; do not drop Set in this rejection scenario.
        for row in original["candidate_payloads"]:
            if row["entity_type"] == "printing":
                row["mapped_fields"]["language"] = "en"
        self.write_payload(original, refresh_checksum=True, refresh_digest=True)
        config = json.loads(self.config.read_text())
        config["integrity"]["expected_candidate_count"] = 8
        self.config.write_text(json.dumps(config))
        state_path = self.root / "data/canonical/state.json"
        original_state = state_path.read_bytes()
        with self.assertRaisesRegex(EvidenceError, "(?i)(unsupported.*set|projection)"):
            self.engine().execute()
        self.assertEqual(state_path.read_bytes(), original_state)
        self.assertFalse((self.root / "data/audit" / (REPAIR_BATCH + ".json")).exists())
        self.assertFalse(self.engine()._checkpoint("bounded_canonical_promotion").exists())

    def test_engine_has_no_mb2_condition_and_fixture_never_targets_production(self):
        source = (ROOT / "src/production_evidence/automatic_updates.py").read_text()
        self.assertNotIn("MB2", source); self.assertNotIn("MSH", source)
        config = json.loads((FIXTURE / "config.json").read_text())
        self.assertTrue(config["synthetic_fixture_only"]); self.assertEqual(config["data_root"], "data")
        self.assertEqual(config["target"]["destination_branch"], "canonical-update/syn-batch-000001-4f2c")


if __name__ == "__main__": unittest.main()
