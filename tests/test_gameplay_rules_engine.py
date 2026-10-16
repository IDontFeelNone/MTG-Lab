"""Executable proof of bounded original fictional gameplay, never real Magic rules."""
from copy import deepcopy
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from gameplay_rules.costs import plan_mana_payment
from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import (
    CardGameplaySemantics, GameState, GameTransition, GameplayRulesSnapshot, LegalityResult,
)
from gameplay_rules.snapshots import load_card_semantics, load_game_state, load_rules_snapshot
from gameplay_rules.models import rule_identity
from gameplay_rules_fixture import (
    action, changed_state, cost, fixture_documents, semantic_body, snapshot_body, write_fixture,
)


class GameplayRulesEngineTests(unittest.TestCase):
    def setUp(self):
        self.snapshot, self.semantics, self.state = fixture_documents()
        self.engine = GameplayRulesEngine(self.snapshot, self.semantics)

    def with_mana(self, state=None, **pool):
        return changed_state(state or self.state,
                             lambda body: body["players"][0].update(mana_pool=pool))

    def cast(self, state=None, card="ember-scroll"):
        state = state or self.state
        return action(state, "cast_spell", object_id=card)

    def check(self, state=None, requested=None):
        state = state or self.state
        return self.engine.evaluate_action(state, requested or self.cast(state)).to_dict()

    def apply(self, state, requested):
        result = self.engine.apply_action(state, requested)
        self.assertIsInstance(result, GameTransition, getattr(result, "to_dict", lambda: {})())
        return result, GameState.from_dict(result.to_dict()["after_state"])

    def checkpoint(self, state):
        transitions = []
        while state.to_dict()["pending_system_actions"]:
            self.assertLess(len(transitions), 8, "Fictional system boundary must terminate")
            kind = state.to_dict()["pending_system_actions"][0]
            transition, state = self.apply(state, action(state, kind, actor=None))
            transitions.append(transition)
        return transitions, state

    def player(self, state, who="A"):
        return next(row for row in state.to_dict()["players"] if row["player_id"] == who)

    def obj(self, state, which):
        return next(row for row in state.to_dict()["objects"] if row["object_id"] == which)

    def supported_semantics(self, card_id, mutate):
        rows = []
        selected = None
        for semantics in self.semantics:
            body = semantic_body(semantics)
            if semantics.card_id == card_id:
                mutate(body)
                selected = CardGameplaySemantics.create(body)
                rows.append(selected)
            else:
                rows.append(semantics)
        state = changed_state(self.state, lambda body: [
            row.update(semantics_id=selected.identity) for row in body["objects"]
            if row["card_id"] == card_id])
        return GameplayRulesEngine(self.snapshot, rows), state

    def test_insufficient_mana_is_illegal_with_explicit_cost_failure_and_rules(self):
        result = self.check()
        self.assertEqual(result["status"], "ILLEGAL")
        self.assertTrue(result["failed_requirements"])
        self.assertTrue(result["required_costs"])
        categories = {ref["category"] for ref in result["rule_references"]}
        self.assertIn("mana_payment", categories)
        self.assertIn("spell_casting", categories)
        self.assertTrue(all(ref["rules_snapshot_id"] == self.snapshot.identity
                            for ref in result["rule_references"]))

    def test_exact_sufficient_mana_is_legal_with_supported_rule_references(self):
        state = self.with_mana(red=2)
        result = self.check(state)
        self.assertEqual(result["status"], "LEGAL")
        self.assertFalse(result["failed_requirements"])
        self.assertTrue(result["satisfied_requirements"])
        self.assertTrue(result["rule_references"])

    def test_evaluate_is_distinct_from_apply_and_does_not_change_input(self):
        state = self.with_mana(red=2)
        before = state.to_dict()
        requested = self.cast(state)
        one = self.engine.evaluate_action(state, requested)
        two = self.engine.evaluate_action(state, requested)
        self.assertIsInstance(one, LegalityResult)
        self.assertEqual(one.to_dict(), two.to_dict())
        self.assertEqual(one.identity, two.identity)
        self.assertEqual(state.to_dict(), before)
        transition, after = self.apply(state, requested)
        self.assertNotEqual(after.identity, state.identity)
        self.assertEqual(state.to_dict(), before)
        self.assertEqual(transition.before_state_id, state.identity)

    def test_apply_known_illegal_returns_result_without_transition_or_mutation(self):
        before = self.state.to_dict()
        result = self.engine.apply_action(self.state, self.cast())
        self.assertIsInstance(result, LegalityResult)
        self.assertEqual(result.status, "ILLEGAL")
        self.assertEqual(self.state.to_dict(), before)

    def test_cast_pays_exact_mana_and_moves_hand_to_stack_explicitly(self):
        state = self.with_mana(red=2)
        transition, after = self.apply(state, self.cast(state))
        self.assertTrue(all(amount == 0 for amount in self.player(after)["mana_pool"].values()))
        self.assertEqual(self.obj(after, "ember-scroll")["zone_id"], "shared:stack")
        self.assertEqual(after.to_dict()["stack"], ["ember-scroll"])
        self.assertTrue(transition.to_dict()["zone_changes"])
        self.assertTrue(transition.to_dict()["resource_changes"])
        self.assertTrue(transition.to_dict()["stack_changes"])
        self.assertEqual(after.revision, state.revision + 1)

    def test_actor_without_priority_is_illegal(self):
        state = self.with_mana(red=2)
        state = changed_state(state, priority_player="B")
        result = self.check(state)
        self.assertEqual(result["status"], "ILLEGAL")
        self.assertTrue(result["failed_requirements"])

    def test_sorcery_cast_requires_own_main_phase(self):
        for changes in ({"phase": "ending", "step": "end"}, {"active_player": "B"}):
            state = changed_state(self.with_mana(red=2), **changes)
            with self.subTest(changes=changes):
                self.assertEqual(self.check(state)["status"], "ILLEGAL")

    def test_sorcery_cast_requires_empty_stack(self):
        state = self.with_mana(red=2, blue=1)
        _, state = self.apply(state, self.cast(state, "swift-lantern"))
        self.assertEqual(self.check(state)["status"], "ILLEGAL")

    def test_instant_cast_is_legal_in_other_players_turn_with_priority(self):
        state = changed_state(self.with_mana(blue=1), active_player="B", phase="ending", step="end")
        self.assertEqual(self.check(state, self.cast(state, "swift-lantern"))["status"], "LEGAL")

    def test_instant_still_requires_actor_priority(self):
        state = changed_state(self.with_mana(blue=1), priority_player="B")
        self.assertEqual(self.check(state, self.cast(state, "swift-lantern"))["status"], "ILLEGAL")

    def test_fictional_tap_mana_ability_adds_resource_without_using_stack(self):
        requested = action(self.state, "activate_ability", object_id="pebble-resource", ability_id="make-red")
        transition, after = self.apply(self.state, requested)
        self.assertEqual(self.player(after)["mana_pool"].get("red"), 2)
        self.assertTrue(self.obj(after, "pebble-resource")["tapped"])
        self.assertEqual(after.to_dict()["stack"], [])
        self.assertTrue(transition.to_dict()["resource_changes"])
        self.assertEqual(self.check(after)["status"], "LEGAL")

    def test_tapped_mana_source_cannot_pay_tap_cost_again(self):
        _, state = self.apply(self.state, action(self.state, "activate_ability",
                                               object_id="pebble-resource", ability_id="make-red"))
        result = self.check(state, action(state, "activate_ability", object_id="pebble-resource", ability_id="make-red"))
        self.assertEqual(result["status"], "ILLEGAL")

    def test_first_land_play_moves_hand_to_battlefield_without_stack(self):
        transition, after = self.apply(self.state, action(self.state, "play_land", object_id="moss-plot"))
        self.assertEqual(self.obj(after, "moss-plot")["zone_id"], "A:battlefield")
        self.assertEqual(self.player(after)["land_plays_used"], 1)
        self.assertEqual(after.to_dict()["stack"], [])
        self.assertTrue(transition.to_dict()["zone_changes"])

    def test_second_land_play_in_same_turn_is_illegal(self):
        def second_land(body):
            row = deepcopy(next(obj for obj in body["objects"] if obj["object_id"] == "moss-plot"))
            row["object_id"] = "another-moss-plot"
            body["objects"].append(row)
        state = changed_state(self.state, second_land)
        _, after = self.apply(state, action(state, "play_land", object_id="moss-plot"))
        _, after = self.checkpoint(after)
        result = self.check(after, action(after, "play_land", object_id="another-moss-plot"))
        self.assertEqual(result["status"], "ILLEGAL")

    def test_unmodeled_land_allowance_override_does_not_bypass_snapshot_policy(self):
        state = changed_state(self.state, lambda body: body["players"][0].update(
            land_plays_used=1, land_plays_available=2))
        result = self.check(state, action(state, "play_land", object_id="moss-plot"))
        self.assertEqual(result["status"], "UNSUPPORTED")
        self.assertIn("unmodeled_land_play_allowance", result["unsupported_dimensions"])

    def test_land_requires_configured_main_phase_and_active_player(self):
        for changes in ({"active_player": "B"}, {"phase": "ending", "step": "end"}, {"priority_player": "B"}):
            state = changed_state(self.state, **changes)
            with self.subTest(changes=changes):
                self.assertEqual(self.check(state, action(state, "play_land", object_id="moss-plot"))["status"], "ILLEGAL")

    def test_cast_and_land_require_actor_hand_zone_not_only_object_ownership(self):
        for kind, which in (("cast_spell", "ember-scroll"), ("play_land", "moss-plot")):
            state = changed_state(self.with_mana(red=2), lambda body: [
                row.update(zone_id="B:hand") for row in body["objects"]
                if row["object_id"] == which])
            with self.subTest(kind=kind):
                self.assertEqual(self.check(state, action(state, kind, object_id=which))["status"], "ILLEGAL")

    def test_timing_and_sba_dependencies_cannot_be_bypassed_by_partial_snapshot(self):
        for capability in ("stack", "turn_structure", "state_based_actions"):
            body = snapshot_body()
            body["capabilities"][capability] = "unsupported"
            body["unsupported_rule_families"].append(capability)
            snapshot = GameplayRulesSnapshot.create(body)
            semantics = []
            replacements = {}
            for original in self.semantics:
                definition = semantic_body(original)
                definition["rules_snapshot_id"] = snapshot.identity
                updated = CardGameplaySemantics.create(definition)
                semantics.append(updated)
                replacements[original.identity] = updated.identity
            state = changed_state(self.with_mana(red=2), lambda data: [
                row.update(semantics_id=replacements[row["semantics_id"]])
                for row in data["objects"] if row["semantics_id"] in replacements],
                rules_snapshot_id=snapshot.identity)
            engine = GameplayRulesEngine(snapshot, semantics)
            for kind, which in (("cast_spell", "ember-scroll"), ("play_land", "moss-plot")):
                with self.subTest(capability=capability, kind=kind):
                    self.assertEqual(engine.evaluate_action(
                        state, action(state, kind, object_id=which)).status, "UNSUPPORTED")

    def test_common_rule_status_is_required_even_for_priority_actions(self):
        for category in ("state_based_actions", "turn_structure", "zones"):
            body = snapshot_body()
            for rule in body["rules"]:
                if rule["category"] == category:
                    rule["status"] = "unknown"
                    rule["rule_hash"] = rule_identity(rule)
            snapshot = GameplayRulesSnapshot.create(body)
            semantics, replacements = [], {}
            for original in self.semantics:
                definition = semantic_body(original)
                definition["rules_snapshot_id"] = snapshot.identity
                updated = CardGameplaySemantics.create(definition)
                semantics.append(updated)
                replacements[original.identity] = updated.identity
            state = changed_state(self.state, lambda data: [
                row.update(semantics_id=replacements[row["semantics_id"]])
                for row in data["objects"] if row["semantics_id"] in replacements],
                rules_snapshot_id=snapshot.identity)
            engine = GameplayRulesEngine(snapshot, semantics)
            with self.subTest(category=category):
                result = engine.evaluate_action(state, action(state, "pass_priority")).to_dict()
                self.assertEqual(result["status"], "INDETERMINATE")
                self.assertTrue(any(ref["category"] == category and ref["status"] == "unknown"
                                    for ref in result["rule_references"]))

    def test_pass_priority_transfers_to_other_player_and_records_sequence(self):
        transition, after = self.apply(self.state, action(self.state, "pass_priority"))
        self.assertEqual(after.priority_player, "B")
        self.assertEqual(after.to_dict()["consecutive_passes"], ["A"])
        self.assertTrue(transition.to_dict()["state_changes"])

    def test_both_players_pass_schedule_system_boundary_before_resolution(self):
        state = self.with_mana(red=2)
        _, state = self.apply(state, self.cast(state))
        _, state = self.apply(state, action(state, "pass_priority"))
        _, state = self.apply(state, action(state, "pass_priority", actor="B"))
        self.assertIsNone(state.priority_player)
        self.assertEqual(state.to_dict()["pending_system_actions"],
                         ["perform_state_based_actions", "resolve_top_of_stack"])
        self.assertEqual(state.to_dict()["stack"], ["ember-scroll"])

    def test_stack_resolution_changes_life_and_moves_object_to_configured_zone(self):
        state = self.with_mana(red=2)
        _, state = self.apply(state, self.cast(state))
        _, state = self.apply(state, action(state, "pass_priority"))
        _, state = self.apply(state, action(state, "pass_priority", actor="B"))
        transitions, after = self.checkpoint(state)
        self.assertEqual(self.obj(after, "ember-scroll")["zone_id"], "A:graveyard")
        self.assertEqual(self.player(after, "B")["life"], 8)
        self.assertEqual(after.to_dict()["stack"], [])
        self.assertTrue(any(row.to_dict()["zone_changes"] for row in transitions))
        self.assertEqual(after.priority_player, "A")

    def test_resolution_requires_exact_pending_system_boundary(self):
        result = self.check(self.state, action(self.state, "resolve_top_of_stack", actor=None))
        self.assertEqual(result["status"], "ILLEGAL")

    def test_player_action_cannot_skip_pending_system_boundary(self):
        state = changed_state(self.with_mana(red=2), priority_player=None,
                              pending_system_actions=["perform_state_based_actions"])
        self.assertEqual(self.check(state)["status"], "ILLEGAL")

    def test_both_pass_on_empty_stack_can_advance_configured_step(self):
        _, state = self.apply(self.state, action(self.state, "pass_priority"))
        _, state = self.apply(state, action(state, "pass_priority", actor="B"))
        self.assertIn("advance_step_or_phase", state.to_dict()["pending_system_actions"])
        transitions, after = self.checkpoint(state)
        self.assertEqual((after.phase, after.step), ("ending", "end"))
        self.assertEqual(after.active_player, "A")
        self.assertTrue(transitions)

    def test_step_advance_cannot_bypass_nonempty_stack(self):
        state = self.with_mana(red=2)
        _, state = self.apply(state, self.cast(state))
        state = changed_state(state, priority_player=None,
                              pending_system_actions=["advance_step_or_phase"])
        result = self.check(state, action(state, "advance_step_or_phase", actor=None))
        self.assertEqual(result["status"], "ILLEGAL")

    def test_turn_wrap_swaps_active_player_without_inventing_draw_or_untap(self):
        state = changed_state(self.state, phase="ending", step="end",
                              priority_player=None, pending_system_actions=["advance_step_or_phase"])
        before_objects = state.to_dict()["objects"]
        _, after = self.apply(state, action(state, "advance_step_or_phase", actor=None))
        self.assertEqual(after.active_player, "B")
        self.assertEqual(after.turn_number, 2)
        self.assertEqual((after.phase, after.step), ("beginning", "start"))
        self.assertEqual(after.to_dict()["objects"], before_objects)

    def test_zero_life_sba_ends_game_with_explicit_loser_and_winner(self):
        state = changed_state(self.state,
                              lambda body: body["players"][1].update(life=0),
                              priority_player=None, pending_system_actions=["perform_state_based_actions"])
        transition, after = self.apply(state, action(state, "perform_state_based_actions", actor=None))
        self.assertEqual(after.status, "ended")
        self.assertEqual(after.to_dict()["loser_ids"], ["B"])
        self.assertEqual(after.to_dict()["winner_ids"], ["A"])
        self.assertTrue(transition.to_dict()["state_changes"])
        self.assertEqual(self.check(after, action(after, "pass_priority"))["status"], "ILLEGAL")

    def test_simultaneous_zero_life_is_draw_without_arbitrary_winner(self):
        state = changed_state(self.state, lambda body: [row.update(life=0) for row in body["players"]],
                              priority_player=None, pending_system_actions=["perform_state_based_actions"])
        _, after = self.apply(state, action(state, "perform_state_based_actions", actor=None))
        self.assertEqual(after.status, "ended")
        self.assertEqual(after.to_dict()["loser_ids"], ["A", "B"])
        self.assertEqual(after.to_dict()["winner_ids"], [])

    def test_unknown_life_at_sba_checkpoint_remains_indeterminate(self):
        state = changed_state(self.state, lambda body: body["players"][1].update(life=None),
                              priority_player=None, pending_system_actions=["perform_state_based_actions"])
        result = self.check(state, action(state, "perform_state_based_actions", actor=None))
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_known_game_loss_condition_requires_sba_before_player_cast(self):
        state = changed_state(self.with_mana(red=2), lambda body: body["players"][1].update(life=0))
        result = self.check(state)
        self.assertEqual(result["status"], "ILLEGAL")
        self.assertIn("state_based_action_required", result["failed_requirements"])

    def test_unknown_life_cannot_bypass_required_sba_information(self):
        state = changed_state(self.with_mana(red=2), lambda body: body["players"][1].update(life=None))
        result = self.check(state)
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_unknown_hidden_unrelated_library_does_not_get_revealed_or_block_known_action(self):
        state = self.with_mana(red=2)
        before = self.obj(state, "unobserved-library-object")
        self.assertEqual(self.check(state)["status"], "LEGAL")
        _, after = self.apply(state, self.cast(state))
        self.assertEqual(self.obj(after, "unobserved-library-object"), before)

    def test_unknown_object_semantics_cannot_be_guessed_from_identity_or_text(self):
        state = changed_state(self.state, lambda body: body["objects"][1].update(
            card_id=None, semantics_id=None, knowledge="unknown"))
        result = self.check(state)
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_unknown_global_priority_state_does_not_become_known_illegal(self):
        state = changed_state(self.with_mana(red=2), priority_player=None,
                              unknown_fields=["priority_player"])
        result = self.check(state)
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_unsupported_replacement_effect_refuses_confident_base_rule_answer(self):
        state = changed_state(self.with_mana(red=2), active_effects=[{
            "effect_id": "fictional-replacement", "capability": "replacement_effects",
            "affected_actions": ["cast_spell"], "knowledge": "unsupported"}])
        result = self.check(state)
        self.assertEqual(result["status"], "UNSUPPORTED")
        self.assertTrue(result["unsupported_dimensions"])

    def test_unsupported_continuous_effect_refuses_confident_base_rule_answer(self):
        state = changed_state(self.with_mana(red=2), active_effects=[{
            "effect_id": "fictional-continuous", "capability": "continuous_effects",
            "affected_actions": ["cast_spell"], "knowledge": "unsupported"}])
        self.assertEqual(self.check(state)["status"], "UNSUPPORTED")

    def test_unknown_override_is_indeterminate_instead_of_base_rule_certainty(self):
        state = changed_state(self.with_mana(red=2), active_effects=[{
            "effect_id": "fictional-unknown-override", "capability": "continuous_effects",
            "affected_actions": ["cast_spell"], "knowledge": "unknown"}])
        self.assertEqual(self.check(state)["status"], "INDETERMINATE")

    def test_trigger_semantics_on_active_object_are_not_silently_ignored(self):
        engine, state = self.supported_semantics("pebble-resource", lambda body: body.update(
            required_capabilities=["triggered_abilities"], completeness="partial"))
        state = self.with_mana(state, red=2)
        result = engine.evaluate_action(state, self.cast(state)).to_dict()
        self.assertIn(result["status"], {"UNSUPPORTED", "INDETERMINATE"})
        self.assertTrue(result["unsupported_dimensions"] or result["unknown_requirements"])

    def test_unknown_structured_effect_cannot_execute_without_capability_annotation(self):
        engine, state = self.supported_semantics("pebble-resource", lambda body: body.update(
            effects=[{"kind": "fictional_unimplemented_replacement"}]))
        state = self.with_mana(state, red=2)
        result = engine.evaluate_action(state, self.cast(state)).to_dict()
        self.assertEqual(result["status"], "UNSUPPORTED")
        self.assertTrue(result["unsupported_dimensions"])

    def test_unmodeled_ability_on_active_object_is_not_silently_ignored(self):
        engine, state = self.supported_semantics("pebble-resource", lambda body: body["abilities"][0].update(
            uses_stack=True))
        state = self.with_mana(state, red=2)
        result = engine.evaluate_action(state, self.cast(state)).to_dict()
        self.assertEqual(result["status"], "UNSUPPORTED")

    def test_authored_restriction_requires_supported_interpretation(self):
        engine, state = self.supported_semantics("ember-scroll", lambda body: body.update(
            restrictions=["fictional-unmodeled-casting-restriction"]))
        state = self.with_mana(state, red=2)
        self.assertEqual(engine.evaluate_action(state, self.cast(state)).status, "UNSUPPORTED")

    def test_unknown_cost_information_is_indeterminate(self):
        engine, state = self.supported_semantics("ember-scroll", lambda body: body["mana_cost"].update(known=False))
        result = engine.evaluate_action(state, self.cast(state)).to_dict()
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_unsupported_cost_type_is_not_ignored(self):
        engine, state = self.supported_semantics("ember-scroll", lambda body: body["mana_cost"].update(
            kind="hybrid", unsupported=["hybrid"]))
        state = self.with_mana(state, red=20, blue=20)
        result = engine.evaluate_action(state, self.cast(state)).to_dict()
        self.assertEqual(result["status"], "UNSUPPORTED")
        self.assertTrue(result["unsupported_dimensions"])

    def test_unknown_action_kind_is_unsupported_not_illegal_or_exception(self):
        result = self.check(self.state, action(self.state, "propose_combat"))
        self.assertEqual(result["status"], "UNSUPPORTED")
        self.assertTrue(result["unsupported_dimensions"])
        self.assertEqual(result["rule_references"], [])
        self.assertEqual(result["rules_snapshot_id"], self.state.rules_snapshot_id)

    def test_format_legality_and_deck_construction_are_separate_unsupported_capabilities(self):
        for kind in ("can_include_in_deck", "check_format_legality", "rank_best_play"):
            with self.subTest(kind=kind):
                self.assertEqual(self.check(self.state, action(self.state, kind))["status"], "UNSUPPORTED")

    def test_legality_payload_contains_no_strategy_score_or_recommendation(self):
        result = self.check(self.with_mana(red=2))
        for forbidden in ("strategy", "score", "win_probability", "recommendation", "best_play", "power_rating"):
            self.assertNotIn(forbidden, result)
        self.assertEqual(result["status"], "LEGAL")

    def test_legal_result_cannot_conceal_failed_unknown_or_unsupported_requirements(self):
        result = self.engine.evaluate_action(self.with_mana(red=2), self.cast(self.with_mana(red=2)))
        for key in ("failed_requirements", "unknown_requirements", "unsupported_dimensions"):
            body = semantic_body(result)
            body[key] = ["contradictory-status"]
            with self.subTest(key=key), self.assertRaises(GameplayContractError):
                LegalityResult.create(body)

    def test_nonlegal_result_must_expose_corresponding_reason(self):
        legal = self.engine.evaluate_action(self.with_mana(red=2), self.cast(self.with_mana(red=2)))
        for status in ("ILLEGAL", "INDETERMINATE", "UNSUPPORTED"):
            body = semantic_body(legal)
            body["status"] = status
            with self.subTest(status=status), self.assertRaises(GameplayContractError):
                LegalityResult.create(body)

    def test_rules_snapshot_mismatch_is_contract_error(self):
        state = changed_state(self.state, rules_snapshot_id="sha256:" + "0" * 64)
        with self.assertRaises(GameplayContractError):
            self.engine.evaluate_action(state, self.cast(state))

    def test_wrong_game_is_contract_error_not_cross_game_inference(self):
        state = changed_state(self.state, game_id="another-fictional-game")
        with self.assertRaises(GameplayContractError):
            self.engine.evaluate_action(state, self.cast(state))

    def test_action_expected_state_mismatch_is_contract_error(self):
        stale = self.cast(self.with_mana(red=2))
        with self.assertRaises(GameplayContractError):
            self.engine.evaluate_action(self.state, stale)

    def test_incompatible_card_semantics_snapshot_is_contract_error(self):
        body = semantic_body(self.semantics[0])
        body["rules_snapshot_id"] = "sha256:" + "0" * 64
        incompatible = CardGameplaySemantics.create(body)
        with self.assertRaises(GameplayContractError):
            GameplayRulesEngine(self.snapshot, [incompatible] + self.semantics[1:])

    def test_card_semantics_cannot_inherit_unbound_source_permission_or_provenance(self):
        for references in ([], ["unbound-source"]):
            body = semantic_body(self.semantics[0])
            body["source_references"] = references
            incompatible = CardGameplaySemantics.create(body)
            with self.subTest(references=references), self.assertRaises(GameplayContractError):
                GameplayRulesEngine(self.snapshot, [incompatible] + self.semantics[1:])

    def test_engine_semantics_cannot_be_retargeted_after_explicit_selection(self):
        original = self.semantics[1]
        body = semantic_body(original)
        body["mana_cost"] = cost()
        changed = CardGameplaySemantics.create(body)
        with self.assertRaises(TypeError):
            self.engine._definitions[original.identity] = changed
        self.engine._definitions = {**self.engine._definitions, original.identity: changed}
        state = self.with_mana(red=2)
        with self.assertRaises(GameplayContractError):
            self.engine.evaluate_action(state, self.cast(state))

    def test_unimplemented_capability_cannot_be_declared_supported(self):
        body = snapshot_body()
        body["capabilities"]["layers"] = "supported"
        body["unsupported_rule_families"].remove("layers")
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_rules_snapshot_and_all_executable_results_relocate_identically(self):
        with tempfile.TemporaryDirectory() as temporary:
            roots = [Path(temporary) / "first", Path(temporary) / "elsewhere"]
            results = []
            for root in roots:
                write_fixture(root)
                snapshot = load_rules_snapshot(root / "rules-snapshot.json")
                semantics = [load_card_semantics(root / (item.card_id + ".semantics.json"))
                             for item in self.semantics]
                state = self.with_mana(load_game_state(root / "game-state.json"), red=2)
                engine = GameplayRulesEngine(snapshot, semantics)
                requested = self.cast(state)
                results.append((snapshot.identity, engine.evaluate_action(state, requested).to_dict(),
                                engine.apply_action(state, requested).to_dict()))
            self.assertEqual(results[0], results[1])

    def test_transition_identity_and_replay_are_exact_and_deterministic(self):
        state = self.with_mana(red=2)
        requested = self.cast(state)
        first = self.engine.apply_action(state, requested)
        second = self.engine.apply_action(state, requested)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.identity, second.identity)
        replayed = self.engine.replay_transition(state, first)
        self.assertEqual(replayed.to_dict(), first.to_dict())
        self.assertEqual(replayed.after_state_id, first.after_state_id)

    def test_transition_replay_rejects_other_snapshot_or_before_state(self):
        state = self.with_mana(red=2)
        transition = self.engine.apply_action(state, self.cast(state))
        changed = changed_state(state, revision=99)
        with self.assertRaises(GameplayContractError):
            self.engine.replay_transition(changed, transition)
        body = transition.to_dict()
        body["rules_snapshot_id"] = "sha256:" + "0" * 64
        with self.assertRaises(GameplayContractError):
            GameTransition.from_dict(body)

    def test_transition_replay_requires_verified_before_state_not_dictionary(self):
        state = self.with_mana(red=2)
        transition = self.engine.apply_action(state, self.cast(state))
        with self.assertRaises(GameplayContractError):
            self.engine.replay_transition(state.to_dict(), transition)

    def test_tampered_transition_after_state_fails_closed(self):
        state = self.with_mana(red=2)
        transition = self.engine.apply_action(state, self.cast(state))
        body = transition.to_dict()
        body["after_state"]["players"][0]["life"] = 1
        with self.assertRaises(GameplayContractError):
            GameTransition.from_dict(body)

    def test_transition_defensive_views_cannot_mutate_after_state(self):
        state = self.with_mana(red=2)
        transition = self.engine.apply_action(state, self.cast(state))
        original = transition.to_dict()
        view = transition.to_dict()
        view["after_state"]["players"][0]["mana_pool"]["red"] = 900
        self.assertEqual(transition.to_dict(), original)
        with self.assertRaises((AttributeError, TypeError)):
            transition.after_state_id = state.identity

    def test_runtime_uses_no_network_randomness_or_wall_clock(self):
        state = self.with_mana(red=2)
        with patch.object(socket, "socket", side_effect=AssertionError("No network")), \
             patch("random.random", side_effect=AssertionError("No randomness")), \
             patch("random.choice", side_effect=AssertionError("No randomness")), \
             patch("time.time", side_effect=AssertionError("No wall clock")):
            result = self.engine.evaluate_action(state, self.cast(state))
            transition = self.engine.apply_action(state, self.cast(state))
        self.assertEqual(result.status, "LEGAL")
        self.assertIsInstance(transition, GameTransition)


class GameplayManaPaymentTests(unittest.TestCase):
    def test_colored_reservation_precedes_deterministic_generic_payment(self):
        result = plan_mana_payment(cost(1, red=1), {"red": 2, "blue": 1}, ["blue", "red"]).to_dict()
        self.assertEqual(result["status"], "LEGAL")
        self.assertEqual(result["payment"], {"blue": 1, "red": 1})
        self.assertEqual(result["pool_after"], {"blue": 0, "red": 1})

    def test_payment_result_identity_is_deterministic(self):
        first = plan_mana_payment(cost(1, red=1), {"red": 2}, ["blue", "red"])
        second = plan_mana_payment(cost(1, red=1), {"red": 2}, ["blue", "red"])
        self.assertEqual(first.identity, second.identity)
        self.assertEqual(first.to_dict(), second.to_dict())

    def test_known_insufficient_colored_mana_is_illegal(self):
        result = plan_mana_payment(cost(red=1), {"blue": 5}, ["blue", "red"]).to_dict()
        self.assertEqual(result["status"], "ILLEGAL")
        self.assertTrue(result["failed_requirements"])

    def test_exact_explicit_payment_plan_is_preserved(self):
        result = plan_mana_payment(cost(1, red=1), {"red": 2, "blue": 1}, ["blue", "red"],
                                   payment={"red": 2}).to_dict()
        self.assertEqual(result["status"], "LEGAL")
        self.assertEqual(result["payment"], {"red": 2})
        self.assertEqual(result["pool_after"].get("blue"), 1)

    def test_bad_explicit_payment_does_not_overpay_or_invent_resources(self):
        for payment in ({"red": 3}, {"blue": 2}, {"red": 1}):
            result = plan_mana_payment(cost(1, red=1), {"red": 2, "blue": 2}, ["blue", "red"],
                                       payment=payment).to_dict()
            with self.subTest(payment=payment):
                self.assertEqual(result["status"], "ILLEGAL")

    def test_unknown_cost_is_indeterminate(self):
        body = cost(red=1)
        body["known"] = False
        result = plan_mana_payment(body, {"red": 10}, ["blue", "red"]).to_dict()
        self.assertEqual(result["status"], "INDETERMINATE")
        self.assertTrue(result["unknown_requirements"])

    def test_unsupported_cost_is_explicit_even_with_large_pool(self):
        for form in ("hybrid", "phyrexian", "snow", "X", "convoke", "spend_restriction"):
            body = cost()
            body["unsupported"] = [form]
            result = plan_mana_payment(body, {"red": 999}, ["blue", "red"]).to_dict()
            with self.subTest(form=form):
                self.assertEqual(result["status"], "UNSUPPORTED")
                self.assertIn(form, " ".join(result["unsupported_dimensions"]))

    def test_negative_boolean_or_unknown_symbol_payment_is_malformed_contract(self):
        for payment in ({"red": -1}, {"red": True}, {"unmodeled-color": 2}):
            with self.subTest(payment=payment), self.assertRaises(GameplayContractError):
                plan_mana_payment(cost(red=1), {"red": 2}, ["blue", "red"], payment=payment)

    def test_payment_does_not_mutate_cost_or_pool(self):
        body = cost(1, red=1)
        pool = {"red": 2, "blue": 1}
        original_cost, original_pool = deepcopy(body), deepcopy(pool)
        plan_mana_payment(body, pool, ["blue", "red"])
        self.assertEqual(body, original_cost)
        self.assertEqual(pool, original_pool)
