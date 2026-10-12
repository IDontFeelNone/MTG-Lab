"""Regressions for the bounded retained-evidence manual ChatGPT demonstration."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_two_card_demo import TARGETS, build_artifacts
from scripts.card_dossier import (CardEvidenceDossierBuilder, MAXIMUM_BYTES,
                                 content_identity, render_explanation)
from reasoning import ReasoningContextResult


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "data/review/two-card-chatgpt-demo"


def protected_inventory():
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for directory in ("data/canonical", "data/knowledge", "data/market/observations",
                              "data/market/imports", "data/market/acquisitions", "data/audit")
            for p in (ROOT / directory).rglob("*") if p.is_file()}


class TwoCardDossierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protected_before = protected_inventory()
        cls.builder = CardEvidenceDossierBuilder(ROOT / "data")
        cls.dossiers = {slug: cls.builder.build(card_id) for slug, card_id, _ in TARGETS}

    def test_exact_production_identities_and_rejected_name_seed_paths(self):
        self.assertEqual(len(self.dossiers), 2)
        for slug, card_id, name in TARGETS:
            dossier = self.dossiers[slug].to_dict()
            self.assertEqual(dossier["card_identity"], {"game_id": "magic", "card_id": card_id, "name": name})
            self.assertEqual(dossier["canonical_entity"]["canonical_identity"], card_id)
            self.assertEqual(dossier["canonical_entity"]["canonical_values"]["card_reference"], card_id)
        for unsupported in ("Sol Ring", "Counterspell", "magic.sol-ring", "magic.counterspell", ""):
            with self.assertRaisesRegex(ValueError, "exact production Card ID"):
                self.builder.build(unsupported)

    def test_promoted_lineage_sources_snapshots_and_exact_reference_preservation(self):
        for dossier in self.dossiers.values():
            d = dossier.to_dict()
            card_id = d["card_identity"]["card_id"]
            raw = self.builder.engine.cards[card_id]
            provenance = d["canonical_entity"]["provenance_summary"]
            self.assertEqual(provenance["record_provenance"], raw["provenance"])
            self.assertEqual([a["id"] for a in provenance["evidence_assertions"]], raw["evidence_references"])
            self.assertEqual(dossier.reasoning_context.canonical_snapshot_id,
                             d["snapshots"]["canonical_query_snapshot_id"])
            self.assertEqual(d["snapshots"]["canonical_state"]["retained_bytes_sha256"],
                             hashlib.sha256((ROOT / "data/canonical/state.json").read_bytes()).hexdigest())
            self.assertNotEqual(dossier.reasoning_context.canonical_snapshot_id,
                                "sha256:" + d["snapshots"]["canonical_state"]["retained_bytes_sha256"])
            self.assertTrue(dossier.reasoning_context.evidence_references)
            for audit in provenance["promotion_history"]:
                ref = audit["audit_reference"]
                self.assertEqual(ref["sha256"], hashlib.sha256((ROOT / "data" / ref["relative_path"]).read_bytes()).hexdigest())

    def test_complete_market_history_provider_isolation_and_explicit_omissions(self):
        for slug, printing_count, numerator in (("sol-ring", 136, 241), ("counterspell", 84, 63)):
            d = self.dossiers[slug].to_dict()
            sections = d["evidence_sections"]
            self.assertEqual(len(sections["observed_price_evidence"]["observations"]), 4)
            self.assertEqual(len(sections["historical_price_evidence"]["descriptive_movement_entries"]), 2)
            self.assertEqual(sections["demand_usage_evidence"]["provider"], "scryfall")
            self.assertEqual(sections["deck_usage_evidence"]["provider"], "mtgjson")
            self.assertEqual(sections["deck_usage_evidence"]["numerator"], numerator)
            self.assertEqual(sections["deck_usage_evidence"]["denominator"], 3004)
            omissions = d["omitted_item_counts"]
            self.assertEqual(omissions["printing_identities"] + len(sections["printing_identities"]), printing_count)
            self.assertEqual(omissions["literal_deck_associations"] + len(sections["deck_usage_evidence"]["literal_deck_associations"]), numerator)
            self.assertEqual(omissions["market_observations"], 0)
            self.assertEqual(omissions["legacy_evidence_quality_section"], 1)
            self.assertNotIn("evidence_quality", sections)
            self.assertTrue(self.dossiers[slug].reasoning_context.truncation["occurred"])
            observed_printing_ids = {o["canonical_printing_id"] for o in sections["observed_price_evidence"]["observations"]}
            self.assertTrue(observed_printing_ids.issubset({p["uuid"] for p in sections["printing_identities"]}))

    def test_source_integrity_labels_and_source_specific_license_notices(self):
        for dossier in self.dossiers.values():
            d = dossier.to_dict()
            self.assertEqual(len(d["provenance"]["sources"]), 7)
            self.assertEqual(len(d["provenance"]["facts"]), 11)
            for source in d["provenance"]["sources"]:
                for reference in source["references"]:
                    path = ROOT / reference["reference"].split("#", 1)[0]
                    self.assertTrue(path.exists())
                    if path.is_file():
                        self.assertEqual(reference["retained_bytes_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
            for acquisition in d["input_integrity"]["market_acquisitions"]:
                self.assertNotEqual(acquisition["provider_source_sha256"], acquisition["retained_source"]["retained_bytes_sha256"])
                self.assertIn("not_retained", acquisition["original_bulk_source_bytes"])
            providers = d["input_integrity"]["demand_providers"]
            self.assertEqual({p["provider"] for p in providers}, {"scryfall", "mtgjson"})
            mtgjson = next(p for p in providers if p["provider"] == "mtgjson")
            self.assertIn("CC BY-SA 4.0", mtgjson["license_considerations"]["license"])
            self.assertEqual(d["input_integrity"]["printing_provider"]["license"], "CC BY 4.0")
            self.assertIn("not_retained", mtgjson["original_source_bytes"])

    def test_tampered_retained_source_fails_closed(self):
        report = self.builder.engine.explain(card_id=TARGETS[0][1], include_demand_evidence=True)
        with tempfile.TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            run = "scryfall-mb2-30754638264-1"
            destination = data / "market/acquisitions" / run
            shutil.copytree(ROOT / "data/market/acquisitions" / run, destination)
            source = destination / "source-mb2.json"
            source.write_bytes(source.read_bytes() + b" ")
            with patch.object(self.builder, "data_root", data), patch.object(self.builder, "repository_root", data.parent):
                with self.assertRaisesRegex(ValueError, "retained source digest mismatch"):
                    self.builder._inputs(report)

    def test_content_identities_bounded_immutable_context_and_replay(self):
        for slug, card_id, _ in TARGETS:
            original = self.dossiers[slug]
            repeated = self.builder.build(card_id)
            self.assertEqual(original.to_json(), repeated.to_json())
            self.assertEqual(original.reasoning_context.to_json(), repeated.reasoning_context.to_json())
            d = original.to_dict()
            dossier_id = d.pop("dossier_id")
            self.assertEqual(dossier_id, content_identity(d))
            context = original.reasoning_context
            self.assertIsInstance(context, ReasoningContextResult)
            c = context.to_dict()
            hashed = {"canonical_snapshot_id": c["canonical_snapshot_id"], "analytics_snapshot_id": c["analytics_snapshot_id"],
                "request": c["normalized_request"], "entities": c["entities"], "relationships": c["relationships"],
                "analytics": c["analytics_results"], "provenance": c["provenance_references"],
                "evidence": c["evidence_references"], "omitted": c["omitted_item_counts"],
                "truncation": c["truncation"], "warnings": c["warnings"]}
            self.assertEqual(context.context_id, content_identity(hashed))
            self.assertIsNone(context.analytics_snapshot_id)
            self.assertFalse(context.normalized_request["include_analytics"])
            self.assertEqual(context.analytics_results[0]["projection"], "bounded_card_value_evidence_manual_handoff")
            for serialized in (original.to_json(), context.to_json()):
                self.assertLessEqual(len(serialized.encode()), MAXIMUM_BYTES)
            with self.assertRaises(TypeError):
                original.payload["permissions"]["production_admission"] = True
            with self.assertRaises(TypeError):
                context.analytics_results[0]["dossier"]["card_identity"]["name"] = "invented"
            with patch("scripts.card_dossier.MAXIMUM_BYTES", 100):
                with self.assertRaisesRegex(ValueError, "exceeds its byte limit"):
                    self.builder.build(card_id)

    def test_explanations_derive_values_and_all_citations_from_dossier(self):
        for slug, dossier in self.dossiers.items():
            text = render_explanation(dossier)
            self.assertEqual(text, (ARTIFACTS / f"{slug}.explanation.md").read_text())
            d = dossier.to_dict()
            for pointer in re.findall(r"`(/[^`]+)`", text):
                current = d
                for field in pointer[1:].split("/"):
                    current = current[int(field)] if isinstance(current, list) else current[field]
            self.assertIn(d["card_identity"]["card_id"], text)
            self.assertIn(d["evidence_sections"]["rules"]["oracle_text"], text)
            for movement in d["evidence_sections"]["historical_price_evidence"]["descriptive_movement_entries"]:
                self.assertIn(f"{movement['first_amount']} → {movement['latest_amount']}", text)
                self.assertIn(f"percentage change {movement['percentage_change']}%", text)
            for boundary in ("not a deck count", "not global usage", "not completed sales or current offers",
                             "Unknown or unsupported conclusions", "No model executed"):
                self.assertIn(boundary, text)
            self.assertFalse(d["permissions"]["acquisition_evaluation"])
            self.assertFalse(d["permissions"]["human_readiness_attestation"])

    def test_artifact_inventory_replay_and_non_promotion(self):
        artifacts = build_artifacts()
        self.assertEqual(len(artifacts), 7)
        self.assertEqual(artifacts, {p.name: p.read_bytes() for p in ARTIFACTS.iterdir() if p.is_file()})
        manifest = json.loads(artifacts["manifest.json"])
        self.assertEqual(len(manifest["cards"]), 2)
        for name, entry in manifest["files"].items():
            self.assertEqual(entry["sha256"], hashlib.sha256(artifacts[name]).hexdigest())
            self.assertEqual(entry["bytes"], len(artifacts[name]))
        self.assertEqual(self.protected_before, protected_inventory())


if __name__ == "__main__":
    unittest.main()
