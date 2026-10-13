"""Admission boundary regressions use fictional data and disposable repositories."""
import json
from dataclasses import replace
from pathlib import Path
import shutil
import tempfile
import unittest

from production_evidence.automatic_updates import (
    AdmissionDecision, AutomaticCanonicalUpdate, IsolatedAdmissionTestBoundary, digest,
)
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/phase_121_synthetic"


class AdmissionBoundaryRegressions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        shutil.copytree(FIXTURE / "data", self.root / "data")
        shutil.copy2(FIXTURE / "config.json", self.root / "config.json")
        self.config = self.root / "config.json"
        payload_path = self.root / "data/evidence/candidates.json"
        payload = json.loads(payload_path.read_text())
        payload["candidate_payloads"] = [row for row in payload["candidate_payloads"] if row["entity_type"] != "set"]
        for row in payload["candidate_payloads"]:
            row.pop("final_classification", None)
            row["review_status"] = "pending"
            if row["entity_type"] == "printing": row["mapped_fields"]["language"] = "English"
            row["unknown_fields"] = {"unmapped_fictional_fact": {"status": "unknown"}}
        payload["candidate_ids"] = [row["candidate_identifier"] for row in payload["candidate_payloads"]]
        payload["test_note"] = "NEW TEST DERIVATIVE; no standalone Set; explicit fictional English evidence"
        payload_path.write_text(json.dumps(payload))
        (self.root / "data/canonical/games/magic").mkdir(parents=True)
        config = json.loads(self.config.read_text())
        from production_evidence.promotion_readiness import canonical_state_digest
        config["target"]["batch_identifier"] = "fiction-repair-1"
        config["target"]["candidate_digest"] = digest(payload["candidate_ids"])
        config["integrity"].update(candidate_payload_sha256=digest(payload_path.read_bytes()),
            expected_candidate_count=len(payload["candidate_ids"]),
            canonical_pre_state_digest=canonical_state_digest(self.root / "data"))
        self.config.write_text(json.dumps(config))
        self.boundary = IsolatedAdmissionTestBoundary(self.temporary)

    def tearDown(self):
        self.temporary.cleanup()

    def engine(self, *, boundary=None, handlers=None):
        return AutomaticCanonicalUpdate(self.root, self.config,
            review_boundary=self.boundary if boundary is None else boundary, handlers=handlers)

    def refresh_payload(self, change):
        path = self.root / "data/evidence/candidates.json"
        payload = json.loads(path.read_text()); change(payload)
        path.write_text(json.dumps(payload))
        config = json.loads(self.config.read_text())
        config["integrity"]["candidate_payload_sha256"] = digest(path.read_bytes())
        self.config.write_text(json.dumps(config))

    def assert_original(self, original):
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), original)
        config = json.loads(self.config.read_text())
        self.assertFalse((self.root / "data" / config["artifacts"]["promotion_audit"]).exists())

    def test_pending_validated_rows_do_not_authorize_execution(self):
        path = self.root / "data/evidence/candidates.json"
        payload = json.loads(path.read_text())
        for row in payload["candidate_payloads"]:
            row.pop("final_classification", None)
            row["review_status"] = "pending"
        path.write_text(json.dumps(payload))
        config = json.loads(self.config.read_text())
        from production_evidence.automatic_updates import digest
        config["integrity"]["candidate_payload_sha256"] = digest(path.read_bytes())
        self.config.write_text(json.dumps(config))
        before = (self.root / "data/canonical/state.json").read_bytes()
        with self.assertRaises(EvidenceError):
            AutomaticCanonicalUpdate(self.root, self.config).execute()
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), before)

    def test_caller_authored_approval_is_not_authenticated_review(self):
        with self.assertRaises(EvidenceError):
            AutomaticCanonicalUpdate(self.root, self.config).execute()

    def test_supported_writer_must_construct_collection_relationships(self):
        engine = AutomaticCanonicalUpdate(self.root, self.config, review_boundary=self.boundary)
        engine.execute(stop_after="query_and_analytics_smoke_tests")
        state = json.loads((self.root / "data/canonical/state.json").read_text())
        printing = state["printing"]["00000000-0000-4000-8000-000000000121"]
        self.assertEqual(printing["values"].get("card_id"), "syn-alpha")
        self.assertEqual(printing["values"].get("set_id"), "syn")
        self.assertEqual(printing["values"].get("finish_ids"), ["nonfoil"])
        self.assertEqual(printing.get("provenance"), {
            "provider": "synthetic-trusted-provider",
            "source_record": "synthetic://phase-121/printing:alpha"})
        self.assertEqual(printing["source_values"]["language"], "English")
        self.assertEqual(printing["values"]["language"], "en")
        self.assertEqual(printing["unknown_fields"], {"unmapped_fictional_fact": {"status": "unknown"}})

    def test_decision_requires_authenticated_host_principal_operation_time_and_exact_bindings(self):
        from production_evidence.automatic_updates import ADMISSION_OPERATION
        class HostBoundary:
            authenticated_reviewer = "host-session:reviewer"
            def __init__(self, change): self.change = change
            def authorize(self, bindings):
                decision = AdmissionDecision("approved", self.authenticated_reviewer,
                    "2026-10-13T00:00:00+00:00", ADMISSION_OPERATION, bindings,
                    "authenticated-host-review:fictional", "production")
                return self.change(decision)
        cases = {
            "pending": lambda d: replace(d, decision="pending"),
            "rejected": lambda d: replace(d, decision="rejected"),
            "actor-only": lambda d: replace(d, reviewer="caller-supplied-name"),
            "operation": lambda d: replace(d, operation="physical-copy-assignment"),
            "scope": lambda d: replace(d, scope="caller-approved"),
            "missing-time": lambda d: replace(d, decided_at=""),
            "naive-time": lambda d: replace(d, decided_at="2026-10-13T00:00:00"),
            "mismatch": lambda d: replace(d, bindings={}),
            "simulated-decision": lambda d: replace(d, scope="isolated-test"),
            "simulated-receipt": lambda d: replace(d, review_reference="SIMULATED_TEST_AUTHORIZATION_ONLY"),
            "bare-json": lambda d: d.as_dict(),
        }
        original = (self.root / "data/canonical/state.json").read_bytes()
        for name, change in cases.items():
            with self.subTest(name=name), self.assertRaises(EvidenceError):
                self.engine(boundary=HostBoundary(change)).execute()
            self.assert_original(original)

    def test_pending_is_not_reclassified_and_rejected_payload_cannot_be_overridden(self):
        self.engine().execute(stop_after="candidate_review")
        checkpoint = json.loads(self.engine()._checkpoint("candidate_review").read_bytes())
        self.assertEqual(checkpoint["details"]["classifications"], {"pending": 7})
        self.assertNotIn("approved", checkpoint["details"]["classifications"])
        self.refresh_payload(lambda p: p["candidate_payloads"][0].update(
            review_status="rejected", final_classification="approved"))
        with self.assertRaises(EvidenceError): self.engine().execute()

    def test_simulated_capability_is_root_and_lifetime_scoped(self):
        with tempfile.TemporaryDirectory() as another:
            other = AutomaticCanonicalUpdate(another, self.config, review_boundary=self.boundary)
            # The capability checks root even if its decision is copied elsewhere.
            with self.assertRaises(EvidenceError): self.boundary._verify_root(other.root)
        directory = tempfile.TemporaryDirectory()
        boundary = IsolatedAdmissionTestBoundary(directory)
        directory.cleanup()
        with self.assertRaises(EvidenceError): boundary._verify_root(Path(directory.name))
        with self.assertRaises(EvidenceError): IsolatedAdmissionTestBoundary(self.root)

    def test_resume_cannot_reapprove_changed_payload_even_with_refreshed_config(self):
        self.engine().execute(stop_after="deterministic_promotion_preflight")
        original = (self.root / "data/canonical/state.json").read_bytes()
        self.refresh_payload(lambda p: p["candidate_payloads"][0]["mapped_fields"].update(name="Changed"))
        # A fresh boundary cannot erase the earlier retained input bindings.
        fresh = IsolatedAdmissionTestBoundary(self.temporary)
        with self.assertRaises(EvidenceError): self.engine(boundary=fresh).execute()
        self.assert_original(original)

    def test_resume_cannot_use_changed_source_with_refreshed_config(self):
        self.engine().execute(stop_after="source_acquisition_verification")
        path = self.root / "data/evidence/source.json"; path.write_text("changed-source")
        config = json.loads(self.config.read_text()); config["integrity"]["source_sha256"] = digest(path.read_bytes())
        self.config.write_text(json.dumps(config))
        with self.assertRaises(EvidenceError): self.engine().execute()

    def test_receipts_are_bound_and_changed_receipt_cannot_resume(self):
        path = self.root / "data/evidence/receipt.json"; path.write_text('{"retrieved_at":"fictional"}')
        config = json.loads(self.config.read_text()); config["artifacts"]["receipts"] = ["evidence/receipt.json"]
        self.config.write_text(json.dumps(config))
        self.engine().execute(stop_after="promotion_readiness_planning")
        path.write_text('{"retrieved_at":"altered"}')
        with self.assertRaises(EvidenceError): self.engine().execute()

    def test_pre_state_drift_cannot_resume_or_be_rebound_by_new_config(self):
        self.engine().execute(stop_after="promotion_readiness_planning")
        (self.root / "data/canonical/drift.txt").write_text("altered")
        config = json.loads(self.config.read_text())
        from production_evidence.promotion_readiness import canonical_state_digest
        config["integrity"]["canonical_pre_state_digest"] = canonical_state_digest(self.root / "data")
        self.config.write_text(json.dumps(config))
        with self.assertRaises(EvidenceError): self.engine(boundary=IsolatedAdmissionTestBoundary(self.temporary)).execute()

    def test_direct_write_boundary_revalidates_inputs_and_ignores_success_checkpoint(self):
        engine = self.engine(); engine.execute(stop_after="deterministic_promotion_preflight")
        (self.root / "data/evidence/source.json").write_text("tampered")
        with self.assertRaises(EvidenceError): engine._stage_bounded_canonical_promotion({})

    def test_dependencies_include_existing_card_finish_and_alias_target(self):
        engine = self.engine(); engine.execute()
        before = (self.root / "data/canonical/state.json").read_bytes()
        self.assertTrue(engine.replay()["idempotent"])
        self.assertEqual(before, (self.root / "data/canonical/state.json").read_bytes())
        self.assertFalse(engine.rollback_plan()["execute"])
        # New Printing depends on an existing Card and Finish, not in its delta.
        payload_path = self.root / "data/evidence/candidates.json"
        first_payload_bytes = payload_path.read_bytes()
        payload = json.loads(first_payload_bytes)
        row = next(row for row in payload["candidate_payloads"] if row["entity_type"] == "printing")
        row["candidate_identifier"] = "printing:gamma"
        row["mapped_fields"].update(uuid="00000000-0000-4000-8000-000000000123", collector_number="3")
        payload["candidate_payloads"] = [row]; payload["candidate_ids"] = [row["candidate_identifier"]]
        payload_path.write_text(json.dumps(payload))
        from production_evidence.promotion_readiness import canonical_state_digest
        config = json.loads(self.config.read_text())
        config["target"].update(batch_identifier="fiction-existing-dependency-2", candidate_digest=digest(payload["candidate_ids"]))
        config["integrity"].update(expected_candidate_count=1, candidate_payload_sha256=digest(payload_path.read_bytes()),
                                   canonical_pre_state_digest=canonical_state_digest(self.root / "data"))
        config["artifacts"]["promotion_audit"] = "audit/second-fictional-admission.json"
        self.config.write_text(json.dumps(config))
        # Preserve the immutable first admission's retained payload by using a new file.
        new_payload = self.root / "data/evidence/second-candidates.json"
        shutil.copy2(payload_path, new_payload)
        # Existing audit needs its original payload, restore from the captured inputs.
        first_audit = json.loads((self.root / "data/audit/syn-batch-000001-4f2c.json").read_text())
        payload_path.write_bytes(first_payload_bytes)
        self.assertEqual(digest(payload_path.read_bytes()), first_audit["input_bindings"]["candidate_payload_sha256"])
        config["artifacts"]["candidate_payload"] = "evidence/second-candidates.json"
        self.config.write_text(json.dumps(config))
        fresh = IsolatedAdmissionTestBoundary(self.temporary)
        second = self.engine(boundary=fresh); second.execute()
        state = json.loads((self.root / "data/canonical/state.json").read_bytes())
        self.assertEqual(len(state["card"]), 2); self.assertEqual(len(state["printing"]), 3)

    def test_consumer_failure_restores_bytes_audit_and_write_checkpoints(self):
        original = (self.root / "data/canonical/state.json").read_bytes()
        def fail(context): raise EvidenceError("deliberate required consumer failure")
        engine = self.engine(handlers={"query_and_analytics_smoke_tests": fail})
        with self.assertRaisesRegex(EvidenceError, "required consumer failure"): engine.execute()
        self.assert_original(original)
        for stage in ("bounded_canonical_promotion", "immutable_promotion_audit", "canonical_post_state_verification"):
            self.assertFalse(engine._checkpoint(stage).exists())
        self.assertTrue(json.loads((engine.run_root / "blocked-report.json").read_text())["canonical_original_bytes_restored"])

    def test_interrupted_postwrite_failure_restores_original_on_resume(self):
        original = (self.root / "data/canonical/state.json").read_bytes()
        self.engine().execute(stop_after="bounded_canonical_promotion")
        def fail(context): raise EvidenceError("resumed consumer failure")
        engine = self.engine(handlers={"query_and_analytics_smoke_tests": fail})
        with self.assertRaisesRegex(EvidenceError, "resumed consumer failure"): engine.execute()
        self.assert_original(original)
        self.assertFalse(engine._checkpoint("bounded_canonical_promotion").exists())

    def test_language_contradiction_missing_finish_and_alias_dependency_fail_before_write(self):
        cases = ("language", "finish", "identifier")
        for case in cases:
            with self.subTest(case=case):
                self.tearDown(); self.setUp()
                original = (self.root / "data/canonical/state.json").read_bytes()
                def change(p):
                    if case == "identifier":
                        row = next(r for r in p["candidate_payloads"] if r["entity_type"] == "identifier")
                        row["mapped_fields"]["printing_uuid"] = "missing-printing"
                    else:
                        row = next(r for r in p["candidate_payloads"] if r["entity_type"] == "printing")
                        if case == "language": row["mapped_fields"]["language_code"] = "ja"
                        else: row["mapped_fields"]["finish"] = "unknown-finish"
                self.refresh_payload(change)
                with self.assertRaises(EvidenceError): self.engine().execute()
                self.assert_original(original)

    def test_untrusted_paths_cannot_escape_disposable_authorization_scope(self):
        with tempfile.TemporaryDirectory() as unrelated:
            outside = Path(unrelated)
            sentinel = outside / "canonical/state.json"
            sentinel.parent.mkdir(); sentinel.write_bytes(b"UNRELATED ORIGINAL BYTES\n")
            base = json.loads(self.config.read_text())
            cases = ("absolute-data", "relative-data", "symlink-data", "payload", "audit", "source", "batch")
            for case in cases:
                with self.subTest(case=case):
                    config = json.loads(json.dumps(base))
                    if case == "absolute-data": config["data_root"] = str(outside)
                    elif case == "relative-data": config["data_root"] = "../" + outside.name
                    elif case == "symlink-data":
                        (self.root / "external-link").symlink_to(outside, target_is_directory=True)
                        config["data_root"] = "external-link"
                    elif case == "payload": config["artifacts"]["candidate_payload"] = str(sentinel)
                    elif case == "audit": config["artifacts"]["promotion_audit"] = str(sentinel)
                    elif case == "source": config["artifacts"]["source_artifact"] = str(sentinel)
                    elif case == "batch": config["target"]["batch_identifier"] = "../../outside-run"
                    self.config.write_text(json.dumps(config))
                    with self.assertRaises(EvidenceError): self.engine().execute()
                    self.assertEqual(sentinel.read_bytes(), b"UNRELATED ORIGINAL BYTES\n")
            self.config.write_text(json.dumps(base))


if __name__ == "__main__":
    unittest.main()
