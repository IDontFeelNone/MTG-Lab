import hashlib
from pathlib import Path
import unittest

from card_intelligence.repository import KnowledgeRepository

ROOT = Path(__file__).resolve().parents[1]


def tree_digest(relative):
    base = ROOT / relative
    digest = hashlib.sha256()
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        digest.update(path.relative_to(base).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


class Phase146ProviderVerificationTests(unittest.TestCase):
    def test_fail_closed_decision_and_provider_census_are_documented(self):
        report = (ROOT / "docs/PHASE_146_PROVIDER_VERIFICATION.md").read_text()
        self.assertIn("No production competitive acquisition is authorized", report)
        for provider in ("TopDeck.gg", "Wizards / Magic.gg", "Melee", "MTGTop8", "MTGGoldfish"):
            self.assertIn(provider, report)
        self.assertIn("retained competitive-evidence\ncensus remains zero", report)

    def test_no_competitive_production_evidence_or_facts(self):
        self.assertFalse((ROOT / "data/card_intelligence/competitive").exists())
        facts = KnowledgeRepository(ROOT / "data/knowledge").validate()
        self.assertEqual(len(facts), 140)
        self.assertFalse(any("competitive" in f.predicate or "tournament" in f.predicate for f in facts))

    def test_protected_data_is_byte_unchanged(self):
        self.assertEqual(tree_digest("data/canonical"), "e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19")
        self.assertEqual(tree_digest("data/market/observations"), "34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9")
        self.assertEqual(len(list((ROOT / "data/market/observations").rglob("*.json"))), 956)


if __name__ == "__main__":
    unittest.main()
