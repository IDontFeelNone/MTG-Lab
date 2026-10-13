"""PR #171 packet regressions using retained evidence and temporary tamper copies."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from scripts import verify_mb2_reference_packet as packet


class MB2ReferencePacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.documents = packet.derive()
        cls.summary = json.loads(cls.documents["review-summary.json"])

    def copy_packet(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name) / "packet"
        shutil.copytree(packet.PACKET, target)
        return target

    def rehash(self, target):
        base = target / packet.REVISION
        manifest = packet.read(base / "manifest.json")
        manifest["files"] = {p.relative_to(base).as_posix(): {
            "bytes": len(p.read_bytes()), "sha256": packet.digest(p.read_bytes())}
            for p in sorted(base.rglob("*")) if p.is_file() and p != base / "manifest.json"}
        (base / "manifest.json").write_bytes(packet.encoded(manifest))

    def test_file_manifest_integrity_and_exact_offline_replay(self):
        self.assertEqual(packet.verify(), self.summary)
        for name, raw in self.documents.items():
            self.assertEqual((packet.PACKET / packet.REVISION / name).read_bytes(), raw)

    def test_unchanged_relocated_packet_validates_against_repository_dependencies(self):
        target = self.copy_packet()
        self.assertNotEqual(target.resolve(), packet.PACKET.resolve())
        self.assertEqual(packet.verify(target, root=packet.ROOT), self.summary)

    def test_schema_valid_historical_source_changes_rejected_in_relocated_packet(self):
        changes = {
            "title": "Altered historical source title",
            "source_location": "https://magic.wizards.com/en/news/feature/altered-source",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                target = self.copy_packet()
                path = target / "source-record.json"
                source = packet.read(path)
                source[field] = value
                # Both substitutions still satisfy the source-record schema;
                # the unchanged historical manifest must reject their bytes.
                packet.validate_document(source, "source-record")
                path.write_bytes(packet.encoded(source))
                with self.assertRaisesRegex(ValueError, "manifest integrity mismatch"):
                    packet.verify(target, root=packet.ROOT)

    def test_missing_relocated_historical_file_rejected_without_checkout_fallback(self):
        target = self.copy_packet()
        name = "acquisition-limitations.json"
        self.assertTrue((packet.PACKET / name).is_file())
        historical_manifest = packet.read(target / "review-manifest.json")
        self.assertIn(f"reference-reviews/mb2-reference-coverage/{name}",
                      historical_manifest["files"])
        (target / name).unlink()
        with self.assertRaisesRegex(ValueError, "manifest.*missing"):
            packet.verify(target, root=packet.ROOT)

    def test_historical_manifest_parent_path_escape_rejected_by_full_verifier(self):
        target = self.copy_packet()
        path = target / "review-manifest.json"
        manifest = packet.read(path)
        key = "reference-reviews/mb2-reference-coverage/source-record.json"
        # Resolving this repository-relative spelling points at the original
        # checkout file. It must not serve as an alternate packet source.
        escaped = "reference-reviews/mb2-reference-coverage/../mb2-reference-coverage/source-record.json"
        manifest["files"][escaped] = manifest["files"].pop(key)
        path.write_bytes(packet.encoded(manifest))
        with self.assertRaisesRegex(ValueError, "manifest path escape"):
            packet.verify(target, root=packet.ROOT)

    def test_historical_packet_symlink_escape_rejected_by_full_verifier(self):
        target = self.copy_packet()
        path = target / "source-record.json"
        path.unlink()
        path.symlink_to(packet.PACKET / "source-record.json")
        # The target has the exact expected bytes, but lies outside this copy.
        with self.assertRaisesRegex(ValueError, "manifest path escape"):
            packet.verify(target, root=packet.ROOT)

    def test_source_to_parsed_counts_identity_and_pending_provenance(self):
        parsed = json.loads(self.documents["parsed-records.json"])
        candidates = json.loads(self.documents["candidate-preparation.json"])
        self.assertEqual(parsed["record_count"], 273)
        self.assertEqual(candidates["candidate_count"], 819)
        self.assertEqual(validate_candidate_artifact(candidates, parsed).state,
                         CandidateValidationState.VALID)
        ids = {r["id"] for r in parsed["records"]}
        for candidate in candidates["candidates"]:
            self.assertEqual(candidate["validation_state"], "requires_review")
            self.assertEqual(candidate["payload"]["review_status"], "pending")
            self.assertTrue(set(candidate["parsed_record_ids"]) <= ids)
            for provenance in candidate["field_provenance"]:
                self.assertIn(provenance["parsed_record_id"], ids)
                self.assertEqual(provenance["raw_evidence_hash"], parsed["raw_evidence_hash"])

    def test_existing_references_snapshot_emblem_and_dependency_closure(self):
        state, _ = packet.check_original()
        self.assertEqual(self.summary["canonical_snapshot_id"], packet.SNAPSHOT)
        self.assertEqual(self.summary["candidate_counts"], {"card": 273, "printing": 273, "identifier": 273})
        self.assertEqual(self.summary["reused_dependencies"], [{"canonical_id": "nonfoil", "entity_type": "finish"}])
        self.assertTrue(self.summary["dependency_closure_valid"])
        candidates = json.loads(self.documents["candidate-preparation.json"])["candidates"]
        card_ids = {c["payload"]["mapped_fields"]["card_reference"] for c in candidates if c["entity_type"] == "card"}
        printing_ids = {c["payload"]["mapped_fields"]["uuid"] for c in candidates if c["entity_type"] == "printing"}
        self.assertFalse(card_ids & set(state["card"]))
        self.assertFalse(printing_ids & set(state["printing"]))
        for c in candidates:
            fields = c["payload"]["mapped_fields"]
            if c["entity_type"] == "printing":
                self.assertIn(fields["card_reference"], card_ids)
                self.assertLessEqual(set(fields["finishes"]), set(state["finish"]))
            elif c["entity_type"] == "identifier":
                self.assertIn(fields["printing_uuid"], printing_ids)
                self.assertEqual(fields["namespace"], "scryfallId")

    def test_saved_projections_do_not_claim_unretained_upstream_or_owner_confirmation(self):
        receipts = packet.read(packet.PACKET / packet.REVISION / "source-receipts.json")
        for key, receipt in receipts.items():
            if key != "provider-checksums":
                self.assertFalse(receipt["upstream_git_retained"])
                self.assertIn("projection" if key != "plst-mb2-records" else "exact", receipt["capture"])
        correspondence = json.loads(self.documents["correspondence.json"])
        self.assertEqual(len({r["oracle_id"] for r in correspondence}), 273)
        japanese = next(r for r in correspondence if r["catalog_label"] == "Gigantosaurus")
        self.assertEqual((japanese["provider_set"], japanese["collector_number"], japanese["provider_language"]),
                         ("PLST", "M19-185j", "ja"))
        for row in correspondence:
            self.assertFalse(row["physical_copy_assignment"])
            self.assertFalse(row["owner_spelling_confirmation"])
        self.assertEqual(self.summary["catalog_card_coverage"], {"current": 0, "conditional": 273})
        self.assertFalse(self.summary["production_coverage_increased"])
        self.assertFalse(self.summary["entity_admission_ready"])

    def test_altered_source_bytes_rejected_in_temporary_copy(self):
        target = self.copy_packet()
        receipt = packet.read(target / packet.REVISION / "source-receipts.json")["plst-mb2-records"]
        path = target / packet.REVISION / receipt["path"] / "payload.bin"
        path.write_bytes(path.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "integrity mismatch"):
            packet.verify(target)

    def test_unmanifested_evidence_rejected(self):
        target = self.copy_packet()
        (target / packet.REVISION / "extra.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "unmanifested evidence"):
            packet.verify(target)

    def test_rehashed_source_path_escape_rejected_before_reading(self):
        target = self.copy_packet()
        path = target / packet.REVISION / "source-receipts.json"
        value = packet.read(path)
        value["plst-mb2-records"]["path"] = "../../../../outside"
        path.write_bytes(packet.encoded(value))
        self.rehash(target)
        with self.assertRaisesRegex(ValueError, "source path escape"):
            packet.verify(target)

    def test_rehashed_parsed_row_or_count_changes_rejected(self):
        for field in ("record_count", "raw_fields"):
            with self.subTest(field=field):
                target = self.copy_packet()
                path = target / packet.REVISION / "parsed-records.json"
                value = packet.read(path)
                if field == "record_count":
                    value[field] -= 1
                else:
                    value["records"][0][field]["name"] = "Forged name"
                path.write_bytes(packet.encoded(value))
                self.rehash(target)
                with self.assertRaisesRegex(ValueError, "deterministic replay mismatch"):
                    packet.verify(target)

    def test_rehashed_candidate_dependency_provenance_and_approval_changes_rejected(self):
        changes = {
            "approval": lambda c: c["payload"].update(review_status="approved"),
            "source": lambda c: c["field_provenance"][0].update(raw_evidence_hash="0" * 64),
            "orphan": lambda c: c["payload"]["mapped_fields"].update(card_reference="missing-card"),
            "review_state": lambda c: c.update(validation_state="valid"),
        }
        for label, change in changes.items():
            with self.subTest(change=label):
                target = self.copy_packet()
                path = target / packet.REVISION / "candidate-preparation.json"
                value = packet.read(path)
                candidate = next(c for c in value["candidates"] if c["entity_type"] == "printing")
                change(candidate)
                payload = candidate["payload"]
                payload["candidate_hash"] = packet.digest(packet.deterministic_json(
                    {k: v for k, v in payload.items() if k != "candidate_hash"}).encode())
                path.write_bytes(packet.encoded(value))
                self.rehash(target)
                with self.assertRaisesRegex(ValueError, "deterministic replay mismatch"):
                    packet.verify(target)

    def test_rehashed_false_summary_and_manifest_approval_claims_rejected(self):
        target = self.copy_packet()
        path = target / packet.REVISION / "review-summary.json"
        value = packet.read(path)
        value.update(human_approvals=819, entity_admission_ready=True, review_status="approved")
        path.write_bytes(packet.encoded(value))
        self.rehash(target)
        with self.assertRaisesRegex(ValueError, "deterministic replay mismatch"):
            packet.verify(target)
        path = target / packet.REVISION / "manifest.json"
        value = packet.read(path)
        value.update(human_approvals=819, review_status="approved")
        path.write_bytes(packet.encoded(value))
        with self.assertRaisesRegex(ValueError, "false approval claim"):
            packet.verify(target)

    def test_rehashed_false_upstream_byte_claim_rejected(self):
        target = self.copy_packet()
        base = target / packet.REVISION
        path = base / "source-receipts.json"
        receipts = packet.read(path)
        receipts["plst-mb2-records"]["upstream_git_retained"] = True
        path.write_bytes(packet.encoded(receipts))
        # Also forge the raw metadata, demonstrating that agreeing inner hashes
        # and an updated outer manifest cannot establish retention.
        path = base / receipts["plst-mb2-records"]["path"] / "provider-metadata.json"
        value = packet.read(path)
        value["provider"]["upstream_git_retained"] = True
        path.write_bytes(packet.encoded(value))
        self.rehash(target)
        with self.assertRaisesRegex(ValueError, "false upstream retention claim"):
            packet.verify(target)

    def test_existing_snapshot_or_card_reference_changes_rejected(self):
        for key, value in (("query_snapshot_id", "sha256:" + "0" * 64),
                           ("canonical_card_id", "missing-card")):
            with self.subTest(field=key):
                target = self.copy_packet()
                path = target / "existing-reference-reuse.json"
                refs = packet.read(path)
                refs["references"][0][key] = value
                path.write_bytes(packet.encoded(refs))
                with self.assertRaisesRegex(ValueError, "manifest integrity mismatch"):
                    packet.verify(target, root=packet.ROOT)


if __name__ == "__main__":
    unittest.main()
