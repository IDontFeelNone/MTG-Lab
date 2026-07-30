"""Stable read contract for canonical repository consumers."""

from .engine import CanonicalQueryEngine, QueryError, QueryResult

__all__ = ["CanonicalQueryEngine", "QueryError", "QueryResult"]
