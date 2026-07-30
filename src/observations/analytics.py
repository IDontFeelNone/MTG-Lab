"""Descriptive analytics over verified observations and a single market snapshot."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from typing import Any, Iterable, Mapping


def summarize_observations(raw_packs: Iterable[Mapping[str, Any]],
                           verifications: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Return deterministic composition and verification counts without market data."""
    packs = list(raw_packs)
    verified_by_id = {item["observation_id"]: item for item in verifications}
    names: Counter[str] = Counter()
    treatments: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    for pack in packs:
        verification = verified_by_id[pack["observation_id"]]
        for card in pack["cards"]:
            names[normalize_key(card["reported_name"])] += 1
            treatments[card.get("reported_treatment") or "standard_or_unreported"] += 1
        statuses.update(card["verification_status"] for card in verification["cards"])
    return {
        "schema_version": "v1",
        "pack_count": len(packs),
        "card_count": sum(len(pack["cards"]) for pack in packs),
        "verification_statuses": dict(sorted(statuses.items())),
        "duplicates": [
            {"normalized_name": name, "count": count}
            for name, count in sorted(names.items()) if count > 1
        ],
        "treatments": dict(sorted(treatments.items())),
        "methodology": (
            "Descriptive summary of reported contents; no prices, probabilities, "
            "slot rules, or collation are inferred."
        ),
    }


def analyze_box(raw_packs: Iterable[Mapping[str, Any]], verifications: Iterable[Mapping[str, Any]],
                snapshot: Mapping[str, Any]) -> dict[str, Any]:
    """Return observed (not predicted) EV and composition summaries."""
    packs = list(raw_packs)
    verified_by_id = {item["observation_id"]: item for item in verifications}
    prices = {key: Decimal(value) for key, value in snapshot["prices"].items()}
    names: Counter[str] = Counter()
    treatments: Counter[str] = Counter()
    pack_values = []
    missing: set[str] = set()
    for pack in packs:
        verification = verified_by_id[pack["observation_id"]]
        by_position = {card["position"]: card for card in verification["cards"]}
        value = Decimal("0")
        for card in pack["cards"]:
            names[normalize_key(card["reported_name"])] += 1
            treatments[card.get("reported_treatment") or "standard_or_unreported"] += 1
            verified = by_position[card["position"]]
            identifier = verified.get("canonical_printing_id") or verified.get("canonical_card_id")
            if identifier in prices:
                value += prices[identifier]
            elif identifier:
                missing.add(identifier)
        pack_values.append({"observation_id": pack["observation_id"], "value": _money(value)})
    total = sum((Decimal(item["value"]) for item in pack_values), Decimal("0"))
    return {
        "snapshot_id": snapshot["snapshot_id"], "captured_on": snapshot["captured_on"],
        "currency": snapshot["currency"], "pack_ev": pack_values,
        "box_ev": _money(total),
        "average_observed_pack_ev": _money(total / len(packs)) if packs else "0.00",
        "duplicates": [{"normalized_name": name, "count": count} for name, count in sorted(names.items()) if count > 1],
        "treatments": dict(sorted(treatments.items())), "missing_price_ids": sorted(missing),
        "methodology": "Observed contents valued at one dated snapshot; this is not predictive expected value.",
    }


def normalize_key(value: str) -> str:
    from .verification import normalize_card_name
    return normalize_card_name(value)


def _money(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")
