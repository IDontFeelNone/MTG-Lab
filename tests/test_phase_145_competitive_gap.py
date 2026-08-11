import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from card_intelligence.competitive_evidence import records_digest, validate_competitive_snapshot
from card_intelligence.repository import KnowledgeRepository

ROOT = Path(__file__).resolve().parents[1]


def tree_digest(relative):
    base = ROOT / relative
    digest = hashlib.sha256()
    for path in sorted(p for p in base.rglob("*") if p.is_file()):
        digest.update(path.relative_to(base).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


class Phase145CompetitiveGapTests(unittest.TestCase):
    def snapshot(self):
        records = [{
            "card_identity": {"game_id": "magic", "card_id": "6ad8011d-3471-4369-9d68-b264cc027487", "name": "Sol Ring"},
            "source_record_identity": "deck/42", "event_identity": "event/7",
            "event_date": "2026-08-01", "format": "Commander",
            "provider_deck_name": "Literal label", "provider_archetype": None,
            "player_identity": None, "placement": 2, "result": None,
            "mainboard_count": 1, "sideboard_count": 0, "event_size": 64,
            "source_record_sha256": "1" * 64,
            "explicit_unknowns": ["provider_archetype", "result"]
        }]
        return {
            "schema_version": "card-competitive-evidence-v1", "snapshot_id": "provider-pilot-1",
            "provider": "provider", "source_dataset": "events-api", "source_endpoint": "https://example.test/events",
            "dataset_timestamp": "2026-08-01T00:00:00Z", "retrieved_at": "2026-08-11T00:00:00Z",
            "source_sha256": "0" * 64, "source_byte_count": 123,
            "license_review": {"status": "approved", "terms_url": "https://example.test/terms", "reviewed_at": "2026-08-11T00:00:00Z", "retention_permitted": True, "notes": "test fixture only"},
            "retention_boundary": "one bounded projection", "population": {"deck_denominator": 64, "event_denominator": 1, "qualifying_event_definition": "one event", "deck_population_definition": "all submitted decklists", "denominator_complete": True},
            "completeness": "bounded_projection", "provenance": "provider response",
            "explicit_unknowns": ["match results"], "records": records,
            "records_sha256": records_digest(records)
        }

    def write(self, document):
        temporary = tempfile.TemporaryDirectory()
        path = Path(temporary.name) / "snapshot.json"
        path.write_text(json.dumps(document))
        return temporary, path

    def test_validates_contract_without_admission(self):
        temporary, path = self.write(self.snapshot())
        with temporary:
            self.assertEqual(validate_competitive_snapshot(path)["snapshot_id"], "provider-pilot-1")

    def test_fails_closed_on_license_digest_duplicate_and_player(self):
        for mutation, message in [
            (lambda d: d["license_review"].update(status="unverified", retention_permitted=False), "retention rights"),
            (lambda d: d.update(records_sha256="f" * 64), "digest mismatch"),
            (lambda d: d["records"][0].update(player_identity="player"), "schema error"),
        ]:
            document = copy.deepcopy(self.snapshot()); mutation(document)
            temporary, path = self.write(document)
            with temporary, self.assertRaisesRegex(ValueError, message):
                validate_competitive_snapshot(path)

    def test_exact_baseline_and_protected_data(self):
        facts = KnowledgeRepository(ROOT / "data/knowledge").validate()
        self.assertEqual(len(facts), 140)
        self.assertEqual(sum(f.fact_id.startswith("phase136-") and f.predicate == "printing.reprint_history" for f in facts), 10)
        self.assertEqual(sum(f.fact_id.startswith("phase142-") and f.predicate == "value_driver.demand" for f in facts), 10)
        self.assertEqual(sum(f.fact_id.startswith("phase144-") and f.predicate == "demand.deck_inclusion" for f in facts), 10)
        self.assertEqual(sum(f.fact_id.startswith("phase144-") and f.predicate == "format.usage" for f in facts), 10)
        self.assertEqual(len(list((ROOT / "data/market/observations").rglob("*.json"))), 956)
        self.assertEqual(tree_digest("data/canonical"), "e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19")
        self.assertEqual(tree_digest("data/market/observations"), "34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9")

    def test_no_production_competitive_snapshot_or_fact(self):
        self.assertFalse((ROOT / "data/card_intelligence/competitive").exists())
        facts = KnowledgeRepository(ROOT / "data/knowledge").validate()
        self.assertFalse(any("competitive" in f.predicate or "tournament" in f.predicate for f in facts))


if __name__ == "__main__":
    unittest.main()
