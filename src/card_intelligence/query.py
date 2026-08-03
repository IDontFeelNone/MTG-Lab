"""Read-only deterministic queries over asserted knowledge."""
from __future__ import annotations
from typing import Any
from .models import KnowledgeValidationError
from .repository import KnowledgeRepository

VALUE_DRIVER_KINDS = frozenset({"popularity", "reprint_history", "reserved_status",
    "product_exclusivity", "scarcity", "supply", "demand", "synergy", "combo",
    "infinite_combo", "staple", "market_catalyst"})


class CardKnowledgeQuery:
    def __init__(self, repository: KnowledgeRepository): self.repository = repository

    def explain(self, game_id: str, card_id: str, *, include_superseded: bool = True) -> dict[str, Any]:
        facts = [x for x in self.repository.validate() if x.game_id == game_id and x.card_id == card_id]
        if not include_superseded:
            replaced = {old for x in facts for old in x.supersedes}
            facts = [x for x in facts if x.fact_id not in replaced]
        return self._report(game_id, card_id, facts, "all")

    def by_kind(self, game_id: str, card_id: str, *kinds: str,
                include_superseded: bool = True) -> dict[str, Any]:
        if not kinds: raise KnowledgeValidationError("at least one kind is required")
        facts = [x for x in self.repository.validate() if x.game_id == game_id
                 and x.card_id == card_id and x.kind in kinds]
        if not include_superseded:
            replaced = {old for x in facts for old in x.supersedes}
            facts = [x for x in facts if x.fact_id not in replaced]
        return self._report(game_id, card_id, facts, ",".join(sorted(kinds)))

    def printing_history(self, game_id: str, card_id: str, *,
                         include_superseded: bool = False) -> dict[str, Any]:
        """Return asserted printing history, active-only unless history is requested."""
        return self.by_kind(game_id, card_id, "reprint_history",
                            include_superseded=include_superseded)

    def value_drivers(self, game_id: str, card_id: str) -> dict[str, Any]:
        return self.by_kind(game_id, card_id, *sorted(VALUE_DRIVER_KINDS))

    def competitive_formats(self, game_id: str, card_id: str) -> dict[str, Any]:
        return self.by_kind(game_id, card_id, "legality")

    def archetypes(self, game_id: str, card_id: str) -> dict[str, Any]:
        return self.by_kind(game_id, card_id, "archetype_usage")

    def market_catalysts(self, game_id: str, card_id: str) -> dict[str, Any]:
        return self.by_kind(game_id, card_id, "market_catalyst")

    @staticmethod
    def _report(game_id, card_id, facts, selection):
        documents = [x.to_dict() for x in facts]
        return {"schema_version": "card-knowledge-query-v1", "subject": {"game_id": game_id,
            "card_id": card_id}, "selection": selection, "count": len(documents),
            "empty": not documents, "facts": documents,
            "evidence_sources": sorted({e.source_id for x in facts for e in x.evidence}),
            "confidence_values": [{"fact_id": x.fact_id,
                "confidence": format(x.confidence, "f") if x.confidence is not None else None}
                for x in facts]}
