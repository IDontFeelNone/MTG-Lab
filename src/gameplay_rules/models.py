"""Strict immutable, domain-separated gameplay contracts.

These envelopes are structured inputs, not scripts or natural-language parsers.
Hash verification proves input identity, never source permission or approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import hashlib
import json
import math
import re
from types import MappingProxyType
from typing import Any, ClassVar, Mapping

from .capabilities import (CAPABILITIES, CAPABILITY_STATUSES, ENGINE_CONTRACT_VERSION,
                           EXECUTION_PROFILE, KERNEL_SUPPORTED_CAPABILITIES,
                           REQUIRED_RULE_CATEGORIES, SOURCE_CLASSES,
                           ZONE_KINDS)
from .errors import GameplayContractError

_HASH = re.compile(r"sha256:[0-9a-f]{64}\Z")
_STATUSES = {"LEGAL", "ILLEGAL", "INDETERMINATE", "UNSUPPORTED"}


def _fail(field: str, message: str = "invalid contract value"):
    raise GameplayContractError("invalid_contract", f"{field}: {message}")


def _json(value: Any) -> Any:
    if isinstance(value, Mapping):
        if any(not isinstance(k, str) for k in value): _fail("JSON", "keys must be strings")
        return {k: _json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [_json(v) for v in value]
    if value is None or isinstance(value, (str, bool, int)): return value
    if isinstance(value, float) and math.isfinite(value): return value
    _fail("JSON", "unsupported or non-finite value")


def _freeze(value):
    if isinstance(value, dict): return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list): return tuple(_freeze(v) for v in value)
    return value


def canonical_json(value: Any) -> bytes:
    return json.dumps(_json(value), ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def content_identity(domain: str, value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json({"domain": domain, "content": value})).hexdigest()


def rule_identity(rule: Mapping) -> str:
    return content_identity("gameplay-rule-definition-v1", {k: v for k, v in rule.items() if k != "rule_hash"})


def _keys(value, keys, field):
    if not isinstance(value, dict) or set(value) != set(keys): _fail(field, "missing or unexpected fields")


def _text(value, field, *, nullable=False):
    if nullable and value is None: return
    if not isinstance(value, str) or not value.strip(): _fail(field, "nonempty string required")


def _version(value, field):
    _text(value, field)
    if value.strip().lower() in {"current", "latest"}: _fail(field, "explicit retained version required")


def _identity(value, field, *, nullable=False):
    if nullable and value is None: return
    if not isinstance(value, str) or not _HASH.fullmatch(value): _fail(field, "content identity required")


def _int(value, field, *, minimum=None):
    if type(value) is not int or (minimum is not None and value < minimum): _fail(field, "integer outside contract")


def _choice(value, values, field):
    if not isinstance(value, str) or value not in values: _fail(field, "unsupported value")


def _strings(value, field, *, unique=True):
    if not isinstance(value, list): _fail(field, "array required")
    for item in value: _text(item, field)
    if unique and len(value) != len(set(value)): _fail(field, "duplicate entries")


def _date(value, field):
    try:
        if not isinstance(value, str) or date.fromisoformat(value).isoformat() != value: _fail(field)
    except ValueError: _fail(field, "ISO date required")


def _pool(value, field):
    if not isinstance(value, dict): _fail(field, "mana map required")
    for key, amount in value.items():
        _text(key, field)
        _int(amount, field, minimum=0)


def validate_cost(value, field="mana_cost"):
    _keys(value, {"kind", "generic", "colored", "known", "unsupported"}, field)
    _text(value["kind"], field)
    _int(value["generic"], field, minimum=0)
    _pool(value["colored"], field)
    if type(value["known"]) is not bool: _fail(field, "known must be boolean")
    _strings(value["unsupported"], field)


def _source(value):
    fields = {"source_id", "source_class", "issuer", "title", "authoritative_reference",
              "effective_date", "retrieved_at", "content_hash", "rules_version", "supersedes",
              "superseded_by", "provenance", "retention_status", "permission_status", "completeness"}
    _keys(value, fields, "source")
    for key in ("source_id", "issuer", "title", "authoritative_reference"):
        _text(value[key], "source." + key)
    _version(value["rules_version"], "source.rules_version")
    _choice(value["source_class"], SOURCE_CLASSES, "source.source_class")
    _date(value["effective_date"], "source.effective_date")
    try:
        observed = datetime.fromisoformat(value["retrieved_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None: _fail("source.retrieved_at", "timezone required")
    except (ValueError, TypeError, AttributeError): _fail("source.retrieved_at", "ISO timestamp required")
    _identity(value["content_hash"], "source.content_hash", nullable=True)
    for key in ("supersedes", "superseded_by", "provenance"): _strings(value[key], "source." + key)
    _choice(value["retention_status"], {"project_authored_public", "reference_only", "private_only", "not_established"}, "source.retention_status")
    permissions = {"processing", "private_retention", "redistribution", "service_use", "ai_export"}
    _keys(value["permission_status"], permissions, "source.permission_status")
    for status in value["permission_status"].values():
        _choice(status, {"ESTABLISHED", "NOT_ESTABLISHED", "NOT_APPLICABLE"}, "source.permission_status")
    _choice(value["completeness"], {"complete", "partial", "unknown"}, "source.completeness")


def _snapshot(body):
    _keys(body, {"game_id", "rules_version", "effective_date", "engine_contract_version", "execution_profile",
                 "sources", "rules", "capabilities", "unsupported_rule_families", "parameters"}, "rules_snapshot")
    _text(body["game_id"], "game_id")
    _version(body["rules_version"], "rules_version")
    _date(body["effective_date"], "effective_date")
    _choice(body["engine_contract_version"], {ENGINE_CONTRACT_VERSION}, "engine_contract_version")
    _choice(body["execution_profile"], {EXECUTION_PROFILE}, "execution_profile")
    if not isinstance(body["sources"], list) or not body["sources"]: _fail("sources", "nonempty array required")
    for source in body["sources"]: _source(source)
    source_ids = [s["source_id"] for s in body["sources"]]
    if len(source_ids) != len(set(source_ids)): _fail("sources", "duplicate source identity")
    if any(s["source_class"] != "project_authored_fictional" for s in body["sources"]):
        raise GameplayContractError("unsupported_execution_profile", "Only project-authored fictional sources may execute")
    _keys(body["capabilities"], CAPABILITIES, "capabilities")
    for status in body["capabilities"].values(): _choice(status, CAPABILITY_STATUSES, "capabilities")
    if any(status in {"supported", "partial"} and name not in KERNEL_SUPPORTED_CAPABILITIES
           for name, status in body["capabilities"].items()):
        _fail("capabilities", "fictional kernel cannot claim an unimplemented capability")
    _strings(body["unsupported_rule_families"], "unsupported_rule_families")
    if set(body["unsupported_rule_families"]) != {name for name, status in body["capabilities"].items() if status == "unsupported"}:
        _fail("unsupported_rule_families", "capability manifest mismatch")
    if not isinstance(body["rules"], list) or not body["rules"]: _fail("rules", "nonempty array required")
    rule_ids = []
    categories = set()
    for rule in body["rules"]:
        _keys(rule, {"rule_id", "rule_hash", "source_id", "external_reference", "category", "description", "status"}, "rule")
        for key in ("rule_id", "source_id", "category", "description"): _text(rule[key], "rule." + key)
        _text(rule["external_reference"], "rule.external_reference", nullable=True)
        _choice(rule["status"], CAPABILITY_STATUSES, "rule.status")
        if rule["source_id"] not in source_ids: _fail("rule.source_id", "unbound source")
        _identity(rule["rule_hash"], "rule.rule_hash")
        if rule["rule_hash"] != rule_identity(rule): raise GameplayContractError("rule_integrity", "Rule definition hash mismatch")
        rule_ids.append(rule["rule_id"])
        categories.add(rule["category"])
    if len(set(rule_ids)) != len(rule_ids): _fail("rules", "duplicate rule identity")
    if not REQUIRED_RULE_CATEGORIES <= categories: _fail("rules", "missing primitive rule category")
    parameters = body["parameters"]
    _keys(parameters, {"mana_symbols", "generic_payment_order", "main_phase", "main_step", "turn_steps", "land_plays_per_turn", "life_loss_threshold"}, "parameters")
    for key in ("mana_symbols", "generic_payment_order"): _strings(parameters[key], "parameters." + key)
    if not parameters["mana_symbols"] or set(parameters["mana_symbols"]) != set(parameters["generic_payment_order"]): _fail("parameters", "payment order must cover exact mana symbols")
    _text(parameters["main_phase"], "main_phase")
    _text(parameters["main_step"], "main_step")
    if not isinstance(parameters["turn_steps"], list) or not parameters["turn_steps"]: _fail("turn_steps")
    seen = []
    for turn in parameters["turn_steps"]:
        _keys(turn, {"phase", "step"}, "turn_steps")
        for key in turn: _text(turn[key], "turn_steps")
        seen.append((turn["phase"], turn["step"]))
    if len(set(seen)) != len(seen) or (parameters["main_phase"], parameters["main_step"]) not in seen: _fail("turn_steps", "duplicate or missing main window")
    _int(parameters["land_plays_per_turn"], "land_plays_per_turn", minimum=0)
    _int(parameters["life_loss_threshold"], "life_loss_threshold")


def _semantics(body):
    _keys(body, {"game_id", "rules_snapshot_id", "card_id", "semantics_version", "object_kind", "timing", "mana_cost", "abilities", "effects", "post_resolution_zone", "restrictions", "required_capabilities", "unsupported_text", "completeness", "review_status", "source_references"}, "card_semantics")
    for key in ("game_id", "card_id"): _text(body[key], key)
    _version(body["semantics_version"], "semantics_version")
    _identity(body["rules_snapshot_id"], "rules_snapshot_id")
    _choice(body["object_kind"], {"land", "spell", "resource"}, "object_kind")
    _choice(body["timing"], {"sorcery", "instant", "none"}, "timing")
    validate_cost(body["mana_cost"])
    _choice(body["post_resolution_zone"], {"graveyard", "battlefield"}, "post_resolution_zone")
    for key in ("restrictions", "required_capabilities", "unsupported_text", "source_references"): _strings(body[key], key)
    _choice(body["completeness"], {"complete", "partial", "unknown"}, "completeness")
    _choice(body["review_status"], {"fictional_test_only"}, "review_status")
    if not isinstance(body["abilities"], list) or not isinstance(body["effects"], list): _fail("semantics", "ability/effect arrays required")
    ability_ids = []
    for ability in body["abilities"]:
        _keys(ability, {"ability_id", "tap_cost", "mana_cost", "effect", "uses_stack"}, "ability")
        _text(ability["ability_id"], "ability_id")
        if type(ability["tap_cost"]) is not bool or type(ability["uses_stack"]) is not bool: _fail("ability", "boolean required")
        validate_cost(ability["mana_cost"])
        _effect(ability["effect"])
        ability_ids.append(ability["ability_id"])
    if len(set(ability_ids)) != len(ability_ids): _fail("abilities", "duplicate ability identity")
    for effect in body["effects"]: _effect(effect)


def _effect(effect):
    if not isinstance(effect, dict) or not isinstance(effect.get("kind"), str): _fail("effect")
    kind = effect["kind"]
    if kind == "add_mana":
        _keys(effect, {"kind", "amount"}, "effect")
        _pool(effect["amount"], "effect.amount")
    elif kind == "adjust_life":
        _keys(effect, {"kind", "target", "amount"}, "effect")
        _choice(effect["target"], {"controller", "opponent"}, "effect.target")
        _int(effect["amount"], "effect.amount")
    else:
        # Unknown structured effect kinds are valid but cannot acquire executable semantics.
        _keys(effect, {"kind"}, "effect")
        _text(kind, "effect.kind")


def _state(body):
    _keys(body, {"game_id", "rules_snapshot_id", "revision", "players", "active_player", "turn_number", "phase", "step", "priority_player", "zones", "objects", "stack", "consecutive_passes", "status", "winner_ids", "loser_ids", "pending_system_actions", "unknown_fields", "active_effects"}, "game_state")
    _text(body["game_id"], "game_id")
    _identity(body["rules_snapshot_id"], "rules_snapshot_id")
    _int(body["revision"], "revision", minimum=0)
    _int(body["turn_number"], "turn_number", minimum=1)
    for key in ("phase", "step"): _text(body[key], key)
    if not isinstance(body["players"], list) or len(body["players"]) != 2: _fail("players", "exactly two required by fictional profile")
    player_ids = []
    for player in body["players"]:
        _keys(player, {"player_id", "life", "mana_pool", "land_plays_used", "land_plays_available"}, "player")
        _text(player["player_id"], "player_id")
        if player["life"] is not None: _int(player["life"], "life")
        _pool(player["mana_pool"], "mana_pool")
        for key in ("land_plays_used", "land_plays_available"): _int(player[key], key, minimum=0)
        player_ids.append(player["player_id"])
    if len(set(player_ids)) != 2: _fail("players", "duplicate player")
    if body["active_player"] not in player_ids or (body["priority_player"] is not None and body["priority_player"] not in player_ids): _fail("priority", "unbound player")
    zone_ids = []
    zone_scopes = []
    zones = {}
    if not isinstance(body["zones"], list): _fail("zones")
    for zone in body["zones"]:
        _keys(zone, {"zone_id", "kind", "owner", "visibility"}, "zone")
        _text(zone["zone_id"], "zone_id")
        _choice(zone["kind"], ZONE_KINDS, "zone.kind")
        _choice(zone["visibility"], {"public", "hidden"}, "zone.visibility")
        if zone["owner"] is not None and zone["owner"] not in player_ids: _fail("zone.owner", "unbound player")
        zone_ids.append(zone["zone_id"])
        zone_scopes.append((zone["kind"], zone["owner"]))
        zones[zone["zone_id"]] = zone
    if len(set(zone_ids)) != len(zone_ids): _fail("zones", "duplicate zone")
    if len(set(zone_scopes)) != len(zone_scopes): _fail("zones", "ambiguous zone scope")
    object_ids = []
    stack_objects = set()
    if not isinstance(body["objects"], list): _fail("objects")
    for obj in body["objects"]:
        _keys(obj, {"object_id", "card_id", "semantics_id", "owner", "controller", "zone_id", "tapped", "knowledge"}, "object")
        _text(obj["object_id"], "object_id")
        _text(obj["card_id"], "card_id", nullable=True)
        _text(obj["zone_id"], "zone_id")
        _identity(obj["semantics_id"], "semantics_id", nullable=True)
        _choice(obj["knowledge"], {"known", "unknown"}, "object.knowledge")
        if obj["owner"] not in player_ids or obj["controller"] not in player_ids or obj["zone_id"] not in zones: _fail("object", "unbound player or zone")
        if obj["tapped"] is not None and type(obj["tapped"]) is not bool: _fail("object.tapped")
        if obj["knowledge"] == "known" and (obj["card_id"] is None or obj["semantics_id"] is None): _fail("object", "known object lacks semantic identity")
        if zones[obj["zone_id"]]["kind"] == "stack": stack_objects.add(obj["object_id"])
        object_ids.append(obj["object_id"])
    if len(set(object_ids)) != len(object_ids): _fail("objects", "duplicate object")
    for key in ("stack", "consecutive_passes", "winner_ids", "loser_ids", "pending_system_actions", "unknown_fields"): _strings(body[key], key)
    if set(body["stack"]) != stack_objects: _fail("stack", "zone membership mismatch")
    for key in ("consecutive_passes", "winner_ids", "loser_ids"):
        if not set(body[key]) <= set(player_ids): _fail(key, "unbound player")
    if len(body["consecutive_passes"]) > 1:
        _fail("consecutive_passes", "completed passes must become a system-action boundary")
    if body["consecutive_passes"] and (body["priority_player"] is None or body["priority_player"] == body["consecutive_passes"][0]):
        _fail("consecutive_passes", "an incomplete pass sequence must grant priority to the other player")
    if body["pending_system_actions"] and body["priority_player"] is not None:
        _fail("priority_player", "system-action boundary cannot grant player priority")
    if body["status"] == "ended" and (body["priority_player"] is not None or body["pending_system_actions"]):
        _fail("status", "ended game cannot grant further actions")
    if set(body["winner_ids"]) & set(body["loser_ids"]): _fail("outcome", "contradictory winners and losers")
    _choice(body["status"], {"in_progress", "ended"}, "status")
    if body["status"] == "in_progress" and (body["winner_ids"] or body["loser_ids"]):
        _fail("outcome", "in-progress game cannot declare winners or losers")
    if not isinstance(body["active_effects"], list): _fail("active_effects")
    effect_ids = []
    for effect in body["active_effects"]:
        _keys(effect, {"effect_id", "capability", "affected_actions", "knowledge"}, "active_effect")
        _text(effect["effect_id"], "effect_id")
        _text(effect["capability"], "capability")
        _strings(effect["affected_actions"], "affected_actions")
        _choice(effect["knowledge"], {"unsupported", "unknown"}, "effect.knowledge")
        effect_ids.append(effect["effect_id"])
    if len(set(effect_ids)) != len(effect_ids): _fail("active_effects", "duplicate identity")


def _action(body):
    _keys(body, {"game_id", "rules_snapshot_id", "expected_state_id", "kind", "actor", "object_id", "ability_id", "payment"}, "game_action")
    for key in ("game_id", "kind"): _text(body[key], key)
    for key in ("actor", "object_id", "ability_id"): _text(body[key], key, nullable=True)
    for key in ("rules_snapshot_id", "expected_state_id"): _identity(body[key], key)
    if body["payment"] is not None: _pool(body["payment"], "payment")


def _rule_refs(refs, *, allow_empty=False):
    if not isinstance(refs, list) or (not refs and not allow_empty):
        _fail("rule_references", "rule reference array required; decided rules require citations")
    identities = []
    for ref in refs:
        _keys(ref, {"rule_id", "external_reference", "rules_snapshot_id", "source_id", "category", "description", "status"}, "rule_reference")
        for key in ("rule_id", "source_id", "category", "description"): _text(ref[key], "rule_reference." + key)
        _text(ref["external_reference"], "external_reference", nullable=True)
        _identity(ref["rules_snapshot_id"], "rules_snapshot_id")
        _choice(ref["status"], CAPABILITY_STATUSES, "rule_reference.status")
        identities.append(ref["rule_id"])
    if len(set(identities)) != len(identities): _fail("rule_references", "duplicate rule identity")


def _payment(body):
    _keys(body, {"status", "cost", "pool_before", "payment", "pool_after", "failed_requirements", "unknown_requirements", "unsupported_dimensions"}, "payment_result")
    _choice(body["status"], _STATUSES, "status")
    validate_cost(body["cost"])
    for key in ("pool_before", "payment", "pool_after"): _pool(body[key], key)
    for key in ("failed_requirements", "unknown_requirements", "unsupported_dimensions"): _strings(body[key], key)
    _status_consistency(body)
    if body["status"] == "LEGAL":
        if not body["cost"]["known"] or body["cost"]["kind"] != "mana" or body["cost"]["unsupported"]:
            _fail("payment_result", "legal payment requires completely known supported cost")
        if set(body["pool_after"]) != set(body["pool_before"]): _fail("pool_after", "resource inventory changed")
        if any(body["payment"].get(symbol, 0) > amount or body["pool_after"][symbol] != amount - body["payment"].get(symbol, 0)
               for symbol, amount in body["pool_before"].items()) or set(body["payment"]) - set(body["pool_before"]):
            _fail("payment_result", "resource subtraction mismatch")
        if sum(body["payment"].values()) != body["cost"]["generic"] + sum(body["cost"]["colored"].values()):
            _fail("payment_result", "payment is not exact")
        if any(body["payment"].get(symbol, 0) < amount for symbol, amount in body["cost"]["colored"].items()):
            _fail("payment_result", "colored requirement unmet")
    elif body["payment"] or body["pool_after"] != body["pool_before"]:
        _fail("payment_result", "blocked payment cannot consume resources")


def _legality(body):
    _keys(body, {"game_id", "action_id", "before_state_id", "rules_snapshot_id", "status", "satisfied_requirements", "failed_requirements", "unknown_requirements", "rule_references", "required_costs", "payment", "assumptions", "unsupported_dimensions", "explanation"}, "legality_result")
    _text(body["game_id"], "game_id")
    for key in ("action_id", "before_state_id", "rules_snapshot_id"): _identity(body[key], key)
    _choice(body["status"], _STATUSES, "status")
    for key in ("satisfied_requirements", "failed_requirements", "unknown_requirements", "assumptions", "unsupported_dimensions"): _strings(body[key], key)
    _rule_refs(body["rule_references"], allow_empty=body["status"] in {"UNSUPPORTED", "INDETERMINATE"})
    if not isinstance(body["required_costs"], list): _fail("required_costs")
    for cost in body["required_costs"]: validate_cost(cost)
    if body["payment"] is not None:
        payment = PaymentResult.from_dict(body["payment"])
        if body["required_costs"] != [payment.to_dict()["cost"]]: _fail("required_costs", "payment cost mismatch")
        if body["status"] == "LEGAL" and payment.status != "LEGAL": _fail("payment", "legal action requires legal payment")
    _status_consistency(body)
    _keys(body["explanation"], {"action_kind", "status", "reason_codes"}, "explanation")
    _text(body["explanation"]["action_kind"], "explanation.action_kind")
    _strings(body["explanation"]["reason_codes"], "explanation.reason_codes")
    if body["explanation"]["status"] != body["status"] or set(body["explanation"]["reason_codes"]) != set(body["failed_requirements"] + body["unknown_requirements"] + body["unsupported_dimensions"]):
        _fail("explanation", "verdict or reason correspondence mismatch")
    if any(r["rules_snapshot_id"] != body["rules_snapshot_id"] for r in body["rule_references"]): _fail("rule_references", "snapshot mismatch")


def _status_consistency(body):
    fields = {"ILLEGAL": "failed_requirements", "INDETERMINATE": "unknown_requirements",
              "UNSUPPORTED": "unsupported_dimensions"}
    if body["status"] == "LEGAL":
        if any(body[key] for key in fields.values()): _fail("status", "legal verdict contradicts unmet requirements")
    elif not body[fields[body["status"]]]:
        _fail("status", "nonlegal verdict requires its explicit reason category")


def _transition(body):
    _keys(body, {"game_id", "rules_snapshot_id", "action_id", "before_state_id", "after_state_id", "actor", "action", "after_state", "state_changes", "zone_changes", "resource_changes", "stack_changes", "rule_references", "required_system_actions"}, "game_transition")
    _text(body["game_id"], "game_id")
    _text(body["actor"], "actor", nullable=True)
    for key in ("rules_snapshot_id", "action_id", "before_state_id", "after_state_id"): _identity(body[key], key)
    action = GameAction.from_dict(body["action"])
    after = GameState.from_dict(body["after_state"])
    if action.identity != body["action_id"] or after.identity != body["after_state_id"]: _fail("transition", "nested identity mismatch")
    if action.game_id != body["game_id"] or after.game_id != body["game_id"] or action.rules_snapshot_id != body["rules_snapshot_id"] or after.rules_snapshot_id != body["rules_snapshot_id"] or action.expected_state_id != body["before_state_id"] or action.actor != body["actor"]: _fail("transition", "nested binding mismatch")
    for key in ("state_changes", "zone_changes", "resource_changes", "stack_changes"):
        if not isinstance(body[key], list) or any(not isinstance(v, dict) for v in body[key]): _fail(key, "structured change array required")
    _rule_refs(body["rule_references"])
    if any(r["rules_snapshot_id"] != body["rules_snapshot_id"] for r in body["rule_references"]): _fail("rule_references", "snapshot mismatch")
    _strings(body["required_system_actions"], "required_system_actions")
    if body["required_system_actions"] != list(after.pending_system_actions): _fail("required_system_actions", "after-state mismatch")


@dataclass(frozen=True)
class _Envelope:
    _payload: Mapping[str, Any]
    SCHEMA: ClassVar[str]
    ID_FIELD: ClassVar[str]
    VALIDATOR: ClassVar[Any]

    def __post_init__(self):
        value = _json(self._payload)
        if not isinstance(value, dict): _fail("envelope", "object required")
        if value.get("schema_version") != self.SCHEMA: raise GameplayContractError("incompatible_contract", "Unsupported gameplay envelope version")
        supplied = value.get(self.ID_FIELD)
        _identity(supplied, self.ID_FIELD)
        body = {k: v for k, v in value.items() if k not in {"schema_version", self.ID_FIELD}}
        self.VALIDATOR(body)
        expected = content_identity(self.SCHEMA, {"schema_version": self.SCHEMA, **body})
        if supplied != expected: raise GameplayContractError("integrity_mismatch", "Gameplay envelope content identity mismatch")
        object.__setattr__(self, "_payload", _freeze(value))

    @classmethod
    def create(cls, body: Mapping[str, Any]):
        value = _json(body)
        if not isinstance(value, dict) or cls.ID_FIELD in value: _fail("create", "unbound body required")
        if "schema_version" in value and value["schema_version"] != cls.SCHEMA: _fail("schema_version")
        value["schema_version"] = cls.SCHEMA
        value[cls.ID_FIELD] = content_identity(cls.SCHEMA, value)
        return cls(value)

    @classmethod
    def from_dict(cls, value: Mapping[str, Any]): return cls(value)

    @property
    def identity(self): return self._payload[self.ID_FIELD]

    @property
    def identity_key(self): return self.ID_FIELD

    def to_dict(self): return _json(self._payload)

    def verify(self):
        type(self).from_dict(self.to_dict())
        return self

    def __getattr__(self, name):
        payload = object.__getattribute__(self, "_payload")
        if name in payload: return payload[name]
        raise AttributeError(name)


@dataclass(frozen=True)
class GameplayRulesSnapshot(_Envelope):
    SCHEMA = "gameplay-rules-snapshot-v1"
    ID_FIELD = "rules_snapshot_id"
    VALIDATOR = staticmethod(_snapshot)


@dataclass(frozen=True)
class CardGameplaySemantics(_Envelope):
    SCHEMA = "gameplay-card-semantics-v1"
    ID_FIELD = "semantics_id"
    VALIDATOR = staticmethod(_semantics)


@dataclass(frozen=True)
class GameState(_Envelope):
    SCHEMA = "gameplay-state-v1"
    ID_FIELD = "state_id"
    VALIDATOR = staticmethod(_state)


@dataclass(frozen=True)
class GameAction(_Envelope):
    SCHEMA = "gameplay-action-v1"
    ID_FIELD = "action_id"
    VALIDATOR = staticmethod(_action)


@dataclass(frozen=True)
class PaymentResult(_Envelope):
    SCHEMA = "gameplay-payment-result-v1"
    ID_FIELD = "payment_id"
    VALIDATOR = staticmethod(_payment)


@dataclass(frozen=True)
class LegalityResult(_Envelope):
    SCHEMA = "gameplay-legality-result-v1"
    ID_FIELD = "result_id"
    VALIDATOR = staticmethod(_legality)


@dataclass(frozen=True)
class GameTransition(_Envelope):
    SCHEMA = "gameplay-transition-v1"
    ID_FIELD = "transition_id"
    VALIDATOR = staticmethod(_transition)
