"""Deterministic, game-agnostic card knowledge contracts."""

from .models import Evidence, KnowledgeFact, KnowledgeValidationError
from .query import CardKnowledgeQuery
from .printing_history_audit import build_phase137_audit, report_bytes
from .explanation import (CardValueExplanationEngine, ExplanationError,
                          explanation_bytes, render_historical_explanation)
from .repository import KnowledgeRepository

__all__ = ["CardKnowledgeQuery", "Evidence", "KnowledgeFact", "KnowledgeRepository",
           "KnowledgeValidationError", "build_phase137_audit", "report_bytes",
           "CardValueExplanationEngine", "ExplanationError", "explanation_bytes",
           "render_historical_explanation"]
