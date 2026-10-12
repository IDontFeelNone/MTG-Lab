import json
import shutil
import tempfile
import unittest
from pathlib import Path

from query.engine import CanonicalQueryEngine

from collection.intelligence import (CanonicalCollectionResolver, CollectionIntelligenceError,
    acquisition_priorities, collection_summary, compare_deck, create_snapshot, read_import,
    verify_snapshot)


ROOT = Path(__file__).parents[1]


class CollectionIntelligenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        self.resolver = CanonicalCollectionResolver("magic", ROOT / "data")
        self.pid = "magic.lea.161.en"; self.card = self.resolver.printings[self.pid]["card_id"]

    def tearDown(self): self.temp.cleanup()

    def write_json(self, entries):
        path=self.root/"import.json"; path.write_text(json.dumps({"schema_version":"collection-import-v1",
            "collection_id":"mine","source":{"type":"fixture","name":"synthetic"},"entries":entries}))
        return path

    def test_json_csv_resolution_unknowns_duplicates_and_invalid(self):
        self.resolver.by_name["synthetic ambiguous"]=[self.pid,"magic.lea.232.en"]
        path=self.write_json([
            {"printing_id":self.pid,"quantity":2,"finish":"nonfoil","language":"en","condition":"near_mint"},
            {"printing_id":self.pid,"quantity":2,"finish":"nonfoil","language":"en","condition":"near_mint"},
            {"printing_id":"missing","quantity":1}, {"card_name":"Synthetic Ambiguous","quantity":1},
            {"printing_id":self.pid,"quantity":0}])
        imported=read_import(path); resolved=self.resolver.resolve(imported)
        self.assertEqual([x["status"] for x in resolved["results"]],
                         ["resolved","duplicate_input_row","unresolved","ambiguous","invalid"])
        self.assertIn("acquisition_price", resolved["results"][0]["row"]["unknown_fields"])
        csv_path=self.root/"import.csv"; csv_path.write_text("printing_id,quantity,finish,language\n%s,1,foil,fr\n"%self.pid)
        csv_result=self.resolver.resolve(read_import(csv_path))["results"][0]
        self.assertEqual((csv_result["status"],csv_result["row"]["finish"],csv_result["row"]["language"]),("resolved","foil","fr"))

    def test_exact_external_identifier_and_name_fallback(self):
        self.resolver.by_name["synthetic ambiguous"]=[self.pid,"magic.lea.232.en"]
        imported={"entries":[{"external_identifiers":{"set_collector_number":"LEA:161"},"quantity":1},
                             {"card_name":"Synthetic Ambiguous","quantity":1}]}
        results=self.resolver.resolve(imported)["results"]
        self.assertEqual(results[0]["printing_id"],self.pid)
        self.assertEqual(results[1]["status"],"ambiguous")

    def snapshot(self):
        imported=read_import(self.write_json([{"printing_id":self.pid,"quantity":3,"finish":"nonfoil",
            "language":"en","condition":"good","acquisition_price":"1.25"},
            {"printing_id":"unknown","quantity":1,"card_name":"Maybe"}]))
        return create_snapshot(imported,self.resolver.resolve(imported),self.root/"snapshots","stable")

    def test_snapshot_replay_conflict_verify_summary_and_no_canonical_write(self):
        before=(ROOT/"data/canonical/state.json").read_bytes(); snapshot=self.snapshot()
        disk=(self.root/"snapshots/stable.json").read_bytes()
        imported=read_import(self.write_json([{"printing_id":self.pid,"quantity":3,"finish":"nonfoil",
            "language":"en","condition":"good","acquisition_price":"1.25"},
            {"printing_id":"unknown","quantity":1,"card_name":"Maybe"}]))
        # Raw import digest changes with serialization, so replay the stored contract inputs directly.
        imported["source_import_digest"]=snapshot["source_import_digest"]
        replay=create_snapshot(imported,self.resolver.resolve(imported),self.root/"snapshots","stable")
        self.assertEqual(replay["replay"],"exact_replay"); self.assertEqual(disk,(self.root/"snapshots/stable.json").read_bytes())
        self.assertTrue(verify_snapshot(self.root/"snapshots/stable.json")["valid"])
        summary=collection_summary(snapshot,self.resolver)
        self.assertEqual((summary["total_owned_quantity"],summary["duplicate_count"],summary["acquisition_cost"]["known_total"]),(3,2,"3.75"))
        self.assertEqual(summary["acquisition_cost"]["missing_quantity"],0)
        with self.assertRaises(CollectionIntelligenceError):
            changed=dict(imported); changed["source_import_digest"]="different"
            create_snapshot(changed,self.resolver.resolve(changed),self.root/"snapshots","stable")
        self.assertEqual(before,(ROOT/"data/canonical/state.json").read_bytes())

    def test_deck_completion_policies_sideboard_excess_and_priorities(self):
        snapshot=self.snapshot()
        deck={"schema_version":"deck-requirement-v1","deck_id":"synthetic-one","format":"fixture",
              "version":"1","snapshot_date":"2026-08-01","acceptable_printing_policy":"any",
              "substitution_policy":"none","source":{"type":"repository_fixture"},
              "requirements":[{"card_id":self.card,"quantity":2,"section":"main"},
                              {"card_id":self.card,"quantity":2,"section":"sideboard"},
                              {"card_id":"magic.missing","quantity":1,"section":"main"}]}
        result=compare_deck(snapshot,deck,self.resolver)
        by_section={x["section"]:x for x in result["requirements"] if x["card_id"]==self.card}
        self.assertEqual(sum(x["owned_quantity"] for x in by_section.values()),3)
        self.assertEqual(result["partially_complete_cards"],1); self.assertTrue(result["unresolved_may_affect_result"])
        exact=dict(deck); exact["deck_id"]="synthetic-exact"; exact["requirements"]=[{
            "card_id":self.card,"printing_id":"magic.mb2.1.en","quantity":1,"section":"main",
            "acceptable_printing_policy":"exact"}]
        self.assertEqual(compare_deck(snapshot,exact,self.resolver)["requirements"][0]["missing_quantity"],1)
        report=acquisition_priorities([result,compare_deck(snapshot,{**deck,"deck_id":"synthetic-two"},self.resolver)])
        self.assertTrue(report["price_independent"]); self.assertEqual(report["priorities"][0]["components"]["shared_deck_points"],20)
        self.assertEqual(report,acquisition_priorities([result,compare_deck(snapshot,{**deck,"deck_id":"synthetic-two"},self.resolver)]))


class ProductionCollectionResolutionTests(unittest.TestCase):
    PRINTINGS = {
        "5c8d3bc4-32fc-5b26-84bf-9921e5884d43": ("02090581-61aa-4348-ad57-451be8ee91c2", "Ponder", "34"),
        "72783a15-4847-5448-8f1d-0c40379594d3": ("3d6fa57a-aa53-4b5c-b8af-a7612c823117", "Faithless Looting", "57"),
        "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade": ("dc0593c2-ccb4-4648-a592-c5bcd121dc72", "Greater Good", "207"),
    }

    @classmethod
    def setUpClass(cls):
        cls.resolver = CanonicalCollectionResolver("magic", ROOT / "data")

    def test_exact_promoted_printings_preserve_card_dimensions_and_provenance(self):
        protected = (ROOT / "data/canonical/state.json").read_bytes()
        result = self.resolver.resolve({"entries": [{"printing_id": pid, "quantity": 1,
            "language": "English", "finish": "nonfoil"} for pid in self.PRINTINGS]})
        self.assertEqual((len(self.resolver.cards), len(self.resolver.printings)), (399, 928))
        self.assertEqual(len(self.resolver.production_printing_ids), 913)
        for resolved in result["results"]:
            pid = resolved["printing_id"]
            card_id, name, collector_number = self.PRINTINGS[pid]
            self.assertEqual((resolved["status"], resolved["card_id"]), ("resolved", card_id))
            self.assertEqual(self.resolver.cards[card_id]["name"], name)
            printing = self.resolver.printings[pid]
            self.assertEqual((printing["set_id"], printing["collector_number"], printing["language"]),
                             ("mb2", collector_number, "English"))
            self.assertIn("nonfoil", printing["finish_ids"])
            self.assertNotIn("treatment_ids", printing)
            reference = resolved["canonical_reference"]
            self.assertEqual(reference["snapshot_id"], result["canonical_snapshot_id"])
            self.assertEqual(reference["printing"]["canonical_identity"], pid)
            self.assertEqual(reference["card"]["canonical_identity"], card_id)
            for entity in (reference["printing"], reference["card"]):
                self.assertTrue(entity["source_ids"])
                self.assertTrue(entity["evidence_reference_ids"])
                self.assertTrue(entity["promotion_references"][0]["audit_reference"]["sha256"])
                self.assertNotIn("review_artifact_digests", entity["promotion_references"][0])
        self.assertEqual(protected, (ROOT / "data/canonical/state.json").read_bytes())

    def test_external_identity_resolves_production_without_seed_name_fallback(self):
        pid = next(iter(self.PRINTINGS))
        scryfall_id = self.resolver.printings[pid]["identifiers"]["scryfallId"]
        results = self.resolver.resolve({"entries": [
            {"external_identifiers": {"scryfallId": scryfall_id}, "quantity": 1},
            {"external_identifiers": {"set_collector_number": "MB2:34"}, "quantity": 1},
            {"card_name": "Sol Ring", "quantity": 1},
        ]})["results"]
        self.assertEqual([result["printing_id"] for result in results[:2]], [pid, pid])
        self.assertEqual(results[2]["status"], "ambiguous")
        self.assertTrue(set(results[2]["candidate_printing_ids"]) & self.resolver.production_printing_ids)
        self.assertTrue(set(results[2]["candidate_printing_ids"]) - self.resolver.production_printing_ids)
        self.assertGreater(len(results[2]["candidate_printing_ids"]), 1)

    def test_known_dimension_and_identifier_conflicts_are_unresolved(self):
        pid = next(iter(self.PRINTINGS))
        other_pid = list(self.PRINTINGS)[1]
        other_scryfall_id = self.resolver.printings[other_pid]["identifiers"]["scryfallId"]
        for field, bad_value in (("card_id", self.PRINTINGS[other_pid][0]),
                                 ("card_name", "Faithless Looting"), ("set_code", "LEA"),
                                 ("collector_number", "57"), ("language", "fr"),
                                 ("finish", "foil"), ("treatment", "borderless"),
                                 ("external_identifiers", {"scryfallId": other_scryfall_id}),
                                 ("external_identifiers", {"unsupported_identity": "unknown-id"})):
            with self.subTest(field=field, bad_value=bad_value):
                result = self.resolver.resolve({"entries": [
                    {"printing_id": pid, "quantity": 1, field: bad_value}]})["results"][0]
                self.assertEqual(result["status"], "unresolved")
                self.assertTrue(result["dimension_conflicts"])
                self.assertEqual(result["candidate_printing_ids"], [pid])
                self.assertNotIn("printing_id", result)
                if field in {"card_id", "set_code", "collector_number", "treatment"}:
                    self.assertEqual(result["row"]["identity_constraints"][field], bad_value)

    def test_unknown_physical_attributes_remain_unknown(self):
        pid = next(iter(self.PRINTINGS))
        result = self.resolver.resolve({"entries": [{"printing_id": pid, "quantity": 1}]})["results"][0]
        self.assertEqual(result["status"], "resolved")
        self.assertIsNone(result["row"]["finish"])
        self.assertIsNone(result["row"]["language"])
        self.assertIn("finish", result["row"]["unknown_fields"])
        self.assertIn("language", result["row"]["unknown_fields"])

    def test_promoted_snapshot_replay_and_identity_drift_are_detected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            canonical = root / "data/canonical"
            shutil.copytree(ROOT / "data/canonical/games", canonical / "games")
            shutil.copyfile(ROOT / "data/canonical/state.json", canonical / "state.json")
            resolver = CanonicalCollectionResolver("magic", root / "data")
            query = CanonicalQueryEngine("magic", games_root=canonical / "games", data_root=root / "data")
            self.assertEqual(resolver.canonical_snapshot_id, query.snapshot().snapshot_id)
            self.assertEqual(resolver.canonical_digest, query.snapshot().snapshot_id.removeprefix("sha256:"))
            pid = next(iter(self.PRINTINGS))
            imported = {"schema_version": "collection-import-v1", "collection_id": "synthetic-pilot",
                        "source": {"type": "fixture", "name": "synthetic"}, "source_import_digest": "synthetic",
                        "entries": [{"printing_id": pid, "quantity": 1}]}
            resolution = resolver.resolve(imported)
            snapshot = create_snapshot(imported, resolution, root / "snapshots", "immutable")
            original = (root / "snapshots/immutable.json").read_bytes()
            self.assertEqual(snapshot["canonical_snapshot_id"], query.snapshot().snapshot_id)
            replay = create_snapshot(imported, resolution, root / "snapshots", "immutable")
            self.assertEqual(replay["replay"], "exact_replay")
            self.assertEqual(original, (root / "snapshots/immutable.json").read_bytes())
            state = json.loads((canonical / "state.json").read_bytes())
            state["printing"][pid]["values"]["language"] = "French"
            (canonical / "state.json").write_text(json.dumps(state))
            changed = CanonicalCollectionResolver("magic", root / "data")
            self.assertNotEqual(resolver.canonical_digest, changed.canonical_digest)
            with self.assertRaises(CollectionIntelligenceError):
                create_snapshot(imported, changed.resolve(imported), root / "snapshots", "immutable")
            state["printing"][pid]["values"]["language"] = "English"
            state["printing"][pid]["provenance"]["artifact_identifier"] = "changed-source"
            (canonical / "state.json").write_text(json.dumps(state))
            changed_source = CanonicalCollectionResolver("magic", root / "data")
            self.assertNotEqual(resolver.canonical_digest, changed_source.canonical_digest)
            state["printing"][pid]["superseded_status"] = True
            (canonical / "state.json").write_text(json.dumps(state))
            superseded = CanonicalCollectionResolver("magic", root / "data")
            self.assertEqual(superseded.resolve(imported)["results"][0]["status"], "unresolved")

    def test_promoted_state_is_not_reinterpreted_as_another_game(self):
        with self.assertRaisesRegex(CollectionIntelligenceError, "game scope"):
            CanonicalCollectionResolver("unrelated-game", ROOT / "data")


if __name__ == "__main__": unittest.main()
