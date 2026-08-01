"""Phase 112A native workflow artifact adapter tests (unittest only)."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from production_evidence import EvidenceError, ProductionEvidenceRepository, WorkflowArtifactAdapter


SOURCE = "a" * 64
RUN = "30663562841"


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class WorkflowArtifactAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def fixture(self, mutate=None, extra=None):
        root = f"streaming/{SOURCE}"
        members, batches = {}, []
        for code, name, unit in (("MB2", "Mystery Booster 2", "000334-mb2"),
                                 ("MSH", "Marvel Super Heroes", "000373-msh")):
            candidate_ids = [f"card-{code.lower()}", f"printing-{code.lower()}"]
            digest = identity(candidate_ids)
            card_reference = f"oracle-{code.lower()}"
            shard = encoded({"set_code": code, "candidates": [
                {"candidate_identifier": candidate_ids[0], "entity_type": "card",
                 "mapped_fields": {"card_reference": card_reference}},
                {"candidate_identifier": candidate_ids[1], "entity_type": "printing",
                 "mapped_fields": {"card_reference": card_reference, "set_code": code.lower()}},
                {"candidate_identifier": f"unrelated-{code.lower()}", "entity_type": "finish",
                 "mapped_fields": {"value": "foil"}}]})
            shard_path = f"{root}/candidate-shards/{unit}.json"
            members[shard_path] = shard
            batch_id = f"{code.lower()}-batch-000001"
            batch_root = f"{root}/review-batches/{code}/{batch_id}"
            reference = {"path": f"/runner/{unit}.json", "sha256": hashlib.sha256(shard).hexdigest(),
                         "byte_length": len(shard)}
            package = {"review_status": "pending", "target_set_code": code,
                "target_set_name": name, "candidate_ids": candidate_ids,
                "candidate_payload_references": [reference], "identifier_findings": [],
                "source_lineage": {"dataset_identifier": f"mtgjson-allprintings-5.3.0-{SOURCE[:12]}",
                                   "source_sha256": SOURCE},
                "provenance": {"provider": "MTGJSON"}, "canonical_write": False,
                "promotion_performed": False}
            package_bytes = encoded(package)
            members[f"{batch_root}/candidate-ids.json"] = encoded({"target_set_code": code,
                "candidate_ids": candidate_ids, "candidate_id_digest": digest})
            members[f"{batch_root}/dependency-closure.json"] = encoded({"target_set_code": code,
                "candidate_ids": candidate_ids, "dependency_closure_digest": digest, "valid": True})
            members[f"{batch_root}/review-package.json"] = package_bytes
            batch = {"batch_id": batch_id, "target_set_code": code, "target_set_name": name,
                     "source_unit": unit, "candidate_ids": candidate_ids,
                     "candidate_id_digest": digest, "dependency_closure_digest": digest}
            members[f"{batch_root}/manifest.json"] = encoded({**batch,
                "review_package_sha256": hashlib.sha256(package_bytes).hexdigest(),
                "canonical_write": False, "promotion_performed": False})
            batches.append(batch)
        manifest = {"status": "awaiting_independent_review",
            "dataset_identifier": f"mtgjson-allprintings-5.3.0-{SOURCE[:12]}",
            "artifact_sha256": SOURCE, "batches": batches,
            "canonical_write": False, "promotion_performed": False}
        members[f"{root}/manifest.json"] = encoded(manifest)
        members[f"{root}/completed-sets.json"] = encoded({"source_sha256": SOURCE, "sets": {
            "000334-mb2": {"sha256": hashlib.sha256(members[
                f"{root}/candidate-shards/000334-mb2.json"]).hexdigest()},
            "000373-msh": {"sha256": hashlib.sha256(members[
                f"{root}/candidate-shards/000373-msh.json"]).hexdigest()}}})
        members[f"{root}/batch-index.json"] = encoded({"batches": batches})
        members["reports/mtgjson-delivery/checksum-verification.json"] = encoded({
            "actual_sha256": SOURCE, "valid": True, "canonical_write": False})
        members["reports/mtgjson-delivery/dataset-summary.json"] = encoded({
            "artifact_sha256": SOURCE,
            "dataset_identifier": f"mtgjson-allprintings-5.3.0-{SOURCE[:12]}"})
        members["mtg-lab-diagnostics/resources-after.log"] = b"exit_code=0\n"
        members["run-result.json"] = encoded({"mode": "dry-run", "manifest": manifest,
            "canonical_write": False, "promotion_performed": False})
        if mutate:
            mutate(members, batches, root)
        if extra:
            members.update(extra)
        archive = self.root / "native.zip"
        with zipfile.ZipFile(archive, "w") as target:
            for path, data in sorted(members.items()):
                target.writestr(path, data)
        return archive

    def normalize(self, archive, output="normalized"):
        return WorkflowArtifactAdapter().normalize(archive, run_id=RUN,
            artifact_name=f"mtgjson-ingestion-{RUN}", output=self.root / output,
            archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
            repository="owner/MTG-Lab", commit_sha="b" * 40)

    def test_native_archive_without_root_manifest_generates_deterministic_contract(self):
        archive = self.fixture()
        self.assertNotIn("manifest.json", zipfile.ZipFile(archive).namelist())
        first = self.normalize(archive, "one")
        second = self.normalize(archive, "two")
        self.assertEqual(first["normalized_zip_sha256"], second["normalized_zip_sha256"])
        manifest = json.loads((self.root / "one/manifest.json").read_text())
        self.assertEqual([x["code"] for x in manifest["target_set_identities"]], ["MB2", "MSH"])
        self.assertFalse(manifest["canonical_write"])
        self.assertFalse(manifest["promotion_performed"])
        self.assertTrue(all(x.startswith("review_batches/") for x in manifest["review_bundle_paths"]))
        self.assertEqual(manifest["retained_payload_count"], 4)
        payload = json.loads((self.root / "one/review_payloads/mb2/mb2-batch-000001.json").read_text())
        self.assertEqual([item["candidate_identifier"] for item in payload["candidate_payloads"]],
                         payload["candidate_ids"])
        self.assertNotIn("unrelated-mb2", str(payload))

    def test_normalized_output_passes_unchanged_phase_111_intake_and_is_idempotent(self):
        archive = self.fixture()
        result = self.normalize(archive)
        normalized = Path(result["normalized_archive"])
        digest = hashlib.sha256(normalized.read_bytes()).hexdigest()
        for name in ("repo-one", "repo-two"):
            repository = ProductionEvidenceRepository(self.root / name)
            identity_value = f"{RUN}-review-payload-v2"
            repository.intake(normalized, digest, identity_value)
            self.assertTrue(repository.verify(identity_value)["valid"])
        with self.assertRaisesRegex(EvidenceError, "duplicate production run"):
            ProductionEvidenceRepository(self.root / "repo-one").intake(
                normalized, digest, f"{RUN}-review-payload-v2")

    def test_safe_unique_paths_are_required(self):
        archive = self.fixture()
        with zipfile.ZipFile(archive, "a") as target:
            target.writestr("../escape.json", b"{}")
        with self.assertRaisesRegex(EvidenceError, "unsafe archive path"):
            self.normalize(archive)
        archive = self.fixture()
        with zipfile.ZipFile(archive, "a") as target:
            target.writestr("run-result.json", b"{}")
        with self.assertRaisesRegex(EvidenceError, "duplicate archive member"):
            self.normalize(archive, "duplicate")

    def test_missing_or_unsuccessful_run_result_is_rejected(self):
        cases = [
            (lambda m, b, r: m.pop("run-result.json"), "run-result"),
            (lambda m, b, r: m.__setitem__("run-result.json", encoded({"mode": "failed"})),
             "successful dry run"),
        ]
        for index, (mutation, message) in enumerate(cases):
            with self.subTest(index=index), self.assertRaisesRegex(EvidenceError, message):
                self.normalize(self.fixture(mutation), f"failed-{index}")

    def test_write_and_promotion_flags_fail_closed(self):
        for field in ("canonical_write", "promotion_performed"):
            def mutation(members, batches, root, selected=field):
                value = json.loads(members["run-result.json"])
                value[selected] = True
                members["run-result.json"] = encoded(value)
            with self.subTest(field=field), self.assertRaisesRegex(EvidenceError, "must be false"):
                self.normalize(self.fixture(mutation), field)

    def test_missing_native_batch_evidence_is_rejected(self):
        names = (("candidate-ids.json", "candidate IDs"),
                 ("dependency-closure.json", "dependency closure"),
                 ("review-package.json", "review package"))
        for filename, message in names:
            def mutation(members, batches, root, selected=filename):
                path = next(path for path in members if path.endswith("/MB2/mb2-batch-000001/" + selected))
                members.pop(path)
            with self.subTest(filename=filename), self.assertRaisesRegex(EvidenceError, message):
                self.normalize(self.fixture(mutation), filename)

    def test_missing_candidate_shard_and_internal_hash_mismatch_are_rejected(self):
        def missing(members, batches, root):
            members.pop(f"{root}/candidate-shards/000334-mb2.json")
        with self.assertRaisesRegex(EvidenceError, "candidate shard reference"):
            self.normalize(self.fixture(missing), "missing-shard")
        def altered(members, batches, root):
            members[f"{root}/candidate-shards/000334-mb2.json"] += b" "
        with self.assertRaisesRegex(EvidenceError, "internal hash mismatch"):
            self.normalize(self.fixture(altered), "altered-shard")

    def test_missing_duplicate_and_unresolved_payloads_fail_closed(self):
        def edit_shard(members, root, edit):
            path = f"{root}/candidate-shards/000334-mb2.json"
            value = json.loads(members[path]); edit(value["candidates"]); members[path] = encoded(value)
            ledger_path = f"{root}/completed-sets.json"
            ledger = json.loads(members[ledger_path])
            ledger["sets"]["000334-mb2"]["sha256"] = hashlib.sha256(members[path]).hexdigest()
            members[ledger_path] = encoded(ledger)
            package_path = next(p for p in members if p.endswith("/MB2/mb2-batch-000001/review-package.json"))
            package = json.loads(members[package_path])
            package["candidate_payload_references"][0].update(
                sha256=hashlib.sha256(members[path]).hexdigest(), byte_length=len(members[path]))
            members[package_path] = encoded(package)
            native_manifest = package_path.replace("review-package.json", "manifest.json")
            native = json.loads(members[native_manifest])
            native["review_package_sha256"] = hashlib.sha256(members[package_path]).hexdigest()
            members[native_manifest] = encoded(native)
        cases = [
            (lambda values: values.pop(0), "lacks a payload"),
            (lambda values: values.append(dict(values[0])), "duplicate candidate payload"),
            (lambda values: values[1]["mapped_fields"].__setitem__("card_reference", "missing"),
             "cannot be resolved"),
        ]
        for index, (edit, message) in enumerate(cases):
            def mutation(members, batches, root, selected=edit): edit_shard(members, root, selected)
            with self.subTest(case=index), self.assertRaisesRegex(EvidenceError, message):
                self.normalize(self.fixture(mutation), f"payload-failure-{index}")

    def test_pending_status_and_target_isolation_are_required(self):
        def edit_package(members, root, edit):
            path = next(path for path in members if path.endswith("/MB2/mb2-batch-000001/review-package.json"))
            value = json.loads(members[path]); edit(value); members[path] = encoded(value)
            manifest_path = path.replace("review-package.json", "manifest.json")
            manifest = json.loads(members[manifest_path])
            manifest["review_package_sha256"] = hashlib.sha256(members[path]).hexdigest()
            members[manifest_path] = encoded(manifest)
        def reviewed(members, batches, root): edit_package(members, root,
            lambda value: value.__setitem__("review_status", "approved"))
        with self.assertRaisesRegex(EvidenceError, "pending"):
            self.normalize(self.fixture(reviewed), "reviewed")
        def contaminated(members, batches, root): edit_package(members, root,
            lambda value: value.__setitem__("target_set_code", "MSH"))
        with self.assertRaisesRegex(EvidenceError, "cross-target"):
            self.normalize(self.fixture(contaminated), "contaminated")

    def test_full_source_artifact_is_forbidden(self):
        with self.assertRaisesRegex(EvidenceError, "full MTGJSON source"):
            self.normalize(self.fixture(extra={"AllPrintings.json.gz": b"dataset"}), "source")

    def test_same_run_different_source_archive_has_distinct_lineage(self):
        first = self.normalize(self.fixture(), "first")
        archive = self.fixture(extra={"reports/extra.json": b"{}"})
        second = self.normalize(archive, "second")
        self.assertNotEqual(first["original_archive_sha256"], second["original_archive_sha256"])
        self.assertNotEqual(first["normalized_zip_sha256"], second["normalized_zip_sha256"])
        repository = ProductionEvidenceRepository(self.root / "collision-repo")
        first_path, second_path = Path(first["normalized_archive"]), Path(second["normalized_archive"])
        evidence_id = f"{RUN}-review-payload-v2"
        repository.intake(first_path, hashlib.sha256(first_path.read_bytes()).hexdigest(), evidence_id)
        with self.assertRaisesRegex(EvidenceError, "production run identity collision"):
            repository.intake(second_path, hashlib.sha256(second_path.read_bytes()).hexdigest(), evidence_id)


if __name__ == "__main__":
    unittest.main()
