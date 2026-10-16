"""Explicit coverage vocabulary, independent of Product/Pack/Collation Rules."""

CAPABILITY_STATUSES = frozenset({"supported", "partial", "unsupported", "unknown"})
CAPABILITIES = (
    "turn_structure", "active_player", "priority", "stack", "zones", "land_play",
    "spell_casting", "activated_abilities", "mana_generation", "mana_payment",
    "generic_costs", "targeting", "resolution", "zone_changes", "state_based_actions",
    "triggered_abilities", "replacement_effects", "prevention_effects",
    "continuous_effects", "layers", "copy_effects", "combat", "damage", "multiplayer",
    "alternate_costs", "additional_costs", "cost_reductions_increases",
    "format_legality", "deck_construction", "commander_specific_rules",
)
SOURCE_CLASSES = frozenset({
    "official_comprehensive_rules", "official_oracle_card_text",
    "official_rulings_release_notes", "format_banned_restricted_policy",
    "project_authored_fictional",
})
ENGINE_CONTRACT_VERSION = "gameplay-kernel-v1"
EXECUTION_PROFILE = "fictional-two-player-v1"
REQUIRED_RULE_CATEGORIES = frozenset({
    "priority", "timing", "zones", "land_play", "spell_casting",
    "activated_abilities", "mana_generation", "mana_payment", "stack",
    "resolution", "turn_structure", "state_based_actions",
})
KERNEL_SUPPORTED_CAPABILITIES = frozenset({
    "turn_structure", "active_player", "priority", "stack", "zones", "land_play",
    "spell_casting", "activated_abilities", "mana_generation", "mana_payment",
    "generic_costs", "resolution", "zone_changes", "state_based_actions",
})
ZONE_KINDS = frozenset({"library", "hand", "battlefield", "graveyard", "stack", "exile", "command"})
