"""Independently replay the two-Card artifacts against retained production bytes."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"
DEMO = DATA / "review/two-card-chatgpt-demo"
TARGETS = {
    "sol-ring": ("6ad8011d-3471-4369-9d68-b264cc027487", "Sol Ring"),
    "counterspell": ("cc187110-1148-4090-bbb8-e205694a39f5", "Counterspell"),
}


def read_json(path):
    return json.loads(path.read_bytes())


class TwoCardRetainedEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state = read_json(DATA / "canonical/state.json")
        cls.dossiers = {slug: read_json(DEMO / f"{slug}.dossier.json")
                        for slug in TARGETS}
        cls.acquisitions = {}
        for path in sorted((DATA / "market/acquisitions").glob("*/manifest.json")):
            manifest = read_json(path)
            records = read_json(path.parent / "source-mb2.json")
            cls.acquisitions[manifest["acquisition_run_id"]] = (
                manifest, {record["id"]: record for record in records})
        cls.rank = read_json(DATA / "card_intelligence/demand/phase-142/scryfall-edhrec-rank.json")
        cls.decks = read_json(DATA / "card_intelligence/demand/phase-143/mtgjson-decks.json")

    def test_all_eight_prices_replay_exact_retained_provider_printings(self):
        observation_ids = set()
        for slug, (card_id, name) in TARGETS.items():
            dossier = self.dossiers[slug]
            observations = dossier["evidence_sections"]["observed_price_evidence"]["observations"]
            self.assertEqual(len(observations), 4)
            for observation in observations:
                with self.subTest(card=name, observation=observation["observation_id"]):
                    manifest, source_records = self.acquisitions[observation["acquisition_run_id"]]
                    source = source_records[observation["provider_record_id"]]
                    printing = self.state["printing"][observation["canonical_printing_id"]]["values"]
                    self.assertEqual(observation["canonical_card_id"], card_id)
                    self.assertEqual(printing["card_id"], card_id)
                    self.assertEqual(source["oracle_id"], card_id)
                    self.assertEqual(source["name"], name)
                    self.assertEqual(printing["identifiers"]["scryfallId"], source["id"])
                    self.assertEqual(observation["collector_number"], source["collector_number"])
                    self.assertEqual(printing["collector_number"], source["collector_number"])
                    self.assertEqual(observation["set_code"].casefold(), source["set"])
                    self.assertEqual(observation["language"], source["lang"])
                    self.assertIn(observation["finish"], source["finishes"])
                    price_field = {"foil": "usd_foil", "nonfoil": "usd"}[observation["finish"]]
                    self.assertEqual(observation["price"],
                                     {"state": "known", "amount": source["prices"][price_field]})
                    self.assertEqual(observation["currency"], "USD")
                    self.assertEqual(observation["price_type"], "market")
                    self.assertEqual(observation["provider"], manifest["provider"])
                    self.assertEqual(observation["source_timestamp"], manifest["source_observed_at"])
                    self.assertEqual(observation["retrieval_timestamp"], manifest["retrieved_at"])
                    self.assertNotIn(observation["observation_id"], observation_ids)
                    observation_ids.add(observation["observation_id"])
        self.assertEqual(len(observation_ids), 8)

    def test_independent_demand_signals_match_provider_projections(self):
        ranks = {record["card_id"]: record for record in self.rank["records"]}
        decks = {record["card_id"]: record for record in self.decks["records"]}
        for slug, (card_id, name) in TARGETS.items():
            sections = self.dossiers[slug]["evidence_sections"]
            demand = sections["demand_usage_evidence"]
            usage = sections["deck_usage_evidence"]
            with self.subTest(card=name):
                self.assertTrue(demand["provider_isolation"])
                self.assertEqual(demand["provider"], self.rank["provider"])
                self.assertEqual(demand["fact_count"], 1)
                rank = demand["facts"][0]
                retained = ranks[card_id]
                self.assertEqual(rank["dataset_timestamp"], retained["dataset_timestamp"])
                self.assertEqual(rank["exact_retained_value"]["rank"], retained["rank"])
                self.assertEqual(rank["exact_retained_value"]["canonical_oracle_id"], card_id)
                self.assertEqual(rank["exact_retained_value"]["provider_printing_id"],
                                 retained["provider_printing_id"])
                self.assertEqual(rank["exact_retained_value"]["metric"], "edhrec_rank")
                retained_usage = decks[card_id]
                self.assertEqual(usage["provider"], self.decks["provider"])
                self.assertNotEqual(usage["provider"], demand["provider"])
                self.assertEqual(usage["provider_native_metric"], retained_usage["metric"])
                for field in ("numerator", "denominator", "dataset_timestamp", "formats"):
                    self.assertEqual(usage[field], retained_usage[field])
                associations = retained_usage["deck_associations"]
                self.assertEqual(usage["numerator"], len(associations))
                self.assertEqual(usage["literal_deck_associations"],
                                 sorted(associations, key=lambda record: record["source_record_identity"])[:5])
                self.assertEqual(self.dossiers[slug]["omitted_item_counts"]["literal_deck_associations"],
                                 len(associations) - len(usage["literal_deck_associations"]))
                self.assertEqual(usage["population_semantics"], self.decks["population_semantics"])

    def test_rules_facts_and_sampled_printings_preserve_canonical_relationships(self):
        for slug, (card_id, name) in TARGETS.items():
            dossier = self.dossiers[slug]
            with self.subTest(card=name):
                self.assertEqual(dossier["card_identity"]["card_id"], card_id)
                self.assertEqual(dossier["canonical_entity"]["canonical_values"],
                                 self.state["card"][card_id]["values"])
                facts = [read_json(path) for path in
                         (DATA / "knowledge/facts/magic" / card_id).glob("*.json")]
                superseded = {old for fact in facts for old in fact["supersedes"]}
                active = {fact["fact_id"]: fact for fact in facts
                          if fact["fact_id"] not in superseded}
                inventory = dossier["provenance"]["facts"]
                self.assertEqual({item["fact_id"] for item in inventory}, set(active))
                self.assertEqual(len(active), 11)
                for item in inventory:
                    fact = active[item["fact_id"]]
                    self.assertEqual(fact["subject"]["card_id"], card_id)
                    for field in ("predicate", "effective_at", "recorded_at"):
                        self.assertEqual(item[field], fact[field])
                    self.assertEqual(item["value_status"], fact["value"]["status"])
                by_predicate = {fact["predicate"]: fact for fact in active.values()}
                rules = dossier["evidence_sections"]["rules"]
                self.assertEqual(rules["oracle_text"],
                                 by_predicate["mechanical.oracle_text"]["value"]["data"]["oracle_text"])
                self.assertEqual(rules["legality"], by_predicate["format.legalities"]["value"]["data"])
                for role in rules["mechanical_roles"]:
                    self.assertEqual(role["evidence"], by_predicate[role["predicate"]]["value"]["data"])
                printings = dossier["evidence_sections"]["printing_identities"]
                self.assertEqual(len(printings), 5)
                for printing in printings:
                    self.assertEqual(printing, self.state["printing"][printing["uuid"]]["values"])
                    self.assertEqual(printing["card_id"], card_id)
                observed_ids = {observation["canonical_printing_id"] for observation in
                                dossier["evidence_sections"]["observed_price_evidence"]["observations"]}
                self.assertTrue(observed_ids <= {printing["uuid"] for printing in printings})

    def test_source_integrity_distinguishes_retained_bytes_from_upstream_assertions(self):
        for dossier in self.dossiers.values():
            for acquisition in dossier["input_integrity"]["market_acquisitions"]:
                manifest, _ = self.acquisitions[acquisition["acquisition_run_id"]]
                reference = acquisition["retained_source"]
                source_bytes = (ROOT / reference["reference"]).read_bytes()
                retained_digest = hashlib.sha256(source_bytes).hexdigest()
                self.assertEqual(reference["retained_bytes_sha256"], retained_digest)
                self.assertEqual(retained_digest, manifest["files"]["source-mb2.json"]["sha256"])
                self.assertEqual(acquisition["provider_source_sha256"], manifest["provider_source_sha256"])
                self.assertNotEqual(retained_digest, acquisition["provider_source_sha256"])
                self.assertEqual(acquisition["normalized_sha256"], manifest["normalized_sha256"])
                self.assertIn("not_retained", acquisition["original_bulk_source_bytes"])
            providers = {item["provider"]: item for item in dossier["input_integrity"]["demand_providers"]}
            for document in (self.rank, self.decks):
                source = providers[document["provider"]]
                reference = source["retained_projection"]
                self.assertEqual(reference["retained_bytes_sha256"],
                                 hashlib.sha256((ROOT / reference["reference"]).read_bytes()).hexdigest())
                self.assertEqual(source["upstream_source_sha256"], document["source_sha256"])
                self.assertEqual(source["projection_records_sha256"], document["records_sha256"])
                self.assertEqual(source["license_considerations"], document["license_considerations"])
                self.assertIn("not_retained", source["original_source_bytes"])
            printing_source = dossier["input_integrity"]["printing_provider"]
            manifest = read_json(DATA / "evidence/phase-135/mtgjson-pilot-30786023976-1/manifest.json")
            self.assertEqual(printing_source["retained_source"]["retained_bytes_sha256"],
                             manifest["normalized_projection_sha256"])
            self.assertEqual(printing_source["upstream_source_sha256"], manifest["source_sha256"])
            self.assertEqual(printing_source["license"], manifest["license"])


if __name__ == "__main__":
    unittest.main()
