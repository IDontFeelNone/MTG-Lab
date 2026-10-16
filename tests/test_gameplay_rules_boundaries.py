"""Governance boundaries independent of the current mutable catalog census."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "reference-reviews/gameplay-rules-foundation"


class GameplayRulesBoundaryTests(unittest.TestCase):
    def test_bounded_source_inventory_retains_metadata_not_a_rules_corpus(self):
        manifest = json.loads((REVIEW / "manifest.json").read_bytes())
        self.assertFalse(manifest["source_permission_clearance"])
        self.assertEqual(set(manifest["files"]), {"source-inventory.json"})
        for name, binding in manifest["files"].items():
            raw = (REVIEW / name).read_bytes()
            self.assertEqual(len(raw), binding["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), binding["sha256"])
        inventory = json.loads((REVIEW / "source-inventory.json").read_bytes())
        self.assertFalse(inventory["real_rules_execution_authorized"])
        self.assertTrue(inventory["fictional_execution_only"])
        self.assertEqual(len(inventory["records"]), 3)
        for record in inventory["records"]:
            self.assertIn(record["url"].split("/")[2],
                          {"magic.wizards.com", "gatherer.wizards.com"})
            self.assertEqual(record["availability"], "EVIDENCE_UNAVAILABLE")
            self.assertIsNone(record["content_sha256"])
            self.assertIsNone(record["rules_version_verified"])
            self.assertIsNone(record["effective_date_verified"])
            self.assertFalse(record["permission_inference_from_availability"])
            self.assertEqual(set(record["permission_status"].values()), {"NOT_ESTABLISHED"})
            self.assertNotIn("content", record)
            self.assertNotIn("headers", record)

    def test_gameplay_package_does_not_import_product_admission_or_transport_domains(self):
        forbidden = {"repository", "production_evidence", "simulation", "requests",
                     "urllib", "socket", "random", "secrets", "subprocess", "http"}
        for path in (ROOT / "src/gameplay_rules").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [entry.name for entry in node.names]
                elif isinstance(node, ast.ImportFrom) and node.level == 0:
                    names = [node.module or ""]
                self.assertFalse({name.split(".")[0] for name in names} & forbidden, path.name)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {"eval", "exec", "compile"}, path.name)

    def test_original_product_rules_and_simulation_boundaries_remain_explicit(self):
        for name in ("docs/RULES_ENGINE.md", "src/repository/rules.py",
                     "src/repository/rule_research.py"):
            self.assertTrue((ROOT / name).is_file())
        self.assertIn("Print Sheet", (ROOT / "src/repository/rules.py").read_text())
        self.assertEqual([p.name for p in (ROOT / "src/simulation").iterdir()
                          if p.name != "__pycache__"], [".gitkeep"])

    def test_historical_card_acquisition_keeps_its_own_v12_dependency(self):
        directory = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((directory / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"],
            "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53")
        for relative, binding in manifest["files"].items():
            raw = (directory / relative).read_bytes()
            self.assertEqual(len(raw), binding["bytes"])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), binding["sha256"])


if __name__ == "__main__":
    unittest.main()
