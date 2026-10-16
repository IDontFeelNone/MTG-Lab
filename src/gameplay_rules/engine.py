"""Small deterministic interpreter for explicitly selected fictional gameplay.

Only ``fictional-two-player-v1`` is executable.  The rules snapshot supplies
versioned evidence and coverage; this engine supplies the reviewed primitive
meaning.  Neither source prose nor card text is executable input.
"""

from collections.abc import Iterable
from types import MappingProxyType

from .costs import plan_mana_payment
from .errors import GameplayContractError
from .models import (
    CardGameplaySemantics, GameAction, GameState, GameTransition,
    GameplayRulesSnapshot, LegalityResult,
)


_PLAYER_ACTIONS = {"pass_priority", "play_land", "cast_spell", "activate_ability"}
_SYSTEM_ACTIONS = {"resolve_top_of_stack", "perform_state_based_actions", "advance_step_or_phase"}
_CAPABILITIES = {
    "pass_priority": ("priority", "stack"),
    "play_land": ("priority", "active_player", "land_play", "zone_changes", "stack"),
    "cast_spell": ("priority", "active_player", "spell_casting", "mana_payment", "generic_costs", "stack", "zone_changes"),
    "activate_ability": ("priority", "activated_abilities", "mana_generation", "mana_payment", "generic_costs"),
    "resolve_top_of_stack": ("stack", "resolution", "zone_changes", "priority", "active_player"),
    "perform_state_based_actions": ("priority", "active_player"),
    "advance_step_or_phase": ("active_player", "priority", "stack"),
}
# Every primitive inspects the explicit turn window and active objects, and
# either performs or verifies the bounded life-loss checkpoint.  These are
# real dependencies, even when the selected action does not itself move a zone.
_COMMON_CAPABILITIES = ("turn_structure", "zones", "state_based_actions")
_COMMON_RULE_CATEGORIES = ("turn_structure", "zones", "state_based_actions")
_RULE_CATEGORIES = {
    "pass_priority": ("priority", "stack"),
    "play_land": ("priority", "timing", "zones", "land_play"),
    "cast_spell": ("priority", "timing", "zones", "spell_casting", "mana_payment", "stack"),
    "activate_ability": ("priority", "activated_abilities", "mana_generation", "mana_payment"),
    "resolve_top_of_stack": ("stack", "resolution", "zones"),
    "perform_state_based_actions": ("state_based_actions",),
    "advance_step_or_phase": ("turn_structure",),
}
_IMPLEMENTED_CAPABILITIES = frozenset({
    "turn_structure", "active_player", "priority", "stack", "zones", "land_play",
    "spell_casting", "activated_abilities", "mana_generation", "mana_payment",
    "generic_costs", "resolution", "zone_changes", "state_based_actions",
})


class GameplayRulesEngine:
    """Read-only evaluator with immutable next-state/transition construction.

    There are no repository roots, ambient snapshots, network lookups, strategy
    policies or parser hooks.  Unknown action-relevant semantics block answers.
    """

    def __init__(self, snapshot, semantics):
        if not isinstance(snapshot, GameplayRulesSnapshot):
            raise GameplayContractError("invalid_snapshot", "an explicit verified rules snapshot is required")
        snapshot.verify()
        body = snapshot.to_dict()
        if body["engine_contract_version"] != "gameplay-kernel-v1" or body["execution_profile"] != "fictional-two-player-v1":
            raise GameplayContractError("incompatible_rules", "the fictional kernel contract is required")
        if any(source["source_class"] != "project_authored_fictional" for source in body["sources"]):
            raise GameplayContractError("nonfictional_execution", "only project-authored fictional sources may execute")
        if any(status == "supported" and capability not in _IMPLEMENTED_CAPABILITIES for capability, status in body["capabilities"].items()):
            raise GameplayContractError("unsupported_coverage_claim", "the fictional kernel cannot claim an unimplemented capability")
        self._snapshot = snapshot
        self._snapshot_identity = snapshot.identity
        self._definitions = {}
        if not isinstance(semantics, Iterable):
            raise GameplayContractError("invalid_semantics", "an explicit iterable of verified structured semantics is required")
        for definition in semantics:
            if not isinstance(definition, CardGameplaySemantics):
                raise GameplayContractError("invalid_semantics", "verified structured card semantics are required")
            definition.verify()
            data = definition.to_dict()
            if data["game_id"] != body["game_id"] or data["rules_snapshot_id"] != snapshot.identity:
                raise GameplayContractError("semantics_snapshot_mismatch", "card semantics must bind the selected game and rules snapshot")
            if not data["source_references"] or not set(data["source_references"]) <= {source["source_id"] for source in body["sources"]}:
                raise GameplayContractError("unbound_semantics_source", "structured semantics must reference selected source identities")
            if definition.identity in self._definitions:
                raise GameplayContractError("duplicate_semantics", "semantics identities must be unique")
            self._definitions[definition.identity] = definition
        self._definition_bindings = tuple(self._definitions.items())
        self._definitions = MappingProxyType(self._definitions)

    @property
    def snapshot(self):
        return self._snapshot

    def _inputs(self, state, action):
        if not isinstance(state, GameState) or not isinstance(action, GameAction):
            raise GameplayContractError("invalid_request", "verified game state and action contracts are required")
        self._snapshot.verify()
        if self._snapshot.identity != self._snapshot_identity:
            raise GameplayContractError("rules_retargeted", "the evaluator rules snapshot cannot be retargeted")
        state.verify()
        action.verify()
        rules = self._snapshot.to_dict()
        before, request = state.to_dict(), action.to_dict()
        for value in (before, request):
            if value["game_id"] != rules["game_id"]:
                raise GameplayContractError("wrong_game", "state and action must belong to the selected game")
            if value["rules_snapshot_id"] != self._snapshot.identity:
                raise GameplayContractError("rules_snapshot_mismatch", "state and action must bind the selected rules snapshot")
        if request["expected_state_id"] != state.identity:
            raise GameplayContractError("stale_state", "action must bind the exact before-state identity")
        if len(self._definitions) != len(self._definition_bindings):
            raise GameplayContractError("semantics_retargeted", "the evaluator semantics inventory cannot be retargeted")
        for identity, definition in self._definition_bindings:
            if self._definitions.get(identity) is not definition or definition.identity != identity:
                raise GameplayContractError("semantics_retargeted", "the evaluator semantics inventory cannot be retargeted")
            definition.verify()
            value = definition.to_dict()
            if value["game_id"] != rules["game_id"] or value["rules_snapshot_id"] != self._snapshot.identity:
                raise GameplayContractError("semantics_snapshot_mismatch", "structured semantics must remain bound to selected rules")
        return rules, before, request

    def _references(self, rules, kind):
        categories = _COMMON_RULE_CATEGORIES + _RULE_CATEGORIES[kind] if kind in _RULE_CATEGORIES else ()
        result = []
        for rule in rules["rules"]:
            if rule["category"] in categories:
                result.append({key: rule[key] for key in (
                    "rule_id", "external_reference", "source_id", "category", "description", "status"
                )} | {"rules_snapshot_id": self._snapshot.identity})
        return sorted(result, key=lambda item: item["rule_id"])

    @staticmethod
    def _zone(state, kind, owner=None):
        zones = [zone for zone in state["zones"] if zone["kind"] == kind and (zone["owner"] == owner or zone["owner"] is None)]
        return zones[0]["zone_id"] if len(zones) == 1 else None

    def _definition(self, obj):
        value = self._definitions.get(obj["semantics_id"])
        if value is None:
            return None
        result = value.to_dict()
        if result["card_id"] != obj["card_id"]:
            raise GameplayContractError("card_semantics_mismatch", "object identity must match its structured semantics")
        return result

    def evaluate_action(self, state, action):
        """Check a request without mutating or applying it."""
        rules, before, request = self._inputs(state, action)
        kind = request["kind"]
        satisfied, failed, unknown, unsupported = [], [], [], []
        required_costs, payment = [], None

        def result():
            # Unknown/unsupported interactions can invalidate apparent base-rule
            # failures, so they take precedence over confident legal/illegal.
            status = "UNSUPPORTED" if unsupported else "INDETERMINATE" if unknown else "ILLEGAL" if failed else "LEGAL"
            return LegalityResult.create({
                "game_id": before["game_id"], "action_id": action.identity,
                "before_state_id": state.identity, "rules_snapshot_id": self._snapshot.identity,
                "status": status,
                "satisfied_requirements": sorted(set(satisfied)),
                "failed_requirements": sorted(set(failed)),
                "unknown_requirements": sorted(set(unknown)),
                "rule_references": self._references(rules, kind),
                "required_costs": required_costs, "payment": payment,
                "assumptions": ["project_authored_fictional_two_player_rules_only"],
                "unsupported_dimensions": sorted(set(unsupported)),
                "explanation": {"action_kind": kind, "status": status, "reason_codes": sorted(set(failed + unknown + unsupported))},
            })

        if kind not in _PLAYER_ACTIONS | _SYSTEM_ACTIONS:
            unsupported.append("action_kind:" + kind)
            return result()
        if before["status"] != "in_progress":
            failed.append("game_not_in_progress")
        if kind != "perform_state_based_actions":
            if any(player["life"] is None for player in before["players"]):
                unknown.append("state_based_action_life_unknown")
            elif any(player["life"] <= rules["parameters"]["life_loss_threshold"] for player in before["players"]):
                failed.append("state_based_action_required")
        if before["unknown_fields"]:
            unknown.extend("state_field:" + field for field in before["unknown_fields"])
        if {"phase": before["phase"], "step": before["step"]} not in rules["parameters"]["turn_steps"]:
            unsupported.append("turn_window_not_defined")
        for capability in _COMMON_CAPABILITIES + _CAPABILITIES[kind]:
            coverage = rules["capabilities"].get(capability, "unsupported")
            if coverage == "unknown":
                unknown.append("capability:" + capability)
            elif coverage != "supported":
                unsupported.append("capability:" + capability)
        for rule in rules["rules"]:
            if rule["category"] in _COMMON_RULE_CATEGORIES + _RULE_CATEGORIES[kind] and rule["status"] != "supported":
                (unknown if rule["status"] == "unknown" else unsupported).append("rule_coverage:" + rule["rule_id"])
        for effect in before["active_effects"]:
            if kind in effect["affected_actions"] or "*" in effect["affected_actions"]:
                destination = unknown if effect["knowledge"] == "unknown" else unsupported
                destination.append("active_effect:" + effect["effect_id"])

        objects = {obj["object_id"]: obj for obj in before["objects"]}
        zones = {zone["zone_id"]: zone for zone in before["zones"]}
        # This is the future override seam: unmodeled active objects/effects
        # refuse a base-rule ruling rather than being silently ignored.
        for obj in before["objects"]:
            if zones[obj["zone_id"]]["kind"] in {"battlefield", "stack"}:
                if obj["knowledge"] != "known":
                    unknown.append("active_object_unknown:" + obj["object_id"])
                definition = self._definition(obj)
                if definition is None:
                    unknown.append("active_object_semantics:" + obj["object_id"])
                else:
                    self._semantics_coverage(definition, rules, unknown, unsupported)

        players = {player["player_id"]: player for player in before["players"]}
        actor = request["actor"]
        if kind in _PLAYER_ACTIONS:
            if actor not in players:
                failed.append("actor_not_a_player")
            elif actor != before["priority_player"]:
                failed.append("actor_lacks_priority")
            else:
                satisfied.append("actor_has_priority")
            if before["pending_system_actions"]:
                failed.append("required_system_action_pending")
        else:
            if actor is not None:
                failed.append("system_action_requires_no_actor")
            if not before["pending_system_actions"] or before["pending_system_actions"][0] != kind:
                failed.append("system_action_not_due")
            else:
                satisfied.append("system_boundary_matches")
        if kind in {"pass_priority", "perform_state_based_actions", "advance_step_or_phase"}:
            if request["object_id"] is not None or request["ability_id"] is not None or request["payment"] is not None:
                raise GameplayContractError("unexpected_action_fields", "this action does not accept object, ability or payment fields")
            if kind == "perform_state_based_actions" and any(player["life"] is None for player in before["players"]):
                unknown.append("player_life_unknown")
            if kind == "advance_step_or_phase" and before["stack"]:
                failed.append("step_advance_requires_empty_stack")
            return result()

        if kind == "resolve_top_of_stack":
            if request["object_id"] is not None or request["ability_id"] is not None or request["payment"] is not None:
                raise GameplayContractError("unexpected_action_fields", "system resolution selects only the exact stack top")
            if not before["stack"]:
                failed.append("stack_empty")
                return result()
            obj = objects[before["stack"][-1]]
        else:
            obj = objects.get(request["object_id"])
            if obj is None:
                failed.append("object_not_in_state")
                return result()
        if obj["knowledge"] != "known":
            unknown.append("object_identity_unknown")
        definition = self._definition(obj)
        if definition is None:
            unknown.append("object_semantics_unavailable")
            return result()
        self._semantics_coverage(definition, rules, unknown, unsupported)
        if obj["controller"] != actor and kind in _PLAYER_ACTIONS:
            failed.append("actor_does_not_control_object")
        if kind in {"play_land", "cast_spell"}:
            if request["ability_id"] is not None:
                raise GameplayContractError("unexpected_action_fields", "land and spell actions do not select an ability")
            object_zone = zones[obj["zone_id"]]
            if object_zone["kind"] != "hand" or obj["owner"] != actor or (object_zone["owner"] is not None and object_zone["owner"] != actor):
                failed.append("object_not_in_actor_hand")
            if object_zone["kind"] == "hand" and object_zone["owner"] is None:
                unsupported.append("shared_hand_semantics")
            expected_kind = "land" if kind == "play_land" else "spell"
            if definition["object_kind"] != expected_kind:
                failed.append("wrong_object_kind")
            timing = "sorcery" if kind == "play_land" else definition["timing"]
            if timing == "sorcery":
                if actor != before["active_player"]:
                    failed.append("not_active_player")
                if before["phase"] != rules["parameters"]["main_phase"] or before["step"] != rules["parameters"]["main_step"]:
                    failed.append("not_main_action_window")
                if before["stack"]:
                    failed.append("sorcery_requires_empty_stack")
            elif timing != "instant":
                unsupported.append("timing_class:" + timing)
            if kind == "play_land":
                if request["payment"] is not None:
                    raise GameplayContractError("unexpected_action_fields", "fictional land play has no payment")
                if actor in players and players[actor]["land_plays_used"] >= players[actor]["land_plays_available"]:
                    failed.append("land_play_allowance_exhausted")
                if actor in players and players[actor]["land_plays_available"] != rules["parameters"]["land_plays_per_turn"]:
                    unsupported.append("unmodeled_land_play_allowance")
                if definition["mana_cost"]["generic"] or any(definition["mana_cost"]["colored"].values()) or not definition["mana_cost"]["known"] or definition["mana_cost"]["kind"] != "mana" or definition["mana_cost"]["unsupported"]:
                    unsupported.append("land_play_cost")
                if any(effect["kind"] != "no_op" for effect in definition["effects"]):
                    unsupported.append("land_entry_effects")
                if self._zone(before, "battlefield", actor) is None:
                    unknown.append("battlefield_zone_unavailable")
            elif self._zone(before, "stack") is None:
                unknown.append("stack_zone_unavailable")

        ability = None
        if kind == "activate_ability":
            if zones[obj["zone_id"]]["kind"] != "battlefield":
                failed.append("ability_object_not_on_battlefield")
            abilities = [value for value in definition["abilities"] if value["ability_id"] == request["ability_id"]]
            if len(abilities) != 1:
                failed.append("ability_not_defined")
            else:
                ability = abilities[0]
                if ability["uses_stack"]:
                    unsupported.append("stack_using_activated_ability")
                if ability["tap_cost"]:
                    if obj["tapped"] is None:
                        unknown.append("tap_state_unknown")
                    elif obj["tapped"]:
                        failed.append("tap_cost_object_already_tapped")
                effect = ability["effect"]
                if effect["kind"] != "add_mana":
                    unsupported.append("ability_effect:" + effect["kind"])
                elif set(effect["amount"]) - set(rules["parameters"]["mana_symbols"]):
                    unsupported.append("unsupported_generated_mana_symbol")

        if kind in {"cast_spell", "activate_ability"} and (kind == "cast_spell" or ability is not None):
            cost = definition["mana_cost"] if kind == "cast_spell" else ability["mana_cost"]
            required_costs.append(cost)
            if actor in players:
                planned = plan_mana_payment(cost, players[actor]["mana_pool"], rules["parameters"]["generic_payment_order"], request["payment"])
                payment = planned.to_dict()
                failed.extend(payment["failed_requirements"])
                unknown.extend(payment["unknown_requirements"])
                unsupported.extend(payment["unsupported_dimensions"])
                if payment["status"] == "LEGAL":
                    satisfied.append("exact_mana_payment_available")
        if kind == "resolve_top_of_stack":
            if definition["object_kind"] != "spell":
                unsupported.append("resolution_object_kind")
            destination_owner = obj["owner"] if definition["post_resolution_zone"] == "graveyard" else obj["controller"]
            if self._zone(before, definition["post_resolution_zone"], destination_owner) is None:
                unknown.append("resolution_destination_unavailable")
            for effect in definition["effects"]:
                if effect["kind"] not in {"adjust_life", "no_op"}:
                    unsupported.append("resolution_effect:" + effect["kind"])
                elif effect["kind"] == "adjust_life":
                    target = obj["controller"] if effect["target"] == "controller" else next(player for player in players if player != obj["controller"])
                    if players[target]["life"] is None:
                        unknown.append("effect_target_life_unknown")
        return result()

    @staticmethod
    def _semantics_coverage(definition, rules, unknown, unsupported):
        if definition["completeness"] != "complete":
            (unknown if definition["completeness"] == "unknown" else unsupported).append("incomplete_card_semantics:" + definition["card_id"])
        unsupported.extend("unsupported_card_text:" + value for value in definition["unsupported_text"])
        if definition["restrictions"]:
            unsupported.append("structured_restrictions_not_implemented")
        for capability in definition["required_capabilities"]:
            status = rules["capabilities"].get(capability, "unsupported")
            if status == "unknown":
                unknown.append("card_capability:" + capability)
            elif status != "supported" or capability not in _IMPLEMENTED_CAPABILITIES:
                unsupported.append("card_capability:" + capability)
        for effect in definition["effects"]:
            if effect["kind"] not in {"adjust_life", "no_op"}:
                unsupported.append("card_effect:" + effect["kind"])
        for ability in definition["abilities"]:
            if ability["uses_stack"] or ability["effect"]["kind"] != "add_mana":
                unsupported.append("unmodeled_ability:" + ability["ability_id"])

    def apply_action(self, state, action):
        """Apply only a LEGAL request, returning a new immutable state envelope."""
        legality = self.evaluate_action(state, action)
        checked = legality.to_dict()
        if checked["status"] != "LEGAL":
            return legality
        rules, before, request = self._inputs(state, action)
        after = state.to_dict()
        after.pop("schema_version", None)
        after.pop("state_id", None)
        after["revision"] += 1
        kind, actor = request["kind"], request["actor"]
        players = {player["player_id"]: player for player in after["players"]}
        objects = {obj["object_id"]: obj for obj in after["objects"]}
        zone_changes, resource_changes = [], []

        def move(obj, destination):
            zone_changes.append({"object_id": obj["object_id"], "from_zone": obj["zone_id"], "to_zone": destination})
            obj["zone_id"] = destination

        if kind in _PLAYER_ACTIONS - {"pass_priority"}:
            after["consecutive_passes"] = []
        if checked["payment"] is not None:
            players[actor]["mana_pool"] = checked["payment"]["pool_after"]
        if kind == "pass_priority":
            after["consecutive_passes"].append(actor)
            if len(after["consecutive_passes"]) == 2:
                after["consecutive_passes"] = []
                after["priority_player"] = None
                after["pending_system_actions"] = ["perform_state_based_actions", "resolve_top_of_stack" if after["stack"] else "advance_step_or_phase"]
            else:
                after["priority_player"] = next(player for player in players if player != actor)
        elif kind == "play_land":
            obj = objects[request["object_id"]]
            move(obj, self._zone(after, "battlefield", actor))
            players[actor]["land_plays_used"] += 1
        elif kind == "cast_spell":
            obj = objects[request["object_id"]]
            move(obj, self._zone(after, "stack"))
            after["stack"].append(obj["object_id"])
        elif kind == "activate_ability":
            obj = objects[request["object_id"]]
            definition = self._definition(obj)
            ability = next(value for value in definition["abilities"] if value["ability_id"] == request["ability_id"])
            if ability["tap_cost"]:
                obj["tapped"] = True
            for symbol, amount in ability["effect"]["amount"].items():
                players[actor]["mana_pool"][symbol] = players[actor]["mana_pool"].get(symbol, 0) + amount
        else:
            after["pending_system_actions"].pop(0)
            if kind == "resolve_top_of_stack":
                obj = objects[after["stack"].pop()]
                definition = self._definition(obj)
                for effect in definition["effects"]:
                    if effect["kind"] == "adjust_life":
                        target = obj["controller"] if effect["target"] == "controller" else next(player for player in players if player != obj["controller"])
                        players[target]["life"] += effect["amount"]
                owner = obj["owner"] if definition["post_resolution_zone"] == "graveyard" else obj["controller"]
                move(obj, self._zone(after, definition["post_resolution_zone"], owner))
                after["pending_system_actions"] = ["perform_state_based_actions"]
            elif kind == "perform_state_based_actions":
                losers = [player for player in players if players[player]["life"] <= rules["parameters"]["life_loss_threshold"]]
                if losers:
                    after["status"] = "ended"
                    after["loser_ids"] = sorted(losers)
                    after["winner_ids"] = sorted(set(players) - set(losers))
                    after["pending_system_actions"] = []
                    after["priority_player"] = None
            elif kind == "advance_step_or_phase":
                sequence = rules["parameters"]["turn_steps"]
                index = sequence.index({"phase": after["phase"], "step": after["step"]})
                new_index = (index + 1) % len(sequence)
                after["phase"], after["step"] = sequence[new_index]["phase"], sequence[new_index]["step"]
                for player in players.values():
                    player["mana_pool"] = {}
                if new_index == 0:
                    after["turn_number"] += 1
                    after["active_player"] = next(player for player in players if player != after["active_player"])
                    for player in players.values():
                        player["land_plays_used"] = 0
                        player["land_plays_available"] = rules["parameters"]["land_plays_per_turn"]
            if after["status"] == "in_progress" and not after["pending_system_actions"]:
                after["priority_player"] = after["active_player"]

        for player in after["players"]:
            original = next(item for item in before["players"] if item["player_id"] == player["player_id"])
            for field in ("life", "mana_pool", "land_plays_used", "land_plays_available"):
                if original[field] != player[field]:
                    resource_changes.append({"player_id": player["player_id"], "resource": field, "before": original[field], "after": player[field]})
        next_state = GameState.create(after)
        state_changes = [{"path": key, "before": before[key], "after": after[key]} for key in sorted(after) if before[key] != after[key]]
        return GameTransition.create({
            "game_id": before["game_id"], "rules_snapshot_id": self._snapshot.identity,
            "action_id": action.identity, "before_state_id": state.identity, "after_state_id": next_state.identity,
            "actor": actor, "action": request, "after_state": next_state.to_dict(),
            "state_changes": state_changes, "zone_changes": zone_changes,
            "resource_changes": resource_changes,
            "stack_changes": [] if before["stack"] == after["stack"] else [{"before": before["stack"], "after": after["stack"]}],
            "rule_references": checked["rule_references"],
            "required_system_actions": after["pending_system_actions"],
        })

    def replay_transition(self, state, transition):
        """Re-execute the bound action and require the entire transition to match."""
        if not isinstance(state, GameState) or not isinstance(transition, GameTransition):
            raise GameplayContractError("invalid_transition", "a verified transition envelope is required")
        state.verify()
        transition.verify()
        body = transition.to_dict()
        if body["before_state_id"] != state.identity:
            raise GameplayContractError("replay_state_mismatch", "transition must bind the exact replay before-state")
        action = GameAction.from_dict(body["action"])
        repeated = self.apply_action(state, action)
        if not isinstance(repeated, GameTransition) or repeated.to_dict() != body:
            raise GameplayContractError("replay_mismatch", "transition does not reproduce exactly under the selected rules")
        return repeated
