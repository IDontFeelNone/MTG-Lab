from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
import tempfile
import unittest

from card_intelligence import (CardKnowledgeQuery, Evidence, KnowledgeFact,
                               KnowledgeRepository, KnowledgeValidationError)
from card_intelligence.repository import fact_from_dict, serialize_fact

UTC = timezone.utc
NOW = datetime(2026, 8, 3, tzinfo=UTC)


def fact(fact_id="fact-1", kind="legality", predicate="format.standard", value=True,
         status="known", confidence="0.80", supersedes=(), day=0, sources=("official",)):
    return KnowledgeFact(fact_id, "fixture-game", "fixture-card", kind, predicate, status,
        value, Decimal(confidence) if confidence is not None else None, NOW + timedelta(days=day),
        NOW + timedelta(days=day), tuple(Evidence(source, "publication", f"ref:{source}",
        NOW, f"Claim from {source}") for source in sources), supersedes)


class CardIntelligenceTests(unittest.TestCase):
    def test_immutable_contract_and_deterministic_serialization(self):
        item = fact(sources=("z-source", "a-source"))
        self.assertEqual([x.source_id for x in item.evidence], ["a-source", "z-source"])
        self.assertEqual(serialize_fact(item), serialize_fact(fact(sources=("z-source", "a-source"))))
        with self.assertRaises(Exception): item.fact_id = "changed"

    def test_unknown_and_confidence_validation(self):
        self.assertIsNone(fact(value=None, status="unknown", confidence=None).confidence)
        for kwargs in ({"value": True, "status": "unknown"}, {"confidence": "1.01"}):
            with self.subTest(kwargs=kwargs), self.assertRaises(KnowledgeValidationError): fact(**kwargs)

    def test_multiple_provenance_and_duplicate_evidence(self):
        self.assertEqual(len(fact(sources=("one", "two")).evidence), 2)
        with self.assertRaisesRegex(KnowledgeValidationError, "duplicate evidence"):
            fact(sources=("one", "one"))

    def test_append_load_duplicate_and_noncanonical_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = KnowledgeRepository(Path(temporary)); item = fact(); path = repo.append(item)
            self.assertEqual(repo.load(path), item)
            with self.assertRaisesRegex(KnowledgeValidationError, "duplicate fact_id"): repo.append(item)
            path.write_text(json.dumps(item.to_dict()))
            with self.assertRaisesRegex(KnowledgeValidationError, "canonically serialized"): repo.load(path)

    def test_supersession_history_active_query_and_replay(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = KnowledgeRepository(Path(temporary))
            old = fact(); new = fact("fact-2", value=False, supersedes=(old.fact_id,), day=1)
            repo.append(new); repo.append(old)
            self.assertEqual(repo.validate(), (old, new))
            query = CardKnowledgeQuery(repo)
            self.assertEqual(query.explain("fixture-game", "fixture-card")["count"], 2)
            active = query.explain("fixture-game", "fixture-card", include_superseded=False)
            self.assertEqual([x["fact_id"] for x in active["facts"]], ["fact-2"])
            self.assertEqual(fact_from_dict(json.loads(serialize_fact(new))), new)

    def test_queries_expose_kinds_evidence_confidence_and_empty(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = KnowledgeRepository(Path(temporary))
            repo.append(fact()); repo.append(fact("fact-2", "archetype_usage", "archetype.control",
                "control", sources=("events",), day=1)); repo.append(fact("fact-3",
                "market_catalyst", "catalyst.reprint", "announced", day=2))
            query = CardKnowledgeQuery(repo)
            self.assertEqual(query.competitive_formats("fixture-game", "fixture-card")["count"], 1)
            self.assertEqual(query.archetypes("fixture-game", "fixture-card")["count"], 1)
            self.assertEqual(query.market_catalysts("fixture-game", "fixture-card")["count"], 1)
            report = query.explain("fixture-game", "fixture-card")
            self.assertEqual(report["evidence_sources"], ["events", "official"])
            self.assertEqual(len(report["confidence_values"]), 3)
            self.assertTrue(query.explain("fixture-game", "absent")["empty"])

    def test_invalid_document_and_supersession_fail_closed(self):
        with self.assertRaises(KnowledgeValidationError): fact_from_dict({})
        with tempfile.TemporaryDirectory() as temporary:
            repo = KnowledgeRepository(Path(temporary)); repo.append(fact(supersedes=("missing",)))
            with self.assertRaisesRegex(KnowledgeValidationError, "missing superseded"): repo.validate()


if __name__ == "__main__": unittest.main()
