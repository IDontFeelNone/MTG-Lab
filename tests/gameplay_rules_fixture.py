"""Original fictional gameplay proof inputs; no provider or real card content.

The retained fixture is authored structured test semantics, not an Oracle parser,
source-policy clearance, production dataset, or complete real-game rule system.
"""
from copy import deepcopy
import json
from pathlib import Path

from gameplay_rules.models import (
    CardGameplaySemantics, GameAction, GameState, GameplayRulesSnapshot,
)
from gameplay_rules.snapshots import rule_identity

FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "gameplay_rules"
GAME = "fictional-duel"
SOURCE = "fictional-authored-rules-v1"
RULE_CATEGORIES = (
    "priority", "timing", "zones", "land_play", "spell_casting",
    "activated_abilities", "mana_generation", "mana_payment", "stack",
    "resolution", "turn_structure", "state_based_actions",
)
CAPABILITIES = (
    "turn_structure", "active_player", "priority", "stack", "zones",
    "land_play", "spell_casting", "activated_abilities", "mana_generation",
    "mana_payment", "generic_costs", "targeting", "resolution", "zone_changes",
    "state_based_actions", "triggered_abilities", "replacement_effects",
    "prevention_effects", "continuous_effects", "layers", "copy_effects",
    "combat", "damage", "multiplayer", "alternate_costs", "additional_costs",
    "cost_reductions_increases", "format_legality", "deck_construction",
    "commander_specific_rules",
)
SUPPORTED = set(RULE_CATEGORIES) | {"active_player", "generic_costs", "zone_changes"}


def cost(generic=0, **colored):
    return {"kind": "mana", "generic": generic, "colored": colored,
            "known": True, "unsupported": []}


def snapshot_body():
    source = {
        "source_id": SOURCE, "source_class": "project_authored_fictional",
        "issuer": "MTG Lab fictional test authors",
        "title": "Fictional Duel bounded gameplay proof, revision 1",
        "authoritative_reference": "urn:mtglab:fictional-duel:rules:v1",
        "effective_date": "2026-10-16", "retrieved_at": "2026-10-16T00:00:00Z",
        "content_hash": None, "rules_version": "fictional-duel-v1",
        "supersedes": [], "superseded_by": [],
        "provenance": ["Original project-authored fictional fixture"],
        "retention_status": "project_authored_public",
        "permission_status": {key: "NOT_APPLICABLE" for key in (
            "processing", "private_retention", "redistribution", "service_use", "ai_export")},
        "completeness": "partial",
    }
    rules = []
    for category in RULE_CATEGORIES:
        rule = {"rule_id": "fictional.rules." + category + ".1", "source_id": SOURCE,
                "external_reference": None, "category": category,
                "description": "Authored bounded fictional " + category.replace("_", " ") + " primitive.",
                "status": "supported"}
        rule["rule_hash"] = rule_identity(rule)
        rules.append(rule)
    return {
        "game_id": GAME, "rules_version": "fictional-duel-v1",
        "effective_date": "2026-10-16", "engine_contract_version": "gameplay-kernel-v1",
        "execution_profile": "fictional-two-player-v1", "sources": [source],
        "rules": rules,
        "capabilities": {key: "supported" if key in SUPPORTED else "unsupported"
                         for key in CAPABILITIES},
        "unsupported_rule_families": [key for key in CAPABILITIES if key not in SUPPORTED],
        "parameters": {"mana_symbols": ["blue", "red"], "generic_payment_order": ["blue", "red"],
                       "main_phase": "main", "main_step": "action",
                       "turn_steps": [{"phase": "beginning", "step": "start"},
                                      {"phase": "main", "step": "action"},
                                      {"phase": "ending", "step": "end"}],
                       "land_plays_per_turn": 1, "life_loss_threshold": 0},
    }


def semantics_body(snapshot_id, card_id, *, kind="spell", timing="sorcery", mana=None,
                   effects=None, abilities=None):
    return {"game_id": GAME, "rules_snapshot_id": snapshot_id, "card_id": card_id,
            "semantics_version": "fictional-card-semantics-v1", "object_kind": kind,
            "timing": timing, "mana_cost": cost() if mana is None else mana,
            "abilities": [] if abilities is None else abilities,
            "effects": [{"kind": "no_op"}] if effects is None else effects,
            "post_resolution_zone": "battlefield" if kind in {"land", "resource"} else "graveyard",
            "restrictions": [], "required_capabilities": [], "unsupported_text": [],
            "completeness": "complete", "review_status": "fictional_test_only",
            "source_references": [SOURCE]}


def fixture_documents():
    snapshot = GameplayRulesSnapshot.create(snapshot_body())
    semantics = [
        CardGameplaySemantics.create(semantics_body(
            snapshot.identity, "pebble-resource", kind="resource", timing="none",
            abilities=[{"ability_id": "make-red", "tap_cost": True, "mana_cost": cost(),
                        "effect": {"kind": "add_mana", "amount": {"red": 2}}, "uses_stack": False}])),
        CardGameplaySemantics.create(semantics_body(
            snapshot.identity, "ember-scroll", mana=cost(1, red=1),
            effects=[{"kind": "adjust_life", "target": "opponent", "amount": -2}])),
        CardGameplaySemantics.create(semantics_body(
            snapshot.identity, "swift-lantern", timing="instant", mana=cost(blue=1))),
        CardGameplaySemantics.create(semantics_body(
            snapshot.identity, "moss-plot", kind="land", timing="none")),
    ]
    by_card = {row.card_id: row.identity for row in semantics}
    zones = [{"zone_id": owner + ":" + kind, "kind": kind, "owner": owner,
              "visibility": "hidden" if kind in {"hand", "library"} else "public"}
             for owner in ("A", "B") for kind in (
                 "library", "hand", "battlefield", "graveyard", "exile", "command")]
    zones.append({"zone_id": "shared:stack", "kind": "stack", "owner": None, "visibility": "public"})
    objects = [{"object_id": card, "card_id": card, "semantics_id": by_card[card],
                "owner": "A", "controller": "A",
                "zone_id": "A:battlefield" if card == "pebble-resource" else "A:hand",
                "tapped": False, "knowledge": "known"} for card in by_card]
    objects.append({"object_id": "unobserved-library-object", "card_id": None,
                    "semantics_id": None, "owner": "B", "controller": "B",
                    "zone_id": "B:library", "tapped": None, "knowledge": "unknown"})
    state = GameState.create({
        "game_id": GAME, "rules_snapshot_id": snapshot.identity, "revision": 0,
        "players": [{"player_id": who, "life": 10, "mana_pool": {},
                     "land_plays_used": 0, "land_plays_available": 1} for who in ("A", "B")],
        "active_player": "A", "turn_number": 1, "phase": "main", "step": "action",
        "priority_player": "A", "zones": zones, "objects": objects, "stack": [],
        "consecutive_passes": [], "status": "in_progress", "winner_ids": [], "loser_ids": [],
        "pending_system_actions": [], "unknown_fields": [], "active_effects": [],
    })
    return snapshot, semantics, state


def semantic_body(model):
    body = model.to_dict()
    body.pop("schema_version")
    # Remove only this envelope's own ID; rules/source bindings remain inputs.
    body.pop(model.identity_key)
    return body


def changed_state(state, mutate=None, **changes):
    body = semantic_body(state)
    if mutate:
        mutate(body)
    body.update(deepcopy(changes))
    return GameState.create(body)


def action(state, kind, actor="A", object_id=None, ability_id=None, payment=None):
    return GameAction.create({"game_id": state.game_id, "rules_snapshot_id": state.rules_snapshot_id,
                              "expected_state_id": state.identity, "kind": kind, "actor": actor,
                              "object_id": object_id, "ability_id": ability_id, "payment": payment})


def write_fixture(root):
    """Write ONLY project-authored fictional bytes to a caller-selected test root."""
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    snapshot, semantics, state = fixture_documents()
    documents = {"rules-snapshot.json": snapshot.to_dict(), "game-state.json": state.to_dict()}
    for item in semantics:
        documents[item.card_id + ".semantics.json"] = item.to_dict()
    for name, body in documents.items():
        (root / name).write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return snapshot, semantics, state
