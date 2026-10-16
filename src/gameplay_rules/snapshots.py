"""Explicit local gameplay contract loading; no discovery, networking or fallback."""
from __future__ import annotations

import json
from pathlib import Path

from .errors import GameplayContractError
from .models import (CardGameplaySemantics, GameAction, GameState, GameTransition,
                     GameplayRulesSnapshot, LegalityResult, PaymentResult, rule_identity)

MAX_CONTRACT_BYTES = 2 * 1024 * 1024


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise GameplayContractError("invalid_json", "Duplicate gameplay JSON key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise GameplayContractError("invalid_json", "Non-finite gameplay JSON number")


def load_contract(path, model):
    """Load one explicitly selected file, without ambient data or root inference.

    Absolute caller-selected file paths are allowed; traversal components,
    backslash ambiguity and symlink substitution are not. Error text never
    includes the caller's path or source contents.
    """
    if model not in {GameplayRulesSnapshot, CardGameplaySemantics, GameState,
                     GameAction, PaymentResult, LegalityResult, GameTransition}:
        raise GameplayContractError("invalid_contract", "Unsupported gameplay contract type")
    try:
        selected = Path(path)
        if ".." in selected.parts or "\\" in str(selected):
            raise GameplayContractError("unsafe_path", "Ambiguous gameplay contract path")
        if any(item.is_symlink() for item in (selected, *selected.parents)):
            raise GameplayContractError("unsafe_path", "Gameplay contract symlinks are not permitted")
        if not selected.is_file():
            raise GameplayContractError("missing_contract", "Requested gameplay contract file is unavailable")
        if selected.stat().st_size > MAX_CONTRACT_BYTES:
            raise GameplayContractError("invalid_contract", "Gameplay contract exceeds bounded file size")
        raw = selected.read_bytes()
        if len(raw) > MAX_CONTRACT_BYTES:
            raise GameplayContractError("invalid_contract", "Gameplay contract exceeds bounded file size")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object,
                           parse_constant=_nonfinite)
        return model.from_dict(value)
    except GameplayContractError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, RecursionError):
        raise GameplayContractError("invalid_contract", "Unreadable or malformed gameplay contract") from None


def load_rules_snapshot(path):
    return load_contract(path, GameplayRulesSnapshot)


def load_card_semantics(path):
    return load_contract(path, CardGameplaySemantics)


def load_game_state(path):
    return load_contract(path, GameState)
