"""Deterministic pre-promotion review for Card and Printing population batches."""
from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

from repository.cards import canonical_repository_bytes, load_card_repository
from validation import validate_document

from .card_printing_wave import CardPrintingWave
from .candidates import CandidateValidationState
from .hashing import hash_bytes


def build_population_review_report(
    wave: CardPrintingWave,
    game: str,
    *,
    generated_at: str,
    games_root=None,
) -> Mapping[str, Any]:
    """Classify a complete batch against one validated canonical snapshot."""
    cards, printings = load_card_repository(game, games_root=games_root)
    snapshot_hash = hash_bytes(canonical_repository_bytes(game, games_root=games_root))
    canonical_cards = {item["id"]: item for item in cards}
    canonical_printings = {item["id"]: item for item in printings}
    card_candidates = list(wave.cards.candidates)
    printing_candidates = list(wave.printings.candidates)
    if len(card_candidates) != len(printing_candidates) or not card_candidates:
        raise ValueError("review requires matching non-empty Card and Printing candidates")
    if len(card_candidates) > 25:
        raise ValueError("review supports at most twenty-five Printing records")

    printing_counts = Counter(item.payload["id"] for item in printing_candidates)
    duplicates: list[dict[str, str]] = []
    conflicts: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    new_cards: set[str] = set()
    reused_cards: set[str] = set()
    new_printings: set[str] = set()

    for card, printing in zip(card_candidates, printing_candidates, strict=True):
        record_id = printing.parsed_record_ids[0]
        card_id = card.payload["id"]
        printing_id = printing.payload["id"]
        invalid = (
            card.validation_state is not CandidateValidationState.VALID
            or printing.validation_state is not CandidateValidationState.VALID
        )
        if invalid:
            rejected.append(_finding(record_id, "record", printing_id,
                                     "Card or Printing candidate is not valid"))
            continue
        if printing_counts[printing_id] > 1:
            duplicates.append(_finding(record_id, "printing", printing_id,
                                       "Printing identifier occurs more than once in the batch"))
            continue

        existing_card = canonical_cards.get(card_id)
        if existing_card is not None and existing_card != card.payload:
            conflicts.append(_finding(record_id, "card", card_id,
                                      "Candidate differs from the canonical Card"))
            continue

        existing_printing = canonical_printings.get(printing_id)
        if existing_printing is not None and existing_printing != printing.payload:
            conflicts.append(_finding(record_id, "printing", printing_id,
                                      "Candidate differs from the canonical Printing"))
            continue

        if existing_card is None:
            new_cards.add(card_id)
        else:
            reused_cards.add(card_id)
        if existing_printing is None:
            new_printings.add(printing_id)
        else:
            duplicates.append(_finding(record_id, "printing", printing_id,
                                       "Printing is already canonical with identical content"))

    duplicates.sort(key=_finding_key)
    conflicts.sort(key=_finding_key)
    rejected.sort(key=_finding_key)
    new_card_ids = sorted(new_cards)
    reused_card_ids = sorted(reused_cards)
    new_printing_ids = sorted(new_printings)
    before = {"cards": len(cards), "printings": len(printings)}
    after = {"cards": len(cards) + len(new_card_ids),
             "printings": len(printings) + len(new_printing_ids)}
    report = {
        "schema_version": "v1", "artifact_version": "1",
        "id": f"{wave.parsed.acquisition_target_id}-review-{wave.parsed.raw_evidence_hash[:12]}-{snapshot_hash[:12]}",
        "product_id": wave.parsed.product_id, "source_id": wave.parsed.source_id,
        "acquisition_target_id": wave.parsed.acquisition_target_id,
        "generated_at": generated_at, "raw_evidence_hash": wave.parsed.raw_evidence_hash,
        "repository_snapshot_hash": snapshot_hash, "parsed_artifact_id": wave.parsed.id,
        "card_candidate_artifact_id": wave.cards.id,
        "printing_candidate_artifact_id": wave.printings.id,
        "summary": {
            "total_records": len(printing_candidates), "new_cards": len(new_card_ids),
            "reused_existing_cards": len(reused_card_ids),
            "new_printings": len(new_printing_ids), "duplicates": len(duplicates),
            "conflicts": len(conflicts), "rejected_records": len(rejected),
            "expected_card_count_change": len(new_card_ids),
            "expected_printing_count_change": len(new_printing_ids),
        },
        "new_card_ids": new_card_ids, "reused_card_ids": reused_card_ids,
        "new_printing_ids": new_printing_ids, "duplicates": duplicates,
        "conflicts": conflicts, "rejected_records": rejected,
        "repository_counts_before": before, "expected_repository_counts_after": after,
    }
    validate_document(report, "population-review-report")
    return report


def report_is_clean(report: Mapping[str, Any]) -> bool:
    """Return whether a report may proceed to explicit promotion review."""
    return not report["conflicts"] and not report["rejected_records"] and not any(
        finding["reason"].startswith("Printing identifier occurs")
        for finding in report["duplicates"]
    )


def _finding(record_id: str, entity_type: str, entity_id: str, reason: str) -> dict[str, str]:
    return {"record_id": record_id, "entity_type": entity_type,
            "entity_id": entity_id, "reason": reason}


def _finding_key(item: Mapping[str, str]) -> tuple[str, str, str, str]:
    return item["record_id"], item["entity_type"], item["entity_id"], item["reason"]


__all__ = ["build_population_review_report", "report_is_clean"]
