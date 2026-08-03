"""Append-only filesystem repository and strict loader for card knowledge."""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
from typing import Any

from .models import Evidence, KnowledgeFact, KnowledgeValidationError


def serialize_fact(fact: KnowledgeFact) -> bytes:
    return (json.dumps(fact.to_dict(), indent=2, sort_keys=True,
                       separators=(",", ": ")) + "\n").encode()


def fact_from_dict(data: Any) -> KnowledgeFact:
    try:
        if not isinstance(data, dict) or set(data) != {"schema_version", "fact_id", "subject",
                "kind", "predicate", "value", "confidence", "effective_at", "recorded_at",
                "evidence", "supersedes"}:
            raise KnowledgeValidationError("knowledge fact has missing or unexpected fields")
        if set(data["subject"]) != {"game_id", "card_id"} or set(data["value"]) != {"status", "data"}:
            raise KnowledgeValidationError("invalid subject or value envelope")
        if any(not isinstance(x, dict) or set(x) != {"source_id", "source_type", "reference",
                "observed_at", "claim"} for x in data["evidence"]):
            raise KnowledgeValidationError("invalid evidence envelope")
        evidence = tuple(Evidence(source_id=x["source_id"], source_type=x["source_type"],
            reference=x["reference"], observed_at=_parse_time(x["observed_at"]), claim=x["claim"])
            for x in data["evidence"])
        return KnowledgeFact(fact_id=data["fact_id"], game_id=data["subject"]["game_id"],
            card_id=data["subject"]["card_id"], kind=data["kind"], predicate=data["predicate"],
            value_status=data["value"]["status"], value=data["value"]["data"],
            confidence=data["confidence"], effective_at=_parse_time(data["effective_at"]),
            recorded_at=_parse_time(data["recorded_at"]), evidence=evidence,
            supersedes=tuple(data["supersedes"]), schema_version=data["schema_version"])
    except (KeyError, TypeError, ValueError) as error:
        if isinstance(error, KnowledgeValidationError):
            raise
        raise KnowledgeValidationError("invalid knowledge fact document") from error


def _parse_time(value: Any) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise KnowledgeValidationError("timestamps must be UTC ISO 8601 strings")
    return datetime.fromisoformat(value[:-1] + "+00:00")


class KnowledgeRepository:
    """Stores facts at ``facts/<game>/<card>/<fact>.json`` without replacement."""

    def __init__(self, root: Path):
        self.root = Path(root)

    def _path(self, fact: KnowledgeFact) -> Path:
        return self.root / "facts" / fact.game_id / fact.card_id / f"{fact.fact_id}.json"

    def append(self, fact: KnowledgeFact) -> Path:
        if not isinstance(fact, KnowledgeFact):
            raise KnowledgeValidationError("only KnowledgeFact records may be appended")
        path = self._path(fact); payload = serialize_fact(fact)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise KnowledgeValidationError(f"duplicate fact_id: {fact.fact_id}") from error
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
        return path

    def load(self, path: Path) -> KnowledgeFact:
        try:
            raw = Path(path).read_bytes(); data = json.loads(raw)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KnowledgeValidationError(f"invalid knowledge document: {path}") from error
        fact = fact_from_dict(data)
        if Path(path).resolve() != self._path(fact).resolve():
            raise KnowledgeValidationError("knowledge path does not match content")
        if raw != serialize_fact(fact):
            raise KnowledgeValidationError("knowledge document is not canonically serialized")
        return fact

    def all(self) -> tuple[KnowledgeFact, ...]:
        facts = tuple(self.load(path) for path in sorted((self.root / "facts").glob("*/*/*.json")))
        identities = [x.fact_id for x in facts]
        if len(identities) != len(set(identities)):
            raise KnowledgeValidationError("duplicate fact_id in repository")
        by_id = {x.fact_id: x for x in facts}
        for fact in facts:
            for prior in fact.supersedes:
                if prior not in by_id:
                    raise KnowledgeValidationError(f"missing superseded fact: {prior}")
                old = by_id[prior]
                if (old.game_id, old.card_id, old.predicate) != (fact.game_id, fact.card_id, fact.predicate):
                    raise KnowledgeValidationError("supersession must preserve subject and predicate")
                if old.recorded_at >= fact.recorded_at:
                    raise KnowledgeValidationError("supersession must move forward in recorded time")
        # Recording order is the stable append-only history order.  Effective
        # dates describe the asserted subject and may legitimately move
        # backwards when a later evidence set adds an older Printing.
        return tuple(sorted(facts, key=lambda x: (x.game_id, x.card_id, x.recorded_at,
                                                  x.effective_at, x.kind, x.predicate, x.fact_id)))

    def validate(self) -> tuple[KnowledgeFact, ...]:
        facts = self.all(); graph = {x.fact_id: x.supersedes for x in facts}
        def visit(node: str, trail: frozenset[str]) -> None:
            if node in trail: raise KnowledgeValidationError("supersession cycle")
            for parent in graph[node]: visit(parent, trail | {node})
        for node in graph: visit(node, frozenset())
        return facts
