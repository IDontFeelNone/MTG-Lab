"""Phase 121 end-to-end validation with an isolated synthetic Magic set."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from production_evidence.automatic_updates import AutomaticCanonicalUpdate, GitHubPersistence, STAGES, digest
from production_evidence.promotion_readiness import canonical_state_digest
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase_121_synthetic"


class Phase121SyntheticUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(FIXTURE / "data", self.root / "data")
        shutil.copy2(FIXTURE / "config.json", self.root / "config.json")
        self.config = self.root / "config.json"

    def tearDown(self): self.temporary.cleanup()

    def engine(self): return AutomaticCanonicalUpdate(self.root, self.config)

    def payload(self): return json.loads((self.root / "data/evidence/candidates.json").read_text())

    def write_payload(self, value, *, refresh_checksum=False, refresh_digest=False):
        path = self.root / "data/evidence/candidates.json"
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
        config = json.loads(self.config.read_text())
        if refresh_checksum: config["integrity"]["candidate_payload_sha256"] = digest(path.read_bytes())
        if refresh_digest: config["target"]["candidate_digest"] = digest(value["candidate_ids"])
        self.config.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")

    def test_complete_sixteen_stage_execution_replay_and_rollback_plan(self):
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
        self.assertEqual({kind: len(rows) for kind, rows in state.items()}, {"card": 2, "finish": 2, "identifier": 1, "printing": 2, "set": 1})
        self.assertIsNone(state["card"]["syn-alpha"]["values"]["oracle_text"])

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
                elif case == "orphan": payload["candidate_payloads"][3]["mapped_fields"]["card_reference"] = "absent"
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
        engine = self.engine(); engine.execute(); audit = self.root / "data/audit/syn-batch-000001-4f2c.json"
        value = json.loads(audit.read_text()); value["promoted_entities"] = []; audit.write_text(json.dumps(value))
        with self.assertRaisesRegex(EvidenceError, "audit digest"): engine.verify()
        # Conflicting replay is detected even if the altered audit is internally re-digested.
        body = {key: item for key, item in value.items() if key != "audit_digest"}; body["batch_id"] = "other"
        audit.write_text(json.dumps({**body, "audit_digest": digest(body)}))
        for stage in STAGES[10:]: engine._checkpoint(stage).unlink(missing_ok=True)
        with self.assertRaisesRegex(EvidenceError, "conflicting replay"): engine.execute()

    def test_cli_all_commands_return_structured_json_and_stable_identity(self):
        commands = ("plan", "verify", "execute", "status", "replay", "rollback-plan")
        for command in commands:
            completed = subprocess.run([sys.executable, str(ROOT / "scripts/automatic_canonical_update.py"), command,
                "--config", str(self.config), "--repository-root", str(self.root)], env={**__import__('os').environ, "PYTHONPATH": str(ROOT / "src")},
                check=True, text=True, capture_output=True)
            value = json.loads(completed.stdout)
            self.assertEqual(value.get("schema_version"), "automatic-canonical-update-v1")
            if "batch_identifier" in value: self.assertEqual(value["batch_identifier"], "syn-batch-000001-4f2c")

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

    def test_engine_has_no_mb2_condition_and_fixture_never_targets_production(self):
        source = (ROOT / "src/production_evidence/automatic_updates.py").read_text()
        self.assertNotIn("MB2", source); self.assertNotIn("MSH", source)
        config = json.loads((FIXTURE / "config.json").read_text())
        self.assertTrue(config["synthetic_fixture_only"]); self.assertEqual(config["data_root"], "data")
        self.assertEqual(config["target"]["destination_branch"], "canonical-update/syn-batch-000001-4f2c")


if __name__ == "__main__": unittest.main()
