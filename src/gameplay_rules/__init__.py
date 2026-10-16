"""Gameplay Rules & Interaction Intelligence; separate from Product Rules.

The initial executable profile contains project-authored fictional rules only.
"""
from .errors import GameplayContractError
from .models import (CardGameplaySemantics, GameAction, GameState, GameTransition,
                     GameplayRulesSnapshot, LegalityResult, PaymentResult)
from .snapshots import load_card_semantics, load_game_state, load_rules_snapshot

__all__ = ["GameplayContractError", "GameplayRulesSnapshot", "CardGameplaySemantics",
           "GameState", "GameAction", "GameTransition", "LegalityResult", "PaymentResult",
           "load_rules_snapshot", "load_card_semantics", "load_game_state"]
