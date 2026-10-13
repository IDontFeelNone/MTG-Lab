"""Whole-execution checks for resume recovery and final authorization races."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from production_evidence.automatic_updates import AutomaticCanonicalUpdate, digest
from production_evidence.promotion_readiness import canonical_state_digest
from production_evidence.repository import EvidenceError
import test_admission_authorization as authorization_fixtures


class AdmissionBoundaryAdversarialTests(unittest.TestCase):
    def setUp(self):
        # Reuse the separately identified seven-record fictional derivative.
        # It has no personal inventory or real authorization evidence.
        self.fixture = authorization_fixtures.AdmissionBoundaryRegressions()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.config = self.fixture.config
        self.boundary = self.fixture.boundary
        self.state = self.root / "data/canonical/state.json"
        self.original = self.state.read_bytes()
        self.engine = AutomaticCanonicalUpdate(self.root, self.config,
            review_boundary=self.boundary)

    def tearDown(self):
        self.fixture.tearDown()

    def test_untrusted_direct_write_boundary_cannot_bypass_execute(self):
        engine = AutomaticCanonicalUpdate(self.root, self.config)
        with self.assertRaises(EvidenceError):
            engine._stage_bounded_canonical_promotion({})
        self.assertEqual(self.state.read_bytes(), self.original)
        self.assertFalse(engine._checkpoint("bounded_canonical_promotion").exists())

    def test_configured_path_escapes_never_read_or_write_disposable_sentinels(self):
        base_config = json.loads(self.config.read_bytes())
        cases = ("absolute-data", "parent-data", "symlink-data", "absolute-payload",
            "parent-payload", "symlink-payload", "absolute-audit", "parent-audit",
            "symlink-audit", "parent-batch", "symlink-batch", "symlink-stages",
            "symlink-backup", "symlink-canonical-extra")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                for relative in ("escaping-data", "data/evidence/escaping-candidates.json",
                        "data/escaping-audit.json", "data/automatic_updates/escaping-batch",
                        "data/automatic_updates/fiction-repair-1/stages",
                        "data/automatic_updates/fiction-repair-1/canonical-pre-state.bytes",
                        "data/canonical/escaping.txt"):
                    stale_link = self.root / relative
                    if stale_link.is_symlink(): stale_link.unlink()
                outside = Path(temporary)
                shutil.copytree(self.root / "data", outside / "data")
                sentinel = outside / "sentinel.txt"
                sentinel.write_bytes(b"DISPOSABLE SENTINEL; NOT PRODUCTION\n")
                config = json.loads(json.dumps(base_config))
                if case == "absolute-data": config["data_root"] = str(outside / "data")
                if case == "parent-data":
                    config["data_root"] = "../" + outside.name + "/data"
                if case == "symlink-data":
                    link = self.root / "escaping-data"
                    link.symlink_to(outside / "data", target_is_directory=True)
                    config["data_root"] = link.name
                if case in {"absolute-payload", "parent-payload", "symlink-payload"}:
                    target = outside / "data/evidence/candidates.json"
                    value = str(target) if case == "absolute-payload" else "../../" + outside.name + "/data/evidence/candidates.json"
                    if case == "symlink-payload":
                        link = self.root / "data/evidence/escaping-candidates.json"
                        link.symlink_to(target)
                        value = "evidence/escaping-candidates.json"
                    config["artifacts"]["candidate_payload"] = value
                if case in {"absolute-audit", "parent-audit", "symlink-audit"}:
                    value = str(outside / "sentinel.txt") if case == "absolute-audit" else "../../" + outside.name + "/sentinel.txt"
                    if case == "symlink-audit":
                        link = self.root / "data/escaping-audit.json"
                        link.symlink_to(outside / "sentinel.txt")
                        value = "escaping-audit.json"
                    config["artifacts"]["promotion_audit"] = value
                if case == "parent-batch": config["target"]["batch_identifier"] = "../../" + outside.name
                if case == "symlink-batch":
                    link = self.root / "data/automatic_updates/escaping-batch"
                    link.parent.mkdir(parents=True, exist_ok=True)
                    link.symlink_to(outside, target_is_directory=True)
                    config["target"]["batch_identifier"] = link.name
                if case in {"symlink-stages", "symlink-backup"}:
                    name = "stages" if case == "symlink-stages" else "canonical-pre-state.bytes"
                    link = self.root / "data/automatic_updates/fiction-repair-1" / name
                    link.parent.mkdir(parents=True, exist_ok=True)
                    if link.is_dir(): shutil.rmtree(link)
                    elif link.exists(): link.unlink()
                    link.symlink_to(outside if case == "symlink-stages" else sentinel,
                        target_is_directory=case == "symlink-stages")
                if case == "symlink-canonical-extra":
                    (self.root / "data/canonical/escaping.txt").symlink_to(sentinel)
                self.config.write_text(json.dumps(config), encoding="utf-8")
                before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
                reads = []
                read_bytes = Path.read_bytes
                def observe_read(path):
                    if path.resolve().is_relative_to(outside): reads.append(str(path))
                    return read_bytes(path)
                with patch.object(Path, "read_bytes", observe_read):
                    with self.assertRaises(EvidenceError):
                        AutomaticCanonicalUpdate(self.root, self.config, review_boundary=self.boundary).execute(
                            stop_after="query_and_analytics_smoke_tests")
                self.assertEqual(reads, [], "out-of-scope files must not be consumed as authorization/evidence")
                self.assertEqual({p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()}, before)

    def test_path_pivots_after_engine_construction_are_rejected_before_external_reads(self):
        for case in ("data-root", "canonical-root"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                outside = Path(temporary)
                shutil.copytree(self.root / "data", outside / "data")
                pivot = self.root / "data" if case == "data-root" else self.root / "data/canonical"
                retained = pivot.with_name(pivot.name + "-retained")
                pivot.rename(retained)
                target = outside / "data" if case == "data-root" else outside / "data/canonical"
                pivot.symlink_to(target, target_is_directory=True)
                before = {p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()}
                reads = []
                read_bytes = Path.read_bytes
                def observe_read(path):
                    if path.resolve().is_relative_to(outside): reads.append(str(path))
                    return read_bytes(path)
                try:
                    with patch.object(Path, "read_bytes", observe_read):
                        with self.assertRaises(EvidenceError):
                            self.engine.execute(stop_after="query_and_analytics_smoke_tests")
                    self.assertEqual(reads, [], "a changed path must be rejected before external bytes are consumed")
                    self.assertEqual({p.relative_to(outside): p.read_bytes() for p in outside.rglob("*") if p.is_file()}, before)
                finally:
                    pivot.unlink()
                    retained.rename(pivot)

    def test_simulated_capability_cannot_be_reused_in_a_different_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary)
            shutil.copytree(self.root / "data", copied / "data")
            shutil.copy2(self.config, copied / "config.json")
            engine = AutomaticCanonicalUpdate(copied, copied / "config.json",
                review_boundary=self.boundary)
            with self.assertRaisesRegex(EvidenceError, "live disposable root"):
                engine.execute(stop_after="query_and_analytics_smoke_tests")
            self.assertEqual((copied / "data/canonical/state.json").read_bytes(), self.original)

    def test_tampered_resume_backup_never_becomes_canonical_data(self):
        self.engine.execute(stop_after="bounded_canonical_promotion")
        before_resume = self.state.read_bytes()
        audit_path = self.root / "data" / self.engine.config["artifacts"]["promotion_audit"]
        audit_bytes = audit_path.read_bytes()
        backup = self.engine.run_root / "canonical-pre-state.bytes"
        backup.write_bytes(b"{}\n")
        source = self.root / "data/evidence/source.json"
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaises(EvidenceError):
            self.engine.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(self.state.read_bytes(), before_resume,
            "an unverified recovery backup must not overwrite current canonical bytes")
        self.assertFalse(self.engine._checkpoint("bounded_canonical_promotion").exists(),
            "a refused recovery must not leave a successful write checkpoint")
        self.assertEqual(audit_path.read_bytes(), audit_bytes,
            "refused compensation must retain the prior immutable partial-write receipt")
        report = json.loads((self.engine.run_root / "blocked-report.json").read_bytes())
        self.assertFalse(report["canonical_original_bytes_restored"])
        self.assertTrue(report["partial_write_audit_retained"])
        self.assertIn("bounded_canonical_promotion", report["invalidated_write_acceptance_checkpoints"])

    def test_resume_pre_state_drift_does_not_erase_an_unrelated_write(self):
        self.engine.execute(stop_after="bounded_canonical_promotion")
        audit_path = self.root / "data" / self.engine.config["artifacts"]["promotion_audit"]
        audit_bytes = audit_path.read_bytes()
        changed = json.loads(self.state.read_bytes())
        changed["card"]["fictional-unrelated-write"] = {"entity_type": "card",
            "values": {"card_reference": "fictional-unrelated-write", "name": "Unrelated Write"}}
        self.state.write_text(json.dumps(changed), encoding="utf-8")
        before_resume = self.state.read_bytes()
        with self.assertRaises(EvidenceError):
            self.engine.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(self.state.read_bytes(), before_resume,
            "rejection of unrelated canonical drift must not undo that unrelated write")
        self.assertFalse(self.engine._checkpoint("bounded_canonical_promotion").exists(),
            "a blocked incomplete operation must not retain a successful write checkpoint")
        self.assertEqual(audit_path.read_bytes(), audit_bytes)
        report = json.loads((self.engine.run_root / "blocked-report.json").read_bytes())
        self.assertFalse(report["canonical_original_bytes_restored"])
        self.assertTrue(report["partial_write_audit_retained"])

    def test_rehashed_partial_audit_cannot_claim_ownership_of_an_unrelated_write(self):
        self.engine.execute(stop_after="bounded_canonical_promotion")
        changed = json.loads(self.state.read_bytes())
        changed["card"]["fictional-unrelated-write"] = {"entity_type": "card",
            "values": {"card_reference": "fictional-unrelated-write", "name": "Unrelated Write"}}
        self.state.write_text(json.dumps(changed), encoding="utf-8")
        before_resume = self.state.read_bytes()
        audit_path = self.root / "data" / self.engine.config["artifacts"]["promotion_audit"]
        audit = json.loads(audit_path.read_bytes())
        audit["canonical_post_state_digest"] = canonical_state_digest(self.root / "data")
        audit["audit_digest"] = digest({key: value for key, value in audit.items() if key != "audit_digest"})
        audit_path.write_text(json.dumps(audit), encoding="utf-8")
        resumed = AutomaticCanonicalUpdate(self.root, self.config, review_boundary=self.boundary)
        with self.assertRaises(EvidenceError):
            resumed.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(self.state.read_bytes(), before_resume,
            "a caller-rehashed post-state receipt is not evidence that this run owns an unrelated write")

    def test_rehashed_audit_and_checkpoint_do_not_grant_recovery_ownership(self):
        self.engine.execute(stop_after="bounded_canonical_promotion")
        changed = json.loads(self.state.read_bytes())
        changed["card"]["fictional-unrelated-write"] = {"entity_type": "card",
            "values": {"card_reference": "fictional-unrelated-write", "name": "Unrelated Write"}}
        self.state.write_text(json.dumps(changed), encoding="utf-8")
        before_resume = self.state.read_bytes()
        claimed_post = canonical_state_digest(self.root / "data")
        audit_path = self.root / "data" / self.engine.config["artifacts"]["promotion_audit"]
        audit = json.loads(audit_path.read_bytes())
        audit["canonical_post_state_digest"] = claimed_post
        audit["audit_digest"] = digest({key: value for key, value in audit.items() if key != "audit_digest"})
        audit_path.write_text(json.dumps(audit), encoding="utf-8")
        checkpoint_path = self.engine._checkpoint("bounded_canonical_promotion")
        checkpoint = json.loads(checkpoint_path.read_bytes())
        checkpoint["details"]["canonical_post_state_digest"] = claimed_post
        checkpoint["result_digest"] = digest({key: value for key, value in checkpoint.items()
            if key != "result_digest"})
        checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
        resumed = AutomaticCanonicalUpdate(self.root, self.config, review_boundary=self.boundary)
        with self.assertRaises(EvidenceError):
            resumed.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(self.state.read_bytes(), before_resume,
            "content hashes on two forged receipts cannot authorize compensation of an unrelated write")

    def test_source_changed_during_final_authorization_is_rejected_before_write(self):
        consumer_validated = False
        source = self.root / "data/evidence/source.json"
        validate = self.engine._validate_consumers
        authorize = self.boundary.authorize
        atomic_write = self.engine._atomic_write
        canonical_writes = []

        def validate_then_mark(*args, **kwargs):
            nonlocal consumer_validated
            result = validate(*args, **kwargs)
            consumer_validated = True
            return result

        def authorize_then_change(bindings):
            decision = authorize(bindings)
            if consumer_validated:
                source.write_bytes(source.read_bytes() + b" ")
            return decision

        def observe_write(path, text, **kwargs):
            if Path(path).resolve() == self.state.resolve():
                canonical_writes.append(text.encode("utf-8"))
            return atomic_write(path, text, **kwargs)

        with patch.object(self.engine, "_validate_consumers", side_effect=validate_then_mark), \
                patch.object(self.boundary, "authorize", side_effect=authorize_then_change), \
                patch.object(self.engine, "_atomic_write", side_effect=observe_write):
            with self.assertRaises(EvidenceError):
                self.engine.execute(stop_after="query_and_analytics_smoke_tests")
        self.assertEqual(self.state.read_bytes(), self.original)
        self.assertFalse(any(raw != self.original for raw in canonical_writes),
            "bound evidence must be checked again after the trusted boundary returns")
        self.assertFalse(self.engine._checkpoint("bounded_canonical_promotion").exists())


if __name__ == "__main__":
    unittest.main()
