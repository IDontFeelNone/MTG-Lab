import copy
import json
import tempfile
import unittest
from pathlib import Path

from acquisition import (AcquisitionEngine, CanonicalPromotionEngine, FixtureProvider,
    PromotionDecision, PromotionError, ProviderPolicy, ProviderTrustPolicy, RawSnapshotStore,
    assertions_from_normalized, build_review_package, normalize_snapshot)

TS = "2026-07-30T12:00:00+00:00"


class CanonicalPromotionEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        fixture = Path("data/fixtures/knowledge/reviewed-cards.json").read_bytes()
        self.provider = FixtureProvider({"reviewed-cards": fixture})
        store = RawSnapshotStore(self.root / "raw"); engine = AcquisitionEngine(store, self.root / "runs")
        engine.register(self.provider); self.run = engine.acquire("fixture", "reviewed-cards", started_at=TS, run_id="phase-85")
        path = Path(self.run["downloaded_snapshots"][0]["path"])
        self.snapshot = json.loads((path / "manifest.json").read_text())
        self.normalized = normalize_snapshot(self.provider, store, path, self.root / "normalized.json")
        self.policy = ProviderPolicy.from_dict(json.loads(Path("data/fixtures/knowledge/provider-policy.json").read_text()))
        self.engine = CanonicalPromotionEngine(self.root / "canonical", self.root / "audit")

    def tearDown(self): self.temp.cleanup()

    def package(self, normalized=None):
        normalized = normalized or self.normalized
        assertions = assertions_from_normalized(normalized,
            ProviderTrustPolicy("authoritative_structured", .8, "verified"), TS)
        return build_review_package(self.run, [self.snapshot], [normalized], assertions, self.policy, "fixture-v1")

    def decision(self, timestamp=TS, **kwargs):
        return PromotionDecision("codex-phase-85", timestamp, allow_unknowns=True, **kwargs)

    def test_success_provenance_unknowns_and_idempotence(self):
        package = self.package(); audit = self.engine.promote(package, self.policy, self.decision())
        self.assertEqual(audit, self.engine.promote(package, self.policy, self.decision()))
        record = self.engine.current("card", "card-001")
        self.assertEqual(record["review_package_id"], package["review_package_id"])
        self.assertEqual(record["dataset_identity"], package["snapshot_lineage"])
        self.assertEqual(record["uncertainty_state"], "unknowns_reviewed")
        self.assertEqual(record["confidence"], .8); self.assertTrue(record["evidence_references"])

    def test_validation_failures_policy_identity_duplicates_conflicts_and_unknowns(self):
        package = self.package()
        with self.assertRaisesRegex(PromotionError, "unknown_values"):
            self.engine.promote(package, self.policy, PromotionDecision("reviewer", TS))
        wrong = ProviderPolicy("other", "official", 1, (), "other", ("card",))
        with self.assertRaisesRegex(PromotionError, "provider_policy"):
            self.engine.promote(package, wrong, self.decision("2026-07-30T12:01:00+00:00"))
        duplicate = copy.deepcopy(package); duplicate["candidate_assertions"].append(duplicate["candidate_assertions"][0])
        with self.assertRaisesRegex(PromotionError, "review_package"):
            self.engine.promote(duplicate, self.policy, self.decision("2026-07-30T12:02:00+00:00"))
        conflict = copy.deepcopy(package); conflict["detected_conflicts"]["count"] = 1
        with self.assertRaisesRegex(PromotionError, "review_package"):
            self.engine.promote(conflict, self.policy, self.decision("2026-07-30T12:03:00+00:00"))
        self.assertFalse((self.root / "canonical/state.json").exists())

    def test_supersession_history_rollback_replay_and_audit_immutability(self):
        first = self.engine.promote(self.package(), self.policy, self.decision())
        changed = copy.deepcopy(self.normalized)
        changed["records"][0]["source_values"]["mana_value"] = 4
        second = self.engine.promote(self.package(changed), self.policy,
                                     self.decision("2026-07-30T13:00:00+00:00"))
        current = self.engine.current("card", "card-001")
        self.assertEqual(current["values"]["/mana_value"], 4)
        self.assertEqual(current["replaces"], first["promotion_id"])
        self.assertEqual(len(self.engine.history("card", "card-001")), 2)
        rollback = self.engine.rollback(second["promotion_id"], self.decision("2026-07-30T14:00:00+00:00"))
        self.assertEqual(self.engine.current("card", "card-001")["values"]["/mana_value"], 3)
        self.assertEqual(self.engine.replay(), json.loads((self.root / "canonical/state.json").read_text()))
        self.assertEqual(rollback, self.engine.rollback(second["promotion_id"], self.decision("2026-07-30T14:00:00+00:00")))
        audit_path = self.root / "audit" / f"{first['promotion_id']}.json"
        before = audit_path.read_bytes()
        with self.assertRaises(PromotionError):
            from acquisition.promotion import _write_once
            _write_once(audit_path, {"different": True})
        self.assertEqual(before, audit_path.read_bytes()); self.assertEqual(len(self.engine.audit()), 3)

    def test_rejected_decision_and_tampered_integrity_fail_closed(self):
        with self.assertRaisesRegex(PromotionError, "decision"):
            self.engine.promote(self.package(), self.policy,
                PromotionDecision("reviewer", TS, approved=False, allow_unknowns=True, reason="reject"))
        package = self.package(); package["snapshot_lineage"][0]["snapshot_hash"] = "0" * 64
        with self.assertRaisesRegex(PromotionError, "review_package"):
            self.engine.promote(package, self.policy, self.decision())


if __name__ == "__main__": unittest.main()
