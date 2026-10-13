import copy
import json
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from collection.assessments import CollectionAssessment
from collection.audit import CollectionAudit, CollectionAuditDossier, CollectionAuditError
from collection.intelligence import (CanonicalCollectionResolver, build_snapshot, canonical_json,
                                     create_snapshot, digest, read_import)


ROOT = Path(__file__).parents[1]
PONDER = "5c8d3bc4-32fc-5b26-84bf-9921e5884d43"


class CollectionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = CanonicalCollectionResolver("magic", ROOT / "data")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.audit = CollectionAudit(self.resolver)

    def tearDown(self):
        self.temp.cleanup()

    def inputs(self, rows, *, name="original.json", source=None, snapshot_id="audit-test-snapshot"):
        path = self.root / name
        path.write_bytes(canonical_json({"schema_version": "collection-import-v1", "collection_id": "audit-test",
            "source": source if source is not None else {
                "type": "synthetic_fixture", "mode": "synthetic_demonstration",
                "real_user_inventory": False, "notice": "Fictional test inventory."}, "entries": rows}))
        imported = read_import(path)
        snapshot = build_snapshot(imported, self.resolver.resolve(imported), snapshot_id)
        return path, imported, snapshot

    def assessment(self, snapshot, source_path, *, name="mock-review.json", prior=None,
                   reviewed_at="2026-10-10T11:00:00Z", kind="synthetic_mock", status="reviewed"):
        card_id = self.resolver.printings[PONDER]["card_id"]
        claim = {"collection_id": snapshot["collection_id"], "card_id": card_id,
            "purpose": "personal_collection_review", "status": status,
            "outcome": "source-bound personal assessment" if status == "reviewed" else None,
            "reason": "Explicit retained test assessment, not a strategic fact.",
            "assessed_at": reviewed_at, "recorded_at": reviewed_at, "assessment_version": "review-v1",
            "prior_assessment_id": prior, "supersedes": [prior] if prior else [],
            "manual_reassessment_trigger": None,
            "human_review": {"kind": kind, "approved": kind == "human",
                "reviewer": "fixture-human" if kind == "human" else None,
                "review_reference": "retained-human-claim" if kind == "human" else None},
            "snapshot_binding": {key: snapshot[key] for key in
                ("snapshot_id", "snapshot_digest", "source_import_digest", "canonical_snapshot_id")},
            "evidence_references": [{"source_id": "test-assessment", "source_type": "retained_user_review",
                "reference": source_path.relative_to(self.root).as_posix(), "observed_at": reviewed_at,
                "claim": "A source-bound personal review claim."}]}
        claim["snapshot_binding"].update(resolved_printing_ids=[PONDER], source_import_reference={
            "relative_path": source_path.relative_to(self.root).as_posix(),
            "sha256": snapshot["source_import_digest"]})
        path = self.root / name
        path.write_bytes(canonical_json({"synthetic": kind == "synthetic_mock", "claim": claim}))
        return CollectionAssessment.from_source(path, self.root, snapshot=snapshot,
                                                trusted_human_review=kind == "human")

    @staticmethod
    def row(quantity=3, *, alias="lot-one", classification="bulk", **attributes):
        return {"printing_id": PONDER, "quantity": quantity,
                "provenance": {"owned_lot_id": alias, "organization": {
                    "schema_version": "collection-organization-v1", "storage_classification": classification}},
                **attributes}

    def build(self, rows, **options):
        path, imported, snapshot = self.inputs(rows)
        dossier = self.audit.build(snapshot, source_path=path, source_root=self.root, **options)
        return dossier, path, imported, snapshot

    def test_pure_snapshot_builder_preserves_existing_publication_bytes(self):
        path, imported, snapshot = self.inputs([self.row()])
        published = create_snapshot(imported, self.resolver.resolve(imported), self.root / "snapshots", snapshot["snapshot_id"])
        self.assertEqual(canonical_json(snapshot), canonical_json(published))
        self.assertEqual(canonical_json(snapshot), (self.root / "snapshots/audit-test-snapshot.json").read_bytes())
        replay = create_snapshot(imported, self.resolver.resolve(imported), self.root / "snapshots", snapshot["snapshot_id"])
        self.assertEqual(replay["replay"], "exact_replay")

    def test_quantity_census_preserves_unresolved_and_excludes_duplicate_and_invalid(self):
        row = self.row()
        dossier, _, _, _ = self.build([row, copy.deepcopy(row),
            {"card_name": "Sol Ring", "quantity": 2}, {"printing_id": "not-a-printing", "quantity": 1},
            self.row(0, alias="invalid-zero")], expected_total=6, candidate_printing_ids=[PONDER])
        census = dossier["quantity_census"]
        self.assertEqual((census["source_valid_positive_quantity"], census["resolved_quantity"],
                          census["ambiguous_reported_quantity"], census["unresolved_reported_quantity"]), (9, 3, 2, 1))
        self.assertEqual((census["excluded_duplicate_input_quantity"], census["excluded_invalid_rows"]), (3, 1))
        self.assertEqual(census["confirmed_total_quantity"], 6)
        self.assertTrue(census["expected_total_matches"])
        self.assertEqual((dossier["identity_census"]["unique_cards"], dossier["identity_census"]["unique_printings"]), (1, 1))
        self.assertEqual(dossier["duplicates"][0]["copies_beyond_first"], 2)
        coverage = dossier["ownership_coverage"]["candidates"][0]
        self.assertEqual(coverage["resolved_reported_quantity"], 3)
        self.assertIsNone(coverage["owned_quantity"])
        self.assertIsNone(dossier["ownership_coverage"]["scope_complete"])
        self.assertFalse(dossier["ownership_coverage"]["acquisition_input_ready"])

    def test_unknown_boolean_and_noninteger_quantity_never_confirm_total(self):
        for quantity in (None, True, "unknown", "1.0"):
            with self.subTest(quantity=quantity):
                dossier, _, _, _ = self.build([self.row(), self.row(quantity, alias="quantity-test")], expected_total=3)
                census = dossier["quantity_census"]
                self.assertEqual(census["resolved_quantity"], 3)
                self.assertIsNone(census["confirmed_total_quantity"])
                self.assertIsNone(census["expected_total_matches"])
                self.assertEqual(census["unknown_quantity_rows"], (2,))

    def test_invalid_quantity_exact_printing_assertion_remains_relevant_to_all_identity_queries(self):
        card_id = self.resolver.printings[PONDER]["card_id"]
        card_name = self.resolver.cards[card_id]["name"]
        for quantity in (None, True, "invalid-quantity"):
            with self.subTest(quantity=quantity):
                dossier, _, _, _ = self.build([self.row(), self.row(quantity, alias="incomplete-lot")])
                invalid = dossier["holdings"][1]
                self.assertEqual(invalid["resolution_status"], "invalid")
                self.assertEqual(invalid["quantity_state"], "invalid_or_unknown")
                self.assertIsNone(invalid["printing_id"])
                self.assertIsNone(invalid["card_id"])
                self.assertIsNone(invalid["row"]["card_name"])
                self.assertEqual(dossier["quantity_census"]["resolved_quantity"], 3)
                self.assertIsNone(dossier["quantity_census"]["confirmed_total_quantity"])
                self.assertEqual(dossier["cards"][0]["quantity"], 3)
                for selector in ({"card_id": card_id}, {"printing_id": PONDER}, {"card_name": card_name}):
                    with self.subTest(selector=selector):
                        query = self.audit.query(dossier, **selector)
                        self.assertEqual(query["unresolved_holding_refs"], [dict(invalid["holding_ref"])])
                        self.assertEqual(query["ownership_state"], "incomplete_or_conflicting")
                        self.assertEqual(query["cards"][0]["quantity"], 3)
                        self.assertIsNone(query["ownership_scope_complete"])
                self.assertEqual(self.audit.query(dossier, card_name="Sol Ring")["unresolved_holding_refs"], [])

    def test_historical_mock_is_nonoperative_for_later_real_inventory(self):
        original_path, _, original = self.inputs([self.row()], snapshot_id="synthetic-snapshot")
        mock = self.assessment(original, original_path)
        record_before = mock.to_dict()
        claim_before = (self.root / "mock-review.json").read_bytes()
        data_root = self.root / "data"
        snapshots = data_root / "collections" / "snapshots"
        snapshots.mkdir(parents=True)
        (snapshots / "synthetic-snapshot.json").write_bytes(canonical_json(original))
        resolver = copy.copy(self.resolver)
        resolver.data_root = data_root
        audit = CollectionAudit(resolver)
        synthetic = audit.build(original, source_path=original_path, source_root=self.root, assessments=[mock])
        self.assertEqual(synthetic["cards"][0]["review_status"], "reviewed")
        self.assertTrue(synthetic["cards"][0]["ever_reviewed"])
        self.assertNotIn("nonoperative_assessment_ids", synthetic["review_census"])

        real_path, _, real = self.inputs([self.row()], name="real.json", snapshot_id="real-snapshot",
            source={"type": "user_inventory", "synthetic": False, "real_user_inventory": True})
        dossier = audit.build(real, source_path=real_path, source_root=self.root, assessments=[mock])
        card = dossier["cards"][0]
        self.assertEqual(card["review_status"], "pending")
        self.assertFalse(card["ever_reviewed"])
        self.assertIsNone(card["assessment_id"])
        self.assertIsNone(card["review_basis"])
        self.assertTrue(card["new_discovery_eligible"])
        self.assertTrue(card["unreviewed_bulk_eligible"])
        self.assertEqual(tuple(card["history_ids"]), (mock.payload["assessment_id"],))
        self.assertEqual(dossier["review_census"]["nonoperative_assessment_ids"], (mock.payload["assessment_id"],))
        self.assertEqual(dossier["review_census"]["review_basis_counts"]["approved_human_assessments"], 0)
        self.assertEqual(dossier.to_dict()["assessment_history"], [record_before])
        self.assertEqual(mock.to_dict(), record_before)
        self.assertEqual((self.root / "mock-review.json").read_bytes(), claim_before)
        context = dossier.reasoning_context(max_assessments=0)
        self.assertEqual(context["review_census"]["nonoperative_assessment_ids"], [mock.payload["assessment_id"]])
        query = audit.query(dossier, card_id=card["card_id"])
        self.assertEqual(query["nonoperative_assessment_ids"], [mock.payload["assessment_id"]])
        replay = CollectionAuditDossier.reconstruct(dossier.to_dict(), resolver=resolver, snapshot=real,
            source_path=real_path, source_root=self.root, assessments=[mock])
        self.assertEqual(replay.to_json(), dossier.to_json())

    def test_applicable_human_review_survives_nonoperative_mock_chain_nodes(self):
        original_path, _, original = self.inputs([self.row()], snapshot_id="synthetic-snapshot")
        first = self.assessment(original, original_path)
        data_root = self.root / "data"
        snapshots = data_root / "collections" / "snapshots"
        snapshots.mkdir(parents=True)
        (snapshots / "synthetic-snapshot.json").write_bytes(canonical_json(original))
        real_path, _, real = self.inputs([self.row()], name="real.json", snapshot_id="real-snapshot",
            source={"type": "user_inventory", "synthetic": False, "real_user_inventory": True})
        human = self.assessment(real, real_path, name="human-review.json", kind="human",
            prior=first.payload["assessment_id"], reviewed_at="2026-10-11T11:00:00Z")
        later_mock = self.assessment(original, original_path, name="later-mock.json", status="pending",
            prior=human.payload["assessment_id"], reviewed_at="2026-10-12T11:00:00Z")
        resolver = copy.copy(self.resolver)
        resolver.data_root = data_root
        dossier = CollectionAudit(resolver).build(real, source_path=real_path, source_root=self.root,
                                                assessments=[later_mock, first, human])
        card = dossier["cards"][0]
        self.assertEqual(card["review_status"], "reviewed")
        self.assertTrue(card["ever_reviewed"])
        self.assertEqual(card["assessment_id"], human.payload["assessment_id"])
        self.assertEqual(card["review_basis"], "human")
        self.assertFalse(card["new_discovery_eligible"])
        self.assertFalse(card["unreviewed_bulk_eligible"])
        self.assertEqual(len(card["history_ids"]), 3)
        self.assertEqual(len(dossier["review_census"]["nonoperative_assessment_ids"]), 2)
        self.assertEqual(dossier["review_census"]["review_basis_counts"]["approved_human_assessments"], 1)

    def test_conflicting_physical_aliases_exclude_both_assertions(self):
        dossier, _, _, _ = self.build([self.row(1), self.row(2)], expected_total=3)
        census = dossier["quantity_census"]
        self.assertEqual(census["excluded_conflicting_lot_quantity"], 3)
        self.assertEqual(census["excluded_conflicting_lot_rows"], 2)
        self.assertEqual(census["resolved_quantity"], 0)
        self.assertIsNone(census["confirmed_total_quantity"])
        self.assertEqual(len(dossier["cards"]), 0)

    def test_separately_declared_lots_and_unknown_physical_fields_are_preserved(self):
        dossier, _, _, _ = self.build([self.row(1), self.row("1", alias="lot-two", classification="sleeved")])
        self.assertEqual(dossier["quantity_census"]["resolved_quantity"], 2)
        self.assertEqual(dossier["quantity_census"]["excluded_duplicate_input_rows"], 0)
        for item in dossier["holdings"]:
            self.assertIsNone(item["row"]["finish"])
            self.assertIsNone(item["row"]["language"])
            self.assertIsNone(item["row"]["condition"])
            self.assertIsNone(item["storage_location"])
        card = dossier["cards"][0]
        self.assertEqual(card["review_status"], "pending")
        self.assertTrue(card["unreviewed_bulk_eligible"])
        self.assertFalse(card["ever_reviewed"])

    def test_snapshot_rehash_does_not_authorize_changed_quantity_or_lineage(self):
        path, _, snapshot = self.inputs([self.row()])
        for mutate in (
            lambda document: document["resolved_holdings"][0]["row"].update(quantity=4),
            lambda document: document["resolved_holdings"][0]["canonical_reference"]["card"].update(source_ids=["forged"]),
        ):
            changed = copy.deepcopy(snapshot)
            mutate(changed)
            changed["snapshot_digest"] = digest({key: value for key, value in changed.items() if key != "snapshot_digest"})
            with self.assertRaisesRegex(CollectionAuditError, "reproduce"):
                self.audit.build(changed, source_path=path, source_root=self.root)

    def test_original_source_bytes_and_confined_paths_are_required(self):
        path, _, snapshot = self.inputs([self.row()])
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(CollectionAuditError, "source byte digest"):
            self.audit.build(snapshot, source_path=path, source_root=self.root)
        with self.assertRaisesRegex(CollectionAuditError, "escapes"):
            self.audit.build(snapshot, source_path=ROOT / "README.md", source_root=self.root)

    def test_canonical_drift_fails_closed(self):
        path, _, snapshot = self.inputs([self.row()])
        changed = copy.copy(self.resolver)
        changed.canonical_digest = "0" * 64
        with self.assertRaisesRegex(CollectionAuditError, "canonical snapshot changed"):
            CollectionAudit(changed).build(snapshot, source_path=path, source_root=self.root)

    def test_public_reconstruction_replays_whole_document_and_is_immutable(self):
        dossier, path, _, snapshot = self.build([self.row()], candidate_printing_ids=[PONDER])
        bound = {"resolver": self.resolver, "snapshot": snapshot, "source_path": path, "source_root": self.root}
        replay = CollectionAuditDossier.reconstruct(dossier.to_dict(), **bound)
        self.assertEqual(replay.to_json(), dossier.to_json())
        with self.assertRaises(TypeError):
            dossier["cards"][0]["review_status"] = "reviewed"
        with self.assertRaises(FrozenInstanceError):
            dossier._document = {}
        changed = dossier.to_dict()
        changed["cards"][0]["ever_reviewed"] = True
        changed["audit_digest"] = digest({k: v for k, v in changed.items() if k != "audit_digest"})
        with self.assertRaisesRegex(CollectionAuditError, "reproduce"):
            CollectionAuditDossier.reconstruct(changed, **bound)
        with self.assertRaises(TypeError):
            CollectionAuditDossier(dossier.to_dict())

    def test_exact_card_query_keeps_dimension_conflicts_and_name_ambiguity(self):
        dossier, _, _, _ = self.build([self.row(), self.row(1, alias="conflict", finish="foil"),
                                     {"card_name": "Sol Ring", "quantity": 2}])
        card_id = self.resolver.printings[PONDER]["card_id"]
        query = self.audit.query(dossier, card_id=card_id)
        self.assertEqual(len(query["unresolved_holding_refs"]), 1)
        self.assertEqual(query["ownership_state"], "incomplete_or_conflicting")
        self.assertTrue(json.loads(canonical_json(query))["source_classification"]["synthetic"])
        self.assertFalse(query["boundaries"]["purchase_execution"])
        self.assertEqual(self.audit.query(dossier, card_name="Sol Ring")["identity_state"], "ambiguous")
        self.assertEqual(len(self.audit.query(dossier, printing_id=PONDER)["unresolved_holding_refs"]), 1)
        with self.assertRaises(CollectionAuditError):
            self.audit.query(dossier.to_dict(), card_id=card_id)

    def test_bounded_context_preserves_global_counts_and_synthetic_classification(self):
        dossier, _, _, _ = self.build([self.row(storage_location="x" * 100000)], expected_total=3)
        self.assertGreater(len(dossier.to_json().encode()), 65536)
        context = dossier.reasoning_context(max_bytes=4096)
        self.assertLessEqual(len(canonical_json(context)), 4096)
        self.assertEqual(context["serialized_byte_count"], len(canonical_json(context)))
        self.assertEqual(context["omissions"]["holdings"]["omitted"], 1)
        self.assertEqual(context["quantity_census"]["confirmed_total_quantity"], 3)
        empty = dossier.reasoning_context(max_holdings=0, max_cards=0, max_assessments=0)
        self.assertTrue(empty["source_classification"]["synthetic"])
        self.assertFalse(empty["source_classification"]["real_user_inventory"])
        self.assertEqual(empty["review_census"]["review_basis_counts"]["approved_human_assessments"], 0)
        self.assertFalse(empty["boundaries"]["role_approval"])
        self.assertFalse(empty["boundaries"]["purchase_execution"])
        with self.assertRaisesRegex(CollectionAuditError, "exceeds"):
            dossier.reasoning_context(max_bytes=1)


if __name__ == "__main__":
    unittest.main()
