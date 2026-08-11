import hashlib
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from jsonschema import Draft202012Validator, FormatChecker

from card_intelligence import CardKnowledgeQuery, CardValueExplanationEngine, KnowledgeRepository
from card_intelligence.cli import main as explanation_cli
from card_intelligence.demand_review import DemandEvidenceError, load_reviewed_demand

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data/card_intelligence/demand/phase-142/scryfall-edhrec-rank.json"
DECK_USAGE_EVIDENCE = ROOT / "data/card_intelligence/demand/phase-143/mtgjson-decks.json"
NAMES = ["Brainstorm", "Command Tower", "Counterspell", "Goblin Charbelcher", "Goblin King",
         "Sol Ring", "Swords to Plowshares", "Treasure Cruise", "Walking Ballista", "Wishclaw Talisman"]


def tree_digest(path):
    digest = hashlib.sha256(); base = ROOT / path
    for item in sorted(x for x in base.rglob("*") if x.is_file()):
        digest.update(item.relative_to(base).as_posix().encode() + b"\0"); digest.update(item.read_bytes())
    return digest.hexdigest()


@contextmanager
def data_without_phase143_usage():
    """Present the production repository with only the later opt-in artifact absent."""
    with tempfile.TemporaryDirectory() as temporary:
        data = Path(temporary) / "data"
        shutil.copytree(ROOT / "data", data, ignore=lambda path, names: (
            {"phase-143"} if Path(path) == ROOT / "data/card_intelligence/demand" else set()))
        yield data


class Phase142DemandEvidenceTests(unittest.TestCase):
    def test_bounded_reviewed_projection_digest_and_identity(self):
        document = load_reviewed_demand(EVIDENCE)
        schema = json.loads((ROOT / "src/schemas/v1/card-demand-evidence.schema.json").read_text())
        self.assertEqual([], list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(document)))
        self.assertEqual([x["card_name"] for x in document["records"]], NAMES)
        self.assertEqual({x["provider"] for x in document["records"]}, {"scryfall"})
        self.assertEqual({x["metric"] for x in document["records"]}, {"edhrec_rank"})
        self.assertEqual(len({x["card_id"] for x in document["records"]}), 10)

    def test_malformed_duplicate_unknown_conflicting_and_omitted_fields_fail(self):
        original = json.loads(EVIDENCE.read_text())
        mutations = []
        for transform in (lambda d: d["records"][0].pop("rank"),
                          lambda d: d["records"].__setitem__(1, dict(d["records"][0])),
                          lambda d: d["records"][0].__setitem__("card_name", "Unknown Card"),
                          lambda d: d["records"][0].__setitem__("provider", "other")):
            value = json.loads(json.dumps(original)); transform(value); mutations.append(value)
        with tempfile.TemporaryDirectory() as temporary:
            for index, value in enumerate(mutations):
                path = Path(temporary) / f"{index}.json"; path.write_text(json.dumps(value))
                with self.assertRaises(DemandEvidenceError): load_reviewed_demand(path)

    def test_append_only_supersession_and_query(self):
        repo = KnowledgeRepository(ROOT / "data/knowledge"); facts = repo.validate()
        phase142 = [x for x in facts if x.fact_id.startswith("phase142-")]
        self.assertEqual(len(phase142), 10)
        self.assertTrue(all(x.kind == "demand" and x.value_status == "known" for x in phase142))
        self.assertEqual({x.supersedes[0] for x in phase142},
                         {x.fact_id for x in facts if x.fact_id.startswith("phase132-") and x.kind == "demand"})
        query = CardKnowledgeQuery(repo)
        for fact in phase142:
            active = query.by_kind("magic", fact.card_id, "demand", include_superseded=False)
            # MTGJSON deck inclusion is an independent demand dimension; selecting
            # the Scryfall predicate still returns the unchanged Phase 142 chain.
            self.assertEqual([x["fact_id"] for x in active["facts"]
                              if x["predicate"] == "value_driver.demand"], [fact.fact_id])

    def test_explanation_v3_is_literal_and_provider_specific(self):
        # Phase 142's version contract applies when the later Phase 143 artifact is absent.
        with data_without_phase143_usage() as data:
            engine = CardValueExplanationEngine(data)
            document = engine.explain(name="Sol Ring", include_demand_evidence=True)
            self.assertEqual(engine.explain(name="Sol Ring")["schema_version"],
                             "card-value-explanation-v1")
            self.assertEqual(engine.explain(name="Sol Ring", include_observed_prices=True)
                             ["schema_version"], "card-value-explanation-v2")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                result = explanation_cli(["--data-root", str(data), "explain", "Sol Ring",
                                          "--include-demand-evidence"])
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(stdout.getvalue()), document)
        self.assertEqual(document["schema_version"], "card-value-explanation-v3")
        evidence = document["evidence_sections"]["demand_usage_evidence"]
        self.assertEqual(evidence["provider"], "scryfall"); self.assertEqual(evidence["fact_count"], 1)
        self.assertEqual(evidence["facts"][0]["exact_retained_value"]["rank"], 1)
        serialized = json.dumps(document, sort_keys=True).lower()
        for forbidden in ('"demand_score"', '"recommendation" :', '"price_prediction"', '"scarcity_inference"'):
            self.assertNotIn(forbidden, serialized)

    def test_retained_phase143_usage_upgrades_v3_to_v4_without_changing_demand(self):
        if not DECK_USAGE_EVIDENCE.exists():
            self.skipTest("retained Phase 143 artifact is supplied by PR #149")

        engine = CardValueExplanationEngine(ROOT / "data")
        v4 = engine.explain(name="Sol Ring", include_demand_evidence=True)
        self.assertEqual(v4["schema_version"], "card-value-explanation-v4")
        demand = v4["evidence_sections"]["demand_usage_evidence"]
        self.assertTrue(demand["provider_isolation"])
        self.assertEqual((demand["provider"], demand["fact_count"]), ("scryfall", 1))
        self.assertEqual(demand["facts"][0]["exact_retained_value"]["rank"], 1)
        self.assertEqual(v4["evidence_sections"]["deck_usage_evidence"]["provider"], "mtgjson")

        stdout = io.StringIO()
        with redirect_stdout(stdout):
            result = explanation_cli(["--data-root", str(ROOT / "data"), "explain", "Sol Ring",
                                      "--include-demand-evidence"])
        self.assertEqual(result, 0)
        cli_document = json.loads(stdout.getvalue())
        self.assertEqual(cli_document, v4)

    def test_deterministic_serialization_and_protected_boundaries(self):
        first = CardValueExplanationEngine(ROOT / "data").explain(name="Brainstorm", include_demand_evidence=True)
        second = CardValueExplanationEngine(ROOT / "data").explain(name="Brainstorm", include_demand_evidence=True)
        self.assertEqual(first, second)
        expected = {"data/canonical": "e3fa0240c17516cfd64e92e17cefcab92a55be8a5d27edb2df439c21a0068e19",
                    "data/market/observations": "34c880d24b3eb6251ce513ad53d682ee5ee1ed11554ce3f2ba8cf7287a5269c9",
                    "data/market/imports": "7daaeb8a031a10c1f4143026a0f57c3873ef3cbbd1500674b6e0b7fdb7a3e0df"}
        for path, identity in expected.items(): self.assertEqual(tree_digest(path), identity)


if __name__ == "__main__":
    unittest.main()
