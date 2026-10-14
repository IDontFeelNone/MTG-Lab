"""Production-backed mechanics regressions; derived evidence never promotes facts."""
import copy
from contextlib import redirect_stdout
from decimal import Decimal, localcontext
import hashlib
from io import StringIO
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import CardValueExplanationEngine, MechanicalCardIntelligence
from card_intelligence.cli import main
from card_intelligence.mechanics import MechanicalEvidenceError, _field, content_identity, stable_json
from scripts.build_mechanical_cohort import build_artifacts
from scripts.build_two_card_demo import build_artifacts as two_card_artifacts


from historical_catalog import historical_repository

# This module replays the retained original catalog, not the current catalog.
ROOT = historical_repository()
DATA = ROOT / "data"
REVIEW = DATA / "review/mechanical-card-cohort"
SOL = "6ad8011d-3471-4369-9d68-b264cc027487"
COUNTER = "cc187110-1148-4090-bbb8-e205694a39f5"
LILIANA = "150be0e9-a65f-4209-bdea-8cf4c691d217"
THERE = "a865ed92-d1aa-416a-b8cd-d4cef11b0fef"


def inventory():
    files = [p for p in DATA.rglob("*") if p.is_file() and not p.is_relative_to(REVIEW)]
    files.extend(ROOT / p for p in ("docs/ARCHITECTURE.md", "docs/DECISIONS.md"))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


class MechanicalCardIntelligenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from historical_catalog import bind_replay_builder
        from scripts import build_mechanical_cohort
        bind_replay_builder(cls, build_mechanical_cohort)
        from scripts import build_two_card_demo
        bind_replay_builder(cls, build_two_card_demo)
        cls.protected = inventory()
        cls.engine = MechanicalCardIntelligence(DATA)
        cls.canonical = json.loads((DATA / "canonical/state.json").read_bytes())
        cls.rows = json.loads((DATA / cls.engine.source["retained_source_reference"].removeprefix("data/")).read_bytes())
        cls.by_id = {r["oracle_id"]: r for r in cls.rows}
        cls.dossiers = {i: cls.engine.dossier(i).to_dict() for i in cls.engine.cards}
        cls.report = cls.engine.cohort_report()

    def test_source_card_census_exact_identities_and_excluded_row(self):
        r = self.engine.reconciliation
        self.assertEqual(set(self.engine.cards), set(self.canonical["card"]))
        self.assertEqual((r["source_row_count"], r["production_card_count"], r["uniquely_mapped_card_count"]), (385, 384, 384))
        self.assertEqual(r["excluded_nonproduction_query_card_count"], 15)
        self.assertEqual(r["missing_canonical_card_ids"], [])
        self.assertEqual(r["ambiguous_canonical_card_ids"], [])
        self.assertEqual(r["excluded_source_row_count"], 1)
        self.assertEqual(r["excluded_source_rows"][0]["name"], "Essence of Ajani")
        self.assertEqual(r["excluded_source_rows"][0]["oracle_id"], "115e3d3a-1625-4cb7-b988-6addcbac6713")
        for invalid in ("Sol Ring", "magic.sol-ring", "Counterspell", "not-a-card"):
            with self.assertRaises(MechanicalEvidenceError): self.engine.dossier(invalid)
        for identity, d in self.dossiers.items():
            self.assertEqual(d["card_identity"]["card_id"], self.by_id[identity]["oracle_id"])
            self.assertEqual(d["card_identity"]["name"], self.canonical["card"][identity]["values"]["name"])
            self.assertEqual(d["source"]["provider_record_id"], self.by_id[identity]["id"])
        self.assertEqual(len(self.report["cards_without_canonical_source_printing"]), 5)

    def test_every_mechanical_value_matches_retained_field_pointer(self):
        for identity, d in self.dossiers.items():
            row = self.by_id[identity]
            sets = [d["fields"], *[f["fields"] for f in d["faces"]]]
            for fields in sets:
                for name, field in fields.items():
                    value = row
                    try:
                        for part in field["source_pointer"][1:].split("/"):
                            value = value[int(part)] if isinstance(value, list) else value[part]
                    except KeyError:
                        self.assertEqual(field["status"], "unknown")
                        self.assertEqual(field["reason"], "field_absent")
                        self.assertNotIn("value", field)
                        continue
                    self.assertEqual(field["status"], "known")
                    expected = format(Decimal(str(value)).normalize(), "f") if name == "mana_value" else value
                    self.assertEqual(field["value"], expected)
            self.assertEqual(d["source"]["record_content_identity"], content_identity(row))

    def test_faces_keep_order_text_and_unknown_mana_values_without_inheritance(self):
        l = self.dossiers[LILIANA]
        self.assertEqual(l["fields"]["oracle_text"]["status"], "unknown")
        self.assertEqual(l["fields"]["colors"]["status"], "unknown")
        self.assertEqual([f["fields"]["name"]["value"] for f in l["faces"]],
                         ["Liliana's Other Contract", "Liliana's Undead Minion"])
        self.assertEqual(l["faces"][1]["fields"]["colors"]["value"], [])
        self.assertEqual(l["faces"][1]["fields"]["mana_cost"]["value"], "")
        self.assertEqual(l["faces"][1]["fields"]["loyalty"]["value"], "5")
        t = self.dossiers[THERE]
        self.assertEqual(len(t["faces"]), 3)
        self.assertEqual([f["fields"]["name"]["value"] for f in t["faces"]], ["There", "They're", "Their"])
        self.assertEqual(t["fields"]["mana_value"]["value"], "6")
        for d in self.dossiers.values():
            for face in d["faces"]:
                self.assertEqual(face["fields"]["mana_value"]["status"], "unknown")
                self.assertEqual(face["fields"]["color_identity"]["status"], "unknown")
                self.assertEqual(face["fields"]["keywords"]["status"], "unknown")

    def test_nonstandard_type_labels_stay_unresolved(self):
        cases = {d["card_identity"]["name"]: d for d in self.dossiers.values()}
        licid = cases["Flanking Licid"]["type_labels"]
        self.assertEqual(licid["status"], "unresolved")
        self.assertEqual(licid["components"][0]["card_types"], [])
        self.assertEqual(licid["components"][0]["unclassified_tokens"], ["Licid", "Summon"])
        orb = cases["Orb of Origin"]["type_labels"]
        self.assertEqual(orb["status"], "unresolved")
        self.assertEqual(orb["components"][0]["card_types"], ["Artifact"])
        self.assertEqual(orb["components"][0]["unclassified_tokens"], ["Poly"])
        self.assertEqual(self.report["fully_classified_type_card_count"], 382)

    def test_aggregate_denominators_and_complete_face_aware_coverage(self):
        r = self.report
        self.assertEqual(r["denominators"]["canonical_cards"], 384)
        self.assertEqual(r["denominators"]["explicit_provider_faces"], 11)
        self.assertEqual(r["denominators"]["represented_source_components"], 390)
        self.assertEqual(r["multi_faced_card_count"], 5)
        self.assertEqual(r["coverage"]["cards_with_all_represented_oracle_text"], 384)
        self.assertEqual(r["coverage"]["card_fields"]["oracle_text"]["known"], 379)
        self.assertEqual(r["coverage"]["explicit_face_fields"]["oracle_text"]["known"], 11)
        self.assertEqual(r["coverage"]["explicit_face_fields"]["mana_value"]["unknown"], 11)
        self.assertEqual(r["coverage"]["card_fields"]["printed_text"]["unknown"], 384)
        self.assertEqual(sum(x["card_count"] for x in r["mana_value_distribution"]), 384)
        self.assertEqual(sum(r["color_identity_distribution"].values()), 384)
        self.assertEqual(r["card_type_memberships"]["Instant"], 52)  # triple split is one vote
        self.assertEqual(r["card_type_memberships"]["Creature"], 147)
        self.assertEqual(r["card_type_memberships"]["Land"], 41)
        self.assertEqual(r["keyword_card_frequencies"]["Flying"], 15)
        self.assertGreater(sum(r["card_type_memberships"].values()), 384)  # overlapping memberships

    def test_empty_missing_null_and_malformed_values_remain_distinct(self):
        for key, value in (("mana_cost", ""), ("colors", []), ("keywords", [])):
            self.assertEqual(_field({key: value}, key), {"source_pointer": "/" + key, "status": "known", "value": value})
        self.assertEqual(_field({}, "oracle_text")["reason"], "field_absent")
        self.assertEqual(_field({"oracle_text": None}, "oracle_text")["reason"], "provider_null")
        for value in (None, True, "2", -1, float("inf")):
            self.assertNotEqual(_field({"cmc": value}, "mana_value")["status"], "known")
        self.assertEqual(_field({"cmc": 0}, "mana_value")["value"], "0")
        self.assertEqual(_field({"colors": ["Q"]}, "colors")["status"], "unresolved")

    def test_mana_value_encoding_is_independent_of_decimal_context(self):
        with localcontext() as context:
            context.prec = 1
            self.assertEqual(_field({"cmc": 2.5}, "mana_value")["value"], "2.5")
            self.assertEqual(_field({"cmc": 0.125}, "mana_value")["value"], "0.125")

    def _fixture(self, temporary, change=None):
        data = Path(temporary) / "data"
        source = data / "market/acquisitions" / self.engine.source["acquisition_run_id"]
        shutil.copytree(DATA / "market/acquisitions" / self.engine.source["acquisition_run_id"], source)
        if change:
            rows = copy.deepcopy(self.rows); change(rows)
            (source / "source-mb2.json").write_text(json.dumps(rows), encoding="utf-8")
            manifest = json.loads((source / "manifest.json").read_bytes())
            report = json.loads((source / "dry-run-report.json").read_bytes())
            manifest["mb2_record_count"] = report["mb2_record_count"] = len(rows)
            (source / "dry-run-report.json").write_text(json.dumps(report), encoding="utf-8")
            for name in manifest["files"]:
                raw = (source / name).read_bytes()
                manifest["files"][name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
            body = {k: v for k, v in manifest.items() if k != "manifest_content_sha256"}
            raw = (json.dumps(body, indent=2, sort_keys=True, separators=(",", ": ")) + "\n").encode()
            manifest["manifest_content_sha256"] = hashlib.sha256(raw).hexdigest()
            (source / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return data, source

    def test_missing_and_ambiguous_identity_bindings_never_select_a_row(self):
        def change(rows):
            rows[:] = [r for r in rows if r["oracle_id"] != SOL]
            duplicate = copy.deepcopy(next(r for r in rows if r["oracle_id"] == COUNTER))
            duplicate["id"] = "synthetic-conflicting-printing"
            rows.append(duplicate)
        with tempfile.TemporaryDirectory() as temporary:
            data, _ = self._fixture(temporary, change)
            with patch("card_intelligence.mechanics.CanonicalQueryEngine", return_value=self.engine.query):
                engine = MechanicalCardIntelligence(data)
            self.assertEqual(engine.reconciliation["missing_canonical_card_ids"], [SOL])
            self.assertEqual(engine.reconciliation["ambiguous_canonical_card_ids"], [COUNTER])
            for identity, state in ((SOL, "missing"), (COUNTER, "ambiguous")):
                d = engine.dossier(identity).to_dict()
                self.assertEqual(d["source"]["resolution"], state)
                self.assertEqual(d["fields"]["oracle_text"]["reason"], "source_binding_" + state)
                self.assertNotIn("value", d["fields"]["oracle_text"])

    def test_source_digest_failure_and_snapshot_relocation(self):
        with tempfile.TemporaryDirectory() as temporary:
            data, source = self._fixture(temporary)
            with patch("card_intelligence.mechanics.CanonicalQueryEngine", return_value=self.engine.query):
                engine = MechanicalCardIntelligence(data)
                self.assertEqual(engine.dossier(SOL).to_json(), self.engine.dossier(SOL).to_json())
                self.assertEqual(engine.reasoning_context(THERE).to_json(), self.engine.reasoning_context(THERE).to_json())
                p = source / "source-mb2.json"; p.write_bytes(p.read_bytes() + b" ")
                with self.assertRaisesRegex(MechanicalEvidenceError, "integrity mismatch"):
                    MechanicalCardIntelligence(data)

    def test_immutable_deterministic_dossier_and_existing_reasoning_envelope(self):
        d = self.engine.dossier(THERE)
        payload = d.to_dict(); expected = payload.pop("dossier_id")
        self.assertEqual(content_identity(payload), expected)
        self.assertEqual(d.to_json(), self.engine.dossier(THERE).to_json())
        with self.assertRaises(TypeError): d.payload["fields"]["oracle_text"]["status"] = "known"
        c = self.engine.reasoning_context(THERE).to_dict()
        hashed = {"canonical_snapshot_id": c["canonical_snapshot_id"], "analytics_snapshot_id": c["analytics_snapshot_id"],
            "request": c["normalized_request"], "entities": c["entities"], "relationships": c["relationships"],
            "analytics": c["analytics_results"], "provenance": c["provenance_references"], "evidence": c["evidence_references"],
            "omitted": c["omitted_item_counts"], "truncation": c["truncation"], "warnings": c["warnings"]}
        self.assertEqual(c["context_id"], content_identity(hashed))
        self.assertEqual(c["canonical_snapshot_id"], self.engine.snapshot_id)
        self.assertTrue(c["evidence_references"])
        self.assertIsNone(c["analytics_snapshot_id"])
        self.assertEqual(c["analytics_results"][0]["projection"], "mechanical_card_evidence_manual_handoff")
        self.assertLessEqual(len(stable_json(c).encode()), 65536)
        with patch("card_intelligence.mechanics.MAXIMUM_BYTES", 100):
            with self.assertRaises(MechanicalEvidenceError): self.engine.dossier(SOL)

    def test_cli_and_existing_card_intelligence_compatibility(self):
        for argv, expected in ((["mechanical", "--card-id", SOL], 0),
                               (["mechanical", "--card-id", "magic.sol-ring"], 2),
                               (["mechanical", "--card-id", COUNTER, "--reasoning-context"], 0)):
            output = StringIO()
            with patch("card_intelligence.cli.MechanicalCardIntelligence", return_value=self.engine), redirect_stdout(output):
                self.assertEqual(main(argv), expected)
            self.assertIn("schema_version", json.loads(output.getvalue()))
        old = CardValueExplanationEngine(DATA).explain(card_id=SOL, include_demand_evidence=True)
        self.assertEqual(self.dossiers[SOL]["fields"]["oracle_text"]["value"], old["evidence_sections"]["rules"]["oracle_text"])
        retained = DATA / "review/two-card-chatgpt-demo"
        self.assertEqual(two_card_artifacts(), {p.name: p.read_bytes() for p in retained.iterdir() if p.is_file()})

    def test_no_functional_role_synergy_rules_or_competitive_claims(self):
        for d in self.dossiers.values():
            self.assertIn("functional_role_classification", d["unsupported_dimensions"])
            self.assertIn("synergy_or_combo_correctness", d["unsupported_dimensions"])
            self.assertIn("verified_rules_interactions", d["unsupported_dimensions"])
            for field in ("functional_roles", "synergies", "combo_results", "rankings", "power_score", "recommendation"):
                self.assertNotIn(field, d)
        self.assertIn("not complete set", self.report["reconciliation"]["scope"])

    def test_retained_cohort_replay_and_production_nonmutation(self):
        artifacts = build_artifacts()
        self.assertEqual(len(artifacts), 11)
        self.assertEqual(artifacts, {p.name: p.read_bytes() for p in REVIEW.iterdir() if p.is_file()})
        manifest = json.loads(artifacts["manifest.json"])
        self.assertEqual(len(manifest["dossiers"]), 384)
        lines = artifacts["dossiers.jsonl"].splitlines()
        identities = [json.loads(line)["card_identity"]["card_id"] for line in lines]
        self.assertEqual(identities, sorted(self.canonical["card"]))
        for name, meta in manifest["files"].items():
            self.assertEqual(meta["sha256"], hashlib.sha256(artifacts[name]).hexdigest())
        self.assertEqual(self.protected, inventory())


if __name__ == "__main__":
    unittest.main()
