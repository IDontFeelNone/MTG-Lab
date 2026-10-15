"""Local snapshot attachment acceptance and adversarial boundary regressions.

Only original fictional fixtures are copied and changed. Rehashing a temporary
attack packet deliberately proves that integrity alone cannot grant authority or
substitute for schema, source, graph, and capability validation.
"""
from dataclasses import FrozenInstanceError
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from collection.intelligence import CanonicalCollectionResolver
from query.engine import CanonicalQueryEngine
from repository.snapshots import (
    LegacyPublicAttachment, SnapshotAttachment, SnapshotError,
    SnapshotVerification, attach_legacy_public, attach_snapshot,
    canonical_json, semantic_identity, verify_snapshot,
)
from snapshot_fixture_builder import FIXTURES, build_snapshot, read, rebind, ref, save


def tree_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class CanonicalSnapshotAttachmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retained_fixture_bytes = tree_bytes(FIXTURES)

    @classmethod
    def tearDownClass(cls):
        if tree_bytes(FIXTURES) != cls.retained_fixture_bytes:
            raise AssertionError("retained fictional snapshot fixtures changed")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.copy_number = 0
        self.root = self.copy_fixture()
        self.expected = read(self.root / "release-manifest.json")["snapshot_id"]

    def copy_fixture(self, game="lantern"):
        self.copy_number += 1
        root = self.work / (game + "-" + str(self.copy_number))
        shutil.copytree(FIXTURES / game, root)
        return root

    def verify(self, root=None, *, game="lantern", expected=None):
        root = root or self.root
        return verify_snapshot(root, game=game,
            expected_snapshot_id=expected or read(root / "release-manifest.json")["snapshot_id"])

    def attach(self, root=None, *, game="lantern", expected=None):
        root = root or self.root
        return attach_snapshot(root, game=game,
            expected_snapshot_id=expected or read(root / "release-manifest.json")["snapshot_id"])

    def blocked(self, action, *codes):
        with self.assertRaises(SnapshotError) as caught:
            action()
        result = caught.exception.as_dict()
        self.assertEqual(result["status"], "blocked")
        self.assertIsInstance(result["message"], str)
        self.assertEqual(set(result), {"status", "code", "message", "relative_path"})
        self.assertNotIn(str(self.work), json.dumps(result))
        if codes:
            self.assertIn(result["code"], codes)
        return result

    def mutate(self, relative, change, *, root=None):
        root = root or self.root
        document = read(root / relative)
        change(document)
        save(root / relative, document)

    def resign_release(self, root=None):
        """Refresh only content identity; never rewrite an approval assertion."""
        root = root or self.root
        release = read(root / "release-manifest.json")
        release["snapshot_id"] = semantic_identity("release-manifest",
            {key: value for key, value in release.items() if key != "snapshot_id"})
        save(root / "release-manifest.json", release)
        return release["snapshot_id"]

    def bind_report_attack(self, change, root=None):
        # rebind() creates a fresh valid report, so report attacks must explicitly
        # update its outer hash without replacing the altered report itself.
        root = root or self.root
        self.mutate("validation-report.json", change, root=root)
        self.mutate("release-manifest.json", lambda release: release.update(
            validation_report=ref(root, "validation-report.json")), root=root)
        return self.resign_release(root)

    def test_two_original_games_verify_with_exact_inventory_and_no_authority(self):
        for game, counts in (("lantern", (2, 3)), ("clockwork", (1, 1))):
            with self.subTest(game=game):
                result = self.verify(self.copy_fixture(game), game=game)
                self.assertIsInstance(result, SnapshotVerification)
                self.assertEqual(result.game, game)
                self.assertEqual(tuple(result.binding["entity_inventory"][kind]["count"]
                    for kind in ("card", "printing")), counts)
                self.assertEqual(result.binding["entity_inventory"]["identifier"]["count"], 0)
                self.assertFalse(result.binding["production_eligible"])
                self.assertEqual(result.binding["approval_state"], "not_granted")
                self.assertEqual(result.binding["source_policy_clearance"], "not_granted")

    def test_original_fictional_fixtures_regenerate_byte_for_byte(self):
        for game, names, printing_counts in (
                ("lantern", ("Lantern Unit", "Paper Glider"), (1, 2)),
                ("clockwork", ("Clockwork Parcel",), (1,))):
            with self.subTest(game=game):
                regenerated = self.work / ("regenerated-" + game)
                identity = build_snapshot(regenerated, game=game, names=names,
                                          printing_counts=printing_counts)
                self.assertEqual(identity, read(FIXTURES / game / "release-manifest.json")["snapshot_id"])
                self.assertEqual(tree_bytes(regenerated), tree_bytes(FIXTURES / game))

    def test_attachment_roots_and_fresh_binding(self):
        attached = self.attach()
        self.assertIsInstance(attached, SnapshotAttachment)
        self.assertEqual(attached.root, self.root.resolve())
        self.assertEqual(attached.data_root, self.root / "data")
        self.assertEqual(attached.games_root, self.root / "data/canonical/games")
        self.assertEqual(attached.canonical_data_root, self.root / "data/canonical")
        self.assertEqual(attached.evidence_root, self.root / "evidence")
        binding = attached.binding
        binding["capabilities"]["mechanical_evidence"] = "available"
        binding["snapshot_id"] = "forged"
        self.assertEqual(attached.snapshot_id, self.expected)
        self.assertEqual(attached.binding["capabilities"]["mechanical_evidence"], "unavailable")
        attached.verify_unchanged()

    def test_verification_and_attachment_handles_are_frozen(self):
        for handle in (self.verify(), self.attach()):
            with self.subTest(handle=type(handle).__name__):
                with self.assertRaises(FrozenInstanceError):
                    handle.root = self.work
                with self.assertRaises(FrozenInstanceError):
                    handle._metadata = b"{}"

    def test_queries_and_printing_relationships_use_attached_game(self):
        for game, counts in (("lantern", (2, 3)), ("clockwork", (1, 1))):
            with self.subTest(game=game):
                engine = CanonicalQueryEngine.from_attachment(self.attach(self.copy_fixture(game), game=game))
                self.assertEqual((len(engine.entities(entity_type="card")),
                                  len(engine.entities(entity_type="printing"))), counts)
                card = engine.related("edition-1-1", "printing_card")[0]
                self.assertEqual(card.canonical_identity, "unit-1")
                self.assertEqual([row.canonical_identity for row in
                    engine.related("unit-1", "card_printings")], ["edition-1-1"])
                self.assertEqual(engine.related("edition-1-1", "printing_set")[0]["canonical_identity"], "fictional")
                self.assertEqual(engine.catalog_binding["game"], game)

    def test_collection_resolution_preserves_query_identity_separately(self):
        attached = self.attach()
        engine = CanonicalQueryEngine.from_attachment(attached)
        resolver = CanonicalCollectionResolver.from_attachment(attached)
        result = resolver.resolve({"entries": [{"printing_id": "edition-1-1", "quantity": 1},
            {"card_name": "Paper Glider", "quantity": 1}, {"card_name": "Unlisted Fixture", "quantity": 1}]})
        self.assertEqual([row["status"] for row in result["results"]], ["resolved", "ambiguous", "unresolved"])
        self.assertEqual(result["results"][0]["card_id"], "unit-1")
        self.assertEqual(result["canonical_snapshot_id"], engine.snapshot().snapshot_id)
        self.assertEqual(result["catalog_attachment"], attached.binding)
        self.assertNotEqual(result["canonical_snapshot_id"], attached.snapshot_id)

    def test_relocation_preserves_release_and_query_identities(self):
        relocated = self.work / "relocated" / "packet"
        shutil.copytree(self.root, relocated)
        first, second = self.attach(), self.attach(relocated)
        self.assertEqual(first.binding, second.binding)
        self.assertEqual(first.snapshot_id, second.snapshot_id)
        self.assertEqual(CanonicalQueryEngine.from_attachment(first).snapshot().as_dict(),
                         CanonicalQueryEngine.from_attachment(second).snapshot().as_dict())

    def test_distinct_games_have_distinct_release_and_query_identities(self):
        lantern = self.attach()
        clockwork = self.attach(self.copy_fixture("clockwork"), game="clockwork")
        self.assertNotEqual(lantern.snapshot_id, clockwork.snapshot_id)
        self.assertNotEqual(lantern.binding["content_id"], clockwork.binding["content_id"])
        self.assertNotEqual(CanonicalQueryEngine.from_attachment(lantern).snapshot().snapshot_id,
                            CanonicalQueryEngine.from_attachment(clockwork).snapshot().snapshot_id)

    def test_explicit_legacy_attachment_matches_existing_constructors(self):
        legacy = attach_legacy_public(game="lantern", data_root=self.root / "data",
                                      games_root=self.root / "data/canonical/games")
        self.assertIsInstance(legacy, LegacyPublicAttachment)
        old = CanonicalQueryEngine("lantern", data_root=legacy.data_root, games_root=legacy.games_root)
        attached = CanonicalQueryEngine.from_attachment(legacy)
        self.assertEqual(attached.snapshot().as_dict(), old.snapshot().as_dict())
        self.assertIsNone(old.catalog_binding)
        self.assertEqual(attached.catalog_binding["profile"], "legacy-public-v1")
        imported = {"entries": [{"printing_id": "edition-1-1", "quantity": 1}]}
        previous = CanonicalCollectionResolver("lantern", legacy.data_root, games_root=legacy.games_root).resolve(imported)
        current = CanonicalCollectionResolver.from_attachment(legacy).resolve(imported)
        self.assertEqual(current.pop("catalog_attachment"), legacy.binding)
        self.assertEqual(current, previous)

    def test_legacy_selection_requires_explicit_existing_game_and_root(self):
        self.blocked(lambda: attach_legacy_public(game="absent", data_root=self.root / "data"), "missing_legacy_catalog")
        self.blocked(lambda: attach_legacy_public(game="lantern", data_root=self.work / "absent"), "missing_legacy_catalog")
        with self.assertRaises(TypeError):
            attach_legacy_public(data_root=self.root / "data")

    def test_failed_snapshot_never_invokes_legacy_fallback(self):
        (self.root / "release-manifest.json").unlink()
        with patch("repository.snapshots.attach_legacy_public", side_effect=AssertionError("legacy fallback used")) as fallback:
            self.blocked(lambda: self.attach(expected=self.expected), "missing_file")
            fallback.assert_not_called()

    def test_verification_objects_and_plain_metadata_cannot_attach_consumers(self):
        verified = self.verify()
        unverified = SnapshotVerification(self.root, b"{}")
        for consumer in (CanonicalQueryEngine, CanonicalCollectionResolver):
            for value in (verified, unverified, verified.binding, object(), None):
                with self.subTest(consumer=consumer.__name__, value=type(value).__name__):
                    self.blocked(lambda: consumer.from_attachment(value), "unverified_attachment")

    def test_verify_attach_query_and_resolution_perform_no_network_calls(self):
        before = tree_bytes(self.root)
        with patch("socket.create_connection", side_effect=AssertionError("network used")), \
                patch("socket.socket", side_effect=AssertionError("network used")), \
                patch("urllib.request.urlopen", side_effect=AssertionError("network used")):
            attached = self.attach()
            CanonicalQueryEngine.from_attachment(attached).snapshot()
            CanonicalCollectionResolver.from_attachment(attached).resolve({"entries": []})
        self.assertEqual(tree_bytes(self.root), before)

    def test_missing_root_and_required_control_files_are_rejected(self):
        self.blocked(lambda: verify_snapshot(self.work / "missing", game="lantern",
                     expected_snapshot_id=self.expected), "missing_snapshot")
        for filename in ("release-manifest.json", "content-manifest.json", "source-manifest.json", "validation-report.json"):
            with self.subTest(filename=filename):
                root = self.copy_fixture()
                (root / filename).unlink()
                self.blocked(lambda: self.attach(root, expected=self.expected), "missing_file")

    def test_missing_manifest_listed_evidence_never_uses_retained_copy(self):
        (self.root / "evidence/original-fictional.txt").unlink()
        self.assertTrue((FIXTURES / "lantern/evidence/original-fictional.txt").is_file())
        self.blocked(lambda: self.attach(), "missing_file")

    def test_modified_canonical_bytes_are_rejected_before_rebinding(self):
        self.mutate("data/canonical/games/lantern/cards/unit-1/card.json", lambda card: card.update(name="Altered Fictional Title"))
        self.blocked(lambda: self.attach(), "integrity_mismatch")

    def test_unlisted_file_is_rejected(self):
        (self.root / "extra.json").write_text("{}\n")
        self.blocked(lambda: self.attach(), "extra_file")

    def test_snapshot_profile_file_size_limit_is_enforced(self):
        (self.root / "oversized.bin").write_bytes(b"x" * (2 * 1024 * 1024 + 1))
        self.blocked(lambda: self.attach(), "size_limit")

    def test_duplicate_json_keys_are_rejected(self):
        release = self.root / "release-manifest.json"
        release.write_bytes(b'{"schema_version":"v1",' + release.read_bytes()[1:])
        self.blocked(lambda: self.attach(expected=self.expected), "invalid_json")

    def test_nonfinite_and_floating_json_values_are_rejected(self):
        for token in (b"NaN", b"Infinity", b"-Infinity", b"1.25"):
            with self.subTest(token=token):
                root = self.copy_fixture()
                path = root / "release-manifest.json"
                path.write_bytes(b'{"unsupported_number":' + token + b"," + path.read_bytes()[1:])
                self.blocked(lambda: self.attach(root, expected=self.expected), "invalid_json")
        for number in (float("nan"), float("inf"), 1.25):
            with self.subTest(number=str(number)):
                self.blocked(lambda: canonical_json({"value": number}), "invalid_json")

    def test_unsupported_contract_and_control_schema_versions_are_rejected(self):
        for key in ("contract_version", "schema_version"):
            with self.subTest(field=key):
                root = self.copy_fixture()
                self.mutate("release-manifest.json", lambda doc: doc.update({key: "v999"}), root=root)
                self.blocked(lambda: self.attach(root, expected=self.resign_release(root)), "unsupported_version")

    def test_requested_identity_and_game_are_mandatory_and_exact(self):
        self.blocked(lambda: self.attach(expected="0" * 64), "identity_mismatch")
        for identity in ("", "sha256:" + self.expected, None, 3):
            with self.subTest(identity=identity):
                self.blocked(lambda: attach_snapshot(self.root, game="lantern", expected_snapshot_id=identity), "invalid_identity")
        self.blocked(lambda: self.attach(game="clockwork"), "wrong_game")
        self.blocked(lambda: self.attach(game="../lantern"), "wrong_game")

    def test_source_record_correspondence_survives_outer_rehash_attack(self):
        self.mutate("data/canonical/games/lantern/sources/original-fixture.json",
                    lambda source: source.update(content_hash="0" * 64))
        identity = rebind(self.root)
        self.blocked(lambda: self.attach(expected=identity), "source_mismatch")

    def test_source_scope_and_duplicate_identity_attacks_are_rejected(self):
        for attack in ("duplicate", "wrong-game", "outside-evidence"):
            with self.subTest(attack=attack):
                root = self.copy_fixture()
                def change(source):
                    if attack == "duplicate":
                        source["sources"].append(dict(source["sources"][0]))
                    elif attack == "wrong-game":
                        source["game"] = "clockwork"
                    else:
                        source["sources"][0]["evidence"] = ref(root, "policy.json")
                self.mutate("source-manifest.json", change, root=root)
                identity = rebind(root)
                self.blocked(lambda: self.attach(root, expected=identity), "source_mismatch", "invalid_manifest")

    def test_malformed_unused_source_record_is_rejected_after_rebinding(self):
        record_path = "data/canonical/games/lantern/sources/unused-fixture.json"
        record = read(self.root / "data/canonical/games/lantern/sources/original-fixture.json")
        record["id"] = "unused-fixture"
        del record["title"]
        save(self.root / record_path, record)
        def add_source(source):
            row = dict(source["sources"][0])
            row.update(source_id="unused-fixture", record_path=record_path)
            source["sources"].append(row)
        self.mutate("source-manifest.json", add_source)
        self.mutate("content-manifest.json", lambda content: content["files"].append(ref(self.root, record_path)))
        self.mutate("content-manifest.json", lambda content: content["files"].sort(key=lambda row: row["path"]))
        self.blocked(lambda: self.attach(expected=rebind(self.root)), "invalid_graph", "source_mismatch")

    def test_changed_schema_binding_is_rejected_after_rebinding(self):
        self.mutate("schema-bindings.json", lambda doc: doc["schemas"][0].update(sha256="0" * 64))
        identity = rebind(self.root)
        self.blocked(lambda: self.attach(expected=identity), "incompatible_schema")

    def test_policy_cannot_grant_production_approval_or_source_clearance(self):
        for key, value in (("production_eligible", True), ("approval_state", "approved"),
                           ("source_policy_clearance", "granted"), ("scope", "production")):
            with self.subTest(field=key):
                root = self.copy_fixture()
                self.mutate("policy.json", lambda doc: doc.update({key: value}), root=root)
                identity = rebind(root)
                self.blocked(lambda: self.attach(root, expected=identity), "invalid_manifest")

    def test_release_cannot_claim_authority_or_unsupported_capabilities(self):
        for key, value in (("approval_state", "approved"), ("production_eligible", True),
                           ("source_policy_clearance", "granted"), ("scope", "production"),
                           ("decision_references", ["invented-owner-approval"])):
            with self.subTest(field=key):
                root = self.copy_fixture()
                self.mutate("release-manifest.json", lambda doc: doc.update({key: value}), root=root)
                self.blocked(lambda: self.attach(root, expected=self.resign_release(root)), "invalid_manifest")
        self.mutate("release-manifest.json", lambda doc: doc["capabilities"].update(mechanical_evidence="available"))
        self.blocked(lambda: self.attach(expected=self.resign_release()), "invalid_manifest")

    def test_report_failure_and_false_authority_rejected_with_valid_outer_hash(self):
        for key, value in (("status", "passed"), ("checks", []), ("unrun_checks", []),
                           ("production_eligible", True), ("approval_state", "approved")):
            with self.subTest(field=key):
                root = self.copy_fixture()
                identity = self.bind_report_attack(lambda report: report.update({key: value}), root)
                self.blocked(lambda: self.attach(root, expected=identity), "invalid_validation")

    def test_report_for_other_input_or_inventory_is_rejected(self):
        for key in ("validation_input_id", "inventory_identity", "content_id"):
            with self.subTest(field=key):
                root = self.copy_fixture()
                identity = self.bind_report_attack(lambda report: report.update({key: "0" * 64}), root)
                self.blocked(lambda: self.attach(root, expected=identity), "invalid_validation")

    def test_unsupported_validator_binding_is_rejected(self):
        self.mutate("release-manifest.json", lambda release: release["validation_input"].update(validator_sha256="0" * 64))
        self.blocked(lambda: self.attach(expected=self.resign_release()), "invalid_validation")

    def test_missing_field_provenance_is_rejected_after_rebinding(self):
        for provenance in ([], [{"source_id": "original-fixture", "field_paths": ["name"], "claim": "Incomplete fictional claim"}]):
            with self.subTest(provenance=provenance):
                root = self.copy_fixture()
                self.mutate("data/canonical/games/lantern/cards/unit-1/card.json",
                            lambda card: card.update(provenance=provenance), root=root)
                identity = rebind(root)
                self.blocked(lambda: self.attach(root, expected=identity), "invalid_graph")

    def test_undeclared_source_reference_is_rejected_after_rebinding(self):
        self.mutate("data/canonical/games/lantern/cards/unit-1/card.json",
                    lambda card: card["provenance"][0].update(source_id="undeclared-source"))
        self.blocked(lambda: self.attach(expected=rebind(self.root)), "source_mismatch")

    def test_orphan_printing_and_duplicate_collector_number_rejected_after_rebind(self):
        for key, value in (("card_id", "missing-card"), ("collector_number", "2-1")):
            with self.subTest(field=key):
                root = self.copy_fixture()
                self.mutate("data/canonical/games/lantern/printings/edition-1-1/printing.json",
                            lambda printing: printing.update({key: value}), root=root)
                self.blocked(lambda: self.attach(root, expected=rebind(root)), "invalid_graph")

    def test_record_schema_and_identity_mismatch_rejected_after_rebinding(self):
        for change, code in ((lambda card: card.update(id="other-card"), "invalid_graph"),
                             (lambda card: card.update(schema_version="v999"), "unsupported_version"),
                             (lambda card: card.update(metadata={"unsupported": True}), "unsupported_profile")):
            with self.subTest(code=code):
                root = self.copy_fixture()
                self.mutate("data/canonical/games/lantern/cards/unit-1/card.json", change, root=root)
                self.blocked(lambda: self.attach(root, expected=rebind(root)), code)

    def test_control_dependency_path_escapes_and_ambiguities_are_rejected(self):
        for path in ("../content-manifest.json", "/tmp/content-manifest.json", "./content-manifest.json",
                     "sub//content-manifest.json", "sub/../content-manifest.json", "sub\\content-manifest.json"):
            with self.subTest(path=path):
                root = self.copy_fixture()
                self.mutate("release-manifest.json", lambda doc: doc["content_manifest"].update(path=path), root=root)
                self.blocked(lambda: self.attach(root, expected=self.resign_release(root)), "unsafe_path")

    def test_duplicate_casefolded_files_and_manifest_entries_are_rejected(self):
        duplicate = self.root / "POLICY.json"
        duplicate.write_bytes((self.root / "policy.json").read_bytes())
        self.blocked(lambda: self.attach(), "duplicate_path")
        duplicate.unlink()
        self.mutate("content-manifest.json", lambda content: content["files"].append(dict(content["files"][0])))
        self.blocked(lambda: self.attach(expected=rebind(self.root)), "duplicate_path")

    def test_file_directory_and_root_symlinks_are_rejected(self):
        for kind in ("file", "directory", "root"):
            with self.subTest(kind=kind):
                root = self.copy_fixture()
                if kind == "file":
                    path = root / "policy.json"
                    path.unlink()
                    path.symlink_to(FIXTURES / "lantern/policy.json")
                elif kind == "directory":
                    (root / "linked").symlink_to(FIXTURES / "lantern/data", target_is_directory=True)
                else:
                    linked = self.work / "linked-root"
                    linked.symlink_to(root, target_is_directory=True)
                    root = linked
                self.blocked(lambda: self.attach(root, expected=self.expected), "symlink")

    def test_source_scope_cannot_import_other_game_or_canonical_state(self):
        for relative in ("data/canonical/state.json", "data/audit/late.json",
                         "data/canonical/games/clockwork/game.json"):
            with self.subTest(path=relative):
                root = self.copy_fixture()
                save(root / relative, {"id": "fictional-extra"})
                self.mutate("content-manifest.json", lambda content: content["files"].append(ref(root, relative)), root=root)
                self.mutate("content-manifest.json", lambda content: content["files"].sort(key=lambda row: row["path"]), root=root)
                self.blocked(lambda: self.attach(root, expected=rebind(root)), "unsupported_profile")

    def test_attached_consumers_reject_post_attachment_file_drift(self):
        attached = self.attach()
        query = CanonicalQueryEngine.from_attachment(attached)
        resolver = CanonicalCollectionResolver.from_attachment(attached)
        self.mutate("data/canonical/games/lantern/cards/unit-1/card.json", lambda card: card.update(name="Drifted Fictional Name"))
        for action in (attached.verify_unchanged, query.snapshot, lambda: query.entities(entity_type="card"),
                       lambda: query.related("edition-1-1", "printing_card"),
                       lambda: resolver.resolve({"entries": []}), lambda: query.catalog_binding,
                       lambda: resolver.catalog_binding):
            self.blocked(action, "integrity_mismatch")

    def test_drift_during_graph_verification_is_rejected(self):
        from repository.snapshots import _validate_graph
        def graph_then_drift(*args):
            _validate_graph(*args)
            (self.root / "evidence/original-fictional.txt").write_text("Changed during fictional validation.\n")
        with patch("repository.snapshots._validate_graph", side_effect=graph_then_drift):
            self.blocked(lambda: self.attach(), "integrity_mismatch")

    def test_lazy_audit_insertion_is_rejected_instead_of_affecting_query(self):
        attached = self.attach()
        query = CanonicalQueryEngine.from_attachment(attached)
        resolver = CanonicalCollectionResolver.from_attachment(attached)
        save(self.root / "data/audit/inserted.json", {"promotion_id": "fictional-late-audit", "promoted_entities": ["unit-1"]})
        self.blocked(lambda: query.provenance("unit-1"), "extra_file")
        self.blocked(lambda: resolver.resolve({"entries": [{"printing_id": "edition-1-1", "quantity": 1}]}), "extra_file")

    def test_attached_consumer_roots_cannot_be_retargeted(self):
        attached = self.attach()
        for consumer in (CanonicalQueryEngine.from_attachment(attached), CanonicalCollectionResolver.from_attachment(attached)):
            with self.subTest(consumer=type(consumer).__name__):
                consumer.data_root = self.work
                self.blocked(lambda: consumer.catalog_binding, "unverified_attachment")

    def test_safe_structured_failure_never_echoes_corrupted_source_content(self):
        marker = "PRIVATE_TEST_MARKER_NOT_A_DIAGNOSTIC"
        path = self.root / "release-manifest.json"
        path.write_text('{"bad":"' + marker)
        result = self.blocked(lambda: self.attach(expected=self.expected), "invalid_json")
        self.assertNotIn(marker, json.dumps(result))
        self.assertEqual(result["relative_path"], "release-manifest.json")

    def test_successful_and_rejected_operations_do_not_write_original_bytes(self):
        before = tree_bytes(self.root)
        attached = self.attach()
        CanonicalQueryEngine.from_attachment(attached).snapshot()
        CanonicalCollectionResolver.from_attachment(attached).resolve({"entries": [{"printing_id": "edition-1-1", "quantity": 1}]})
        self.blocked(lambda: self.attach(expected="0" * 64), "identity_mismatch")
        self.assertEqual(tree_bytes(self.root), before)


if __name__ == "__main__":
    unittest.main()
