"""Non-retaining TopDeck.gg response projection for Phase 147.

The module is deliberately transport-free: callers may supply transient decoded API
responses, but this code cannot download or publish provider data.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Sequence

from .deck_usage import PILOT_NAMES

API_ORIGIN = "https://topdeck.gg"
TOURNAMENTS_ENDPOINT = f"{API_ORIGIN}/api/v2/tournaments"
AUTHORIZATION_ENV = "TOPDECK_API_KEY"


class TopDeckProbeError(ValueError):
    """A provider record cannot safely be projected."""


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, separators=(",", ":"),
                       sort_keys=True) + "\n").encode()


def authorization_header(api_key: str) -> dict[str, str]:
    """Build the documented header without ever embedding the secret in a URL."""
    if not isinstance(api_key, str) or not api_key.strip() or any(c.isspace() for c in api_key):
        raise TopDeckProbeError(f"a non-whitespace {AUTHORIZATION_ENV} value is required")
    return {"Authorization": api_key, "Content-Type": "application/json"}


def safe_request_descriptor(body: Mapping[str, Any]) -> dict[str, Any]:
    """Return diagnostics safe for logs and commits (headers are intentionally absent)."""
    return {"method": "POST", "endpoint": TOURNAMENTS_ENDPOINT,
            "body_sha256": hashlib.sha256(canonical_bytes(body)).hexdigest()}


def _integer(value: Any, field: str, *, minimum: int = 0) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise TopDeckProbeError(f"malformed {field}")
    return value


def _cards(value: Any, board: str) -> dict[str, int]:
    if value is None:
        return {}
    entries = value.items() if isinstance(value, dict) else enumerate(value) if isinstance(value, list) else None
    if entries is None:
        raise TopDeckProbeError(f"malformed {board}")
    result: dict[str, int] = {}
    for key, raw in entries:
        if isinstance(raw, dict):
            name = raw.get("name") or raw.get("cardName")
            count = raw.get("count", raw.get("quantity"))
        elif isinstance(value, dict):
            name, count = key, raw
        else:
            raise TopDeckProbeError(f"malformed {board} card")
        if not isinstance(name, str) or not name.strip():
            raise TopDeckProbeError(f"malformed {board} card name")
        count = _integer(count, f"{board} count", minimum=1)
        if name in result:
            raise TopDeckProbeError(f"duplicate {board} card name")
        result[name] = count
    return result


def project_tournaments(payload: Any, pilot_cards: Mapping[str, str]) -> list[dict[str, Any]]:
    """Project only pilot-card evidence; discard all player/account fields.

    ``payload`` is used transiently. Returned rows use tournament/deck-level identities,
    never names, emails, usernames, Discord handles, or provider account identifiers.
    """
    if tuple(sorted(pilot_cards)) != tuple(sorted(PILOT_NAMES)) or len(set(pilot_cards.values())) != 10:
        raise TopDeckProbeError("pilot scope must be the exact ten Cards with unique identities")
    tournaments = payload.get("data", payload) if isinstance(payload, dict) else payload
    if not isinstance(tournaments, list):
        raise TopDeckProbeError("provider response must be a tournament array")
    rows: list[dict[str, Any]] = []
    seen_decks: dict[tuple[str, str], bytes] = {}
    for tournament in tournaments:
        if not isinstance(tournament, dict):
            raise TopDeckProbeError("malformed tournament record")
        tid = tournament.get("TID")
        event_date = tournament.get("startDate")
        event_format = tournament.get("format")
        standings = tournament.get("standings")
        if not all(isinstance(v, str) and v for v in (tid, event_date, event_format)):
            raise TopDeckProbeError("tournament requires TID, startDate, and format")
        if not isinstance(standings, list):
            raise TopDeckProbeError("tournament standings must be an array")
        event_size = _integer(tournament.get("participantCount", len(standings)),
                              "participantCount", minimum=1)
        for standing in standings:
            if not isinstance(standing, dict):
                raise TopDeckProbeError("malformed standing")
            placement = _integer(standing.get("standing"), "standing", minimum=1)
            deck = standing.get("deckObj")
            if deck is None:
                continue
            if not isinstance(deck, dict):
                raise TopDeckProbeError("malformed deckObj")
            main = _cards(deck.get("mainboard", deck.get("mainBoard")), "mainboard")
            side = _cards(deck.get("sideboard", deck.get("sideBoard")), "sideboard")
            deck_native = standing.get("deckId")
            if deck_native is not None and (not isinstance(deck_native, str) or not deck_native):
                raise TopDeckProbeError("malformed deckId")
            deck_identity = deck_native or hashlib.sha256(canonical_bytes(
                {"TID": tid, "standing": placement, "mainboard": main, "sideboard": side}
            )).hexdigest()
            replay = canonical_bytes({"placement": placement, "main": main, "side": side,
                                      "wins": standing.get("wins"), "draws": standing.get("draws"),
                                      "losses": standing.get("losses")})
            key = (tid, deck_identity)
            if key in seen_decks:
                if seen_decks[key] != replay:
                    raise TopDeckProbeError("conflicting tournament/deck replay")
                raise TopDeckProbeError("duplicate tournament/deck identity")
            seen_decks[key] = replay
            for name in PILOT_NAMES:
                if name not in main and name not in side:
                    continue
                rows.append({
                    "card_id": pilot_cards[name], "card_name": name, "tournament_id": tid,
                    "deck_identity": deck_identity, "event_date": event_date,
                    "format": event_format, "event_size": event_size,
                    "placement": placement, "wins": _integer(standing.get("wins"), "wins"),
                    "draws": _integer(standing.get("draws"), "draws"),
                    "losses": _integer(standing.get("losses"), "losses"),
                    "mainboard_count": main.get(name, 0), "sideboard_count": side.get(name, 0),
                    "rounds_available": isinstance(tournament.get("rounds"), list),
                })
    return sorted(rows, key=lambda r: (r["tournament_id"], r["deck_identity"], r["card_id"]))


def competitive_metrics(rows: Sequence[Mapping[str, Any]], *, event_format: str) -> dict[str, dict[str, int]]:
    """Compute literal metrics for one exact provider format; never a score."""
    filtered = [r for r in rows if r["format"] == event_format]
    result: dict[str, dict[str, int]] = {}
    for name in PILOT_NAMES:
        card_rows = [r for r in filtered if r["card_name"] == name]
        decks = {(r["tournament_id"], r["deck_identity"]) for r in card_rows}
        result[name] = {
            "retained_tournament_deck_count": len(decks),
            "retained_tournament_count": len({r["tournament_id"] for r in card_rows}),
            "retained_copies_main_deck": sum(r["mainboard_count"] for r in card_rows),
            "retained_copies_sideboard": sum(r["sideboard_count"] for r in card_rows),
            "top_8_count": sum(r["placement"] is not None and r["placement"] <= 8 for r in card_rows),
            "top_16_count": sum(r["placement"] is not None and r["placement"] <= 16 for r in card_rows),
            "first_place_count": sum(r["placement"] == 1 for r in card_rows),
            "aggregate_wins": sum(r["wins"] or 0 for r in card_rows),
            "aggregate_draws": sum(r["draws"] or 0 for r in card_rows),
            "aggregate_losses": sum(r["losses"] or 0 for r in card_rows),
        }
    return result


__all__ = ["AUTHORIZATION_ENV", "TOURNAMENTS_ENDPOINT", "TopDeckProbeError",
           "authorization_header", "canonical_bytes", "competitive_metrics",
           "project_tournaments", "safe_request_descriptor"]
