import json
import tempfile
import unittest
from pathlib import Path

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


if __name__ == "__main__": unittest.main()
