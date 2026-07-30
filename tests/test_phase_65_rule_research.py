"""Phase 65 evidence-backed product-rule research tests."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from repository import RuleResearchError, load_evidence_bundle, load_rule_research, rule_research_bytes
from validation import validate_document

ROOT = Path(__file__).parents[1]
RESEARCH_ROOT = ROOT / "data/intermediate/research"


class Phase65RuleResearchTests(unittest.TestCase):
    def test_retained_evidence_and_research_are_valid_and_deterministic(self) -> None:
        bundle = load_evidence_bundle("magic", "mb2-phase-65-product-overview")
        self.assertEqual(len(bundle.artifacts), 1)
        self.assertEqual(
            hashlib.sha256(bundle.artifacts[0].content).hexdigest(),
            bundle.manifest["artifacts"][0]["sha256"],
        )
        matrix, report = load_rule_research("magic", "mystery_booster_2", "phase_65")
        validate_document(matrix, "rule-claim-matrix")
        validate_document(report, "evidence-sufficiency-report")
        self.assertEqual(rule_research_bytes("magic", "mystery_booster_2", "phase_65"), rule_research_bytes("magic", "mystery_booster_2", "phase_65"))

    def test_matrix_is_complete_bounded_and_never_promotes_rules(self) -> None:
        matrix, report = load_rule_research("magic", "mystery_booster_2", "phase_65")
        categories = {claim["category"] for claim in matrix["claims"]}
        self.assertTrue({"pack structure", "slot", "print sheet", "card pool", "replacement", "treatment", "collation", "probability"}.issubset(categories))
        self.assertEqual(report["architectural_sufficiency"]["complete_product_status"], "indeterminate")
        self.assertFalse(report["architectural_sufficiency"]["tier_0_change_authorized"])
        self.assertFalse((ROOT / "data/canonical/games/magic/print_sheets").exists())
        self.assertFalse((ROOT / "data/canonical/games/magic/slots").exists())
        product = json.loads((ROOT / "data/canonical/games/magic/products/mystery_booster_2/product.json").read_text())
        self.assertEqual(product["lifecycle_status"], "foundation")
        self.assertEqual(product["slot_ids"], [])

    def test_cross_validation_rejects_untraceable_and_duplicate_claims(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            research_root = Path(directory) / "research"
            shutil.copytree(RESEARCH_ROOT, research_root)
            matrix_path = research_root / "mystery_booster_2/phase_65/rule-claim-matrix.json"
            matrix = json.loads(matrix_path.read_text())
            supported = next(claim for claim in matrix["claims"] if claim["classification"] == "confirmed")
            supported["evidence_references"][0]["artifact_id"] = "missing"
            matrix_path.write_text(json.dumps(matrix))
            with self.assertRaisesRegex(RuleResearchError, "missing artifact"):
                load_rule_research("magic", "mystery_booster_2", "phase_65", research_root=research_root)

            matrix = json.loads((RESEARCH_ROOT / "mystery_booster_2/phase_65/rule-claim-matrix.json").read_text())
            matrix["claims"].append(copy.deepcopy(matrix["claims"][0]))
            matrix_path.write_text(json.dumps(matrix))
            with self.assertRaisesRegex(RuleResearchError, "duplicate claim"):
                load_rule_research("magic", "mystery_booster_2", "phase_65", research_root=research_root)


if __name__ == "__main__":
    unittest.main()
