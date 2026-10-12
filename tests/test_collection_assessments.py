"""Personal review history preserves sources, provenance, and manual boundaries."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from collection.assessments import (CollectionAssessment, CollectionAssessmentError,
    CollectionAssessmentRepository, assessment_inventory_compatible,
    assessment_review_states, validate_assessment_history)
from collection.audit import CollectionAudit
from collection.intelligence import CanonicalCollectionResolver, canonical_json, create_snapshot, digest, read_import


ROOT = Path(__file__).resolve().parents[1]
PONDER = "02090581-61aa-4348-ad57-451be8ee91c2"
PONDER_PRINTING = "5c8d3bc4-32fc-5b26-84bf-9921e5884d43"
FAITHLESS = "3d6fa57a-aa53-4b5c-b8af-a7612c823117"
FAITHLESS_PRINTING = "72783a15-4847-5448-8f1d-0c40379594d3"


class CollectionAssessmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resolver = CanonicalCollectionResolver("magic", ROOT / "data")

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.source_path = self.root / "inventory.json"
        self.source_path.write_bytes(canonical_json({"schema_version": "collection-import-v1",
            "collection_id": "fictional-collection", "source": {"type": "synthetic_fixture", "name": "inventory"},
            "entries": [{"printing_id": printing, "card_id": card, "quantity": 1,
                         "finish": "nonfoil", "language": "English",
                         "provenance": {"organization": {"schema_version": "collection-organization-v1",
                                                          "storage_classification": "bulk"}}}
                        for card, printing in [(PONDER, PONDER_PRINTING), (FAITHLESS, FAITHLESS_PRINTING)]]}))
        imported = read_import(self.source_path)
        self.snapshot = create_snapshot(imported, self.resolver.resolve(imported),
            self.data / "collections" / "snapshots", "fictional-snapshot")
        self.counter = 0

    def claim(self, **updates):
        card = updates.get("card_id", PONDER)
        printings = sorted({x["printing_id"] for x in self.snapshot["resolved_holdings"] if x["card_id"] == card})
        claim = {"collection_id": "fictional-collection", "card_id": card,
            "purpose": "personal_collection_review", "status": "reviewed", "outcome": "fictional keep",
            "reason": "Fictional user review example; no actual attestation.",
            "assessed_at": "2026-10-10T10:00:00Z", "recorded_at": "2026-10-10T11:00:00Z",
            "assessment_version": "fictional-review-v1", "prior_assessment_id": None, "supersedes": [],
            "manual_reassessment_trigger": None,
            "human_review": {"kind": "synthetic_mock", "approved": False, "reviewer": None, "review_reference": None},
            "snapshot_binding": {"snapshot_id": self.snapshot["snapshot_id"],
                "snapshot_digest": self.snapshot["snapshot_digest"], "source_import_digest": self.snapshot["source_import_digest"],
                "canonical_snapshot_id": self.snapshot["canonical_snapshot_id"], "resolved_printing_ids": printings,
                "source_import_reference": {"relative_path": "inventory.json", "sha256": self.snapshot["source_import_digest"]}},
            "evidence_references": [{"source_id": "fictional-review", "source_type": "synthetic_fixture",
                "reference": "inventory.json#/entries/0", "observed_at": "2026-10-10T09:00:00Z",
                "claim": "Fictional source-bound personal review, not a role or canonical approval."}]}
        claim.update(updates)
        return claim

    def record(self, claim=None, *, snapshot=None, trusted=False, synthetic=True):
        self.counter += 1
        path = self.root / f"review-{self.counter}.json"
        path.write_bytes(canonical_json({"synthetic": synthetic, "claim": claim or self.claim()}))
        return CollectionAssessment.from_source(path, self.root, snapshot=snapshot or self.snapshot,
            trusted_human_review=trusted)

    def reassessment(self, prior, **updates):
        claim = {k: v for k, v in prior.to_dict().items() if k not in {"schema_version", "assessment_id", "source"}}
        claim.update(status="reassessment_needed", prior_assessment_id=prior.payload["assessment_id"],
            supersedes=[prior.payload["assessment_id"]], recorded_at="2026-10-11T11:00:00Z",
            manual_reassessment_trigger="User manually requested review after changing their collection objective.")
        claim.update(updates)
        return self.record(claim)

    def test_append_replay_manual_reassessment_and_ever_reviewed(self):
        first = self.record()
        later = self.reassessment(first)
        repository = CollectionAssessmentRepository(self.data, self.root, resolver=self.resolver)
        first_path = repository.append(first)
        first_bytes = first_path.read_bytes()
        self.assertEqual(repository.append(first), first_path)
        repository.append(later)
        self.assertEqual(first_path.read_bytes(), first_bytes)
        self.assertEqual(len(repository.all()), 2)
        state = assessment_review_states(repository.all(), collection_id="fictional-collection")[PONDER]
        self.assertEqual(state["status"], "reassessment_needed")
        self.assertTrue(state["ever_reviewed"])
        self.assertEqual(state["review_basis"], "synthetic_mock")
        self.assertFalse(later.payload["human_review"]["approved"])
        self.assertEqual(later.payload["outcome"], first.payload["outcome"])
        self.assertEqual(state["history_ids"], [first.payload["assessment_id"], later.payload["assessment_id"]])

    def test_pending_never_reviewed_and_later_pending_preserves_history(self):
        pending = self.record(self.claim(status="pending", outcome=None,
            human_review={"kind": "not_applicable", "approved": False, "reviewer": None, "review_reference": None}))
        self.assertFalse(assessment_review_states([pending], collection_id="fictional-collection")[PONDER]["ever_reviewed"])
        reviewed = self.record()
        change = self.record(self.claim(status="pending", prior_assessment_id=reviewed.payload["assessment_id"],
            supersedes=[reviewed.payload["assessment_id"]], recorded_at="2026-10-11T11:00:00Z"))
        self.assertTrue(assessment_review_states([change, reviewed], collection_id="fictional-collection")[PONDER]["ever_reviewed"])

    def test_missing_parent_forks_subject_purpose_and_backwards_time_fail(self):
        first = self.record()
        later = self.reassessment(first)
        with self.assertRaisesRegex(CollectionAssessmentError, "missing prior"):
            validate_assessment_history([later])
        fork = self.reassessment(first, recorded_at="2026-10-12T11:00:00Z")
        with self.assertRaisesRegex(CollectionAssessmentError, "fork"):
            validate_assessment_history([first, later, fork])
        for updates in [{"card_id": FAITHLESS}, {"purpose": "another-purpose"},
                        {"recorded_at": "2026-10-10T11:00:00Z"}]:
            changed = self.record(self.claim(prior_assessment_id=first.payload["assessment_id"],
                supersedes=[first.payload["assessment_id"]], **updates))
            with self.assertRaises(CollectionAssessmentError):
                validate_assessment_history([first, changed])
        with self.assertRaisesRegex(CollectionAssessmentError, "conflicting assessment roots"):
            validate_assessment_history([first, self.record()])

    def test_manual_trigger_cannot_replace_the_prior_assessment(self):
        first = self.record()
        for updates in [{"outcome": "new computed outcome"}, {"assessment_version": "new-method"},
                        {"assessed_at": "2026-10-11T10:00:00Z"}]:
            changed = self.reassessment(first, **updates)
            with self.assertRaisesRegex(CollectionAssessmentError, "preserve"):
                validate_assessment_history([first, changed])
        with self.assertRaises(CollectionAssessmentError):
            self.record(self.claim(status="reassessment_needed", manual_reassessment_trigger="manual request"))

    def test_source_claim_changes_and_raw_source_tampering_fail(self):
        record = self.record()
        changed = record.to_dict()
        changed["outcome"] = "tampered"
        changed["assessment_id"] = "sha256:" + digest({k: v for k, v in changed.items() if k != "assessment_id"})
        with self.assertRaisesRegex(CollectionAssessmentError, "exact retained claim"):
            CollectionAssessment(changed, self.root, snapshot=self.snapshot)
        source = self.root / record.payload["source"]["relative_path"]
        source.write_bytes(source.read_bytes() + b" ")
        with self.assertRaisesRegex(CollectionAssessmentError, "source digest"):
            record.validate()

    def test_rehashed_snapshot_cannot_fabricate_old_owned_quantities_or_card(self):
        for mutate in ("quantity", "card"):
            forged = copy.deepcopy(self.snapshot)
            if mutate == "quantity":
                forged["resolved_holdings"][0]["row"]["quantity"] = 999
                forged["inventory"]["total_quantity"] = 1000
            else:
                forged["resolved_holdings"][0]["card_id"] = FAITHLESS
                forged["resolved_holdings"][0]["printing_id"] = FAITHLESS_PRINTING
            forged["snapshot_digest"] = digest({k: v for k, v in forged.items() if k != "snapshot_digest"})
            claim = self.claim()
            claim["snapshot_binding"]["snapshot_digest"] = forged["snapshot_digest"]
            with self.assertRaises(CollectionAssessmentError):
                self.record(claim, snapshot=forged)

    def test_real_human_approval_requires_trusted_caller_and_known_metadata(self):
        human = {"kind": "human", "approved": True, "reviewer": "fixture-human-example", "review_reference": "retained-user-review"}
        claim = self.claim(human_review=human)
        with self.assertRaisesRegex(CollectionAssessmentError, "trusted"):
            self.record(claim, synthetic=False)
        real = self.record(claim, trusted=True, synthetic=False)
        self.assertTrue(real.payload["human_review"]["approved"])
        with self.assertRaisesRegex(CollectionAssessmentError, "synthetic source"):
            self.record(claim, trusted=True)
        with self.assertRaisesRegex(CollectionAssessmentError, "known reviewer"):
            self.record(self.claim(human_review={**human, "reviewer": "unknown"}), trusted=True, synthetic=False)
        with self.assertRaises(CollectionAssessmentError):
            self.record(self.claim(assessment_version="unknown"))
        with self.assertRaises(CollectionAssessmentError):
            self.record(self.claim(human_review={**human, "kind": "synthetic_mock"}), trusted=True)

    def test_mock_review_cannot_be_bound_to_real_or_unclassified_inventory(self):
        original = json.loads(self.source_path.read_bytes())
        review_files = []
        for source in (
                {"type": "user_inventory", "synthetic": False, "real_user_inventory": True},
                {"type": "user_inventory"},
                {"type": "synthetic_fixture", "synthetic": False, "real_user_inventory": False},
                {"type": "synthetic_fixture", "synthetic": True, "real_user_inventory": True},
                {"type": "synthetic_fixture", "synthetic": "true"},
                {"type": "synthetic_fixture", "synthetic": True, "mode": []}):
            with self.subTest(source=source):
                inventory = {**original, "source": source}
                self.source_path.write_bytes(canonical_json(inventory))
                imported = read_import(self.source_path)
                self.snapshot = create_snapshot(imported, self.resolver.resolve(imported),
                    self.data / "collections" / "snapshots")
                for trusted in (False, True):
                    with self.assertRaisesRegex(CollectionAssessmentError, "synthetic inventory"):
                        self.record(trusted=trusted)
                    review_files.append((self.root / f"review-{self.counter}.json").read_bytes())
                repository = CollectionAssessmentRepository(self.data, self.root,
                    trusted_human_review=True, resolver=self.resolver)
                self.assertEqual(repository.all(), ())
                self.assertEqual(self.source_path.read_bytes(), canonical_json(inventory))
        self.assertEqual(len(review_files), 12)
        self.assertTrue(all(json.loads(raw)["synthetic"] for raw in review_files))

    def test_mock_history_is_nonoperative_when_current_inventory_becomes_real(self):
        first = self.record()
        later = self.reassessment(first)
        real_source = {"type": "user_inventory", "synthetic": False, "real_user_inventory": True}
        original_records = [first.to_dict(), later.to_dict()]
        state = assessment_review_states([later, first], collection_id="fictional-collection",
            inventory_source=real_source)[PONDER]
        self.assertEqual(state["status"], "pending")
        self.assertFalse(state["ever_reviewed"])
        self.assertIsNone(state["assessment_id"])
        self.assertIsNone(state["review_basis"])
        self.assertEqual(state["history_ids"], [first.payload["assessment_id"], later.payload["assessment_id"]])
        self.assertEqual([first.to_dict(), later.to_dict()], original_records)
        self.assertFalse(assessment_inventory_compatible(first.payload, source=real_source))
        synthetic_state = assessment_review_states([first, later], collection_id="fictional-collection",
            inventory_source=self.snapshot["source"])[PONDER]
        self.assertTrue(synthetic_state["ever_reviewed"])
        self.assertEqual(synthetic_state["status"], "reassessment_needed")

    def test_actual_review_can_supersede_mock_and_later_mock_cannot_override_it(self):
        first = self.record()
        synthetic_snapshot = self.snapshot
        inventory = json.loads(self.source_path.read_bytes())
        inventory["source"] = {"type": "user_inventory", "synthetic": False, "real_user_inventory": True}
        real_import_path = self.root / "real-inventory.json"
        real_import_path.write_bytes(canonical_json(inventory))
        imported = read_import(real_import_path)
        self.snapshot = create_snapshot(imported, self.resolver.resolve(imported),
            self.data / "collections" / "snapshots", "real-snapshot")
        claim = self.claim(prior_assessment_id=first.payload["assessment_id"],
            supersedes=[first.payload["assessment_id"]], recorded_at="2026-10-11T11:00:00Z",
            human_review={"kind": "human", "approved": True, "reviewer": "fixture-human-review",
                          "review_reference": "retained-user-review"})
        claim["snapshot_binding"]["source_import_reference"]["relative_path"] = "real-inventory.json"
        actual = self.record(claim, trusted=True, synthetic=False)
        self.snapshot = synthetic_snapshot
        later_mock = self.record(self.claim(status="pending", outcome=None,
            prior_assessment_id=actual.payload["assessment_id"], supersedes=[actual.payload["assessment_id"]],
            recorded_at="2026-10-12T11:00:00Z"))
        state = assessment_review_states([later_mock, first, actual], collection_id="fictional-collection",
            inventory_source=inventory["source"])[PONDER]
        self.assertEqual(state["status"], "reviewed")
        self.assertTrue(state["ever_reviewed"])
        self.assertEqual(state["assessment_id"], actual.payload["assessment_id"])
        self.assertEqual(state["review_basis"], "human")
        self.assertEqual(state["history_ids"], [x.payload["assessment_id"] for x in (first, actual, later_mock)])

    def test_collection_reader_scopes_validated_complete_chains(self):
        first = self.record()
        later = self.reassessment(first)
        repository = CollectionAssessmentRepository(self.data, self.root, resolver=self.resolver)
        repository.append(first)
        repository.append(later)
        inventory = json.loads(self.source_path.read_bytes())
        inventory["collection_id"] = "second-collection"
        source = self.root / "second-inventory.json"
        source.write_bytes(canonical_json(inventory))
        imported = read_import(source)
        self.snapshot = create_snapshot(imported, self.resolver.resolve(imported),
            self.data / "collections" / "snapshots", "second-snapshot")
        claim = self.claim(collection_id="second-collection")
        claim["snapshot_binding"]["source_import_reference"]["relative_path"] = "second-inventory.json"
        second = self.record(claim)
        repository.append(second)
        self.assertEqual(repository.for_collection("fictional-collection"), (first, later))
        self.assertEqual(repository.for_collection("second-collection"), (second,))
        self.assertEqual(repository.for_collection("missing-collection"), ())
        self.assertEqual(len(repository.all()), 3)
        changed_claim = {**claim, "prior_assessment_id": first.payload["assessment_id"],
            "supersedes": [first.payload["assessment_id"]], "recorded_at": "2026-10-12T11:00:00Z"}
        invalid_child = self.record(changed_claim)
        with self.assertRaisesRegex(CollectionAssessmentError, "preserve collection"):
            repository.append(invalid_child)
        # A malformed cross-collection chain must not disappear behind the reader's filter.
        invalid_path = repository.root / f"{invalid_child.payload['assessment_id'].removeprefix('sha256:')}.json"
        invalid_path.write_bytes(canonical_json(invalid_child.to_dict()))
        with self.assertRaisesRegex(CollectionAssessmentError, "preserve collection"):
            repository.for_collection("fictional-collection")

    def test_timestamp_shape_synthetic_label_and_import_path_are_explicit(self):
        for timestamp in ("2026-10-10Z", "2026-10-10T10:00:00+01:00Z", "2026-02-30T10:00:00Z"):
            with self.assertRaises(CollectionAssessmentError):
                self.record(self.claim(assessed_at=timestamp))
        with self.assertRaisesRegex(CollectionAssessmentError, "explicitly synthetic"):
            self.record(synthetic=False)
        claim = self.claim()
        claim["snapshot_binding"]["source_import_reference"]["relative_path"] = "../inventory.json"
        with self.assertRaises(CollectionAssessmentError):
            self.record(claim)
        for invalid in (self.claim(status=[]), self.claim(human_review={"kind": [], "approved": False,
                        "reviewer": None, "review_reference": None})):
            with self.assertRaises(CollectionAssessmentError):
                self.record(invalid)

    def test_repository_verifies_original_snapshot_and_never_overwrites_conflict(self):
        repository = CollectionAssessmentRepository(self.data, self.root, resolver=self.resolver)
        record = self.record()
        path = repository.append(record)
        retained = path.read_bytes()
        path.write_bytes(retained + b" ")
        with self.assertRaises(CollectionAssessmentError):
            repository.append(record)
        self.assertEqual(path.read_bytes(), retained + b" ")
        path.write_bytes(retained)
        snapshot_path = self.data / "collections" / "snapshots" / "fictional-snapshot.json"
        modified = json.loads(snapshot_path.read_bytes())
        modified["resolved_holdings"][0]["row"]["quantity"] = 999
        modified["snapshot_digest"] = digest({k: v for k, v in modified.items() if k != "snapshot_digest"})
        snapshot_path.write_bytes(canonical_json(modified))
        with self.assertRaises(CollectionAssessmentError):
            repository.all()
        with self.assertRaises(CollectionAssessmentError):
            CollectionAssessmentRepository(self.data, self.root, assessment_root=self.root / "another-store")

    def test_audit_excludes_formerly_reviewed_bulk_from_discovery_and_pending_bulk(self):
        first = self.record()
        later = self.reassessment(first)
        audit = CollectionAudit(self.resolver).build(self.snapshot, source_path=self.source_path,
            source_root=self.root, assessments=[later, first])
        cards = {x["card_id"]: x for x in audit["cards"]}
        self.assertEqual(cards[PONDER]["review_status"], "reassessment_needed")
        self.assertTrue(cards[PONDER]["ever_reviewed"])
        self.assertFalse(cards[PONDER]["new_discovery_eligible"])
        self.assertFalse(cards[PONDER]["unreviewed_bulk_eligible"])
        self.assertEqual(cards[FAITHLESS]["review_status"], "pending")
        self.assertTrue(cards[FAITHLESS]["unreviewed_bulk_eligible"])
        status_sets = [set(audit["review_census"][status]) for status in
                       ("reviewed", "pending", "unresolved", "reassessment_needed")]
        self.assertEqual(sum(map(len, status_sets)), len(set.union(*status_sets)))
        self.assertEqual(len(set.union(*status_sets)), len(cards))
        self.assertFalse(audit["boundaries"]["automatic_reassessment"])

    def test_repository_cannot_admit_a_candidate_with_another_source_or_trust_boundary(self):
        approved = self.record(self.claim(human_review={"kind": "human", "approved": True,
            "reviewer": "example-user", "review_reference": "user-supplied-review"}), trusted=True, synthetic=False)
        repository = CollectionAssessmentRepository(self.data, self.root, resolver=self.resolver)
        with self.assertRaisesRegex(CollectionAssessmentError, "trusted"):
            repository.append(approved)
        self.assertEqual(repository.all(), ())
        elsewhere = self.root / "another-root"
        elsewhere.mkdir()
        wrong_root = CollectionAssessmentRepository(self.data, elsewhere, resolver=self.resolver)
        with self.assertRaises(CollectionAssessmentError):
            wrong_root.append(self.record())
        self.assertEqual(wrong_root.all(), ())

    def test_repository_replays_canonical_card_mapping_before_admission(self):
        imported = json.loads(self.source_path.read_bytes())
        for row in imported["entries"]:
            row.pop("card_id")
        self.source_path.write_bytes(canonical_json(imported))
        imported = read_import(self.source_path)
        snapshot = create_snapshot(imported, self.resolver.resolve(imported),
            self.data / "collections" / "snapshots", "printing-only-snapshot")
        forged = copy.deepcopy(snapshot)
        forged["resolved_holdings"][0]["card_id"] = FAITHLESS
        forged["resolved_holdings"][0]["canonical_reference"]["card"] = forged["resolved_holdings"][1]["canonical_reference"]["card"]
        forged["snapshot_digest"] = digest({k: v for k, v in forged.items() if k != "snapshot_digest"})
        claim = self.claim(card_id=FAITHLESS)
        claim["snapshot_binding"] = {"snapshot_id": forged["snapshot_id"], "snapshot_digest": forged["snapshot_digest"],
            "source_import_digest": forged["source_import_digest"], "canonical_snapshot_id": forged["canonical_snapshot_id"],
            "resolved_printing_ids": sorted([PONDER_PRINTING, FAITHLESS_PRINTING]),
            "source_import_reference": {"relative_path": "inventory.json", "sha256": forged["source_import_digest"]}}
        candidate = self.record(claim, snapshot=forged)
        (self.data / "collections" / "snapshots" / "printing-only-snapshot.json").write_bytes(canonical_json(forged))
        repository = CollectionAssessmentRepository(self.data, self.root, resolver=self.resolver)
        with self.assertRaisesRegex(CollectionAssessmentError, "does not replay"):
            repository.append(candidate)
        self.assertEqual(repository.all(), ())


if __name__ == "__main__":
    unittest.main()
