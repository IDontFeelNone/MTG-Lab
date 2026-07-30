"""Application boundary for ingestion from repository-verified evidence."""

from __future__ import annotations

import json
from pathlib import Path

from ingestion.card_printing_wave import CardPrintingWave, ingest_card_printing_wave
from repository.cards import load_card_repository
from repository.evidence import EvidenceRepositoryError, load_evidence_bundle


def ingest_verified_card_printing_wave(
    game: str,
    bundle_id: str,
    artifact_id: str,
    *,
    acquisition_target_id: str,
    acquired_at: str,
    limit: int = 5,
    evidence_root: Path | None = None,
    games_root: Path | None = None,
) -> CardPrintingWave:
    """Load one archived artifact, validate its context, and ingest its verified bytes."""
    bundle = load_evidence_bundle(
        game, bundle_id, evidence_root=evidence_root, games_root=games_root
    )
    artifacts = [artifact for artifact in bundle.artifacts if artifact.id == artifact_id]
    if len(artifacts) != 1:
        raise EvidenceRepositoryError(
            f"Evidence artifact identifier is missing or ambiguous: {artifact_id}"
        )
    artifact = artifacts[0]
    if artifact.media_type != "application/json":
        raise EvidenceRepositoryError("Card and Printing evidence must be application/json")

    document = _load_wave_document(artifact.content)
    attributed_sources = {entry["source_id"] for entry in artifact.provenance}
    embedded_sources = {
        record[field]
        for record in document["records"]
        for field in ("card_source_id", "printing_source_id", "membership_source_id")
        if isinstance(record, dict) and field in record
    }
    undeclared = embedded_sources - attributed_sources
    if undeclared:
        raise EvidenceRepositoryError(
            "Wave records reference sources not attributed to the verified artifact: "
            + ", ".join(sorted(undeclared))
        )

    wave = ingest_card_printing_wave(
        artifact.content,
        product_id=bundle.manifest["product_id"],
        bundle_source_id=bundle_id,
        acquisition_target_id=acquisition_target_id,
        acquired_at=acquired_at,
        limit=limit,
    )
    return wave


def card_candidate_ids_requiring_promotion(
    wave: CardPrintingWave, game: str, *, games_root: Path | None = None
) -> tuple[str, ...]:
    """Return only Card candidates whose canonical Card does not already exist."""
    cards, _ = load_card_repository(game, games_root=games_root)
    existing_ids = {card["id"] for card in cards}
    return tuple(
        candidate.id for candidate in wave.cards.candidates
        if candidate.payload["id"] not in existing_ids
    )


def _load_wave_document(content: bytes) -> dict:
    try:
        document = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise EvidenceRepositoryError("Wave artifact is not valid UTF-8 JSON") from error
    if not isinstance(document, dict) or not isinstance(document.get("records"), list):
        raise EvidenceRepositoryError("Wave artifact records must be a list")
    return document


__all__ = ["card_candidate_ids_requiring_promotion", "ingest_verified_card_printing_wave"]
