"""Stable read contract for canonical repository consumers."""

from .engine import CanonicalQueryEngine, QueryError, QueryResult, QuerySnapshot

__all__ = ["CanonicalQueryEngine", "QueryError", "QueryResult", "QuerySnapshot"]
