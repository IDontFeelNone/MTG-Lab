"""Documentation-only contract checks; no production snapshot loader/authority."""
import copy
import hashlib
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path, PurePosixPath

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from collection.intelligence import CanonicalCollectionResolver
from query import CanonicalQueryEngine
from repository.cards import load_card_repository
from validation import validate_document


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs/examples/external-card-data-plane"
BUNDLE = EXAMPLES / "fictional-snapshot"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def semantic(kind, value):
    return hashlib.sha256(canonical({
        "identity_domain": "mtg-lab:" + kind + ":design-v1", "document": value,
    })).hexdigest()


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    return json.loads(path.read_bytes(), object_pairs_hook=unique_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))


class ExternalCardDataPlaneDesignTests(unittest.TestCase):
    """An illustrative example verifier only; not a reusable admission boundary."""

    def setUp(self):
        self.release = read_json(BUNDLE / "release-manifest.json")
        self.schema = read_json(EXAMPLES / "fictional-release.schema.json")

    def copy_bundle(self, root):
        target = Path(root) / "relocated"
        shutil.copytree(BUNDLE, target)
        return target

    def check_example(self, root):
        root = Path(root)
        release = read_json(root / "release-manifest.json")
        Draft202012Validator(self.schema).validate(release)
        inventory = {"release-manifest.json"}

        def checked_file(binding):
            path = binding["path"]
            parts = PurePosixPath(path).parts
            if (not path or "\\" in path or ":" in path or path.startswith("/")
                    or ".." in parts or "." in path.split("/")
                    or PurePosixPath(path).as_posix() != path):
                raise ValueError("unbounded example path")
            if path in inventory:
                raise ValueError("duplicate example path")
            inventory.add(path)
            target = root / path
            if any((root.joinpath(*parts[:index])).is_symlink()
                   for index in range(1, len(parts) + 1)):
                raise ValueError("example symlink")
            if not target.is_file():
                raise ValueError("missing example file: " + path)
            raw = target.read_bytes()
            if len(raw) != binding["byte_length"] or hashlib.sha256(raw).hexdigest() != binding["sha256"]:
                raise ValueError("example checksum mismatch: " + path)
            return target

        content = read_json(checked_file(release["content_manifest"]))
        source_path = checked_file(release["source_manifest"])
        source = read_json(source_path)
        report = read_json(checked_file(release["validation_report"]))
        if content["source_manifest"] != release["source_manifest"]:
            raise ValueError("source manifest binding disagreement")
        for key in ("game", "schema_set_id", "policy_id", "representation_profile",
                    "providers", "entity_inventory", "source_manifest_id"):
            if release[key] != content[key]:
                raise ValueError("contradictory metadata: " + key)
        for document, key, kind in ((release, "snapshot_id", "release-manifest"),
                                    (content, "content_id", "content-manifest"),
                                    (source, "source_manifest_id", "source-manifest")):
            body = {k: v for k, v in document.items() if k != key}
            if semantic(kind, body) != document[key]:
                raise ValueError("semantic identity mismatch: " + key)
        if content["content_id"] != release["content_id"] or source["source_manifest_id"] != release["source_manifest_id"]:
            raise ValueError("root identity disagreement")
        if [entry["path"] for entry in content["files"]] != sorted(entry["path"] for entry in content["files"]):
            raise ValueError("unsorted example inventory")
        for binding in content["files"]:
            checked_file(binding)
        actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() or p.is_symlink()}
        if actual != inventory:
            raise ValueError("extra example files")
        for source_entry in source["sources"]:
            if source_entry["evidence"] not in content["files"]:
                raise ValueError("source evidence not bound")
            record = read_json(root / source_entry["record_path"])
            validate_document(record, "source-record")
            if record["content_hash"] != source_entry["evidence"]["sha256"] or record["archival_location"] != source_entry["evidence"]["path"]:
                raise ValueError("source correspondence mismatch")
        policy = read_json(root / "policy.json")
        schemas = read_json(root / "schema-bindings.json")
        if semantic("policy", policy) != release["policy_id"] or semantic("schema-set", schemas) != release["schema_set_id"]:
            raise ValueError("policy/schema identity mismatch")
        for binding in schemas["schemas"]:
            raw = (ROOT / binding["repository_path"]).read_bytes()
            if len(raw) != binding["byte_length"] or hashlib.sha256(raw).hexdigest() != binding["sha256"]:
                raise ValueError("current v1 schema changed")
        expected_input = {"content_id": content["content_id"], "validator": {
            "profile": "documentation-fixture-checks-v1", "schema_set_id": content["schema_set_id"],
            "policy_id": content["policy_id"]}, "check_profile": "fictional-integrity-and-current-read-only-roots-only"}
        if release["validation_input"] != expected_input or semantic("validation-input", expected_input) != release["validation_input_id"]:
            raise ValueError("validation input mismatch")
        if report["content_id"] != content["content_id"] or report["validation_input_id"] != release["validation_input_id"]:
            raise ValueError("validation report binding mismatch")
        if report["production_eligible"] or report["approval_state"] != "not_granted" or not report["unrun_production_checks"]:
            raise ValueError("example cannot authorize production")
        cards, printings = load_card_repository("fictional", games_root=root / "data/canonical/games")
        expected_inventory = {"card": {"count": len(cards), "ids": [row["id"] for row in cards]},
                              "printing": {"count": len(printings), "ids": [row["id"] for row in printings]},
                              "identifier": {"count": 0, "ids": []}}
        if content["entity_inventory"] != expected_inventory:
            raise ValueError("entity inventory mismatch")
        return release

    def test_example_schema_is_valid_and_closed(self):
        Draft202012Validator.check_schema(self.schema)
        self.check_example(BUNDLE)
        changed = {**self.release, "approved": True}
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(changed)

    def test_canonical_serialization_rejects_duplicate_keys_and_nonfinite_numbers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
                path.write_bytes(raw)
                with self.assertRaises(ValueError):
                    read_json(path)
        with self.assertRaises(ValueError):
            canonical({"x": float("inf")})

    def test_tampered_retained_bytes_are_rejected_without_repinning(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            card = copied / "data/canonical/games/fictional/cards/fixture-card-a/card.json"
            document = read_json(card)
            document["name"] = "Changed fictional name"
            card.write_bytes(canonical(document) + b"\n")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                self.check_example(copied)

    def test_missing_retained_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            (copied / "evidence/fixture-source.txt").unlink()
            with self.assertRaisesRegex(ValueError, "missing example file"):
                self.check_example(copied)

    def test_extra_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            (copied / "unlisted.txt").write_text("Original unrelated fixture")
            with self.assertRaisesRegex(ValueError, "extra example files"):
                self.check_example(copied)

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            release = read_json(copied / "release-manifest.json")
            release["content_manifest"]["path"] = "../content-manifest.json"
            (copied / "release-manifest.json").write_bytes(canonical(release))
            with self.assertRaises(ValidationError):
                self.check_example(copied)

    def test_symlink_replacement_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            source = copied / "evidence/fixture-source.txt"
            retained = Path(directory) / "original.txt"
            retained.write_bytes(source.read_bytes())
            source.unlink()
            source.symlink_to(retained)
            with self.assertRaisesRegex(ValueError, "symlink"):
                self.check_example(copied)

    def test_relocated_query_preserves_entity_ids_relationships_and_query_snapshot(self):
        before = {p.relative_to(BUNDLE).as_posix(): p.read_bytes() for p in BUNDLE.rglob("*") if p.is_file()}
        original = CanonicalQueryEngine("fictional", games_root=BUNDLE / "data/canonical/games", data_root=BUNDLE / "data")
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            self.check_example(copied)
            query = CanonicalQueryEngine("fictional", games_root=copied / "data/canonical/games", data_root=copied / "data")
            self.assertEqual(query.snapshot(), original.snapshot())
            self.assertEqual(query.entity("fixture-card-a").canonical_values["name"], "Fixture Card A")
            self.assertEqual([x.canonical_identity for x in query.related("fixture-card-a", "card_printings")], ["fixture-print-a"])
            self.assertEqual(query.related("fixture-print-a", "printing_card")[0].canonical_identity, "fixture-card-a")
            self.assertNotEqual(query.snapshot().snapshot_id, "sha256:" + self.release["snapshot_id"])
            self.assertEqual({p.relative_to(copied).as_posix(): p.read_bytes() for p in copied.rglob("*") if p.is_file()}, before)
        self.assertEqual({p.relative_to(BUNDLE).as_posix(): p.read_bytes() for p in BUNDLE.rglob("*") if p.is_file()}, before)

    def test_existing_collection_resolver_accepts_explicit_fictional_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            resolver = CanonicalCollectionResolver("fictional", copied / "data")
            result = resolver.resolve({"collection_id": "fictional-test", "entries": [{"printing_id": "fixture-print-a", "quantity": 1}]})
            self.assertEqual(result["results"][0]["status"], "resolved")
            self.assertEqual(result["results"][0]["printing_id"], "fixture-print-a")
            self.assertEqual(resolver.printings["fixture-print-a"]["card_id"], "fixture-card-a")
            self.assertEqual(result["canonical_snapshot_id"], resolver.canonical_snapshot_id)

    def test_content_policy_and_schema_are_decision_relevant(self):
        content = read_json(BUNDLE / "content-manifest.json")
        original = {key: value for key, value in content.items() if key != "content_id"}
        for key in ("policy_id", "schema_set_id", "source_manifest_id", "game", "representation_profile"):
            changed = {**original, key: "changed"}
            self.assertNotEqual(semantic("content-manifest", changed), content["content_id"])
        self.assertNotEqual(semantic("release-manifest", original), semantic("content-manifest", original))

    def test_release_metadata_cannot_contradict_content(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = self.copy_bundle(directory)
            release = read_json(copied / "release-manifest.json")
            release["policy_id"] = "0" * 64
            release["snapshot_id"] = semantic("release-manifest", {k: v for k, v in release.items() if k != "snapshot_id"})
            (copied / "release-manifest.json").write_bytes(canonical(release))
            with self.assertRaisesRegex(ValueError, "contradictory metadata: policy_id"):
                self.check_example(copied)

    def test_report_changes_release_identity_without_content_cycle(self):
        report = read_json(BUNDLE / "validation-report.json")
        changed = {**report, "extra_fixture_check": "changed"}
        release = copy.deepcopy(self.release)
        release["validation_report"]["sha256"] = hashlib.sha256(canonical(changed) + b"\n").hexdigest()
        body = {k: v for k, v in release.items() if k != "snapshot_id"}
        self.assertNotEqual(semantic("release-manifest", body), self.release["snapshot_id"])
        self.assertEqual(release["content_id"], self.release["content_id"])
        self.assertNotIn("snapshot_id", report)

    def test_fixture_never_claims_production_eligibility_or_decision(self):
        self.assertEqual(self.release["decision_references"], [])
        changed = {**self.release, "production_eligible": True}
        with self.assertRaises(ValidationError):
            Draft202012Validator(self.schema).validate(changed)
        report = read_json(BUNDLE / "validation-report.json")
        self.assertEqual(report["approval_state"], "not_granted")
        self.assertIn("authenticated_release_authority", report["unrun_production_checks"])

    def test_accepted_architecture_text_is_preserved_as_exact_prefix(self):
        baseline = read_json(EXAMPLES / "baseline-audit.json")
        for entry in baseline["files"]:
            if entry["path"] in {"docs/DECISIONS.md", "docs/ARCHITECTURE.md", "docs/DATA_MODEL.md", "docs/DATA_REPOSITORY.md"}:
                prefix = (ROOT / entry["path"]).read_bytes()[:entry["byte_length"]]
                self.assertEqual(hashlib.sha256(prefix).hexdigest(), entry["sha256"], entry["path"])
        decision = (ROOT / "docs/DECISIONS.md").read_text()
        proposed = decision.split("## Decision 017", 1)[1]
        self.assertIn("Proposed", proposed)
        self.assertIn("ARCHITECTURE V13 REQUIRED", proposed)
        self.assertIn("Decision 004", proposed)
        self.assertIn("Decision 009", proposed)

    def test_proposal_links_and_component_paths_exist(self):
        docs = sorted((ROOT / "docs").glob("EXTERNAL_CARD_DATA_PLANE*.md"))
        self.assertEqual(len(docs), 6)
        for path in docs:
            text = path.read_text()
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((path.parent / target.split("#")[0]).exists(), f"{path.name}: {target}")
            for component in re.findall(r"`((?:src|scripts)/[^` ]+\.py)`", text):
                self.assertTrue((ROOT / component).is_file(), component)


if __name__ == "__main__":
    unittest.main()
