"""Deterministic ingestion for bounded, reviewed Card and Printing evidence waves."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from validation import validate_document

from .candidates import (
    ArtifactStatus, CandidateValidationState, FieldProvenance, NormalizedCandidate,
    NormalizedCandidateArtifact, ParsedArtifact, ParsedRecord,
)
from .hashing import hash_bytes

_IDENTIFIER_PART = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class CardPrintingWave:
    """The immutable artifacts produced by one bounded evidence bundle."""

    parsed: ParsedArtifact
    cards: NormalizedCandidateArtifact
    printings: NormalizedCandidateArtifact


def _slug(value: str) -> str:
    return _IDENTIFIER_PART.sub("-", value.casefold()).strip("-")


def ingest_card_printing_wave(
    content: bytes, *, product_id: str, bundle_source_id: str,
    acquisition_target_id: str, acquired_at: str, limit: int = 25,
) -> CardPrintingWave:
    """Convert one complete, reviewed evidence batch of at most ``limit`` pairs."""
    if not 1 <= limit <= 25:
        raise ValueError("limit must be between one and twenty-five")
    document = json.loads(content.decode("utf-8"))
    records = document.get("records")
    if not isinstance(records, list):
        raise ValueError("evidence bundle records must be a list")
    if not records:
        raise ValueError("evidence bundle contains no reviewable records")
    if len(records) > limit:
        raise ValueError(
            f"evidence bundle contains {len(records)} records, exceeding the limit of {limit}"
        )
    selected = records

    digest = hash_bytes(content)
    artifact_id = f"{acquisition_target_id}-parsed-{digest[:16]}"
    parsed_records: list[ParsedRecord] = []
    card_candidates: list[NormalizedCandidate] = []
    printing_candidates: list[NormalizedCandidate] = []
    for index, evidence_record in enumerate(selected, start=1):
        _validate_evidence_record(evidence_record)
        record_id = f"{acquisition_target_id}-record-{index:02d}"
        parsed_records.append(ParsedRecord(
            id=record_id,
            record_type="card_printing_pair",
            raw_fields=evidence_record,
            source_location=evidence_record["source_location"],
            source_excerpt={
                "name": evidence_record["name"], "set_code": evidence_record["set_code"],
                "collector_number": evidence_record["collector_number"],
            },
        ))
        card_candidates.append(_card_candidate(evidence_record, artifact_id, record_id, digest,
                                                   acquisition_target_id))
        printing_candidates.append(_printing_candidate(
            evidence_record, artifact_id, record_id, digest, acquisition_target_id
        ))

    parsed = ParsedArtifact(
        id=artifact_id, product_id=product_id, source_id=bundle_source_id,
        acquisition_target_id=acquisition_target_id, raw_evidence_hash=digest,
        parser_id="bounded-card-printing-evidence-bundle", parser_version="1",
        parsed_at=acquired_at, input_content_type="application/json",
        status=ArtifactStatus.SUCCEEDED, records=tuple(parsed_records),
    )
    common = dict(
        product_id=product_id, source_id=bundle_source_id,
        acquisition_target_id=acquisition_target_id, raw_evidence_hash=digest,
        parsed_artifact_id=artifact_id, normalizer_id="bounded-card-printing-wave",
        normalizer_version="1", normalized_at=acquired_at, status=ArtifactStatus.SUCCEEDED,
    )
    cards = NormalizedCandidateArtifact(
        id=f"{acquisition_target_id}-card-candidates-{digest[:16]}", candidate_type="card",
        candidates=tuple(card_candidates), **common,
    )
    printings = NormalizedCandidateArtifact(
        id=f"{acquisition_target_id}-printing-candidates-{digest[:16]}",
        candidate_type="printing", candidates=tuple(printing_candidates), **common,
    )
    return CardPrintingWave(parsed, cards, printings)


def _validate_evidence_record(record: Mapping[str, Any]) -> None:
    required = {
        "name", "set_code", "collector_number", "rarity", "language",
        "card_source_id", "printing_source_id", "membership_source_id", "source_location",
    }
    missing = sorted(required - set(record))
    if missing:
        raise ValueError(f"evidence record lacks required fields: {', '.join(missing)}")
    card_id = f"magic.{_slug(str(record['name']))}"
    printing_id = (
        f"magic.{_slug(str(record['set_code']))}."
        f"{_slug(str(record['collector_number']))}.{record['language']}"
    )
    card = _card_payload(record, card_id)
    printing = _printing_payload(record, card_id, printing_id)
    validate_document(card, "card")
    validate_document(printing, "printing")


def _card_payload(record: Mapping[str, Any], card_id: str) -> dict[str, Any]:
    return {
        "schema_version": "v1", "id": card_id, "game": "magic", "name": record["name"],
        "provenance": [{
            "source_id": record["card_source_id"],
            "field_paths": ["id", "game", "name"],
            "claim": "The cited card database establishes the Magic card identity and name.",
            "notes": "The MTG Lab ID is deterministically derived from game and normalized name.",
        }],
    }


def _printing_payload(
    record: Mapping[str, Any], card_id: str, printing_id: str,
) -> dict[str, Any]:
    return {
        "schema_version": "v1", "id": printing_id, "card_id": card_id,
        "set_code": record["set_code"], "collector_number": record["collector_number"],
        "rarity": record["rarity"], "language": record["language"],
        "provenance": [
            {
                "source_id": record["printing_source_id"],
                "field_paths": [
                    "id", "card_id", "set_code", "collector_number", "rarity", "language",
                ],
                "claim": "The cited printing database establishes the exact printing fields.",
                "notes": "The MTG Lab ID is deterministically derived from printing identity fields.",
            },
            {
                "source_id": record["membership_source_id"],
                "field_paths": ["metadata"],
                "claim": "The official gallery identifies this printing as Mystery Booster 2 content.",
            },
        ],
        "metadata": {"product_membership": ["mystery_booster_2"]},
    }


def _field_provenance(
    *, payload: Mapping[str, Any], sources: Mapping[str, str], artifact_id: str,
    record_id: str, digest: str, target_id: str,
) -> tuple[FieldProvenance, ...]:
    return tuple(FieldProvenance(
        field_path=field, value_origin=field, source_id=source_id,
        acquisition_target_id=target_id, raw_evidence_hash=digest,
        parsed_artifact_id=artifact_id, parsed_record_id=record_id,
        transformation_id="bounded-card-printing-wave", transformation_version="1",
        provenance_classification=("community" if source_id.startswith("scryfall-") else "official"),
        confidence=1.0,
    ) for field, source_id in sources.items() if field in payload)


def _card_candidate(
    record: Mapping[str, Any], artifact_id: str, record_id: str, digest: str, target_id: str,
) -> NormalizedCandidate:
    card_id = f"magic.{_slug(str(record['name']))}"
    payload = _card_payload(record, card_id)
    provenance = _field_provenance(
        payload=payload,
        sources={field: record["card_source_id"] for field in payload},
        artifact_id=artifact_id, record_id=record_id, digest=digest, target_id=target_id,
    )
    return NormalizedCandidate(
        id=f"{card_id}-candidate", entity_type="card", payload=payload,
        parsed_record_ids=(record_id,), field_provenance=provenance, confidence=1.0,
        validation_state=CandidateValidationState.VALID,
    )


def _printing_candidate(
    record: Mapping[str, Any], artifact_id: str, record_id: str, digest: str, target_id: str,
) -> NormalizedCandidate:
    card_id = f"magic.{_slug(str(record['name']))}"
    printing_id = (
        f"magic.{_slug(str(record['set_code']))}."
        f"{_slug(str(record['collector_number']))}.{record['language']}"
    )
    payload = _printing_payload(record, card_id, printing_id)
    sources = {
        field: record["printing_source_id"] for field in payload if field != "metadata"
    }
    sources["metadata"] = record["membership_source_id"]
    provenance = _field_provenance(
        payload=payload, sources=sources, artifact_id=artifact_id, record_id=record_id,
        digest=digest, target_id=target_id,
    )
    return NormalizedCandidate(
        id=f"{printing_id}-candidate", entity_type="printing", payload=payload,
        parsed_record_ids=(record_id,), field_provenance=provenance, confidence=1.0,
        validation_state=CandidateValidationState.VALID,
    )


__all__: Sequence[str] = ("CardPrintingWave", "ingest_card_printing_wave")
