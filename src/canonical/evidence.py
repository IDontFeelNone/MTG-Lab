"""Assertion evidence, uncertainty, promotion, and simulation-readiness contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable


class KnowledgeStatus(str, Enum):
    KNOWN = "known"
    KNOWN_ABSENT = "known_absent"
    UNKNOWN = "unknown"
    PROVISIONAL = "provisional"
    CONFLICTING = "conflicting"
    UNRESOLVED = "unresolved"


class EvidenceClass(str, Enum):
    OFFICIAL = "official"
    AUTHORITATIVE_STRUCTURED = "authoritative_structured"
    VERIFIED_COMMUNITY = "verified_community"
    DIRECT_OBSERVATION = "direct_observation"
    DERIVED = "derived"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"


@dataclass(frozen=True)
class KnowledgeValue:
    status: KnowledgeStatus
    value: Any = None
    assertion_ids: tuple[str, ...] = ()

    def require_known(self, path: str) -> Any:
        if self.status is not KnowledgeStatus.KNOWN:
            raise UnresolvedCanonicalFact(f"{path} is {self.status.value}; simulation must fail closed")
        return self.value


@dataclass(frozen=True)
class EvidenceAssertion:
    id: str
    subject_id: str
    path: str
    value: Any
    source_id: str
    source_type: str
    evidence_class: EvidenceClass
    timestamp: str
    confidence: float
    verification_status: str
    status: str = "candidate"
    notes: str | None = None
    supersedes: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()


class UnresolvedCanonicalFact(ValueError):
    """A required downstream semantic has not been established."""


_PRIORITY = {
    EvidenceClass.OFFICIAL: 7,
    EvidenceClass.AUTHORITATIVE_STRUCTURED: 6,
    EvidenceClass.DIRECT_OBSERVATION: 5,
    EvidenceClass.VERIFIED_COMMUNITY: 4,
    EvidenceClass.DERIVED: 3,
    EvidenceClass.INFERRED: 2,
    EvidenceClass.UNKNOWN: 1,
    EvidenceClass.CONFLICTING: 0,
}


def promote_assertions(assertions: Iterable[EvidenceAssertion]) -> EvidenceAssertion | None:
    """Deterministically select a verified claim, rejecting tied disagreement.

    Assertions remain inputs to this pure function: promotion never deletes evidence.
    Explicitly rejected/superseded claims and non-verified hypotheses cannot win.
    """
    eligible = [a for a in assertions if a.status not in {"rejected", "superseded"}
                and a.verification_status in {"verified", "confirmed"}
                and a.evidence_class not in {EvidenceClass.UNKNOWN, EvidenceClass.CONFLICTING}]
    if not eligible:
        return None
    eligible.sort(key=lambda a: (-_PRIORITY[a.evidence_class], -a.confidence,
                                 a.timestamp, a.source_id, a.id))
    winner = eligible[0]
    rank = (_PRIORITY[winner.evidence_class], winner.confidence)
    peers = [a for a in eligible if (_PRIORITY[a.evidence_class], a.confidence) == rank]
    if any(a.value != winner.value for a in peers):
        return None
    return winner


def require_simulation_facts(facts: dict[str, KnowledgeValue], required_paths: Iterable[str]) -> None:
    """Fail closed unless every named collation semantic is canonically known."""
    for path in required_paths:
        if path not in facts:
            raise UnresolvedCanonicalFact(f"{path} is absent; simulation must fail closed")
        facts[path].require_known(path)
