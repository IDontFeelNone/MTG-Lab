"""Stable read contract for canonical repository consumers."""

from .engine import CanonicalQueryEngine, QueryError, QueryResult, QuerySnapshot
from .service import CanonicalAnswer, CanonicalQueryService

__all__ = ["CanonicalAnswer", "CanonicalQueryEngine", "CanonicalQueryService",
           "QueryError", "QueryResult", "QuerySnapshot"]
