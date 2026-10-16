"""Immutable, version-bound fictional Gameplay Rules contracts."""
from copy import deepcopy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import (
    CardGameplaySemantics, GameAction, GameState, GameplayRulesSnapshot,
)
from gameplay_rules.snapshots import load_card_semantics, load_rules_snapshot
from gameplay_rules_fixture import (
    CAPABILITIES, FIXTURE_ROOT, action, changed_state, fixture_documents,
    semantic_body, snapshot_body, write_fixture,
)


class GameplayRulesContractTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.semantics, self.state = fixture_documents()

    def test_rules_snapshot_identity_is_deterministic_and_domain_bound(self):
        self.assertEqual(self.snapshot.identity, GameplayRulesSnapshot.create(snapshot_body()).identity)
        self.assertTrue(self.snapshot.identity.startswith("sha256:"))
        self.assertNotEqual(self.snapshot.identity, self.state.identity)
        self.snapshot.verify()

    def test_rules_snapshot_requires_explicit_version_and_effective_date(self):
        for field in ("rules_version", "effective_date", "engine_contract_version"):
            with self.subTest(field=field):
                body = snapshot_body()
                body.pop(field)
                with self.assertRaises(GameplayContractError):
                    GameplayRulesSnapshot.create(body)

    def test_no_implicit_latest_rules_selection(self):
        for version in ("latest", "current", ""):
            body = snapshot_body()
            body["rules_version"] = version
            with self.subTest(version=version), self.assertRaises(GameplayContractError):
                GameplayRulesSnapshot.create(body)
        with self.assertRaises(TypeError):
            load_rules_snapshot()

    def test_capability_manifest_is_explicit_including_unsupported_families(self):
        capabilities = self.snapshot.to_dict()["capabilities"]
        self.assertEqual(set(capabilities), set(CAPABILITIES))
        for name in ("replacement_effects", "continuous_effects", "triggered_abilities",
                     "layers", "combat", "format_legality", "deck_construction"):
            self.assertEqual(capabilities[name], "unsupported")
        body = snapshot_body()
        del body["capabilities"]["priority"]
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_unsupported_rule_family_list_cannot_contradict_coverage_manifest(self):
        body = snapshot_body()
        body["unsupported_rule_families"].remove("combat")
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_source_authority_metadata_is_not_catalog_or_real_permission(self):
        source = self.snapshot.to_dict()["sources"][0]
        self.assertEqual(source["source_class"], "project_authored_fictional")
        self.assertEqual(source["authoritative_reference"], "urn:mtglab:fictional-duel:rules:v1")
        self.assertEqual(source["effective_date"], self.snapshot.effective_date)
        self.assertIn("provenance", source)
        self.assertIn("permission_status", source)
        self.assertEqual(set(source["permission_status"].values()), {"NOT_APPLICABLE"})
        self.assertIn("retention_status", source)
        self.assertNotIn("source_policy_clearance", source)

    def test_official_source_metadata_does_not_become_executable_fictional_authority(self):
        body = snapshot_body()
        body["sources"][0]["source_class"] = "official_comprehensive_rules"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_source_identity_must_close_rule_provenance(self):
        body = snapshot_body()
        body["sources"][0]["source_id"] = "another-source"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_tampered_rule_definition_hash_fails_closed(self):
        body = self.snapshot.to_dict()
        body["rules"][0]["description"] = "Altered fictional rule"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.from_dict(body)
        unbound = semantic_body(self.snapshot)
        unbound["rules"][0]["description"] = "Altered without new rule hash"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(unbound)

    def test_tampered_snapshot_capability_identity_fails_closed(self):
        body = self.snapshot.to_dict()
        body["capabilities"]["combat"] = "supported"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.from_dict(body)

    def test_tampered_card_semantics_fails_closed(self):
        body = self.semantics[1].to_dict()
        body["mana_cost"]["generic"] += 1
        with self.assertRaises(GameplayContractError):
            CardGameplaySemantics.from_dict(body)

    def test_card_semantics_has_explicit_structured_not_oracle_execution(self):
        for semantics in self.semantics:
            body = semantics.to_dict()
            self.assertEqual(body["review_status"], "fictional_test_only")
            self.assertEqual(body["rules_snapshot_id"], self.snapshot.identity)
            self.assertNotIn("oracle_text", body)
            self.assertNotIn("script", body)
            self.assertNotIn("python", body)
            self.assertIn("unsupported_text", body)

    def test_state_identity_and_defensive_views_are_immutable(self):
        original = self.state.to_dict()
        changed = self.state.to_dict()
        changed["players"][0]["life"] = -200
        self.assertEqual(self.state.to_dict(), original)
        with self.assertRaises((AttributeError, TypeError)):
            self.state.revision = 50
        self.assertEqual(GameState.create(semantic_body(self.state)).identity, self.state.identity)

    def test_unknown_hidden_library_identity_is_not_invented(self):
        row = next(row for row in self.state.to_dict()["objects"] if row["knowledge"] == "unknown")
        self.assertIsNone(row["card_id"])
        self.assertIsNone(row["semantics_id"])
        self.assertIsNone(row["tapped"])
        self.assertEqual(row["zone_id"], "B:library")

    def test_core_zones_are_first_class_and_membership_is_unambiguous(self):
        state = self.state.to_dict()
        self.assertEqual({zone["kind"] for zone in state["zones"]},
                         {"library", "hand", "battlefield", "graveyard", "stack", "exile", "command"})
        self.assertEqual(len({obj["object_id"] for obj in state["objects"]}), len(state["objects"]))
        for obj in state["objects"]:
            self.assertIn(obj["zone_id"], {zone["zone_id"] for zone in state["zones"]})

    def test_duplicate_objects_and_invalid_zone_references_are_contract_errors(self):
        for mutation in (
            lambda body: body["objects"].append(deepcopy(body["objects"][0])),
            lambda body: body["objects"][0].update(zone_id="absent-zone"),
            lambda body: body["stack"].append("absent-object"),
        ):
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                changed_state(self.state, mutation)

    def test_duplicate_semantic_zone_identity_is_rejected(self):
        def duplicate_zone(body):
            row = deepcopy(body["zones"][0])
            row["zone_id"] = "same-owner-kind-other-id"
            body["zones"].append(row)
        with self.assertRaises(GameplayContractError):
            changed_state(self.state, duplicate_zone)

    def test_unconsumed_two_player_pass_sequence_is_an_impossible_state(self):
        with self.assertRaises(GameplayContractError):
            changed_state(self.state, consecutive_passes=["A", "B"])

    def test_system_or_ended_boundary_cannot_retain_an_incomplete_pass_sequence(self):
        for updates in (
            {"pending_system_actions": ["perform_state_based_actions"]},
            {"status": "ended"},
            {},
        ):
            with self.subTest(updates=updates), self.assertRaises(GameplayContractError):
                changed_state(self.state, priority_player=None, consecutive_passes=["A"], **updates)

    def test_in_progress_state_cannot_already_declare_outcome(self):
        for field in ("winner_ids", "loser_ids"):
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                changed_state(self.state, **{field: ["A"]})

    def test_executable_scripts_and_clock_metadata_are_not_accepted_contract_fields(self):
        for key in ("script", "eval", "created_at", "build_timestamp"):
            body = snapshot_body()
            body[key] = "untrusted data is never code"
            with self.subTest(key=key), self.assertRaises(GameplayContractError):
                GameplayRulesSnapshot.create(body)
        body = semantic_body(self.semantics[0])
        body["effects"] = [{"kind": "python", "script": "raise Exception('never execute')"}]
        with self.assertRaises(GameplayContractError):
            CardGameplaySemantics.create(body)

    def test_action_identity_binds_exact_before_state_and_rules(self):
        one = action(self.state, "cast_spell", object_id="ember-scroll")
        two = action(self.state, "cast_spell", object_id="ember-scroll")
        self.assertEqual(one.identity, two.identity)
        changed = changed_state(self.state, revision=1)
        self.assertNotEqual(one.identity, action(changed, "cast_spell", object_id="ember-scroll").identity)
        self.assertEqual(one.expected_state_id, self.state.identity)
        self.assertEqual(one.rules_snapshot_id, self.snapshot.identity)

    def test_malformed_identity_or_nonfinite_numeric_state_is_rejected(self):
        body = self.state.to_dict()
        body["state_id"] = "not-a-content-identity"
        with self.assertRaises(GameplayContractError):
            GameState.from_dict(body)
        for value in (float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(GameplayContractError):
                changed_state(self.state, lambda body: body["players"][0].update(life=value))

    def test_explicit_snapshot_loader_relocation_preserves_identity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_fixture(root / "first")
            shutil.copytree(root / "first", root / "relocated")
            one = load_rules_snapshot(root / "first" / "rules-snapshot.json")
            two = load_rules_snapshot(root / "relocated" / "rules-snapshot.json")
            self.assertEqual(one.identity, two.identity)
            self.assertEqual(one.to_dict(), two.to_dict())
            one_semantics = load_card_semantics(root / "first" / "ember-scroll.semantics.json")
            two_semantics = load_card_semantics(root / "relocated" / "ember-scroll.semantics.json")
            self.assertEqual(one_semantics.identity, two_semantics.identity)

    def test_loader_rejects_duplicate_json_keys_and_nonfinite_numbers(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "bad.json"
            for raw in ('{"game_id":"a","game_id":"b"}', '{"not_finite":NaN}'):
                target.write_text(raw, encoding="utf-8")
                with self.subTest(raw=raw), self.assertRaises(GameplayContractError):
                    load_rules_snapshot(target)

    def test_missing_explicit_snapshot_fails_without_ambient_fallback(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(GameplayContractError):
                load_rules_snapshot(Path(temporary) / "missing-snapshot.json")

    def test_retained_fixture_has_pinned_identities_and_original_fictional_only_status(self):
        retained = load_rules_snapshot(FIXTURE_ROOT / "rules-snapshot.json")
        self.assertEqual(retained.to_dict(), self.snapshot.to_dict())
        for expected in self.semantics:
            actual = load_card_semantics(FIXTURE_ROOT / (expected.card_id + ".semantics.json"))
            self.assertEqual(actual.to_dict(), expected.to_dict())
        raw_state = json.loads((FIXTURE_ROOT / "game-state.json").read_text(encoding="utf-8"))
        self.assertEqual(GameState.from_dict(raw_state).to_dict(), self.state.to_dict())
