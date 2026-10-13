from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.mechanics import content_identity, stable_json
from collection.assessments import CollectionAssessment
from collection.audit import CollectionAudit, CollectionAuditDossier
from collection.intelligence import canonical_json, digest
from scripts import build_collection_audit_pilot as pilot


EXPECTED = {
    "Ponder": ("02090581-61aa-4348-ad57-451be8ee91c2", "5c8d3bc4-32fc-5b26-84bf-9921e5884d43", 100),
    "Faithless Looting": ("3d6fa57a-aa53-4b5c-b8af-a7612c823117", "72783a15-4847-5448-8f1d-0c40379594d3", 75),
    "Greater Good": ("dc0593c2-ccb4-4648-a592-c5bcd121dc72", "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade", 25),
    "Sol Ring": ("6ad8011d-3471-4369-9d68-b264cc027487", "b43c646f-797d-5b5f-8ade-142486708c88", 80),
    "Counterspell": ("cc187110-1148-4090-bbb8-e205694a39f5", "d5bfe686-da3c-5a8d-9dd5-4a1fe5aaef3d", 45),
    "Veil of Summer": ("002965be-a36f-4a09-9ce0-c6535bca1703", "e930c78d-2ef1-5853-83e5-571d8efb6f51", 5),
}


def data_inventory(root):
    """Also catch an identical-byte rewrite during a supposedly read-only check."""
    return {p.relative_to(root).as_posix(): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
            for p in (root / "data").rglob("*") if p.is_file()}


class CollectionAuditPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = pilot.protected_inventory()
        cls.artifacts = pilot.build_artifacts()
        cls.dossier = json.loads(cls.artifacts["audit-dossier.json"])
        cls.audit = json.loads(cls.artifacts["audit-result.json"])
        cls.projection = cls.dossier["audit"]
        cls.context = json.loads(cls.artifacts["reasoning-context.json"])
        cls.imported, cls.resolver, cls.snapshot = pilot.load_inputs()
        cls.engine = CollectionAudit(cls.resolver)
        cls.validated = CollectionAuditDossier.reconstruct(cls.audit, resolver=cls.resolver,
            snapshot=cls.snapshot, source_path=pilot.IMPORT, source_root=pilot.ROOT,
            assessments=pilot._load_assessments(cls.snapshot))
        cls.cards = {c["card_name"]: c for c in cls.audit["cards"]}
        cls.holdings = {h["owned_lot_id"]: h for h in cls.audit["holdings"] if h["exclusion"] is None}

    def test_compressed_fixture_declares_twelve_distinct_lots_and_only_fictional_ownership(self):
        fixture = pilot.fixture_document()
        self.assertEqual(json.loads(pilot.IMPORT.read_bytes()), fixture)
        self.assertEqual(fixture["source"]["type"], "synthetic_fixture")
        self.assertEqual(fixture["source"]["mode"], "synthetic_demonstration")
        self.assertFalse(fixture["source"]["real_user_inventory"])
        self.assertEqual(fixture["source"]["expected_nonduplicate_quantity"], 360)
        rows = fixture["entries"]
        self.assertEqual(len(rows), 14)
        self.assertEqual(len({r["provenance"]["owned_lot_id"] for r in rows[:12]}), 12)
        self.assertEqual(sum(r["quantity"] for r in rows[:12]), 360)
        self.assertEqual(rows[12], rows[0])
        self.assertEqual((rows[12]["quantity"], rows[13]["quantity"]), (80, 0))
        self.assertIn("SYNTHETIC ONLY", self.dossier["notice"])
        real = self.dossier["real_inventory"]
        self.assertEqual(real["status"], "not_retained")
        self.assertEqual((real["partial_observation_pack_count"], real["partial_observation_position_count"]), (6, 90))
        self.assertFalse(real["complete_360_copy_inventory"])
        self.assertFalse(real["observation_to_ownership_conversion"])
        source = self.audit["source_classification"]
        self.assertIs(source["synthetic"], True)
        self.assertIs(source["real_user_inventory"], False)
        self.assertEqual(source["metadata"], fixture["source"])
        self.assertEqual(self.dossier["review"], {"status": "requires_review", "human_attestation": None,
                                                "canonical_admission": False})

    def test_exact_six_production_cards_and_printings_are_bound_to_resolved_holdings(self):
        self.assertEqual({s["card_name"]: (s["card_id"], s["printing_id"])
                          for s in self.dossier["subjects"]},
                         {name: values[:2] for name, values in EXPECTED.items()})
        self.assertEqual({name: c["quantity"] for name, c in self.cards.items()},
                         {name: values[2] for name, values in EXPECTED.items()})
        canonical = json.loads((pilot.ROOT / "data/canonical/state.json").read_bytes())
        for name, (card_id, printing_id, _) in EXPECTED.items():
            with self.subTest(card=name):
                self.assertEqual(canonical["card"][card_id]["values"]["name"], name)
                printing = canonical["printing"][printing_id]["values"]
                self.assertEqual((printing["card_id"], printing["set_id"], printing["language"]),
                                 (card_id, "mb2", "English"))
                self.assertNotIn("treatment_ids", printing)
                self.assertEqual(self.cards[name]["printing_ids"], [printing_id])
                for holding in (h for h in self.audit["holdings"] if h["card_id"] == card_id):
                    reference = holding["canonical_reference"]
                    self.assertEqual(reference["snapshot_id"], self.audit["bindings"]["canonical_snapshot_id"])
                    self.assertEqual(reference["card"]["canonical_identity"], card_id)
                    self.assertEqual(reference["printing"]["canonical_identity"], printing_id)
                    for entity in (reference["card"], reference["printing"]):
                        self.assertTrue(entity["source_ids"])
                        self.assertTrue(entity["evidence_reference_ids"])
                        self.assertTrue(entity["promotion_references"])
                        self.assertTrue(all(p["audit_reference"]["sha256"] for p in entity["promotion_references"]))

    def test_census_excludes_duplicate_import_and_invalid_row_from_the_360_copies(self):
        census = self.audit["quantity_census"]
        expected = {"source_valid_positive_quantity": 440, "resolved_quantity": 330,
                    "ambiguous_reported_quantity": 15, "unresolved_reported_quantity": 15,
                    "excluded_duplicate_input_quantity": 80, "excluded_invalid_quantity": 0,
                    "excluded_conflicting_lot_quantity": 0, "excluded_duplicate_input_rows": 1,
                    "excluded_invalid_rows": 1, "excluded_conflicting_lot_rows": 0,
                    "reported_total_quantity": 360, "confirmed_total_quantity": 360,
                    "expected_total": 360, "expected_total_matches": True,
                    "total_state": "known_reported_total", "unknown_quantity_rows": [],
                    "conflicting_owned_lot_ids": []}
        self.assertEqual(census, expected)
        self.assertEqual(self.audit["identity_census"], {"unique_cards": 6, "unique_printings": 6,
            "row_status_counts": {"resolved": 10, "ambiguous": 1, "unresolved": 1,
                                  "duplicate_input_row": 1, "invalid": 1}})
        self.assertEqual(len(self.audit["holdings"]), 14)
        excluded = [h for h in self.audit["holdings"] if h["exclusion"]]
        self.assertEqual([(h["exclusion"], h["reported_quantity"]) for h in excluded],
                         [("duplicate_input", 80), ("invalid", 0)])
        # The older snapshot field includes the repeated row; the audit must not
        # present its 110 as another 110 physical copies.
        self.assertEqual(self.snapshot["inventory"]["unresolved_quantity"], 110)
        self.assertEqual(sum(d["copies_beyond_first"] for d in self.audit["duplicates"]), 324)
        self.assertEqual({d["printing_id"]: d["quantity"] for d in self.audit["duplicates"]},
                         {pid: quantity for _, pid, quantity in EXPECTED.values()})

    def test_unknown_storage_and_physical_attributes_remain_unknown_despite_exact_identity(self):
        unknown = self.holdings["fictional-counterspell-unknown"]
        self.assertEqual(unknown["resolution_status"], "resolved")
        self.assertEqual(unknown["reported_quantity"], 5)
        for field in ("finish", "language", "condition", "acquisition_date", "acquisition_price"):
            self.assertIsNone(unknown["row"][field])
            self.assertIn(field, unknown["row"]["unknown_fields"])
        archive = self.holdings["fictional-ponder-archive"]
        self.assertIsNone(archive["storage_location"])
        self.assertIsNone(archive["organization"]["storage_classification"])
        self.assertIsNone(archive["row"]["condition"])
        foil = self.holdings["fictional-greater-foil"]
        self.assertEqual((foil["row"]["finish"], foil["reported_quantity"]), ("foil", 5))
        self.assertEqual(foil["printing_id"], self.holdings["fictional-greater-nonfoil"]["printing_id"])
        groups = self.audit["organization"]["groups"]
        self.assertEqual(sum(g["reported_quantity"] for g in groups), 360)
        missing_storage = next(g for g in groups if g["storage_location"] is None and
                               g["storage_classification"] is None)
        self.assertEqual(missing_storage["reported_quantity"], 50)
        pending = self.holdings["fictional-name-ambiguous"]
        self.assertEqual(pending["resolution_status"], "ambiguous")
        self.assertIsNone(pending["card_id"])
        self.assertIsNone(pending["printing_id"])
        self.assertGreater(len(pending["candidate_printing_ids"]), 1)
        self.assertEqual(self.holdings["fictional-unresolved-lot"]["candidate_printing_ids"], [])

    def test_assessment_records_bind_exact_retained_claim_bytes_and_snapshot(self):
        history = self.audit["assessment_history"]
        self.assertEqual(len(history), 6)
        self.assertEqual(len({r["assessment_id"] for r in history}), 6)
        for record in history:
            source = record["source"]
            raw = (pilot.ROOT / source["relative_path"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["sha256"])
            self.assertEqual(source["json_pointer"], "/claim")
            source_document = json.loads(raw)
            self.assertEqual(source_document["mode"], "synthetic_demonstration")
            self.assertIs(source_document["synthetic"], True)
            unsigned = {k: v for k, v in record.items() if k != "assessment_id"}
            self.assertEqual(record["assessment_id"], "sha256:" + digest(unsigned))
            claim = {k: v for k, v in record.items() if k not in {"schema_version", "assessment_id", "source"}}
            self.assertEqual(source_document["claim"], claim)
            self.assertEqual(CollectionAssessment(record, pilot.ROOT, snapshot=self.snapshot).to_dict(), record)
            self.assertEqual(record["human_review"], {"kind": "synthetic_mock", "approved": False,
                                                     "reviewer": None, "review_reference": None})
            binding = record["snapshot_binding"]
            for key in ("snapshot_id", "snapshot_digest", "source_import_digest", "canonical_snapshot_id"):
                self.assertEqual(binding[key], self.snapshot[key])
            printing_ids = sorted({h["printing_id"] for h in self.snapshot["resolved_holdings"]
                                   if h["card_id"] == record["card_id"]})
            self.assertEqual(binding["resolved_printing_ids"], printing_ids)

    def test_reviewed_and_formerly_reviewed_cards_do_not_reappear_as_new_discoveries(self):
        expected = {"Ponder": ("reviewed", True, False, False),
                    "Greater Good": ("reassessment_needed", True, False, False),
                    "Sol Ring": ("reviewed", True, False, False),
                    "Veil of Summer": ("reviewed", True, False, False),
                    "Counterspell": ("pending", False, True, True),
                    "Faithless Looting": ("pending", False, True, True)}
        self.assertEqual({n: tuple(c[k] for k in ("review_status", "ever_reviewed", "new_discovery_eligible",
                                                 "unreviewed_bulk_eligible")) for n, c in self.cards.items()}, expected)
        self.assertEqual(self.audit["review_census"]["unit"], "unique_resolved_cards")
        self.assertEqual(self.audit["review_census"]["counts"],
                         {"reviewed": 3, "pending": 2, "unresolved": 0, "reassessment_needed": 1})
        self.assertEqual(self.audit["review_census"]["review_basis_counts"],
                         {"synthetic_mock_assessments": 6, "approved_human_assessments": 0,
                          "reviewed_cards_by_basis": {"synthetic_mock": 3}})
        bulk = {EXPECTED[n][0] for n in ("Counterspell", "Faithless Looting")}
        self.assertEqual(set(self.audit["organization"]["unreviewed_bulk_card_ids"]), bulk)
        self.assertEqual(set(self.audit["organization"]["new_discovery_card_ids"]), bulk)
        self.assertIsNone(self.cards["Faithless Looting"]["assessment_id"])
        self.assertEqual(self.cards["Faithless Looting"]["history_ids"], [])
        ponder = next(r for r in self.audit["assessment_history"] if r["card_id"] == EXPECTED["Ponder"][0])
        self.assertEqual(ponder["outcome"], "already_processed")

    def test_manual_reassessment_preserves_the_previous_review_without_rewriting_it(self):
        records = [r for r in self.audit["assessment_history"] if r["card_id"] == EXPECTED["Greater Good"][0]]
        old = next(r for r in records if r["status"] == "reviewed")
        current = next(r for r in records if r["status"] == "reassessment_needed")
        self.assertEqual(current["prior_assessment_id"], old["assessment_id"])
        self.assertEqual(current["supersedes"], [old["assessment_id"]])
        self.assertEqual(current["assessed_at"], old["assessed_at"])
        self.assertGreater(current["recorded_at"], old["recorded_at"])
        self.assertTrue(current["manual_reassessment_trigger"])
        for field in ("outcome", "reason", "assessment_version", "human_review"):
            self.assertEqual(current[field], old[field])
        self.assertEqual(self.cards["Greater Good"]["assessment_id"], current["assessment_id"])
        self.assertEqual(self.cards["Greater Good"]["history_ids"], [old["assessment_id"], current["assessment_id"]])
        self.assertFalse(self.audit["boundaries"]["automatic_reassessment"])

    def test_three_exact_acquisition_printing_queries_remain_informational(self):
        boundary = self.dossier["acquisition_boundary"]
        candidates = {EXPECTED[n][1] for n in ("Ponder", "Faithless Looting", "Greater Good")}
        self.assertEqual(set(boundary["candidate_printing_ids"]), candidates)
        self.assertFalse(boundary["actual_purchase_advice"])
        self.assertEqual(boundary["status"], "informational_ownership_counts_only")
        self.assertTrue(boundary["required_real_inputs"])
        coverage = self.audit["ownership_coverage"]
        self.assertIsNone(coverage["scope_complete"])
        self.assertFalse(coverage["acquisition_input_ready"])
        self.assertEqual({c["printing_id"] for c in coverage["candidates"]}, candidates)
        for name in ("Ponder", "Faithless Looting", "Greater Good"):
            card_id, printing_id, quantity = EXPECTED[name]
            query = self.engine.query(self.validated, printing_id=printing_id)
            self.assertEqual(query["identity_state"], "resolved")
            self.assertEqual([(c["card_id"], c["quantity"]) for c in query["cards"]], [(card_id, quantity)])
            row = next(c for c in coverage["candidates"] if c["printing_id"] == printing_id)
            self.assertEqual(row["resolved_reported_quantity"], quantity)
            self.assertIsNone(row["owned_quantity"])
            self.assertEqual(row["ownership_state"], "incomplete_scope")
            self.assertTrue(row["unresolved_evidence"])
        self.assertEqual(self.engine.query(self.validated, card_name="Sol Ring")["identity_state"], "ambiguous")

    def test_mechanical_and_pending_role_identities_reference_unchanged_companion_dossiers(self):
        mechanical = {d["dossier_id"]: d for d in map(json.loads,
            (pilot.ROOT / "data/review/mechanical-card-cohort/dossiers.jsonl").read_text().splitlines())}
        roles = {d["dossier_id"]: d for d in map(json.loads,
            (pilot.ROOT / "data/review/functional-role-pilot/dossiers.jsonl").read_text().splitlines())}
        for subject in self.dossier["subjects"]:
            self.assertIn(subject["mechanical_dossier_id"], mechanical)
            self.assertEqual(mechanical[subject["mechanical_dossier_id"]]["card_identity"]["card_id"], subject["card_id"])
            original = roles[subject["pending_role_dossier_id"]]
            self.assertEqual(original["card_identity"]["card_id"], subject["card_id"])
            self.assertEqual(subject["pending_role_candidate_count"], len(original["role_candidates"]))
            self.assertEqual(subject["role_review_status"], "requires_review")
            self.assertFalse(subject["human_role_approval"])
            self.assertTrue(all(c["review"]["status"] == "requires_review" and
                                c["review"]["human_attestation"] is None and
                                not c["review"]["canonical_admission"] for c in original["role_candidates"]))
            self.assertEqual(set(subject["omissions"]), {"mechanical_payload", "functional_roles"})

    def test_projection_preserves_every_calculation_and_binds_all_omitted_lineage(self):
        reference = self.projection["validated_audit_reference"]
        raw = self.artifacts["audit-result.json"]
        self.assertEqual(reference["relative_path"], "data/review/collection-audit-pilot/audit-result.json")
        self.assertEqual(reference["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(reference["bytes"], len(raw))
        self.assertEqual(self.projection["schema_version"], "collection-audit-projection-v1")
        for key in ("audit_id", "audit_digest", "source_classification", "quantity_census", "identity_census", "review_census",
                    "assessment_history", "organization", "duplicates", "ownership_coverage", "boundaries"):
            self.assertEqual(self.projection[key], self.audit[key])
        self.assertEqual(len(self.projection["holdings"]), 14)
        self.assertEqual(len(self.projection["cards"]), 6)
        for projected, full in zip(self.projection["holdings"], self.audit["holdings"]):
            self.assertEqual(projected["holding_ref"], full["holding_ref"])
            self.assertEqual(projected["source_row_pointer"], "/entries/" + str(full["row"]["row_number"] - 1))
            self.assertEqual(projected["physical_attributes"], {k: full["row"][k]
                             for k in ("finish", "language", "condition")})
            self.assertEqual(projected["unknown_fields"], full["row"]["unknown_fields"])
            for key in ("reported_quantity", "resolution_status", "exclusion", "printing_id", "card_id",
                        "candidate_printing_ids", "storage_location", "organization"):
                self.assertEqual(projected[key], full[key])
        omissions = self.projection["omissions"]
        self.assertEqual({k: omissions[k] for k in ("holdings_omitted", "cards_omitted", "quantities_omitted",
                                                  "assessment_records_omitted")},
                         {"holdings_omitted": 0, "cards_omitted": 0, "quantities_omitted": 0,
                          "assessment_records_omitted": 0})
        self.assertEqual(omissions["normalized_source_rows_referenced"], 14)
        self.assertEqual(omissions["holding_canonical_references_referenced"], 10)
        self.assertEqual(omissions["card_canonical_references_referenced"], 6)
        self.assertEqual(omissions["identity_evidence_referenced"], sum(len(h["identity_evidence"])
                                                                     for h in self.audit["holdings"]))
        self.assertEqual(self.projection["projection_id"], content_identity(
            {k: v for k, v in self.projection.items() if k != "projection_id"}))

    def test_handoff_byte_bounds_content_identities_canonical_contexts_and_omissions(self):
        for name in ("audit-dossier.json", "reasoning-context.json", "canonical-contexts.json", "manifest.json"):
            raw = self.artifacts[name]
            self.assertLessEqual(len(raw), 65536)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            self.assertEqual(raw[:-1].decode(), stable_json(json.loads(raw)))
        for document, key in ((self.dossier, "dossier_id"), (self.context, "handoff_id")):
            unsigned = {k: v for k, v in document.items() if k != key}
            self.assertEqual(document[key], content_identity(unsigned))
        self.assertEqual(self.context["dossier"], self.dossier)
        self.assertEqual(self.context["maximum_serialized_bytes_including_trailing_lf"], 65536)
        self.assertEqual(self.context["delivery"], "bounded manual handoff; no model execution or live transport")
        originals = json.loads(self.artifacts["canonical-contexts.json"])
        self.assertEqual(len(originals), 6)
        self.assertEqual([c["context_id"] for c in self.context["canonical_contexts"]],
                         [c["context_id"] for c in originals])
        for subject, context, reference in zip(self.dossier["subjects"], originals, self.context["canonical_contexts"]):
            self.assertEqual(context["schema_version"], "canonical-reasoning-context-v1")
            self.assertEqual(context["canonical_snapshot_id"], self.snapshot["canonical_snapshot_id"])
            self.assertEqual(reference["card_id"], subject["card_id"])
            self.assertEqual(reference["omitted_item_counts"], context["omitted_item_counts"])
            self.assertEqual(context["entities"], [])
            self.assertEqual(context["relationships"], [])
            self.assertEqual(context["evidence_references"], {})
            self.assertGreater(context["omitted_item_counts"]["entities"], 0)
            self.assertTrue(context["truncation"]["occurred"])
        reference = self.context["canonical_contexts_reference"]
        self.assertEqual(reference["sha256"], hashlib.sha256(self.artifacts["canonical-contexts.json"]).hexdigest())
        self.assertEqual(reference["bytes"], len(self.artifacts["canonical-contexts.json"]))
        self.assertEqual(reference["contract_count"], 6)
        omissions = self.context["omissions"]
        self.assertEqual({k: omissions[k] for k in ("audit_holdings", "audit_cards", "audit_census")},
                         {"audit_holdings": 0, "audit_cards": 0, "audit_census": 0})
        self.assertEqual(omissions["canonical_contexts"], [c["omitted_item_counts"] for c in originals])
        # JSON quotes and LF consume three bytes beyond the ASCII payload.
        self.assertEqual(len(pilot.compact_payload("x" * 65533)), 65536)
        with self.assertRaisesRegex(ValueError, "including trailing LF"):
            pilot.compact_payload("x" * 65534)
        with self.assertRaisesRegex(ValueError, "including trailing LF"):
            pilot.compact_payload("é" * 32767)

    def test_public_renderers_reject_rehashed_changes_to_counts_review_unknowns_and_boundaries(self):
        changes = {
            "quantity": lambda d: d["audit"]["quantity_census"].update(reported_total_quantity=440),
            "previous_review": lambda d: next(c for c in d["audit"]["cards"] if c["card_name"] == "Greater Good").update(
                ever_reviewed=False, new_discovery_eligible=True),
            "unknown_attribute": lambda d: next(h for h in d["audit"]["holdings"]
                if h["owned_lot_id"] == "fictional-counterspell-unknown")["physical_attributes"].update(finish="nonfoil"),
            "purchase_advice": lambda d: d["acquisition_boundary"].update(actual_purchase_advice=True),
            "role_approval": lambda d: d["subjects"][0].update(human_role_approval=True),
        }
        for label, change in changes.items():
            forged = copy.deepcopy(self.dossier)
            change(forged)
            forged["audit"]["projection_id"] = content_identity(
                {k: v for k, v in forged["audit"].items() if k != "projection_id"})
            forged["dossier_id"] = content_identity({k: v for k, v in forged.items() if k != "dossier_id"})
            for renderer in (pilot.pilot_reasoning_context, pilot.pilot_explanation):
                with self.subTest(change=label, renderer=renderer.__name__):
                    with self.assertRaisesRegex(ValueError, "bound input/result replay"):
                        renderer(forged)

    def test_handoff_rejects_rehashed_canonical_context_omission_tampering(self):
        forged = json.loads(self.artifacts["canonical-contexts.json"])
        forged[0]["omitted_item_counts"]["entities"] = 0
        forged[0]["context_id"] = content_identity({k: v for k, v in forged[0].items() if k != "context_id"})
        with self.assertRaisesRegex(ValueError, "contexts contradict canonical replay"):
            pilot.pilot_reasoning_context(self.dossier, contexts=forged)

    def test_rehashed_retained_projection_cannot_replace_complete_source_replay(self):
        forged = copy.deepcopy(self.dossier)
        forged["audit"]["quantity_census"]["reported_total_quantity"] = 440
        forged["audit"]["projection_id"] = content_identity(
            {k: v for k, v in forged["audit"].items() if k != "projection_id"})
        forged["dossier_id"] = content_identity({k: v for k, v in forged.items() if k != "dossier_id"})
        substituted_bytes = pilot.compact_payload(forged)
        original = Path.read_bytes
        def substituted(path):
            return substituted_bytes if path == pilot.REVIEW / "audit-dossier.json" else original(path)
        # Simulate matching altered retained bytes without changing any file. A
        # retained-byte comparison and a valid outer hash must both be inadequate.
        with patch.object(Path, "read_bytes", substituted):
            for renderer in (pilot.pilot_reasoning_context, pilot.pilot_explanation):
                with self.subTest(renderer=renderer.__name__):
                    with self.assertRaisesRegex(ValueError, "bound input/result replay"):
                        renderer(forged)

    def test_source_and_assessment_byte_changes_are_rejected_before_rendering(self):
        original = Path.read_bytes
        paths = [pilot.IMPORT, pilot.ROOT / self.dossier["snapshot_reference"]["relative_path"],
                 pilot.ROOT / self.audit["assessment_history"][0]["source"]["relative_path"]]
        for changed in paths:
            def corrupted(path, target=changed):
                raw = original(path)
                return raw + b" " if path == target else raw
            with self.subTest(path=changed.name), patch.object(Path, "read_bytes", corrupted):
                with self.assertRaisesRegex(ValueError, "differs from|source digest mismatch"):
                    pilot.build_pilot_dossier()

    def test_retained_companion_byte_changes_are_rejected_before_manual_handoff(self):
        original = Path.read_bytes
        cases = [(pilot.REVIEW / "audit-result.json", pilot.pilot_explanation, "retained full audit result"),
                 (pilot.REVIEW / "canonical-contexts.json", pilot.pilot_reasoning_context,
                  "retained collection canonical contexts")]
        for changed, renderer, message in cases:
            def corrupted(path, target=changed):
                raw = original(path)
                return raw + b" " if path == target else raw
            with self.subTest(path=changed.name), patch.object(Path, "read_bytes", corrupted):
                with self.assertRaisesRegex(ValueError, message):
                    renderer(self.dossier)

    def test_actual_root_cli_bounds_context_and_queries_and_rejects_oversize_full_result(self):
        before = data_inventory(pilot.ROOT)
        argv = [sys.executable, "-m", "mtglab", "--data-root", str(pilot.ROOT / "data"),
            "collection", "audit", "--snapshot", self.snapshot["snapshot_id"],
            "--source", str(pilot.IMPORT), "--source-root", str(pilot.ROOT),
            "--assessment-root", str(pilot.ASSESSMENTS / "records"), "--expected-total", "360"]
        for name in ("Ponder", "Faithless Looting", "Greater Good"):
            argv.extend(["--candidate-printing-id", EXPECTED[name][1]])
        expected = [(argv + ["--reasoning-context"], canonical_json(self.validated.reasoning_context()))]
        expected.extend((argv + ["--printing-id", EXPECTED[name][1]],
                         canonical_json(self.engine.query(self.validated, printing_id=EXPECTED[name][1])))
                        for name in ("Ponder", "Faithless Looting", "Greater Good"))
        for arguments, payload in expected:
            with self.subTest(selector=arguments[-1]):
                completed = subprocess.run(arguments, cwd=pilot.ROOT,
                    env={**os.environ, "PYTHONPATH": str(pilot.ROOT / "src")},
                    capture_output=True, check=False, timeout=180)
                self.assertEqual(completed.returncode, 0, completed.stderr.decode())
                self.assertEqual(completed.stderr, b"")
                self.assertEqual(completed.stdout, payload)
                self.assertLessEqual(len(completed.stdout), 65536)
                self.assertTrue(completed.stdout.endswith(b"\n"))
                self.assertFalse(completed.stdout.endswith(b"\n\n"))
                self.assertEqual(completed.stdout[:-1].decode(), stable_json(json.loads(completed.stdout)))
        self.assertGreater(len(self.artifacts["audit-result.json"]), 65536)
        completed = subprocess.run(argv, cwd=pilot.ROOT,
            env={**os.environ, "PYTHONPATH": str(pilot.ROOT / "src")},
            capture_output=True, check=False, timeout=180)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(completed.stderr, b"")
        error = json.loads(completed.stdout)
        self.assertFalse(error["valid"])
        self.assertIn("including trailing LF", error["error"])
        self.assertLess(len(completed.stdout), 1000)
        self.assertNotIn(b'"schema_version":"collection-audit-v1"', completed.stdout)
        self.assertEqual(data_inventory(pilot.ROOT), before)

    def test_retained_manifest_replays_every_input_and_preserves_prior_data(self):
        actual = {p.name: p.read_bytes() for p in pilot.REVIEW.iterdir() if p.is_file()}
        self.assertEqual(actual, self.artifacts)
        manifest = json.loads(self.artifacts["manifest.json"])
        for name, reference in manifest["files"].items():
            self.assertEqual(reference, {"bytes": len(actual[name]),
                                         "sha256": hashlib.sha256(actual[name]).hexdigest()})
        self.assertEqual(len(manifest["source_and_snapshot_files"]), 14)
        for name, reference in manifest["source_and_snapshot_files"].items():
            raw = (pilot.ROOT / name).read_bytes()
            self.assertEqual(reference, {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
        snapshot_ref = self.dossier["snapshot_reference"]
        raw = (pilot.ROOT / snapshot_ref["relative_path"]).read_bytes()
        self.assertEqual(json.loads(raw), self.snapshot)
        self.assertEqual(snapshot_ref["bytes"], len(raw))
        self.assertEqual(snapshot_ref["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(manifest["protected_inventory"]["file_count"], len(self.before))
        self.assertEqual(manifest["protected_inventory"]["content_identity"], content_identity(self.before))
        self.assertEqual(pilot.protected_inventory(), self.before)
        self.assertTrue(all(value is False for value in self.dossier["protection_boundary"].values()))

    def test_check_exact_replay_is_read_only_and_emits_one_compact_summary(self):
        before = data_inventory(pilot.ROOT)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(pilot.main(["--check"]), 0)
        self.assertEqual(data_inventory(pilot.ROOT), before)
        raw = output.getvalue().encode("utf-8")
        self.assertLessEqual(len(raw), 65536)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertFalse(raw.endswith(b"\n\n"))
        self.assertEqual(raw[:-1].decode(), stable_json(json.loads(raw)))
        self.assertEqual(json.loads(raw), {"schema_version": "collection-audit-pilot-build-v1",
            "artifact_count": 6, "fictional_copies": 360, "production_cards": 6, "verified": True})

    def test_immutable_publish_preflights_all_conflicts_without_partial_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "retained.json"
            existing.write_bytes(b"original evidence\n")
            before = (existing.read_bytes(), existing.stat().st_mtime_ns)
            documents = {"would-be-new.json": b"new\n", "retained.json": b"conflicting\n"}
            with patch.object(pilot, "ROOT", root):
                for check in (False, True):
                    with self.subTest(check=check), self.assertRaises(ValueError):
                        pilot._publish_immutable(documents, check=check)
                    self.assertFalse((root / "would-be-new.json").exists())
                    self.assertEqual((existing.read_bytes(), existing.stat().st_mtime_ns), before)
                pilot._publish_immutable({"retained.json": before[0]}, check=False)
                self.assertEqual((existing.read_bytes(), existing.stat().st_mtime_ns), before)

    def test_check_with_missing_inputs_does_not_create_any_collection_artifacts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(pilot, "ROOT", root), \
                    patch.object(pilot, "IMPORT", root / "data/collections/imports/fictional.json"), \
                    patch.object(pilot, "ASSESSMENTS", root / "data/collections/assessments/fictional"), \
                    patch.object(pilot, "REVIEW", root / "data/review/fictional"):
                with self.assertRaisesRegex(ValueError, "missing retained"):
                    pilot.main(["--check"])
            self.assertEqual(list(root.rglob("*")), [])


if __name__ == "__main__":
    unittest.main()
