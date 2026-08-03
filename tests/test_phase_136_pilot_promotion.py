from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from card_intelligence import CardKnowledgeQuery, KnowledgeRepository
from production_evidence.phase136_promotion import (
    COUNTS, EXPECTED_PRE_STATE, PROMOTION_ID, build_plan, promote, rollback, verify_evidence,
)
from production_evidence.repository import EvidenceError

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
REPORT = DATA / "reviews/phase-136/pilot-review.json"


def tree_digest(path):
    root = ROOT / path; digest = hashlib.sha256()
    for item in sorted(x for x in root.rglob("*") if x.is_file()):
        digest.update(item.relative_to(root).as_posix().encode() + b"\0")
        digest.update(item.read_bytes())
    return digest.hexdigest()


class Phase136PromotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.verified = verify_evidence(DATA)
        cls.report = json.loads(REPORT.read_bytes())
        cls.state = json.loads((DATA / "canonical/state.json").read_bytes())
        cls.audit = json.loads((DATA / f"audit/bounded_promotions/{PROMOTION_ID}.json").read_bytes())

    def test_exact_evidence_inventory_integrity_and_baseline(self):
        self.assertEqual(self.verified["report"]["retained_file_inventory"],
                         ["acquisition-report.json", "manifest.json", "source-pilot-printings.json"])
        manifest = self.verified["manifest"]
        self.assertEqual(manifest["printing_counts_by_pilot_card"], COUNTS)
        self.assertEqual(manifest["retained_printing_count"], 534)
        self.assertEqual(manifest["source_byte_count"], 177237377)
        self.assertEqual(len(self.verified["source"]["pilot_printings"]), 534)

    def test_deterministic_candidates_identity_fields_unknowns_and_review(self):
        # Reconstruct against an isolated exact pre-state because production is now post-state.
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); shutil.copytree(DATA / "evidence", root / "evidence")
            shutil.copytree(DATA / "canonical", root / "canonical")
            state = json.loads((root / "canonical/state.json").read_text())
            for identity in self.audit["promoted_printing_ids"]: state["printing"].pop(identity)
            (root / "canonical/state.json").write_text(json.dumps(state, indent=2, sort_keys=True,
                                                        ensure_ascii=False) + "\n")
            plan1 = build_plan(root); plan2 = build_plan(root)
            self.assertEqual(plan1, plan2); self.assertEqual(plan1["candidate_count"], 534)
            self.assertEqual(sum(plan1["review_census"].values()), 534)
            self.assertEqual(plan1["review_census"]["accepted"], 534)
            self.assertEqual(set(plan1["cards_reused"]), set(COUNTS))
            for candidate in plan1["candidates"]:
                value = candidate["values"]
                self.assertEqual(candidate["candidate_id"].rsplit(":", 1)[-1], value["uuid"])
                for field in ("set_code", "set_name", "collector_number", "release_date",
                              "language", "finish_ids", "rarity", "frame_or_treatment"):
                    self.assertIn(field, value)
                self.assertIn(value["promotional"], (True, "unknown"))
                self.assertIn(value["digital_or_paper"], ("digital", "unknown"))

    def test_dependency_closure_no_orphans_scope_and_canonical_counts(self):
        pilot_ids = set(self.report["cards"][i]["card_id"] for i in range(10))
        promoted = [self.state["printing"][x] for x in self.audit["promoted_printing_ids"]]
        self.assertEqual(len(promoted), 534)
        self.assertTrue(all(x["values"]["card_id"] in pilot_ids for x in promoted))
        self.assertTrue(all(x["values"]["set_code"] != "MB2" for x in promoted))
        self.assertEqual(len(self.state["printing"]), 913)
        self.assertEqual(Counter(x["values"]["card_id"] for x in promoted),
                         Counter({x["card_id"]: x["retained_printing_count"] for x in self.report["cards"]}))

    def test_atomic_failure_replay_conflict_and_rollback(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); shutil.copytree(DATA / "evidence", root / "evidence")
            shutil.copytree(DATA / "canonical", root / "canonical")
            state = json.loads((root / "canonical/state.json").read_text())
            for identity in self.audit["promoted_printing_ids"]: state["printing"].pop(identity)
            (root / "canonical/state.json").write_text(json.dumps(state, indent=2, sort_keys=True,
                                                        ensure_ascii=False) + "\n")
            before = (root / "canonical/state.json").read_bytes()
            with self.assertRaises(RuntimeError):
                promote(root, failure_hook=lambda point: (_ for _ in ()).throw(RuntimeError(point)))
            self.assertEqual((root / "canonical/state.json").read_bytes(), before)
            first = promote(root); state_bytes = (root / "canonical/state.json").read_bytes()
            replay = promote(root)
            self.assertTrue(replay["idempotent"]); self.assertEqual(state_bytes, (root / "canonical/state.json").read_bytes())
            self.assertEqual(rollback(root)["canonical_state_digest"], EXPECTED_PRE_STATE)
            with self.assertRaisesRegex(EvidenceError, "conflicting promotion replay"): promote(root)

    def test_ten_facts_supersession_queries_and_coverage(self):
        repo = KnowledgeRepository(DATA / "knowledge"); facts = repo.validate()
        new = [x for x in facts if x.fact_id.startswith("phase136-")]
        self.assertEqual(len(new), 10)
        query = CardKnowledgeQuery(repo)
        for row in self.report["cards"]:
            active = query.printing_history("magic", row["card_id"])
            history = query.printing_history("magic", row["card_id"], include_superseded=True)
            self.assertEqual(active["count"], 1); self.assertEqual(history["count"], 3)
            self.assertEqual([x["fact_id"].split("-", 1)[0] for x in history["facts"]],
                             ["phase132", "phase133", "phase136"])
            value = active["facts"][0]["value"]["data"]
            self.assertEqual(value["total_known_canonical_printings"], row["printing_count_after"])
            self.assertEqual(value["reprint_count"], row["reprint_count"])
            self.assertEqual(value["coverage_state"], "incomplete")
            self.assertIn("Printing count is not supply quantity.", value["limitations"])

    def test_protected_boundaries_and_deterministic_artifacts(self):
        self.assertEqual(len(list((DATA / "market/observations").glob("*/*/*/*.json"))), 478)
        self.assertEqual(tree_digest("data/market/observations"),
                         "7ecc2c6064856e4921802813e186d34ccafb0ca6daf6a59b0b6c1dd11ad999f8")
        self.assertEqual(len(list((DATA / "knowledge/facts").glob("*/*/phase132-*.json"))), 90)
        self.assertEqual(len(list((DATA / "knowledge/facts").glob("*/*/phase133-*.json"))), 10)
        expected = (json.dumps(self.report, indent=2, sort_keys=True,
                               separators=(",", ": ")) + "\n").encode()
        self.assertEqual(REPORT.read_bytes(), expected)
        self.assertFalse(self.report["external_acquisition_performed"])
        self.assertFalse(self.report["unsupported_inference_performed"])


if __name__ == "__main__": unittest.main()
