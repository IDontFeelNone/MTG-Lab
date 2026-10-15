"""Fictional, mixed-representation Tier A attachment and fail-closed regressions.

No real catalog/provider bytes are copied into these temporary roots. These
checks demonstrate local read-side behavior, never production/source approval.
"""
from dataclasses import FrozenInstanceError
import json
import os
from pathlib import Path
import shutil
import socket
import tempfile
import unittest
from unittest.mock import patch

from analytics import CanonicalAnalyticsEngine
from collection.intelligence import CanonicalCollectionResolver
from query.engine import CanonicalQueryEngine
from repository.legacy_profile import (AUTHORITY, CAPABILITIES, OPERATIONS,
    LegacyCompatibilityAttachment, attach_legacy_compatibility, closure_identity,
    profile_identity)
from repository.snapshots import SnapshotError, attach_legacy_public
from semantic import CanonicalSemanticQueryEngine, SemanticRequest
from legacy_profile_fixture import (CONTROL, EXCLUDED_AUDIT, SELECTED_AUDITS,
    binding, build_legacy_fixture, read, resign, save)


def tree_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


class LegacyCompatibilityProfileTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.work = Path(self.temporary.name)
        self.root = self.work / "original"
        self.document = build_legacy_fixture(self.root)
        self.game = self.document["game"]
        self.prefix = "data/canonical/games/" + self.game + "/"
        self.card_path = self.prefix + "cards/paper-unit/card.json"
        self.source_path = self.prefix + "sources/original-author.json"
        self.unselected_source = self.prefix + "sources/unselected-author.json"

    def attach(self, root=None, *, expected=None, game=None, control=CONTROL):
        root = root or self.root
        return attach_legacy_compatibility(root, control_path=control,
            game=game or self.game, expected_profile_id=expected or read(root / CONTROL)["profile_id"])

    def blocked(self, action, *codes):
        with self.assertRaises(SnapshotError) as caught:
            action()
        result = caught.exception.as_dict()
        self.assertEqual(result["status"], "blocked")
        self.assertNotIn(str(self.work), json.dumps(result))
        if codes:
            self.assertIn(result["code"], codes)
        return result

    def mutate_control(self, change, *, reidentify=True):
        document = read(self.root / CONTROL)
        change(document)
        save(self.root / CONTROL, document)
        return resign(self.root) if reidentify else document["profile_id"]

    def mutate_selected(self, name, change):
        document = read(self.root / name)
        change(document)
        save(self.root / name, document)

    def rebind_one_fictional_file(self, name):
        """Deliberately update a fictional attack's bindings; not production repair."""
        def change(document):
            row = next(row for row in document["files"] if row["path"] == name)
            row.update(binding(self.root, name, row["placement"]))
            document["closure_id"] = closure_identity(document["files"])
        return self.mutate_control(change)

    def test_mixed_original_fictional_fixture_verifies_and_attaches(self):
        attached = self.attach()
        self.assertIsInstance(attached, LegacyCompatibilityAttachment)
        self.assertEqual(attached.binding, self.document)
        self.assertEqual(attached.data_root, self.root / "data")
        self.assertEqual(attached.games_root, self.root / "data/canonical/games")
        attached.verify_unchanged()

    def test_deterministic_fixture_generation_and_control_identity(self):
        second = self.work / "second"
        self.assertEqual(build_legacy_fixture(second), self.document)
        self.assertEqual(tree_bytes(second), tree_bytes(self.root))
        self.assertEqual(self.document["profile_id"], profile_identity(self.document))
        self.assertEqual(self.document["closure_id"], closure_identity(self.document["files"]))

    def test_second_original_game_uses_same_generic_profile(self):
        second = self.work / "different-game"
        document = build_legacy_fixture(second, game="marble-courier")
        attached = self.attach(second, game="marble-courier")
        engine = CanonicalQueryEngine.from_attachment(attached)
        self.assertEqual(engine.snapshot().snapshot_id, document["query_snapshot_id"])
        self.assertEqual(engine.entity("paper-unit").canonical_values["game_id"], "marble-courier")

    def test_existing_query_engine_keeps_typed_first_and_promoted_relationships(self):
        engine = CanonicalQueryEngine.from_attachment(self.attach())
        self.assertEqual(len(engine.snapshot().entities), 8)
        self.assertEqual(engine.entity("paper-unit").canonical_values["name"], "Paper Voyager")
        self.assertEqual(engine.entity("paper-edition").canonical_values["card_id"], "paper-unit")
        self.assertEqual(engine.entity("cloth-unit").canonical_values["name"], "Cloth Cartographer")
        self.assertEqual(engine.related("cloth-edition", "printing_card")[0].canonical_identity, "cloth-unit")
        self.assertEqual([x.canonical_identity for x in engine.related("paper-unit", "card_printings")], ["paper-edition"])
        self.assertEqual(engine.entity("cloth-edition").canonical_values["language"], "Japanese")
        self.assertEqual(engine.search("cloth cartographer", mode="normalized")[0].canonical_identity, "cloth-unit")

    def test_collection_exact_alias_dimensions_and_separate_identity_bindings(self):
        attached = self.attach()
        resolver = CanonicalCollectionResolver.from_attachment(attached)
        imported = {"entries": [
            {"printing_id": "paper-edition", "quantity": 2},
            {"external_identifiers": {"fictional-provider": "external-cloth"}, "quantity": 1},
            {"printing_id": "cloth-edition", "quantity": 1, "language": "English"}]}
        result = resolver.resolve(imported)
        self.assertEqual([row["status"] for row in result["results"]], ["resolved", "resolved", "unresolved"])
        self.assertEqual(result["results"][0]["card_id"], "paper-unit")
        self.assertEqual(result["results"][1]["printing_id"], "cloth-edition")
        self.assertEqual(result["results"][1]["card_id"], "cloth-unit")
        self.assertEqual(result["results"][2]["dimension_conflicts"], ["language"])
        self.assertEqual(result["canonical_snapshot_id"], self.document["query_snapshot_id"])
        self.assertEqual(result["catalog_attachment"]["profile_id"], self.document["profile_id"])
        self.assertNotEqual(result["canonical_snapshot_id"], result["catalog_attachment"]["profile_id"])
        self.assertEqual(result["results"][0]["canonical_reference"]["snapshot_id"], self.document["query_snapshot_id"])
        self.assertNotIn("owner", json.dumps(attached.binding))
        self.assertNotIn("entries", json.dumps(attached.binding))
        self.assertNotIn("physical_printing_verified", json.dumps(result))

    def test_query_identity_is_not_profile_closure_or_historical_prestate(self):
        engine = CanonicalQueryEngine.from_attachment(self.attach())
        query_id = engine.snapshot().snapshot_id
        self.assertEqual(query_id, self.document["query_snapshot_id"])
        self.assertEqual(len({query_id, self.document["profile_id"], self.document["closure_id"],
                              self.document["historical_prestate_reference"]}), 4)

    def test_relocation_preserves_profile_closure_query_and_collection_results(self):
        relocated = self.work / "relocated" / "catalog"
        shutil.copytree(self.root, relocated)
        first, second = self.attach(), self.attach(relocated)
        self.assertEqual(first.binding, second.binding)
        self.assertEqual(CanonicalQueryEngine.from_attachment(first).snapshot().as_dict(),
                         CanonicalQueryEngine.from_attachment(second).snapshot().as_dict())
        imported = {"entries": [{"printing_id": "cloth-edition", "quantity": 1}]}
        self.assertEqual(CanonicalCollectionResolver.from_attachment(first).resolve(imported),
                         CanonicalCollectionResolver.from_attachment(second).resolve(imported))

    def test_relocation_with_changed_selected_bytes_fails(self):
        relocated = self.work / "relocated"
        shutil.copytree(self.root, relocated)
        with (relocated / self.card_path).open("ab") as stream:
            stream.write(b" ")
        self.blocked(lambda: self.attach(relocated), "integrity_mismatch")

    def test_only_declared_audits_and_source_records_are_opened(self):
        real_os_open, real_path_open = os.open, Path.open
        observed = set()
        excluded = {EXCLUDED_AUDIT, self.unselected_source}
        def checked(path):
            try:
                name = Path(path).relative_to(self.root).as_posix()
            except (ValueError, TypeError):
                return
            if name in excluded:
                raise AssertionError("excluded dependency was opened: " + name)
            if name.startswith("data/audit/") or "/sources/" in name:
                observed.add(name)
        def os_open(path, *args, **kwargs):
            checked(path)
            return real_os_open(path, *args, **kwargs)
        def path_open(path, *args, **kwargs):
            checked(path)
            return real_path_open(path, *args, **kwargs)
        with patch("os.open", side_effect=os_open), patch.object(Path, "open", path_open):
            engine = CanonicalQueryEngine.from_attachment(self.attach())
            engine.entity("cloth-edition")
            engine.provenance("paper-unit")
            engine.snapshot()
            CanonicalCollectionResolver.from_attachment(self.attach()).resolve(
                {"entries": [{"printing_id": "cloth-edition", "quantity": 1}]})
        self.assertEqual(observed, {*SELECTED_AUDITS, self.source_path})
        histories = engine.provenance("cloth-unit")["promotion_history"]
        self.assertEqual({item["audit_reference"]["relative_path"] for item in histories},
                         {SELECTED_AUDITS[1].removeprefix("data/")})

    def test_unselected_audit_and_source_values_are_not_interpreted(self):
        (self.root / EXCLUDED_AUDIT).write_bytes(b"THIS IS NOT AUDIT JSON")
        (self.root / self.unselected_source).write_bytes(b"THIS IS NOT A SOURCE RECORD")
        engine = CanonicalQueryEngine.from_attachment(self.attach())
        self.assertEqual(engine.snapshot().snapshot_id, self.document["query_snapshot_id"])

    def test_undeclared_dependency_direct_read_fails_before_open(self):
        attached = self.attach()
        with patch("repository.legacy_profile._read", side_effect=AssertionError("unselected I/O")):
            for name in (EXCLUDED_AUDIT, self.unselected_source, "data/market/private.json"):
                with self.subTest(path=name):
                    self.blocked(lambda: attached.read_json(self.root / name), "unsupported_capability")

    def test_tier_b_and_c_operations_fail_before_attachment_or_dependency_io(self):
        attached = self.attach()
        query = CanonicalQueryEngine.from_attachment(attached)
        semantic = CanonicalSemanticQueryEngine(query)
        analytics = CanonicalAnalyticsEngine(query)
        operations = [
            lambda: query.related("fixture-promotion", "promotion_audits"),
            lambda: query.validation("rejected"),
            lambda: query.validation("validation_failure"),
            lambda: analytics.validation(),
            lambda: attached.require_capability("historical_admission_replay"),
            lambda: attached.require_capability("admission_validation"),
            lambda: semantic.execute(SemanticRequest("list_validation", {"state": "rejected"})),
            lambda: semantic.execute(SemanticRequest("list_validation", {"state": "validation_failure"})),
            lambda: semantic.execute(SemanticRequest("validation_statistics", {}))]
        with patch.object(LegacyCompatibilityAttachment, "verify_unchanged",
                          side_effect=AssertionError("unsupported operation performed attachment I/O")):
            for index, operation in enumerate(operations):
                with self.subTest(operation=index):
                    self.blocked(operation, "unsupported_capability")

    def test_entity_local_semantic_and_epistemic_queries_remain_available(self):
        query = CanonicalQueryEngine.from_attachment(self.attach())
        semantic = CanonicalSemanticQueryEngine(query)
        response = semantic.execute(SemanticRequest("find_name", {"name": "paper voyager"}))
        self.assertEqual(response.to_dict()["result"][0]["canonical_identity"], "paper-unit")
        for state in ("unknown", "conflicting", "unresolved", "superseded"):
            self.assertIsInstance(query.validation(state), tuple)
            semantic.execute(SemanticRequest("list_validation", {"state": state}))

    def test_unrestricted_explicit_legacy_keeps_its_audit_api(self):
        attached = attach_legacy_public(game=self.game, data_root=self.root / "data",
                                        games_root=self.root / "data/canonical/games")
        query = CanonicalQueryEngine.from_attachment(attached)
        self.assertEqual(query.snapshot().snapshot_id, self.document["query_snapshot_id"])
        self.assertEqual(query.validation("rejected")[0]["promotion_id"], "outside-tier-a")
        self.assertEqual(len(query.related("fixture-promotion", "promotion_audits")), 1)

    def test_missing_profile_and_missing_root_fail_without_fallback(self):
        self.blocked(lambda: self.attach(self.work / "missing", expected=self.document["profile_id"]), "missing_compatibility_root")
        (self.root / CONTROL).unlink()
        self.blocked(lambda: self.attach(expected=self.document["profile_id"]), "missing_file")

    def test_wrong_requested_game_and_profile_identity_fail(self):
        self.blocked(lambda: self.attach(game="another-game"), "wrong_game")
        self.blocked(lambda: self.attach(expected="sha256:" + "0" * 64), "identity_mismatch")

    def test_tampered_control_is_not_silently_reidentified(self):
        self.mutate_control(lambda d: d["entity_counts"].update(card=999), reidentify=False)
        self.blocked(lambda: self.attach(), "identity_mismatch")

    def test_wrong_contract_version_and_capability_tier_fail_even_if_rehashed(self):
        for key, value in (("contract_version", "v999"), ("profile", "canonical-snapshot-fictional-v1"),
                           ("capability_tier", "FULL_QUERY_AUDIT")):
            with self.subTest(key=key):
                original = (self.root / CONTROL).read_bytes()
                self.mutate_control(lambda d: d.update({key: value}))
                self.blocked(lambda: self.attach(), "unsupported_version", "unsupported_capability")
                (self.root / CONTROL).write_bytes(original)

    def test_authority_and_permission_claims_are_fixed_not_switches(self):
        attached = self.attach()
        for key, value in AUTHORITY.items():
            self.assertEqual(attached.binding[key], value)
        self.assertEqual(attached.binding["permissions"], dict.fromkeys(OPERATIONS, "NOT_ESTABLISHED"))
        for key, value in (("production_eligible", True), ("approval_state", "approved"),
                           ("source_policy_clearance", "granted"), ("data_processing_permission_established", True)):
            with self.subTest(key=key):
                original = (self.root / CONTROL).read_bytes()
                self.mutate_control(lambda d: d.update({key: value}))
                self.blocked(lambda: self.attach(), "unsupported_capability")
                (self.root / CONTROL).write_bytes(original)
        self.mutate_control(lambda d: d["permissions"].update(LOCAL_PRIVATE_PROCESSING="ESTABLISHED"))
        self.blocked(lambda: self.attach(), "unsupported_capability")

    def test_incompleteness_is_explicit_and_no_mechanical_rules_or_collation_is_invented(self):
        binding = self.attach().binding
        self.assertEqual(binding["capabilities"], CAPABILITIES)
        self.assertEqual(binding["incompleteness"]["typed_materialization"], "incomplete")
        self.assertEqual(binding["incompleteness"]["optional_knowledge_state"], "absent")
        self.assertEqual(binding["incompleteness"]["product_slots"], 0)
        product = CanonicalQueryEngine.from_attachment(self.attach()).entity("paper-box")
        self.assertEqual(product.canonical_values["version_ids"], [])
        self.assertEqual(CanonicalQueryEngine.from_attachment(self.attach()).entities(entity_type="slot"), ())
        self.assertEqual(binding["capabilities"]["gameplay_rules"], "unsupported")
        self.assertEqual(binding["capabilities"]["mechanical_evidence"], "outside_tier_a")
        self.assertEqual(binding["capabilities"]["product_collation"], "unsupported")

    def test_extra_nested_control_values_cannot_hide_provider_content_or_approval(self):
        self.mutate_control(lambda d: d["incompleteness"].update(unreviewed_source_values={"approved": True}))
        self.blocked(lambda: self.attach(), "invalid_manifest")

    def test_third_selected_audit_cannot_expand_tier_a(self):
        def change(document):
            document["files"].append(binding(self.root, EXCLUDED_AUDIT, "AUDIT_CONTEXT"))
            document["files"].sort(key=lambda row: row["path"])
            document["closure_id"] = closure_identity(document["files"])
        self.mutate_control(change)
        self.blocked(lambda: self.attach(), "scope_mismatch")

    def test_casefold_collision_on_disk_is_rejected_without_reading_extra_bytes(self):
        original = self.root / self.card_path
        original.with_name("CARD.JSON").write_bytes(b"NOT A CANONICAL RECORD")
        self.blocked(lambda: self.attach(), "duplicate_path")

    def test_duplicate_keys_or_nonfinite_selected_json_rejected_after_fictional_rehash(self):
        path = self.root / self.card_path
        original = path.read_bytes()
        for raw in (b'{"name":"duplicate",' + original[1:], b'{"bad":NaN,' + original[1:]):
            with self.subTest(attack=raw[:20]):
                path.write_bytes(raw)
                self.rebind_one_fictional_file(self.card_path)
                self.blocked(lambda: self.attach(), "invalid_json")
        path.write_bytes(original)

    def test_missing_selected_file_fails(self):
        (self.root / self.card_path).unlink()
        self.blocked(lambda: self.attach(), "inventory_mismatch", "missing_file")

    def test_changed_selected_canonical_audit_and_source_files_fail(self):
        for name in (self.card_path, "data/canonical/state.json", *SELECTED_AUDITS, self.source_path):
            with self.subTest(path=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b" ")
                self.blocked(lambda: self.attach(), "integrity_mismatch")
                path.write_bytes(original)

    def test_optional_knowledge_absence_is_enforced(self):
        save(self.root / "data/canonical/knowledge/state.json", {})
        self.blocked(lambda: self.attach(), "scope_mismatch")

    def test_new_entity_in_selected_namespace_blocks(self):
        save(self.root / self.prefix / "cards/new-unit/card.json", {"id": "new-unit"})
        self.blocked(lambda: self.attach(), "inventory_mismatch")

    def test_new_empty_namespace_content_blocks(self):
        for suffix in ("finishes/new.json", "treatments/new.json", "rarities/new.json", "identifiers/new.json",
                       "packs/new.json", "slots/new.json", "sheets/new.json", "print_sheets/nested/new.json",
                       "product_versions/new.json"):
            with self.subTest(namespace=suffix):
                path = self.root / self.prefix / suffix
                save(path, {"id": "new"})
                self.blocked(lambda: self.attach(), "inventory_mismatch")
                path.unlink()

    def test_new_source_namespace_member_blocks_even_when_unselected(self):
        save(self.root / self.prefix / "sources/new-source.json", {"id": "new-source"})
        self.blocked(lambda: self.attach(), "inventory_mismatch")

    def test_new_game_namespace_blocks(self):
        (self.root / "data/canonical/games/new-game").mkdir()
        self.blocked(lambda: self.attach(), "scope_mismatch")

    def test_selected_symlink_and_namespace_directory_symlink_block(self):
        path = self.root / self.card_path
        backup = self.work / "saved-card.json"
        path.rename(backup)
        path.symlink_to(backup)
        self.blocked(lambda: self.attach(), "symlink")
        path.unlink()
        backup.rename(path)
        directory = self.root / self.prefix / "finishes"
        directory.symlink_to(self.work / "outside", target_is_directory=True)
        self.blocked(lambda: self.attach(), "symlink")

    def test_path_traversal_absolute_and_platform_ambiguous_bindings_block(self):
        for name in ("../outside.json", "/absolute.json", "data/../outside.json", "data\\canonical\\state.json",
                     "data//canonical/state.json", "data/./canonical/state.json"):
            with self.subTest(path=name):
                original = (self.root / CONTROL).read_bytes()
                self.mutate_control(lambda d: d["files"][0].update(path=name))
                self.blocked(lambda: self.attach())
                (self.root / CONTROL).write_bytes(original)
        self.blocked(lambda: self.attach(control="../outside.json"))

    def test_duplicate_and_casefold_colliding_selected_paths_block(self):
        for upper in (False, True):
            with self.subTest(casefold=upper):
                original = (self.root / CONTROL).read_bytes()
                def change(document):
                    row = dict(document["files"][0])
                    if upper:
                        row["path"] = row["path"].upper()
                    document["files"].append(row)
                    document["files"].sort(key=lambda r: r["path"])
                    document["closure_id"] = closure_identity(document["files"])
                self.mutate_control(change)
                self.blocked(lambda: self.attach(), "duplicate_path", "scope_mismatch")
                (self.root / CONTROL).write_bytes(original)

    def test_duplicate_json_keys_and_nonfinite_control_numbers_block(self):
        for raw in (b'{"profile":1,"profile":2}', b'{"x":NaN}', b'{"x":1e999}'):
            with self.subTest(raw=raw):
                (self.root / CONTROL).write_bytes(raw)
                self.blocked(lambda: self.attach(expected=self.document["profile_id"]), "invalid_json")

    def test_missing_namespace_or_absence_declaration_is_not_accepted(self):
        for change in (lambda d: d["namespaces"].pop(), lambda d: d.update(absent=[])):
            original = (self.root / CONTROL).read_bytes()
            self.mutate_control(change)
            self.blocked(lambda: self.attach(), "scope_mismatch")
            (self.root / CONTROL).write_bytes(original)

    def test_query_census_and_snapshot_must_match_the_reviewed_metadata(self):
        for change in (lambda d: d["entity_counts"].update(card=999),
                       lambda d: d.update(query_snapshot_id="sha256:" + "0" * 64)):
            original = (self.root / CONTROL).read_bytes()
            self.mutate_control(change)
            attached = self.attach()
            self.blocked(lambda: CanonicalQueryEngine.from_attachment(attached), "query_mismatch")
            (self.root / CONTROL).write_bytes(original)

    def test_rehashed_source_reference_injection_cannot_read_unselected_source(self):
        self.mutate_selected(self.card_path, lambda card: card["provenance"][0].update(source_id="unselected-author"))
        self.rebind_one_fictional_file(self.card_path)
        attached = self.attach()
        real_open = os.open
        def guarded(path, *args, **kwargs):
            if Path(path) == self.root / self.unselected_source:
                raise AssertionError("injected source was read")
            return real_open(path, *args, **kwargs)
        with patch("os.open", side_effect=guarded):
            self.blocked(lambda: CanonicalQueryEngine.from_attachment(attached), "unsupported_capability", "invalid_catalog")

    def test_post_attachment_content_control_and_inventory_drift_block_cached_queries(self):
        for attack in ("content", "control", "namespace", "knowledge"):
            with self.subTest(attack=attack):
                copy = self.work / ("drift-" + attack)
                shutil.copytree(self.root, copy)
                attached = self.attach(copy)
                engine = CanonicalQueryEngine.from_attachment(attached)
                resolver = CanonicalCollectionResolver.from_attachment(attached)
                if attack == "content":
                    path = copy / self.card_path
                    path.write_bytes(path.read_bytes() + b" ")
                elif attack == "control":
                    document = read(copy / CONTROL)
                    document["query_snapshot_id"] = "sha256:" + "0" * 64
                    save(copy / CONTROL, document)
                elif attack == "namespace":
                    save(copy / self.prefix / "finishes/new.json", {"id": "new"})
                else:
                    save(copy / "data/canonical/knowledge/state.json", {})
                self.blocked(lambda: engine.entity("paper-unit"))
                self.blocked(lambda: engine.snapshot())
                self.blocked(lambda: resolver.resolve({"entries": [{"printing_id": "paper-edition", "quantity": 1}]}))

    def test_attachment_binding_is_fresh_and_handle_is_immutable(self):
        attached = self.attach()
        binding = attached.binding
        binding["production_eligible"] = True
        binding["files"].clear()
        self.assertFalse(attached.binding["production_eligible"])
        self.assertEqual(len(attached.binding["files"]), 8)
        with self.assertRaises(FrozenInstanceError):
            attached.root = self.work

    def test_query_and_collection_root_retargeting_fail(self):
        attached = self.attach()
        for name in ("data_root", "games_root", "game"):
            with self.subTest(scope=name):
                engine = CanonicalQueryEngine.from_attachment(attached)
                resolver = CanonicalCollectionResolver.from_attachment(attached)
                setattr(engine, name, "wrong-game" if name == "game" else self.work)
                setattr(resolver, name, "wrong-game" if name == "game" else self.work)
                self.blocked(engine.snapshot)
                self.blocked(lambda: resolver.resolve({"entries": []}))
        engine = CanonicalQueryEngine.from_attachment(attached)
        engine._read_inventory = None
        self.blocked(engine.snapshot, "scope_changed")

    def test_attachment_failure_does_not_invoke_unrestricted_legacy_fallback(self):
        (self.root / self.card_path).unlink()
        with patch.object(CanonicalQueryEngine, "__init__", side_effect=AssertionError("ambient query fallback")):
            self.blocked(lambda: CanonicalQueryEngine.from_attachment(self.attach()))
        self.blocked(lambda: CanonicalQueryEngine.from_attachment(object()))
        self.blocked(lambda: CanonicalCollectionResolver.from_attachment(object()))

    def test_unrelated_domains_may_remain_present_but_never_enter_attachment(self):
        for name in ("data/market/never-open.json", "data/knowledge/facts/never-open.json",
                     "private/personal-collection.json", "data/test-evidence/fixture-only.json"):
            save(self.root / name, {"outside_catalog": "sentinel"})
        # Unselected name collisions do not become catalog inputs either.
        save(self.root / "unrelated-A.json", {})
        save(self.root / "unrelated-a.json", {})
        attached = self.attach()
        query = CanonicalQueryEngine.from_attachment(attached)
        self.assertEqual(query.snapshot().snapshot_id, self.document["query_snapshot_id"])
        self.assertFalse(any("market/" in r["path"] or "private/" in r["path"] or "test-evidence" in r["path"]
                             for r in attached.binding["files"]))

    def test_read_side_never_mutates_catalog_evidence_or_separate_collection_input(self):
        collection_path = self.work / "personal-input.json"
        save(collection_path, {"entries": [{"printing_id": "cloth-edition", "quantity": 1}]})
        before_catalog, before_personal = tree_bytes(self.root), collection_path.read_bytes()
        real_open = os.open
        def read_only(path, flags, *args, **kwargs):
            self.assertEqual(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC), 0)
            return real_open(path, flags, *args, **kwargs)
        with patch("os.open", side_effect=read_only), patch.object(Path, "write_bytes", side_effect=AssertionError("write attempted")):
            attached = self.attach()
            query = CanonicalQueryEngine.from_attachment(attached)
            query.snapshot()
            CanonicalCollectionResolver.from_attachment(attached).resolve(read(collection_path))
        self.assertEqual(tree_bytes(self.root), before_catalog)
        self.assertEqual(collection_path.read_bytes(), before_personal)

    def test_attachment_query_and_collection_need_no_network(self):
        with patch.object(socket, "create_connection", side_effect=AssertionError("network access")), \
             patch.object(socket.socket, "connect", side_effect=AssertionError("network access")):
            attached = self.attach()
            CanonicalQueryEngine.from_attachment(attached).snapshot()
            CanonicalCollectionResolver.from_attachment(attached).resolve({"entries": []})


if __name__ == "__main__":
    unittest.main()
