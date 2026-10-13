"""Bounded Card acquisition projection over existing canonical and Decision contracts.

This adapter validates supplied evidence; it does not acquire offers, infer
strategic suitability, approve role candidates, or execute a purchase.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, Mapping

from decision_intelligence import (AcquisitionDecisionOrchestrator, AnalysisMetric,
    DecisionAlternative, DecisionPolicy, DecisionRequest, DomainAnalysisEnvelope,
    EvidenceReference, MetricCriterion, recommendation_reasoning_context)
from decision_intelligence.models import freeze, thaw, identity as decision_identity

from .mechanics import MechanicalCardIntelligence, content_identity, stable_json


INPUT_VERSION = "card-acquisition-input-v1"
DOSSIER_VERSION = "card-acquisition-dossier-v1"
RECONSTRUCTION_VERSION = "card-acquisition-reconstruction-v1"
_PINNED_SCOPE = "Read-only projections of the existing canonical query snapshot and referenced mechanical dossiers."
MAXIMUM_BYTES = 65536
MAXIMUM_MONEY_SCALE = 6
MAXIMUM_OFFER_AGE_SECONDS = 2592000
_MONEY = re.compile(r"(?:0|[1-9][0-9]{0,11})(?:\.[0-9]{1,6})?\Z")
_COSTS = ("unit_price", "shipping", "taxes", "fees", "discounts")
_REQUIREMENTS = ("card_id", "printing_id", "acceptable_printing_ids",
                 "desired_quantity", "preferred_dimensions")
_CONSTRAINTS = frozenset({"condition", "allowed_seller_ids"})
_UNKNOWN_TEXT = frozenset({"unknown", "null", "incomplete", "unsupported", "unresolved", "missing"})


class CardAcquisitionError(ValueError):
    """An input or result cannot preserve the bounded acquisition contract."""


def _known_text(value: Any) -> bool:
    """Exact unknown sentinels cannot supply a decision-critical known value."""
    return isinstance(value, str) and bool(value.strip()) and value.strip().casefold() not in _UNKNOWN_TEXT


def _time(value: Any) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", value):
        raise CardAcquisitionError("an explicit UTC timestamp is required")
    try:
        return datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise CardAcquisitionError("invalid UTC timestamp") from error


def _integer(value: Any, *, positive: bool = False) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < int(positive):
        raise CardAcquisitionError("a nonnegative integer is required")
    return value


def _units(value: Any, scale: int) -> int:
    """Decimal parsing plus integer arithmetic; no float or context rounding."""
    if not isinstance(value, str) or not _MONEY.fullmatch(value):
        raise CardAcquisitionError("money requires a bounded nonnegative decimal string")
    number = Decimal(value)
    digits = -number.as_tuple().exponent
    if digits > scale:
        raise CardAcquisitionError("money exceeds the declared currency precision")
    whole, _, fraction = value.partition(".")
    return int(whole) * 10 ** scale + int((fraction + "0" * scale)[:scale] or "0")


def _amount(units: int, scale: int) -> str:
    if not scale:
        return str(units)
    sign = "-" if units < 0 else ""
    whole, fraction = divmod(abs(units), 10 ** scale)
    return f"{sign}{whole}.{fraction:0{scale}d}"


def _pointer(document: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise CardAcquisitionError("a non-root JSON source pointer is required")
    try:
        for part in pointer[1:].split("/"):
            part = part.replace("~1", "/").replace("~0", "~")
            document = document[int(part)] if isinstance(document, list) else document[part]
        return document
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise CardAcquisitionError("source pointer is absent") from error


@dataclass(frozen=True)
class CardAcquisitionInput:
    payload: Mapping[str, Any]

    def __post_init__(self):
        document = thaw(freeze(self.payload))
        if not isinstance(document, dict):
            raise CardAcquisitionError("acquisition input must be an object")
        if document.get("schema_version") != INPUT_VERSION or document.get("mode") not in {
                "synthetic_demonstration", "real_world"}:
            raise CardAcquisitionError("unsupported acquisition input schema/mode")
        _time(document.get("as_of"))
        candidates = document.get("candidates", [])
        if not isinstance(candidates, list) or not 2 <= len(candidates) <= 3:
            raise CardAcquisitionError("two or three Card acquisition candidates required")
        if any(not isinstance(c, dict) for c in candidates):
            raise CardAcquisitionError("candidate objects required")
        if any(not isinstance(c.get(k), str) or not c[k] for c in candidates for k in ("card_id", "printing_id")):
            raise CardAcquisitionError("candidate exact identity strings required")
        if any(not isinstance(c.get("acceptable_printing_ids"), list) or
               any(not isinstance(i, str) or not i for i in c["acceptable_printing_ids"]) for c in candidates):
            raise CardAcquisitionError("acceptable Printing identities must be an array of strings")
        sources = document.get("sources", [])
        if not isinstance(sources, list) or any(not isinstance(s, dict) for s in sources):
            raise CardAcquisitionError("retained sources must be an array of objects")
        if len({c.get("card_id") for c in candidates}) != len(candidates) or \
                len({c.get("printing_id") for c in candidates}) != len(candidates):
            raise CardAcquisitionError("duplicate acquisition Card or Printing identity")
        if len(stable_json(document).encode("utf-8")) > MAXIMUM_BYTES:
            raise CardAcquisitionError("acquisition input exceeds its byte bound")
        object.__setattr__(self, "payload", freeze(document))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    @property
    def input_id(self) -> str:
        return content_identity(self.to_dict())


@dataclass(frozen=True)
class CardAcquisitionDossier:
    payload: Mapping[str, Any]

    def __post_init__(self):
        document = thaw(freeze(self.payload))
        if not isinstance(document, dict):
            raise CardAcquisitionError("acquisition dossier must be an object")
        body = {k: v for k, v in document.items() if k != "dossier_id"}
        if document.get("schema_version") != DOSSIER_VERSION or \
                document.get("dossier_id") != content_identity(body):
            raise CardAcquisitionError("acquisition dossier content identity/schema mismatch")
        if len(stable_json(document).encode("utf-8")) > MAXIMUM_BYTES:
            raise CardAcquisitionError("acquisition dossier exceeds its byte bound")
        # An outer hash only detects accidental edits. Reconstruct the domain
        # projection from its original input and retained bytes, then let the
        # existing Decision orchestrator reproduce the complete recommendation.
        try:
            proof = document.get("reconstruction")
            if not isinstance(proof, dict) or set(proof) != {
                    "schema_version", "input_packet", "decision_request", "analyses", "analysis_shared", "sources", "canonical"} or \
                    proof.get("schema_version") != RECONSTRUCTION_VERSION:
                raise CardAcquisitionError("original acquisition reconstruction proof is required")
            packet = CardAcquisitionInput(proof["input_packet"])
            if packet.input_id != document.get("input_id"):
                raise CardAcquisitionError("original acquisition input identity mismatch")
            adapter = CardAcquisitionAdapter._from_pinned_canonical(proof["canonical"], packet)
            sources, evidence, blockers, snapshots = adapter._sources(packet.to_dict(),
                Path("/__card_acquisition_source_root__"), snapshots=proof["sources"])
            replay, request, analyses = adapter._evaluate_bound(packet, sources, evidence, blockers)
            shared, serialized = adapter._serialize_analyses(analyses)
            if stable_json(proof["sources"]) != stable_json(snapshots) or \
                    stable_json(proof["decision_request"]) != stable_json(request.to_dict()) or \
                    stable_json(proof["analysis_shared"]) != stable_json(shared) or \
                    stable_json(proof["analyses"]) != stable_json(serialized) or \
                    stable_json({k: v for k, v in body.items() if k != "reconstruction"}) != stable_json(replay):
                raise CardAcquisitionError("acquisition reconstruction or Decision replay mismatch")
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            if isinstance(error, CardAcquisitionError):
                raise
            raise CardAcquisitionError("invalid acquisition reconstruction proof") from error
        mode = document.get("mode")
        decision = document.get("decision", {})
        if not isinstance(decision, dict) or not isinstance(document.get("policy"), dict):
            raise CardAcquisitionError("decision and policy objects required")
        recommendation = decision.get("recommendation", {})
        if not isinstance(recommendation, dict):
            raise CardAcquisitionError("existing recommendation object required")
        rbody = {k: v for k, v in recommendation.items() if k != "recommendation_id"}
        if mode not in {"synthetic_demonstration", "real_world"} or \
                recommendation.get("recommendation_id") != decision_identity("recommendation-sha256:", rbody) or \
                recommendation.get("request_id") != document.get("decision_request_id") or \
                recommendation.get("policy") != {"policy_id": document.get("policy", {}).get("policy_id"),
                    "policy_version": document.get("policy", {}).get("version")} or \
                document.get("canonical_snapshot_id") not in recommendation.get("input_snapshot_ids", []) or \
                document.get("input_id") not in recommendation.get("input_snapshot_ids", []):
            raise CardAcquisitionError("nested decision identity or snapshot binding mismatch")
        rows = document.get("candidates", [])
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise CardAcquisitionError("dossier candidate objects required")
        ids = [r.get("printing_id") for r in rows]
        if not 2 <= len(rows) <= 3 or len(set(ids)) != len(ids):
            raise CardAcquisitionError("dossier requires distinct candidate Printings")
        selected = recommendation.get("selected_alternative_id")
        if recommendation.get("outcome") == "selected":
            chosen = next((r for r in rows if r["printing_id"] == selected), None)
            if document.get("blockers") or chosen is None or chosen.get("acquisition_eligible") is not True or \
                    not isinstance(chosen.get("missing_quantity"), int) or chosen["missing_quantity"] < 1 or \
                    chosen.get("exclusion_reasons") or not isinstance(chosen.get("complete_cost_units"), int) or \
                    not isinstance(chosen.get("remaining_budget"), str) or \
                    not _MONEY.fullmatch(chosen["remaining_budget"]) or Decimal(chosen["remaining_budget"]) < 0:
                raise CardAcquisitionError("selected acquisition contradicts the domain eligibility boundary")
        elif recommendation.get("outcome") != "abstain" or selected is not None or not recommendation.get("abstention_reasons"):
            raise CardAcquisitionError("invalid acquisition abstention")
        if document.get("actual_purchase_advice") != (mode == "real_world" and selected is not None) or \
                document.get("review") != {"status": "requires_review", "canonical_admission": False,
                    "role_approval": False, "purchase_executed": False}:
            raise CardAcquisitionError("acquisition mode or non-admission boundary changed")
        object.__setattr__(self, "payload", freeze(document))

    def to_dict(self) -> dict[str, Any]:
        return thaw(self.payload)

    def to_json(self) -> str:
        return stable_json(self.to_dict())

    def reasoning_context(self) -> dict[str, Any]:
        context = {"schema_version": "card-acquisition-reasoning-context-v1",
            "instruction": "Explain only this deterministic result. Synthetic inputs are demonstrations, not actual purchase advice. Do not infer competitive strength or approve pending roles.",
            "dossier": self.to_dict(),
            "omissions": {"full_source_bytes": "Supplied acquisition source bytes are pinned in reconstruction; canonical mechanical source bytes remain retained by references and digests.",
                "historical_prices": "not current executable offers",
                "pending_role_payloads": "not approved eligibility evidence",
                "competitive_rankings_and_forecasts": "unsupported"}}
        context["context_id"] = content_identity(context)
        if len(stable_json(context).encode("utf-8")) > MAXIMUM_BYTES:
            raise CardAcquisitionError("acquisition reasoning context exceeds its byte bound")
        return context


class CardAcquisitionAdapter:
    """Generic source-bound domain adapter; existing engine owns ordered policy."""

    def __init__(self, data_root: Path):
        self.mechanical = MechanicalCardIntelligence(Path(data_root))
        self.query = self.mechanical.query
        self.printings = {p.canonical_identity: p for p in self.query.entities(entity_type="printing")
            if p.canonical_values.get("uuid") == p.canonical_identity and p.supersession_state == "current"}
        self.policy = self._policy()

    @staticmethod
    def _policy() -> DecisionPolicy:
        return DecisionPolicy("collection-aware-card-acquisition", "1.0.0", (
            MetricCriterion("acquisition_eligible", "maximize"),
            MetricCriterion("declared_priority", "minimize"),
            MetricCriterion("complete_cost_units", "minimize")))

    @staticmethod
    def _printing_provenance(printing: Any) -> dict[str, Any]:
        lineage = printing.provenance_summary
        return {"source_ids": lineage.get("source_ids", []),
            "evidence_ids": [e.get("id") for e in lineage.get("evidence_assertions", [])],
            "promotion_references": [{"promotion_id": audit.get("promotion_id"),
                "audit_reference": audit.get("audit_reference"), "entity_binding": audit.get("entity_binding")}
                for audit in lineage.get("promotion_history", [])]}

    def _pinned_canonical(self, packet: CardAcquisitionInput) -> dict[str, Any]:
        p = packet.to_dict()
        ids = {c["printing_id"] for c in p["candidates"]} | {
            i for c in p["candidates"] for i in c["acceptable_printing_ids"]}
        cards = {}
        for candidate in p["candidates"]:
            card_id = candidate["card_id"]
            dossier = self.mechanical.dossier(card_id).to_dict()
            cards[card_id] = {key: dossier[key] for key in ("dossier_id", "card_identity", "source")}
        return {"scope": _PINNED_SCOPE, "snapshot_id": self.mechanical.snapshot_id, "cards": cards,
            "printings": {pid: {"canonical_values": thaw(freeze(self.printings[pid].canonical_values)),
                "provenance": self._printing_provenance(self.printings[pid])}
                for pid in sorted(ids) if pid in self.printings}}

    @classmethod
    def _from_pinned_canonical(cls, canonical: Any, packet: CardAcquisitionInput) -> CardAcquisitionAdapter:
        if not isinstance(canonical, dict) or set(canonical) != {"scope", "snapshot_id", "cards", "printings"} or \
                canonical["scope"] != _PINNED_SCOPE or \
                not isinstance(canonical["cards"], dict) or not isinstance(canonical["printings"], dict):
            raise CardAcquisitionError("pinned canonical acquisition scope is required")
        p = packet.to_dict()
        if set(canonical["cards"]) != {c["card_id"] for c in p["candidates"]}:
            raise CardAcquisitionError("pinned canonical Card scope mismatch")
        needed = {c["printing_id"] for c in p["candidates"]} | {
            i for c in p["candidates"] for i in c["acceptable_printing_ids"]}
        if set(canonical["printings"]) - needed:
            raise CardAcquisitionError("pinned canonical Printing scope mismatch")
        adapter = cls.__new__(cls)
        cards = canonical["cards"]
        for card_id, dossier in cards.items():
            if not isinstance(dossier, dict) or set(dossier) != {"dossier_id", "card_identity", "source"} or \
                    not isinstance(dossier["card_identity"], dict) or \
                    dossier["card_identity"].get("card_id") != card_id:
                raise CardAcquisitionError("pinned canonical mechanical Card binding mismatch")
            cls._mechanical_source_status(dossier["source"], card_id)
        adapter.mechanical = SimpleNamespace(snapshot_id=canonical["snapshot_id"], cards=cards,
            dossier=lambda card_id: SimpleNamespace(to_dict=lambda: thaw(freeze(cards[card_id]))))
        adapter.printings = {}
        for pid, printing in canonical["printings"].items():
            if not isinstance(printing, dict) or set(printing) != {"canonical_values", "provenance"} or \
                    printing["canonical_values"].get("uuid") != pid:
                raise CardAcquisitionError("pinned canonical exact Printing binding mismatch")
            lineage = printing["provenance"]
            if not isinstance(lineage, dict) or set(lineage) != {"source_ids", "evidence_ids", "promotion_references"}:
                raise CardAcquisitionError("pinned canonical Printing provenance mismatch")
            adapter.printings[pid] = SimpleNamespace(canonical_values=printing["canonical_values"],
                provenance_summary={"source_ids": lineage["source_ids"],
                    "evidence_assertions": [{"id": eid} for eid in lineage["evidence_ids"]],
                    "promotion_history": lineage["promotion_references"]})
        adapter.policy = cls._policy()
        return adapter

    @staticmethod
    def _serialize_analyses(analyses: list[DomainAnalysisEnvelope]) -> tuple[dict, list]:
        """Losslessly share identical contract fields within the byte bound.

        Each original Decision analysis is exactly {**shared, **item}; neither
        metrics nor evidence are dropped or replaced by asserted summary hashes.
        """
        documents = [analysis.to_dict() for analysis in analyses]
        shared = {key: value for key, value in documents[0].items()
            if all(stable_json(document[key]) == stable_json(value) for document in documents[1:])}
        return shared, [{key: value for key, value in document.items() if key not in shared}
            for document in documents]

    def _sources(self, packet: dict[str, Any], root: Path, *, snapshots: Any = None) -> tuple[dict, list, list, list]:
        sources, evidence, blockers, retained = {}, [], [], []
        entries = packet.get("sources", [])
        ids = [x.get("source_id") for x in entries]
        if any(not isinstance(x, str) or not x for x in ids) or len(ids) != len(set(ids)):
            raise CardAcquisitionError("source evidence identities must be unique and nonempty")
        pinned = None
        if snapshots is not None:
            if not isinstance(snapshots, list) or any(not isinstance(s, dict) or
                    set(s) not in ({"source_id", "source_text"}, {"source_id", "unavailable_reason"}) for s in snapshots):
                raise CardAcquisitionError("pinned retained source bytes are required")
            pinned = {s["source_id"]: s for s in snapshots}
            if len(pinned) != len(snapshots) or set(pinned) != set(ids):
                raise CardAcquisitionError("pinned retained source scope mismatch")
        for entry in entries:
            sid = entry["source_id"]
            snapshot = {"source_id": sid}
            try:
                relative = Path(entry["relative_path"])
                path = (root / relative).resolve()
                if relative.is_absolute() or not path.is_relative_to(root):
                    raise CardAcquisitionError("source locator escapes retained source root")
                if pinned is None:
                    raw = path.read_bytes()
                    snapshot["source_text"] = raw.decode("utf-8")
                elif "unavailable_reason" in pinned[sid]:
                    reason = pinned[sid]["unavailable_reason"]
                    if not isinstance(reason, str) or not reason:
                        raise CardAcquisitionError("pinned unavailable source reason is required")
                    raise CardAcquisitionError(reason)
                else:
                    source_text = pinned[sid]["source_text"]
                    if not isinstance(source_text, str):
                        raise CardAcquisitionError("pinned retained source text must be a string")
                    raw = source_text.encode("utf-8")
                    snapshot["source_text"] = source_text
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                if digest != entry["content_digest"]:
                    raise CardAcquisitionError("retained source byte digest mismatch")
                source = json.loads(raw)
                if not isinstance(source, dict):
                    raise CardAcquisitionError("retained source JSON must be an object")
                for field in ("mode", "kind", "provider_identity", "seller_identity", "captured_at"):
                    expected = packet["mode"] if field == "mode" else entry[field]
                    if source.get(field) != expected:
                        raise CardAcquisitionError("source metadata or mode binding mismatch")
                if _time(entry["captured_at"]) > _time(packet["as_of"]):
                    raise CardAcquisitionError("source capture occurs after evaluation")
                if not _known_text(entry["provider_identity"]):
                    raise CardAcquisitionError("provider identity is required")
                review = entry.get("review", {})
                if not isinstance(review, dict):
                    raise CardAcquisitionError("source review must be an object")
                if packet["mode"] == "synthetic_demonstration":
                    if entry["kind"] != "synthetic_fixture" or review.get("status") != "not_applicable":
                        raise CardAcquisitionError("synthetic source must be explicitly labeled")
                else:
                    if entry["kind"] not in {"buyer_declaration", "reviewed_offer", "objective_eligibility_review"}:
                        raise CardAcquisitionError("real inputs cannot use synthetic or historical price sources")
                    if review.get("status") != "reviewed" or review.get("content_digest") != digest or \
                            not _known_text(review.get("reviewer")) or \
                            not _time(entry["captured_at"]) <= _time(review.get("reviewed_at")) <= _time(packet["as_of"]):
                        raise CardAcquisitionError("real acquisition source requires scoped human review")
                sources[sid] = (entry, source)
                evidence.append(EvidenceReference(sid, entry["provider_identity"], digest,
                    entry["captured_at"], entry["relative_path"]))
            except (OSError, KeyError, TypeError, ValueError) as error:
                if "source_text" not in snapshot:
                    snapshot["unavailable_reason"] = str(error)
                blockers.append(f"source:{sid}:{error}")
            retained.append(snapshot)
        return sources, evidence, blockers, retained

    @staticmethod
    def _bound(wrapper: Any, sources: dict, *, mode: str, kinds: set[str]) -> Any:
        if not isinstance(wrapper, dict) or wrapper.get("value") is None:
            raise CardAcquisitionError("required supplied evidence is missing")
        if not isinstance(wrapper["value"], dict):
            raise CardAcquisitionError("supplied evidence value must be an object")
        binding = wrapper.get("binding")
        if not isinstance(binding, dict) or binding.get("source_id") not in sources:
            raise CardAcquisitionError("whole-object source binding is missing")
        entry, source = sources[binding["source_id"]]
        if mode == "real_world" and entry["kind"] not in kinds:
            raise CardAcquisitionError("source kind cannot establish this input")
        if stable_json(_pointer(source, binding.get("pointer"))) != stable_json(wrapper["value"]):
            raise CardAcquisitionError("payload differs from retained source evidence")
        return wrapper["value"]

    def evaluate(self, value: Mapping[str, Any] | CardAcquisitionInput, *, source_root: Path) -> CardAcquisitionDossier:
        packet = value if isinstance(value, CardAcquisitionInput) else CardAcquisitionInput(value)
        p = packet.to_dict()
        root = Path(source_root).resolve()
        sources, evidence, blockers, snapshots = self._sources(p, root)
        body, request, analyses = self._evaluate_bound(packet, sources, evidence, blockers)
        shared, serialized = self._serialize_analyses(analyses)
        body["reconstruction"] = {"schema_version": RECONSTRUCTION_VERSION,
            "input_packet": packet.to_dict(), "decision_request": request.to_dict(),
            "analyses": serialized, "analysis_shared": shared, "sources": snapshots,
            "canonical": self._pinned_canonical(packet)}
        return CardAcquisitionDossier({**body, "dossier_id": content_identity(body)})

    def _evaluate_bound(self, packet: CardAcquisitionInput, sources: dict, evidence: list,
                        blockers: list) -> tuple[dict[str, Any], DecisionRequest, list[DomainAnalysisEnvelope]]:
        p = packet.to_dict()
        if p.get("canonical_snapshot_id") != self.mechanical.snapshot_id:
            blockers.append("canonical_snapshot_mismatch")
        mode, now = p["mode"], _time(p["as_of"])
        context, ownership, scale, budget = {}, {}, None, None
        try:
            context = self._bound(p.get("context"), sources, mode=mode, kinds={"buyer_declaration"})
            if not isinstance(context, dict) or not _known_text(context.get("objective")):
                raise CardAcquisitionError("declared objective is missing")
            if not _known_text(context.get("objective_id")):
                raise CardAcquisitionError("objective identity is missing")
            currency = context.get("currency")
            if not isinstance(currency, str) or not re.fullmatch(r"[A-Z]{3}", currency):
                raise CardAcquisitionError("explicit uppercase currency is required")
            scale = _integer(context.get("money_scale"))
            if scale > MAXIMUM_MONEY_SCALE:
                raise CardAcquisitionError("unsupported currency precision")
            budget = _units(context.get("budget"), scale)
            buyer = context.get("buyer_context", {})
            if not isinstance(buyer, dict):
                raise CardAcquisitionError("buyer context must be an object")
            for field in ("buyer_id", "destination_country", "postal_code", "purchase_method", "discount_basis"):
                if not _known_text(buyer.get(field)):
                    raise CardAcquisitionError(f"actual or explicitly synthetic buyer {field} required")
            if buyer.get("order_assumption") != "one_copy_independent_order":
                raise CardAcquisitionError("only a complete independent one-copy order is supported")
            hard = context.get("hard_constraints", {})
            if not isinstance(hard, dict) or set(hard) - _CONSTRAINTS:
                raise CardAcquisitionError("unsupported hard constraint")
            if not _known_text(hard.get("condition")):
                raise CardAcquisitionError("exact acceptable physical condition is required")
            if "allowed_seller_ids" in hard and (not isinstance(hard["allowed_seller_ids"], list) or
                    not hard["allowed_seller_ids"] or any(not isinstance(x, str) or not x for x in hard["allowed_seller_ids"])):
                raise CardAcquisitionError("explicit nonempty allowed seller identities required")
            if not isinstance(context.get("eligibility_required"), bool):
                raise CardAcquisitionError("objective eligibility requirement must be explicit")
            if not isinstance(context.get("freshness_policy"), dict):
                raise CardAcquisitionError("freshness policy must be an object")
            age = _integer(context["freshness_policy"].get("max_age_seconds"), positive=True)
            if age > MAXIMUM_OFFER_AGE_SECONDS:
                raise CardAcquisitionError("freshness window exceeds this bounded offer contract")
            priorities = context.get("priority_order")
            selected = [c["printing_id"] for c in p["candidates"]]
            if not isinstance(priorities, list) or len(priorities) != len(set(priorities)) or set(priorities) != set(selected):
                raise CardAcquisitionError("explicit complete user priority order is required")
        except (KeyError, TypeError, ValueError) as error:
            blockers.append(f"context:{error}")
        scope = {i for c in p["candidates"] for i in c.get("acceptable_printing_ids", [])}
        try:
            ownership = self._bound(p.get("ownership"), sources, mode=mode, kinds={"buyer_declaration"})
            if ownership.get("scope_complete") is not True or set(ownership.get("scope_printing_ids", [])) != scope:
                raise CardAcquisitionError("ownership scope must completely cover acceptable Printings")
            cbuyer = context.get("buyer_context")
            if not isinstance(cbuyer, dict) or ownership.get("buyer_id") != cbuyer.get("buyer_id") or not ownership.get("buyer_id"):
                raise CardAcquisitionError("owned copies belong to a different or unknown buyer")
            if len(set(ownership["scope_printing_ids"])) != len(ownership["scope_printing_ids"]):
                raise CardAcquisitionError("duplicate ownership scope identity")
            lots = ownership.get("lots")
            if not isinstance(lots, list) or any(not isinstance(x, dict) for x in lots) or len({x.get("lot_id") for x in lots}) != len(lots):
                raise CardAcquisitionError("duplicate or missing ownership lot identities")
            for lot in lots:
                if not isinstance(lot.get("lot_id"), str) or not lot["lot_id"] or lot.get("printing_id") not in scope:
                    raise CardAcquisitionError("ownership lot is outside declared scope")
                _integer(lot.get("quantity"))
                self._dimensions(lot, self.printings.get(lot["printing_id"]))
        except (KeyError, TypeError, ValueError) as error:
            ownership = {}
            blockers.append(f"ownership:{error}")
        rows = []
        offer_ids = set()
        for candidate in sorted(p["candidates"], key=lambda c: c["printing_id"]):
            rows.append(self._candidate(candidate, p, context, ownership, sources, evidence,
                blockers, offer_ids, now, scale, budget))
        if not any(row["acquisition_eligible"] is True for row in rows):
            blockers.append("no_missing_affordable_available_eligible_candidate")
        blockers = sorted(set(blockers))
        analyses, alternatives = [], []
        evidence = tuple(sorted({e.evidence_id: e for e in evidence}.values(), key=lambda e: e.evidence_id))
        policy_rows = rows if blockers else [r for r in rows if r["acquisition_eligible"] is True]
        for row in policy_rows:
            aid = row["printing_id"]
            alternatives.append(DecisionAlternative(aid, "ACQUIRE_ONE_MISSING_COPY",
                (row["card_id"], aid), {"mode": mode, "desired_quantity": row["desired_quantity"]}))
            known = not blockers
            values = (int(row["acquisition_eligible"] is True), row["declared_priority"], row["complete_cost_units"])
            metrics = tuple(AnalysisMetric(name, "known" if known else "incomplete", item if known else None,
                "integer_currency_units" if name == "complete_cost_units" else None,
                {} if known else {"blockers": blockers}, tuple(e.evidence_id for e in evidence))
                for name, item in zip(("acquisition_eligible", "declared_priority", "complete_cost_units"), values))
            analyses.append(DomainAnalysisEnvelope("card-acquisition", "1.0.0", aid, metrics, evidence,
                "known" if known else "incomplete",
                ("Only one missing copy and independent complete orders are compared.",
                 "Preference order is supplied by the user; it is not inferred card strength."),
                ("Pending functional-role proposals are not approved objective eligibility.",
                 "No competitive suitability, future price, or purchase execution is established.",
                 "Synthetic selection is a demonstration, not actual purchase advice." if mode == "synthetic_demonstration"
                 else "Result applies only to the reviewed buyer context and valid source-bound offers."),
                {"blockers": blockers} if blockers else {},
                {"budget": context.get("budget"), "ownership": "decision changes if acceptable owned quantity changes",
                 "availability_and_costs": "decision changes when valid complete offers change"},
                (self.mechanical.snapshot_id, packet.input_id)))
        request = DecisionRequest(context.get("objective") or "Assess supplied Card acquisition inputs", tuple(alternatives),
            {"budget": context.get("budget"), "currency": context.get("currency"),
             "hard_constraints": context.get("hard_constraints"), "one_missing_copy": True},
            {"priority_order": context.get("priority_order")}, {"acquisition_input_id": packet.input_id},
            evidence, self.policy.policy_id, self.policy.version,
            {"input_mode": mode, "decision_critical_blockers": blockers}, (self.mechanical.snapshot_id, packet.input_id))
        result = AcquisitionDecisionOrchestrator().evaluate(request, analyses, self.policy)
        body = {"schema_version": DOSSIER_VERSION, "mode": mode,
            "actual_purchase_advice": mode == "real_world" and result.outcome == "selected",
            "as_of": p["as_of"], "canonical_snapshot_id": self.mechanical.snapshot_id,
            "input_id": packet.input_id, "context": context, "candidates": rows,
            "blockers": blockers, "decision_request_id": request.request_id,
            "policy": self.policy.to_dict(), "decision": recommendation_reasoning_context(result),
            "evidence": [e.to_dict() for e in evidence],
            "review": {"status": "requires_review", "canonical_admission": False,
                       "role_approval": False, "purchase_executed": False}}
        return body, request, analyses

    @staticmethod
    def _dimensions(value: dict, printing: Any) -> None:
        if not isinstance(value, dict):
            raise CardAcquisitionError("explicit physical Printing dimensions required")
        if printing is None:
            raise CardAcquisitionError("exact canonical production Printing is required")
        canonical = printing.canonical_values
        if value.get("language") != canonical.get("language") or value.get("finish") not in canonical.get("finish_ids", []):
            raise CardAcquisitionError("Printing language or finish is incompatible")
        if "treatment" not in value or value["treatment"] != canonical.get("treatment"):
            raise CardAcquisitionError("treatment is unsupported or differs from canonical evidence")

    @staticmethod
    def _mechanical_source_status(source: Any, card_id: str) -> str | None:
        """Separate ordinary unbound coverage from a corrupt claimed binding.

        Missing/ambiguous dossiers do not have a provider row identity, digest or
        index. Those fields cannot be synthesized just to create an evidence
        reference. A source claiming a unique row must instead be complete.
        """
        if not isinstance(source, dict):
            raise CardAcquisitionError("invalid mechanical source binding")
        resolution = source.get("resolution")
        matches = source.get("matching_provider_record_ids")
        row_keys = {"oracle_id", "provider_record_id", "record_content_identity", "source_record_index"}
        if not isinstance(matches, list) or any(not _known_text(x) for x in matches) or \
                len(matches) != len(set(matches)):
            raise CardAcquisitionError("invalid mechanical source binding")
        for key in ("acquisition_run_id", "source_timestamp", "retained_source_reference"):
            if not _known_text(source.get(key)):
                raise CardAcquisitionError("invalid mechanical source binding metadata")
        _time(source["source_timestamp"])
        if resolution in {"missing", "ambiguous"}:
            if row_keys.intersection(source) or (resolution == "missing" and matches) or \
                    (resolution == "ambiguous" and len(matches) < 2):
                raise CardAcquisitionError("invalid incomplete mechanical source binding")
            return "source_binding_" + resolution
        if resolution != "unique" or source.get("oracle_id") != card_id or \
                matches != [source.get("provider_record_id")] or \
                not isinstance(source.get("record_content_identity"), str) or \
                not re.fullmatch(r"sha256:[0-9a-f]{64}", source["record_content_identity"]) or \
                isinstance(source.get("source_record_index"), bool) or \
                not isinstance(source.get("source_record_index"), int) or source["source_record_index"] < 0:
            raise CardAcquisitionError("invalid unique mechanical source binding")
        return None

    def _candidate(self, candidate, packet, context, ownership, sources, evidence, blockers,
                   offer_ids, now, scale, budget):
        card_id, pid = candidate.get("card_id"), candidate.get("printing_id")
        if card_id not in self.mechanical.cards or pid not in self.printings or \
                self.printings[pid].canonical_values.get("card_id") != card_id:
            raise CardAcquisitionError("exact linked canonical production Card and Printing required")
        mechanical = self.mechanical.dossier(card_id).to_dict()
        source = mechanical["source"]
        source_reason = self._mechanical_source_status(source, card_id)
        row = {"card_id": card_id, "card_name": mechanical["card_identity"]["name"],
            "printing_id": pid, "printing_values": thaw(freeze(self.printings[pid].canonical_values)),
            "mechanical_dossier_id": mechanical["dossier_id"],
            "source": source, "preferred_dimensions": candidate.get("preferred_dimensions"),
            "desired_quantity": candidate.get("desired_quantity"), "owned_acceptable_quantity": None,
            "missing_quantity": None, "acquisition_quantity": 1, "acquisition_eligible": None,
            "declared_priority": None, "complete_cost_units": None, "complete_cost": None,
            "remaining_budget": None, "offer_id": None, "exclusion_reasons": [],
            "objective_eligibility": "unknown", "unsupported_dimensions": ["competitive_strength", "future_prices", "approved_pending_roles"]}
        row["canonical_printing_provenance"] = self._printing_provenance(self.printings[pid])
        if source_reason:
            row["source_status"] = {"status": "incomplete", "reason": source_reason}
            row["exclusion_reasons"].append(source_reason)
            blockers.append(f"mechanical_source:{card_id}:{source_reason}")
            return row
        ref = EvidenceReference(mechanical["dossier_id"], source["acquisition_run_id"],
            source["record_content_identity"], source["source_timestamp"],
            source["retained_source_reference"] + f"#/{source['source_record_index']}")
        if any(e.evidence_id == ref.evidence_id and e != ref for e in evidence):
            raise CardAcquisitionError("conflicting evidence identity")
        evidence.append(ref)
        try:
            required = {k: candidate[k] for k in _REQUIREMENTS}
            self._bound({"value": required, "binding": candidate.get("requirements_binding")}, sources,
                mode=packet["mode"], kinds={"buyer_declaration"})
            desired = _integer(candidate["desired_quantity"], positive=True)
            acceptable = candidate["acceptable_printing_ids"]
            if not isinstance(candidate.get("preferred_dimensions"), dict) or \
                    set(candidate["preferred_dimensions"]) != {"language", "finish", "treatment"}:
                raise CardAcquisitionError("unsupported or missing exact Printing preference dimensions")
            if not isinstance(acceptable, list) or not acceptable or len(set(acceptable)) != len(acceptable) or pid not in acceptable:
                raise CardAcquisitionError("exact preferred Printing must occur in distinct acceptable Printings")
            for identity in acceptable:
                printing = self.printings.get(identity)
                if printing is None or printing.canonical_values.get("card_id") != card_id:
                    raise CardAcquisitionError("acceptable Printing belongs to another or unresolved Card")
                self._dimensions(candidate["preferred_dimensions"], printing)
            if ownership:
                if context.get("hard_constraints", {}).get("condition") and any(
                        not _known_text(l.get("condition")) for l in ownership["lots"]
                        if l["printing_id"] in acceptable):
                    raise CardAcquisitionError("owned physical condition is unknown")
                owned = sum(l["quantity"] for l in ownership["lots"] if l["printing_id"] in acceptable and
                    all(l.get(k) == candidate["preferred_dimensions"].get(k) for k in ("finish", "language", "treatment")) and
                    l.get("condition") == context.get("hard_constraints", {}).get("condition"))
                row.update(owned_acceptable_quantity=owned, missing_quantity=max(0, desired - owned))
                if owned >= desired:
                    row["exclusion_reasons"].append("already_owned_desired_acceptable_copies")
                    # Missing offers for a known duplicate cannot be made into
                    # zero-valued metrics or block unrelated missing copies.
                    if candidate.get("offer") is None:
                        row["acquisition_eligible"] = False
                        return row
            if context.get("eligibility_required") is False:
                row["objective_eligibility"] = "user_preference_only_not_strategic_suitability"
            elif context.get("eligibility_required") is True:
                eligibility = self._bound(candidate.get("eligibility"), sources, mode=packet["mode"],
                    kinds={"objective_eligibility_review"})
                status = "reviewed_for_demonstration" if packet["mode"] == "synthetic_demonstration" else "reviewed"
                if eligibility.get("status") != status or not isinstance(eligibility.get("eligible"), bool) or \
                        eligibility.get("card_id") != card_id or eligibility.get("printing_id") != pid or \
                        eligibility.get("objective_id") != context.get("objective_id") or \
                        eligibility.get("mechanical_dossier_id") != mechanical["dossier_id"] or \
                        eligibility.get("basis_category") != "reviewed_mechanical_objective" or \
                        not _known_text(eligibility.get("basis")):
                    raise CardAcquisitionError("reviewed mechanical objective eligibility is missing or unsupported")
                row["objective_eligibility"] = status
                if not eligibility["eligible"]:
                    row["exclusion_reasons"].append("objective_ineligible")
            offer = self._bound(candidate.get("offer"), sources, mode=packet["mode"], kinds={"reviewed_offer"})
            if not context or scale is None or budget is None:
                raise CardAcquisitionError("valid buyer context and exact budget are required")
            offer_id = offer.get("offer_id")
            if not isinstance(offer_id, str) or not offer_id or offer_id in offer_ids:
                raise CardAcquisitionError("offer identities must be unique and nonempty")
            offer_ids.add(offer_id)
            row["offer_id"] = offer_id
            self._dimensions(offer, self.printings[pid])
            if any(offer.get(k) != candidate["preferred_dimensions"].get(k)
                    for k in ("language", "finish", "treatment")):
                raise CardAcquisitionError("offer differs from exact preferred Printing dimensions")
            buyer = context["buyer_context"]
            if offer.get("printing_id") != pid or offer.get("currency") != context["currency"] or \
                    offer.get("buyer_id") != buyer["buyer_id"] or offer.get("order_assumption") != buyer["order_assumption"] or \
                    offer.get("buyer_context_identity") != content_identity(buyer) or \
                    offer.get("market") != buyer["destination_country"] or offer.get("condition") != context["hard_constraints"]["condition"] or \
                    not _known_text(offer.get("seller_id")):
                raise CardAcquisitionError("offer dimensions are incomparable with buyer context or exact preferences")
            entry, _ = sources[candidate["offer"]["binding"]["source_id"]]
            if entry["seller_identity"] != offer["seller_id"] or entry["captured_at"] != offer.get("retrieved_at"):
                raise CardAcquisitionError("offer seller or retrieval provenance mismatch")
            if _integer(offer.get("quantity"), positive=True) != 1:
                raise CardAcquisitionError("offer must price exactly one independent missing copy")
            observed, retrieved, until = (_time(offer.get(k)) for k in ("observed_at", "retrieved_at", "valid_until"))
            if not observed <= retrieved <= now <= until or (now - observed).total_seconds() > context["freshness_policy"]["max_age_seconds"]:
                raise CardAcquisitionError("offer is stale, future-dated, or outside its validity window")
            if not isinstance(offer.get("available"), bool):
                raise CardAcquisitionError("offer availability is unknown")
            stock = _integer(offer.get("available_quantity"))
            if offer["available"] and stock < 1:
                raise CardAcquisitionError("availability contradicts the declared available quantity")
            if not offer["available"] or stock < 1:
                row["exclusion_reasons"].append("offer_unavailable")
            if "allowed_seller_ids" in context["hard_constraints"] and offer["seller_id"] not in context["hard_constraints"]["allowed_seller_ids"]:
                row["exclusion_reasons"].append("seller_disallowed")
            costs = offer.get("costs")
            if not isinstance(costs, dict) or set(costs) != set(_COSTS):
                raise CardAcquisitionError("all five transaction cost terms require evidence; unknown is not zero")
            amounts = {}
            for key in _COSTS:
                term = costs[key]
                if not isinstance(term, dict) or set(term) != {"amount", "basis"} or \
                        not _known_text(term["basis"]):
                    raise CardAcquisitionError(f"{key} including zero requires an evidenced basis")
                amounts[key] = _units(term["amount"], scale)
            total = sum(amounts[k] for k in _COSTS if k != "discounts") - amounts["discounts"]
            if total < 0:
                raise CardAcquisitionError("discount exceeds evidenced acquisition charges")
            row.update(complete_cost_units=total, complete_cost=_amount(total, scale),
                remaining_budget=_amount(budget - total, scale), currency=context["currency"],
                money_scale=scale, costs=costs, offer_availability={"available": offer["available"],
                "available_quantity": stock, "observed_at": offer["observed_at"],
                "retrieved_at": offer["retrieved_at"], "valid_until": offer["valid_until"]},
                declared_priority=context["priority_order"].index(pid))
            if total > budget:
                row["exclusion_reasons"].append("over_budget")
            if row["missing_quantity"] is not None:
                row["acquisition_eligible"] = not row["exclusion_reasons"]
        except (KeyError, TypeError, ValueError) as error:
            blockers.append(f"candidate:{pid}:{error}")
        return row
