"""Phase 80 canonical fact, evidence, compatibility, and uncertainty contract."""
from __future__ import annotations
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from canonical import (EvidenceAssertion, EvidenceClass, KnowledgeStatus, KnowledgeValue,
                       UnresolvedCanonicalFact, promote_assertions, require_simulation_facts)
from repository.canonical import CanonicalRepository, CanonicalRepositoryError
from repository.cards import CardRepositoryError
from validation import SchemaValidationError, validate_document
from canonical_import import JSONSource, import_dataset

ROOT = Path(__file__).parents[1] / "data/canonical/games"


def assertion(identifier, subject, path, value, source="fixture", status="promoted"):
    return {"id": identifier, "subject_id": subject, "path": path, "asserted_value": value,
            "source_id": source, "source_type": "test fixture", "evidence_class": "official",
            "timestamp": "2026-07-30T00:00:00Z", "confidence": 1,
            "verification_status": "confirmed", "status": status}


def assertions(subject, document):
    return [assertion(f"{subject}.a{i}", subject, f"/{key}", value)
            for i, (key, value) in enumerate(document.items())
            if key not in {"schema_version", "assertions", "metadata"}]


class CanonicalV3Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name) / "games"
        shutil.copytree(ROOT / "magic", self.root / "magic")
        source = {"schema_version":"v1","id":"fixture","title":"Fixture","source_classification":"official",
                  "provider":"Test","source_location":"local","access_date":"2026-07-30",
                  "verification_status":"confirmed","claims":["fixture"],"record_version":"1"}
        (self.root/"magic/sources/fixture.json").write_text(json.dumps(source))
    def tearDown(self): self.temp.cleanup()

    def test_complete_multifaced_card_and_printing_preserve_printed_text(self):
        card = {"schema_version":"v3","id":"magic.fixture.card","game":"magic","name":"Front // Back",
                "normalized_name":"front // back","layout":"transform",
                "faces":[{"name":"Front","mana_cost":"{1}{U}","type_line":"Creature","oracle_text":"Draw."},
                         {"name":"Back","type_line":"Creature","oracle_text":"Fly."}],
                "mana_value":2,"colors":["U"],"color_identity":["U"],"type_line":"Creature // Creature",
                "supertypes":[],"card_types":["Creature"],"subtypes":[],"oracle_text":"Draw. // Fly.",
                "keywords":["Flying"],"legalities":{"modern":"legal"},"related_cards":[],"assertions":[]}
        card["assertions"] = assertions(card["id"], card)
        printing = {"schema_version":"v3","id":"magic.fix.1.en","card_id":card["id"],"set_id":"fix",
                    "collector_number":"1","language":"en","rarity":"rare","artist":"Artist",
                    "printed_name":"Localized Front","printed_text":"Printing-specific wording.",
                    "printed_type_line":"Printed Creature","frame":"2015","border":"black",
                    "finishes":["nonfoil"],"treatments":[],"promotional_flags":[],
                    "release_date":"2026-07-30","external_identifiers":{"provider":"123"},
                    "image_references":[],"assertions":[]}
        printing["assertions"] = assertions(printing["id"], printing)
        validate_document(card, "card"); validate_document(printing, "printing")
        for relative, value in [(f"cards/{card['id']}/card.json",card),(f"printings/{printing['id']}/printing.json",printing)]:
            path=self.root/"magic"/relative; path.parent.mkdir(parents=True); path.write_text(json.dumps(value))
        repo=CanonicalRepository("magic", games_root=self.root)
        self.assertEqual(repo.get_card(card["id"]).faces[1]["oracle_text"], "Fly.")
        self.assertEqual(repo.get_printing(printing["id"]).facts["printed_text"], "Printing-specific wording.")

    def test_invalid_face_evidence_and_dispatch_fail_closed(self):
        bad={"schema_version":"v3","id":"magic.bad","game":"magic","name":"Bad","normalized_name":"bad",
             "layout":"transform","faces":[{"name":"only"}],"assertions":[]}
        with self.assertRaises(SchemaValidationError): validate_document(bad,"card")
        bad["schema_version"]="v99"
        with self.assertRaises((FileNotFoundError, SchemaValidationError)): validate_document(bad,"card")

    def test_unknown_absent_and_simulation_readiness_are_distinct(self):
        facts={"/replacement":KnowledgeValue(KnowledgeStatus.UNKNOWN),
               "/weight":KnowledgeValue(KnowledgeStatus.KNOWN, 2)}
        with self.assertRaises(UnresolvedCanonicalFact): require_simulation_facts(facts,["/replacement","/weight"])
        with self.assertRaisesRegex(UnresolvedCanonicalFact,"absent"):
            require_simulation_facts(facts,["/composition"])
        self.assertIsNone(KnowledgeValue(KnowledgeStatus.KNOWN_ABSENT).value)

    def test_promotion_is_deterministic_and_tied_conflict_is_unresolved(self):
        def claim(i,value,klass=EvidenceClass.OFFICIAL,confidence=1):
            return EvidenceAssertion(i,"card","/name",value,i,"fixture",klass,"2026-07-30T00:00:00Z",confidence,"confirmed")
        low=claim("community","A",EvidenceClass.VERIFIED_COMMUNITY,.9); official=claim("official","B")
        self.assertEqual(promote_assertions([low,official]),promote_assertions([official,low]))
        self.assertIsNone(promote_assertions([claim("a","A"),claim("b","B")]))

    def test_duplicate_collector_namespace_and_contradictory_promotions_fail(self):
        original=json.loads((self.root/"magic/printings/magic.mb2.1.en/printing.json").read_text())
        duplicate=dict(original); duplicate["id"]="magic.mb2.1-copy.en"
        path=self.root/"magic/printings"/duplicate["id"]/"printing.json"; path.parent.mkdir(); path.write_text(json.dumps(duplicate))
        with self.assertRaisesRegex(CanonicalRepositoryError,"Duplicate collector"):
            CanonicalRepository("magic",games_root=self.root)

    def test_legacy_bytes_are_unchanged_by_reconciled_projection(self):
        path=self.root/"magic/cards/magic.abzan-falconer/card.json"; before=path.read_bytes()
        CanonicalRepository("magic",games_root=self.root)
        self.assertEqual(path.read_bytes(),before)

    def test_v3_import_is_idempotent_and_retains_assertions(self):
        card={"schema_version":"v3","id":"magic.imported","game":"magic","name":"Imported",
              "normalized_name":"imported","layout":"normal","assertions":[]}
        card["assertions"]=assertions(card["id"],card)
        dataset={"schema_version":"v3","source":"fixture","source_version":"1","review_status":"reviewed",
                 "game":"magic","cards":[card]}
        source_path=Path(self.temp.name)/"dataset.json"; source_path.write_text(json.dumps(dataset))
        first=import_dataset(JSONSource(source_path),"magic",games_root=self.root)
        second=import_dataset(JSONSource(source_path),"magic",games_root=self.root)
        self.assertEqual((first.created,second.unchanged),(1,2))
        stored=json.loads((self.root/"magic/cards/magic.imported/card.json").read_text())
        self.assertEqual(stored["assertions"],card["assertions"])
