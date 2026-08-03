"""Phase 120 reusable automatic canonical update coverage (unittest only)."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from production_evidence.automatic_updates import (
    AutomaticCanonicalUpdate, GitHubPersistence, STAGES, TargetDescriptor, digest,
)
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config/automatic_updates/mb2-first-batch.json"


class AutomaticUpdateTests(unittest.TestCase):
    def synthetic(self, directory, *, code="NEW", provider="trusted", classifications=None):
        root = Path(directory); (root / "data/canonical").mkdir(parents=True)
        (root / "data/canonical/state.json").write_text('{"card": {}, "finish": {}, "identifier": {}, "printing": {}}\n')
        candidates = classifications or [
            {"candidate_identifier": "card:1", "entity_type": "card", "validation_state": "validated",
             "mapped_fields": {"card_reference": "c1", "set_code": code}, "provenance": {"provider": provider}},
            {"candidate_identifier": "printing:1", "entity_type": "printing", "validation_state": "validated",
             "mapped_fields": {"uuid": "p1", "card_reference": "c1", "set_code": code}, "provenance": {"provider": provider}},
        ]
        ids = [row["candidate_identifier"] for row in candidates]
        payload = {"candidate_ids": ids, "candidate_payloads": candidates, "target_set_code": code}
        (root / "data/evidence").mkdir(); (root / "data/evidence/payload.json").write_text(json.dumps(payload))
        (root / "data/evidence/source.json").write_text("source")
        from production_evidence.promotion_readiness import canonical_state_digest
        config = {"schema_version": "automatic-canonical-update-v1", "data_root": "data",
          "target": {"game": "magic", "target_code": code, "target_name": "Future Set",
            "trusted_provider": provider, "source_dataset_identity": "dataset-1",
            "source_artifact_or_workflow_run": "run-1", "evidence_identity": "evidence-1",
            "batch_identifier": f"{code.lower()}-batch-1", "candidate_digest": digest(ids),
            "expected_target_isolation": code, "promotion_policy": "deterministic-v1",
            "destination_branch": f"canonical-update/{code.lower()}-batch-1", "base_branch": "main"},
          "artifacts": {"source_artifact": "evidence/source.json", "candidate_payload": "evidence/payload.json",
                        "promotion_audit": "audit/promotion.json"},
          "integrity": {"source_sha256": digest(b"source"), "expected_candidate_count": len(ids),
                        "canonical_pre_state_digest": canonical_state_digest(root / "data")},
          "policy": {"trusted_providers": ["trusted"], "permitted_final_classifications": ["approved"]}}
        path = root / "config.json"; path.write_text(json.dumps(config)); return root, path

    def test_reference_descriptor_is_generic_and_completed_mb2_is_not_repromoted(self):
        descriptor, raw = TargetDescriptor.load(CONFIG)
        self.assertEqual(descriptor.game, "magic")
        self.assertEqual(descriptor.target_code, "MB2")
        self.assertTrue(raw["reference_completed_promotion"])
        self.assertNotIn("MB2", Path(ROOT / "src/production_evidence/automatic_updates.py").read_text())
        engine = AutomaticCanonicalUpdate(ROOT, CONFIG)
        self.assertTrue(engine.verify()["audit_present"])
        phase136 = json.loads((ROOT / "data/audit/bounded_promotions/phase-136-mtgjson-pilot-30786023976-1.json").read_text())
        self.assertEqual(phase136["canonical_pre_state_digest"], raw["integrity"]["canonical_post_state_digest"])
        self.assertEqual(engine.verify()["canonical_state_digest"], phase136["canonical_post_state_digest"])

    def test_exact_stage_order_and_interrupted_run_recovery(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.synthetic(temporary); observed = []
            handlers = {stage: (lambda context, stage=stage: observed.append(stage) or {"ok": True}) for stage in STAGES}
            engine = AutomaticCanonicalUpdate(root, config, handlers=handlers)
            engine.execute(stop_after=STAGES[4]); self.assertEqual(observed, list(STAGES[:5]))
            engine.execute(); self.assertEqual(observed, list(STAGES)); self.assertTrue(engine.status()["complete"])
            self.assertTrue(engine.replay()["idempotent"])

    def test_failure_stops_later_stages_and_retains_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.synthetic(temporary); observed = []
            def handler(stage):
                def run(context):
                    observed.append(stage)
                    if stage == STAGES[3]: raise EvidenceError("isolated failure")
                    return {"ok": True}
                return run
            engine = AutomaticCanonicalUpdate(root, config, handlers={x: handler(x) for x in STAGES})
            with self.assertRaises(EvidenceError): engine.execute()
            self.assertEqual(observed, list(STAGES[:4]))
            self.assertTrue((engine.run_root / "blocked-report.json").is_file())

    def test_trust_isolation_classification_dependency_and_drift_fail_closed(self):
        cases = ("trust", "isolation", "quarantine", "orphan", "drift")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                rows = None
                if case == "quarantine": rows = [{"candidate_identifier": "x", "entity_type": "card", "final_classification": "quarantined", "mapped_fields": {"card_reference": "c", "set_code": "NEW"}, "provenance": {"provider": "trusted"}}]
                root, config = self.synthetic(temporary, provider="bad" if case == "trust" else "trusted", classifications=rows)
                engine = AutomaticCanonicalUpdate(root, config)
                if case == "isolation":
                    value = json.loads((root / "data/evidence/payload.json").read_text()); value["candidate_payloads"][0]["mapped_fields"]["set_code"] = "OTHER"; (root / "data/evidence/payload.json").write_text(json.dumps(value))
                elif case == "orphan":
                    value = json.loads((root / "data/evidence/payload.json").read_text()); value["candidate_payloads"][1]["mapped_fields"]["card_reference"] = "missing"; (root / "data/evidence/payload.json").write_text(json.dumps(value))
                elif case == "drift": (root / "data/canonical/drift").write_text("x")
                with self.assertRaises(EvidenceError): engine.execute()

    def test_conflicting_checkpoint_and_immutable_audit_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root, config = self.synthetic(temporary)
            handlers = {stage: (lambda context: {"ok": True}) for stage in STAGES}
            engine = AutomaticCanonicalUpdate(root, config, handlers=handlers); engine.execute(stop_after=STAGES[0])
            checkpoint = engine._checkpoint(STAGES[0]); value = json.loads(checkpoint.read_text()); value["details"] = {"tampered": True}; checkpoint.write_text(json.dumps(value))
            with self.assertRaises(EvidenceError): engine.execute()

    def test_github_pr_creation_reuse_and_no_protection_bypass(self):
        calls = []
        def success(command, **kwargs): calls.append(command); return subprocess.CompletedProcess(command, 0, "", "")
        self.assertTrue(GitHubPersistence(success).persist("canonical-update/x", "main", "title", "body")["created"])
        flattened = " ".join(" ".join(command) for command in calls)
        self.assertNotIn("--force", flattened); self.assertNotIn("--admin", flattened)
        calls.clear()
        def reuse(command, **kwargs):
            calls.append(command)
            if command[1:3] == ["pr", "create"]: return subprocess.CompletedProcess(command, 1, "", "exists")
            if command[1:3] == ["pr", "view"]: return subprocess.CompletedProcess(command, 0, json.dumps({"headRefName": "canonical-update/x", "baseRefName": "main", "url": "u"}), "")
            return subprocess.CompletedProcess(command, 0, "", "")
        self.assertTrue(GitHubPersistence(reuse).persist("canonical-update/x", "main", "title", "body")["reused"])

    def test_workflow_has_merge_gates_and_diagnostic_retention(self):
        workflow = (ROOT / ".github/workflows/automatic-canonical-update.yml").read_text()
        for token in ("git diff --check", "headRefOid", "baseRefName", "--auto", "if: always()", "push origin"):
            self.assertIn(token, workflow)
        self.assertNotIn("--force", workflow); self.assertNotIn("--admin", workflow)


if __name__ == "__main__": unittest.main()
