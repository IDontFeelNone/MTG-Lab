"""Deterministic collection snapshots and deck-completion intelligence.

Collection artifacts are downstream user data.  This module only reads canonical
state and never promotes or modifies it.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping

from repository.cards import canonical_repository_bytes, load_card_repository

SCHEMA_VERSION = "collection-import-v1"
SNAPSHOT_VERSION = "collection-snapshot-v1"
DECK_VERSION = "deck-requirement-v1"


class CollectionIntelligenceError(ValueError):
    pass


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value)).hexdigest()


def read_import(path: Path) -> dict:
    """Adapt JSON or CSV to the versioned import contract without resolving it."""
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        value = json.loads(raw)
        if isinstance(value, list):
            value = {"schema_version": SCHEMA_VERSION, "collection_id": "default",
                     "source": {"type": "json", "name": path.name}, "entries": value}
        if not isinstance(value, dict) or not isinstance(value.get("entries"), list):
            raise CollectionIntelligenceError("JSON import must contain an entries array")
        value.setdefault("schema_version", SCHEMA_VERSION)
        value.setdefault("collection_id", "default")
        value.setdefault("source", {"type": "json", "name": path.name})
    elif path.suffix.lower() == ".csv":
        text = raw.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text)))
        value = {"schema_version": SCHEMA_VERSION, "collection_id": "default",
                 "source": {"type": "csv", "name": path.name}, "entries": rows}
    else:
        raise CollectionIntelligenceError("collection import must be .json or .csv")
    if value["schema_version"] != SCHEMA_VERSION:
        raise CollectionIntelligenceError("unsupported collection import schema")
    value["source_import_digest"] = hashlib.sha256(raw).hexdigest()
    return value


class CanonicalCollectionResolver:
    """Read-only, explicit-priority resolver over Cards, Printings and Identifiers."""
    def __init__(self, game: str, data_root: Path = Path("data")):
        self.game, self.data_root = game, Path(data_root)
        root = self.data_root / "canonical" / "games"
        cards, printings = load_card_repository(game, games_root=root)
        self.cards = {x["id"]: dict(x) for x in cards}
        self.printings = {x["id"]: dict(x) for x in printings}
        self.by_name: dict[str, list[str]] = defaultdict(list)
        for printing in printings:
            self.by_name[self.cards[printing["card_id"]]["name"].casefold()].append(printing["id"])
        self.external: dict[tuple[str, str], list[str]] = defaultdict(list)
        for printing in printings:
            self.external[("canonical_printing_id", printing["id"])].append(printing["id"])
            self.external[("set_collector_number", f"{printing.get('set_code')}:{printing.get('collector_number')}")].append(printing["id"])
        state_path = self.data_root / "canonical" / "state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text())
            uuid_to_printing = {}
            for key, record in state.get("printing", {}).items():
                values = record.get("values", {})
                uuid_to_printing[str(values.get("uuid", key))] = key
            for record in state.get("identifier", {}).values():
                values = record.get("values", {})
                target = uuid_to_printing.get(str(values.get("printing_uuid")))
                if target in self.printings:
                    self.external[(str(values.get("namespace", "")).casefold(),
                                   str(values.get("value", "")))].append(target)
        self.canonical_digest = hashlib.sha256(canonical_repository_bytes(game, games_root=root)).hexdigest()

    def resolve(self, imported: Mapping[str, Any]) -> dict:
        results, seen = [], set()
        for number, raw in enumerate(imported["entries"], 1):
            row = _normalize_row(raw, number)
            fingerprint = digest(raw)
            if fingerprint in seen:
                results.append(_result(row, "duplicate_input_row", "identical normalized row already appeared", []))
                continue
            seen.add(fingerprint)
            if row.pop("_invalid", False):
                results.append(_result(row, "invalid", "quantity must be a positive integer", [])); continue
            printing_id = row.get("printing_id")
            if printing_id:
                if printing_id in self.printings:
                    results.append(_result(row, "resolved", "exact canonical printing identifier", [printing_id]))
                else:
                    results.append(_result(row, "unresolved", "canonical printing identifier not found", []))
                continue
            identifiers = row.get("external_identifiers") or {}
            candidates = None
            evidence = []
            for namespace, value in sorted(identifiers.items()):
                matches = set(self.external.get((namespace.casefold(), str(value)), ()))
                evidence.append({"namespace": namespace, "value": value, "matches": sorted(matches)})
                candidates = matches if candidates is None else candidates & matches
            if identifiers:
                matches = sorted(candidates or ())
                reason = "exact external identifier match" if len(matches) == 1 else (
                    "external identifiers match multiple printings" if matches else "external identifiers not found")
                results.append(_result(row, "resolved" if len(matches) == 1 else
                                       "ambiguous" if matches else "unresolved", reason, matches, evidence)); continue
            matches = sorted(self.by_name.get(str(row.get("card_name") or "").casefold(), ()))
            reason = "name fallback matches one printing" if len(matches) == 1 else (
                "name fallback matches multiple printings; review required" if matches else "no usable identity evidence")
            results.append(_result(row, "resolved" if len(matches) == 1 else
                                   "ambiguous" if matches else "unresolved", reason, matches));
        for result in results:
            if result["status"] == "resolved":
                result["card_id"] = self.printings[result["printing_id"]]["card_id"]
        return {"resolution_version": "collection-resolution-v1", "canonical_digest": self.canonical_digest,
                "results": results}


def _normalize_row(raw: Mapping[str, Any], number: int) -> dict:
    if not isinstance(raw, Mapping):
        return {"row_number": number, "quantity": raw, "_invalid": True}
    def optional(name):
        value = raw.get(name)
        return None if value is None or str(value).strip().casefold() in {"", "unknown", "null"} else value
    try:
        quantity = int(str(raw.get("quantity", "")).strip())
        invalid = isinstance(raw.get("quantity"), bool) or quantity < 1 or str(quantity) != str(raw.get("quantity")).strip()
    except (ValueError, TypeError): quantity, invalid = raw.get("quantity"), True
    external = raw.get("external_identifiers") or {}
    if isinstance(external, str):
        try: external = json.loads(external) if external.strip() else {}
        except json.JSONDecodeError: external = {"unparsed": external}
    known = ("printing_id", "card_name", "quantity", "finish", "language", "condition",
             "acquisition_price", "acquisition_date", "storage_location", "notes", "external_identifiers")
    row = {"row_number": number, "printing_id": optional("printing_id"), "external_identifiers": external,
           "card_name": optional("card_name"), "quantity": quantity, "finish": optional("finish"),
           "language": optional("language"), "condition": optional("condition"),
           "acquisition_price": optional("acquisition_price"), "acquisition_date": optional("acquisition_date"),
           "storage_location": optional("storage_location"), "notes": optional("notes"),
           "provenance": raw.get("provenance") or {"source_row": number},
           "unknown_fields": sorted(k for k in known if optional(k) is None)}
    row["_invalid"] = invalid
    if row["acquisition_date"]:
        try: date.fromisoformat(str(row["acquisition_date"]))
        except ValueError: row["_invalid"] = True
    if row["acquisition_price"] is not None:
        try: Decimal(str(row["acquisition_price"]))
        except InvalidOperation: row["_invalid"] = True
    return row


def _result(row, status, reason, candidates, evidence=None):
    result = {"row": row, "status": status, "reason": reason,
              "candidate_printing_ids": candidates, "evidence": evidence or []}
    if status == "resolved": result["printing_id"] = candidates[0]
    return result


def create_snapshot(imported: Mapping[str, Any], resolution: Mapping[str, Any],
                    snapshots_root: Path, snapshot_id: str | None = None) -> dict:
    payload = {"schema_version": SNAPSHOT_VERSION, "collection_id": imported["collection_id"],
               "source_import_digest": imported["source_import_digest"],
               "canonical_digest": resolution["canonical_digest"], "source": imported["source"],
               "resolved_holdings": [x for x in resolution["results"] if x["status"] == "resolved"],
               "unresolved_holdings": [x for x in resolution["results"] if x["status"] != "resolved"]}
    resolved = payload["resolved_holdings"]
    payload["inventory"] = {
        "total_quantity": sum(x["row"]["quantity"] for x in resolved),
        "unique_cards": len({x["card_id"] for x in resolved}),
        "unique_printings": len({x["printing_id"] for x in resolved}),
        "finishes": sorted({x["row"]["finish"] for x in resolved}, key=lambda x: (x is not None, str(x))),
        "languages": sorted({x["row"]["language"] for x in resolved}, key=lambda x: (x is not None, str(x))),
        "conditions": sorted({x["row"]["condition"] for x in resolved}, key=lambda x: (x is not None, str(x))),
        "unresolved_quantity": sum(x["row"]["quantity"] for x in payload["unresolved_holdings"]
                                   if isinstance(x["row"].get("quantity"), int)),
    }
    identity_digest = digest(payload)
    payload["snapshot_id"] = snapshot_id or identity_digest[:24]
    payload["snapshot_digest"] = digest(payload)
    root = Path(snapshots_root); root.mkdir(parents=True, exist_ok=True)
    path = root / f"{payload['snapshot_id']}.json"; content = canonical_json(payload)
    if path.exists():
        if path.read_bytes() != content: raise CollectionIntelligenceError("snapshot identity conflict")
        payload["replay"] = "exact_replay"; return payload
    path.write_bytes(content)
    return payload


def verify_snapshot(path: Path) -> dict:
    value = json.loads(path.read_bytes())
    claimed = value.pop("snapshot_digest", None)
    valid = claimed == digest(value)
    value["snapshot_digest"] = claimed
    return {"valid": valid, "snapshot_id": value.get("snapshot_id"), "snapshot_digest": claimed}


def collection_summary(snapshot: Mapping[str, Any], resolver: CanonicalCollectionResolver) -> dict:
    holdings = snapshot["resolved_holdings"]; quantities = Counter(); cards = Counter()
    finish, language, condition, sets, rarity = (Counter() for _ in range(5)); cost = Decimal("0"); priced = 0
    for item in holdings:
        row, printing = item["row"], resolver.printings[item["printing_id"]]; q = row["quantity"]
        quantities[item["printing_id"]] += q; cards[printing["card_id"]] += q
        for counter, value in ((finish,row["finish"]),(language,row["language"]),(condition,row["condition"]),
                               (sets,printing.get("set_code")),(rarity,printing.get("rarity"))): counter[value or "unknown"] += q
        if row["acquisition_price"] is not None: cost += Decimal(str(row["acquisition_price"])) * q; priced += q
    total = sum(quantities.values())
    return {"schema_version": "collection-summary-v1", "snapshot_id": snapshot["snapshot_id"],
            "total_owned_quantity": total, "unique_cards": len(cards), "unique_printings": len(quantities),
            "duplicate_count": sum(max(0,q-1) for q in quantities.values()),
            "duplicates": [{"printing_id": k, "quantity": q, "duplicate_copies": q-1} for k,q in sorted(quantities.items()) if q>1],
            "finish_distribution": dict(sorted(finish.items())), "language_distribution": dict(sorted(language.items())),
            "condition_distribution": dict(sorted(condition.items())), "set_distribution": dict(sorted(sets.items())),
            "rarity_distribution": dict(sorted(rarity.items())), "color_distribution": {"unknown": total},
            "ambiguous_count": sum(x["status"] == "ambiguous" for x in snapshot["unresolved_holdings"]),
            "unresolved_count": sum(x["status"] == "unresolved" for x in snapshot["unresolved_holdings"]),
            "invalid_count": sum(x["status"] == "invalid" for x in snapshot["unresolved_holdings"]),
            "acquisition_cost": {"known_total": format(cost,"f"), "currency": None,
                                 "known_quantity": priced, "missing_quantity": total-priced},
            "missing_value_coverage": {name: sum(x["row"][name] is None for x in holdings)
                for name in ("finish","language","condition","acquisition_price","acquisition_date","storage_location","notes")}}


def compare_deck(snapshot: Mapping[str, Any], deck: Mapping[str, Any], resolver: CanonicalCollectionResolver) -> dict:
    if deck.get("schema_version") != DECK_VERSION: raise CollectionIntelligenceError("unsupported deck requirement schema")
    by_printing, by_card = Counter(), Counter()
    for item in snapshot["resolved_holdings"]:
        q=item["row"]["quantity"]; pid=item["printing_id"]; by_printing[pid]+=q; by_card[resolver.printings[pid]["card_id"]]+=q
    remaining_printing, remaining_card = by_printing.copy(), by_card.copy()
    results=[]; required_total=owned_total=0
    for req in sorted(deck["requirements"], key=lambda x:(x.get("section","main"),x["card_id"],x.get("printing_id", ""))):
        required=int(req["quantity"]); policy=req.get("acceptable_printing_policy", deck.get("acceptable_printing_policy","any"))
        available=remaining_card[req["card_id"]] if policy=="any" else remaining_printing[req.get("printing_id")]
        used=min(available,required); missing=required-used; required_total+=required; owned_total+=used
        if policy=="any": remaining_card[req["card_id"]]-=used
        else: remaining_printing[req.get("printing_id")]-=used
        total_owned=by_card[req["card_id"]] if policy=="any" else by_printing[req.get("printing_id")]
        results.append({**req,"section":req.get("section","main"),"owned_quantity":used,"required_quantity":required,
                        "missing_quantity":missing,"excess_copies":max(0,total_owned-required),
                        "reusable_owned_copies":max(0,available-used),
                        "status":"complete" if not missing else "partial" if used else "missing"})
    return {"schema_version":"deck-comparison-v1","deck_id":deck["deck_id"],"snapshot_id":snapshot["snapshot_id"],
            "completion_percentage": "100.00" if not required_total else format(Decimal(owned_total*100)/required_total,".2f"),
            "requirements":results,"complete_cards":sum(x["status"]=="complete" for x in results),
            "partially_complete_cards":sum(x["status"]=="partial" for x in results),
            "missing_cards":sum(x["status"]=="missing" for x in results),
            "unresolved_may_affect_result": [x for x in snapshot["unresolved_holdings"] if x["status"] in {"ambiguous","unresolved"}]}


def acquisition_priorities(comparisons: Iterable[Mapping[str, Any]]) -> dict:
    comparisons=list(comparisons); grouped=defaultdict(list)
    for comparison in comparisons:
        for req in comparison["requirements"]:
            if req["missing_quantity"]: grouped[req["card_id"]].append((comparison,req))
    output=[]
    for card_id, entries in grouped.items():
        missing=sum(x[1]["missing_quantity"] for x in entries); shared=len({x[0]["deck_id"] for x in entries})
        partial=sum(x[1]["owned_quantity"]>0 for x in entries); completes=sum(x[1]["owned_quantity"]>0 and x[1]["missing_quantity"]>0 for x in entries)
        unlock=sum(Decimal(x[1]["missing_quantity"]*100)/sum(r["required_quantity"] for r in x[0]["requirements"]) for x in entries)
        uncertainty=sum(bool(x[0]["unresolved_may_affect_result"]) for x in entries)
        components={"missing_copy_points":missing,"completion_unlock_points":format(unlock,".2f"),
                    "shared_deck_points":shared*10,"partial_ownership_points":partial*5,
                    "playset_completion_points":completes*3,"uncertainty_penalty":uncertainty*2}
        score=Decimal(missing)+unlock+shared*10+partial*5+completes*3-uncertainty*2
        output.append({"card_id":card_id,"score":format(score,".2f"),"components":components,
                       "explanation":"missing copies + completion unlocked + shared decks + partial/playset bonuses - unresolved-evidence penalty"})
    output.sort(key=lambda x:(-Decimal(x["score"]),x["card_id"]))
    return {"schema_version":"acquisition-priorities-v1","price_independent":True,"priorities":output}
