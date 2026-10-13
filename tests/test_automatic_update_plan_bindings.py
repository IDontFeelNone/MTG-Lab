"""Read-only admission previews bind retained bytes without granting authority."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import test_phase_120_automatic_updates as fixtures
from production_evidence.automatic_updates import AutomaticCanonicalUpdate, digest
from production_evidence.repository import EvidenceError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/automatic_canonical_update.py"


class AdmissionPlanBindingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        fixture = fixtures.AutomaticUpdateTests()
        _, self.config = fixture.synthetic(self.root)
        self.payload = self.root / "data/evidence/payload.json"
        self.source = self.root / "data/evidence/source.json"
        self.receipt = self.root / "data/evidence/fictional-policy-notice.txt"
        self.receipt.write_text("Fictional retained notice; no rights decision or owner approval.\n")
        config = json.loads(self.config.read_bytes())
        config["integrity"]["candidate_payload_sha256"] = digest(self.payload.read_bytes())
        config["artifacts"]["receipts"] = [{"path": "evidence/fictional-policy-notice.txt",
            "role": "source-policy", "sha256": digest(self.receipt.read_bytes())}]
        self.config.write_text(json.dumps(config))

    def engine(self):
        return AutomaticCanonicalUpdate(self.root, self.config)

    def inventory(self):
        return {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                for p in self.root.rglob("*") if p.is_file()}

    def cli(self, *arguments):
        result = subprocess.run([sys.executable, str(SCRIPT), "--config", str(self.config),
            "--repository-root", str(self.root), *arguments], capture_output=True, text=True,
            env=dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1"), timeout=10)
        self.assertEqual(result.stderr, "")
        return result, json.loads(result.stdout)

    def assert_cli_blocked_without_changes(self, reason):
        before = self.inventory()
        result, document = self.cli()
        self.assertEqual(result.returncode, 1)
        self.assertEqual(document["status"], "blocked")
        self.assertIn(reason, document["error"])
        self.assertEqual(self.inventory(), before)

    def test_unchanged_inputs_have_identical_exact_bound_plans(self):
        before = self.inventory()
        engine = self.engine()
        first = engine.plan()
        second = engine.plan(expected_plan_id=first["plan_id"])
        self.assertEqual(first, second)
        inputs = first["decision_inputs"]
        self.assertEqual(first["plan_id"], "sha256:" + digest(inputs))
        self.assertEqual(inputs["bindings"], engine.admission_bindings())
        self.assertEqual(inputs["bindings"]["candidate_ids"], json.loads(self.payload.read_bytes())["candidate_ids"])
        self.assertEqual(inputs["candidate_counts_by_type"], {"card": 1, "finish": 1, "printing": 1})
        self.assertEqual(inputs["bindings"]["candidate_payload_sha256"], digest(self.payload.read_bytes()))
        self.assertEqual(inputs["bindings"]["evidence_files"][0]["sha256"], digest(self.source.read_bytes()))
        self.assertEqual(inputs["bindings"]["evidence_files"][1]["sha256"], digest(self.receipt.read_bytes()))
        self.assertEqual(inputs["observed_canonical_pre_state_digest"], inputs["bindings"]["canonical_pre_state_digest"])
        self.assertTrue(first["integrity_verified"])
        self.assertTrue(first["pre_state_matches_expected"])
        self.assertEqual(first["approval_state"], "not_granted")
        self.assertFalse(first["execution_authorized"])
        self.assertFalse(first["admission_ready"])
        self.assertEqual({g["gate"] for g in inputs["unresolved_gates"]},
                         {"admission_authorization", "source_policy", "admission_readiness"})
        self.assertEqual(self.inventory(), before)

    def test_missing_source_payload_or_receipt_blocks_without_fallback(self):
        for path in (self.source, self.payload, self.receipt):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.unlink()
                self.assert_cli_blocked_without_changes("retained evidence is missing")
                path.write_bytes(original)

    def test_source_payload_and_receipt_checksum_changes_are_rejected(self):
        for path, reason in ((self.source, "source artifact hash mismatch"),
                             (self.payload, "candidate payload checksum mismatch"),
                             (self.receipt, "retained receipt hash mismatch")):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                # Trailing JSON whitespace keeps the payload schema-valid.
                path.write_bytes(original + b" \n")
                self.assert_cli_blocked_without_changes(reason)
                path.write_bytes(original)

    def test_candidate_order_and_order_digest_mismatches_are_rejected(self):
        original = self.payload.read_bytes()
        for reorder_rows, reason in ((False, "candidate inventory/order mismatch"),
                                     (True, "candidate digest mismatch")):
            with self.subTest(reorder_rows=reorder_rows):
                payload = json.loads(original)
                payload["candidate_ids"].reverse()
                if reorder_rows:
                    payload["candidate_payloads"].reverse()
                self.payload.write_text(json.dumps(payload))
                self.assert_cli_blocked_without_changes(reason)
        self.payload.write_bytes(original)

    def test_canonical_pre_state_drift_is_not_rebound(self):
        old = self.engine().plan()["plan_id"]
        (self.root / "data/canonical/unexpected-file.txt").write_text("Unplanned current-state change")
        self.assert_cli_blocked_without_changes("canonical pre-state drift")
        with self.assertRaisesRegex(EvidenceError, "canonical pre-state drift"):
            self.engine().plan(expected_plan_id=old)

    def test_new_previews_require_explicit_hash_pins(self):
        original = self.config.read_bytes()
        for field in ("source_sha256", "candidate_payload_sha256", "receipt"):
            with self.subTest(field=field):
                config = json.loads(original)
                if field == "receipt":
                    config["artifacts"]["receipts"][0].pop("sha256")
                else:
                    config["integrity"].pop(field)
                self.config.write_text(json.dumps(config))
                self.assert_cli_blocked_without_changes("requires expected hash pins")
        self.config.write_bytes(original)

    def test_previous_plan_cannot_validate_changed_policy_target_or_construction(self):
        original = self.config.read_bytes()
        engine = self.engine()
        old = engine.plan()["plan_id"]
        for field in ("policy", "target", "construction"):
            with self.subTest(field=field):
                config = json.loads(original)
                if field == "policy":
                    config["policy"]["permitted_final_classifications"].append("pending")
                elif field == "target":
                    config["target"]["destination_branch"] += "-different"
                else:
                    config["canonical_identity_fields"] = {"card": "different-field"}
                self.config.write_text(json.dumps(config))
                self.assertNotEqual(self.engine().plan()["plan_id"], old)
                with self.assertRaisesRegex(EvidenceError, "configuration changed"):
                    engine.plan(expected_plan_id=old)
                before = self.inventory()
                result, document = self.cli("--expected-plan-id", old)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(document["status"], "blocked")
                self.assertIn("decision-relevant inputs", document["error"])
                self.assertEqual(self.inventory(), before)
        self.config.write_bytes(original)

    def test_old_plan_does_not_validate_changed_payload_bytes(self):
        old = self.engine().plan()["plan_id"]
        self.payload.write_bytes(self.payload.read_bytes() + b"\n")
        with self.assertRaisesRegex(EvidenceError, "payload checksum mismatch"):
            self.engine().plan(expected_plan_id=old)

    def test_explicitly_different_proposal_cannot_reuse_previous_plan_identity(self):
        old = self.engine().plan()["plan_id"]
        payload = json.loads(self.payload.read_bytes())
        payload["proposal_note"] = "A separate fictional proposal, never an approval"
        self.payload.write_text(json.dumps(payload))
        # The test supplies a distinct versioned proposal explicitly. The planner
        # must neither update this pin itself nor accept the old plan identity.
        config = json.loads(self.config.read_bytes())
        config["integrity"]["candidate_payload_sha256"] = digest(self.payload.read_bytes())
        self.config.write_text(json.dumps(config))
        before = self.inventory()
        different = self.engine().plan()
        self.assertNotEqual(different["plan_id"], old)
        self.assertFalse(different["execution_authorized"])
        with self.assertRaisesRegex(EvidenceError, "decision-relevant inputs"):
            self.engine().plan(expected_plan_id=old)
        self.assertEqual(self.inventory(), before)

    def test_evidence_changed_during_planning_cannot_claim_verified_integrity(self):
        engine = self.engine()
        canonical = (self.root / "data/canonical/state.json").read_bytes()
        verify_target = engine._stage_target_partitioning

        def change_after_checks(context):
            result = verify_target(context)
            self.receipt.write_text("Changed after the initial integrity checks")
            return result

        with patch.object(engine, "_stage_target_partitioning", side_effect=change_after_checks):
            with self.assertRaisesRegex(EvidenceError, "retained receipt hash mismatch"):
                engine.plan()
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), canonical)
        self.assertFalse(engine.run_root.exists())

    def test_planning_calls_no_authorization_execution_or_checkpoint_writer(self):
        engine = self.engine()
        before = self.inventory()
        with patch.object(engine, "execute", side_effect=AssertionError("execution called")), \
             patch.object(engine, "_authorization", side_effect=AssertionError("authorization called")), \
             patch.object(engine, "_atomic_write", side_effect=AssertionError("write called")), \
             patch("production_evidence.automatic_updates.AdmissionDecision",
                   side_effect=AssertionError("decision created")):
            engine.plan()
        self.assertEqual(self.inventory(), before)
        self.assertFalse(engine.run_root.exists())

    def test_saved_plan_option_never_authorizes_execute(self):
        old = self.engine().plan()["plan_id"]
        before = self.inventory()
        result, document = self.cli("execute", "--expected-plan-id", old)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(document["status"], "blocked")
        self.assertIn("only valid for read-only planning", document["error"])
        self.assertEqual(self.inventory(), before)


class HistoricalAdmissionPlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(ROOT / "data", self.root / "data")
        self.config = self.root / "historical-config.json"
        shutil.copyfile(ROOT / "config/automatic_updates/mb2-first-batch.json", self.config)

    def engine(self):
        return AutomaticCanonicalUpdate(self.root, self.config)

    def test_real_history_retains_original_pre_state_and_raw_pin_limits(self):
        before = {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                  for p in self.root.rglob("*") if p.is_file()}
        engine = self.engine()
        with patch.object(engine, "execute", side_effect=AssertionError("execution called")), \
             patch.object(engine, "_authorization", side_effect=AssertionError("authorization called")):
            first = engine.plan()
            second = engine.plan(expected_plan_id=first["plan_id"])
        self.assertEqual(first, second)
        self.assertEqual(first["decision_inputs"]["scope"], "historical_inspection")
        self.assertTrue(first["decision_inputs"]["historical_admission"]["verified"])
        self.assertFalse(first["pre_state_matches_expected"])
        self.assertFalse(first["integrity_verified"])
        self.assertEqual(first["decision_inputs"]["missing_expected_hashes"],
                         ["integrity.candidate_payload_sha256"])
        self.assertFalse(first["execution_authorized"])
        self.assertFalse(first["admission_ready"])
        self.assertEqual(before, {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                                  for p in self.root.rglob("*") if p.is_file()})

    def test_missing_historical_receipt_never_falls_back_to_checkout(self):
        config = json.loads(self.config.read_bytes())
        (self.root / "data" / config["artifacts"]["promotion_audit"]).unlink()
        with self.assertRaisesRegex(EvidenceError, "historical admission audit is missing"):
            self.engine().plan()

    def test_changed_historical_admitted_record_is_rejected(self):
        config = json.loads(self.config.read_bytes())
        audit = json.loads((self.root / "data" / config["artifacts"]["promotion_audit"]).read_bytes())
        path = self.root / "data/canonical/state.json"
        state = json.loads(path.read_bytes())
        record = next(r for r in state["card"].values() if r["promotion_id"] == audit["promotion_id"])
        record["values"]["name"] = "Schema-valid historical tampering"
        path.write_text(json.dumps(state))
        with self.assertRaisesRegex(EvidenceError, "historical admitted record conflicts"):
            self.engine().plan()


if __name__ == "__main__":
    unittest.main()
