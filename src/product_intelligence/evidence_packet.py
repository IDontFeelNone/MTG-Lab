"""Governed evidence and human-review boundary for fixed-content acquisition."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import json
import re
from typing import Mapping

from .models import (ComponentValuationInput, FixedContentProductManifest,
                     ProductAcquisitionOffer, ProductValidationError, _decimal,
                     _identity, _plain, _stamp, _text)

PACKET_SCHEMA = "fixed-content-acquisition-evidence-v1"
REVIEW_SCHEMA = "fixed-content-acquisition-evidence-review-v1"
READY_FOR_EVALUATION = "READY_FOR_EVALUATION"
NOT_READY_FOR_EVALUATION = "NOT_READY_FOR_EVALUATION"
EVIDENCE_STATES = frozenset({"known", "unknown", "incomplete", "not_applicable"})
FUTURE_EVIDENCE_CLASSES = frozenset({"presale_observations", "post_release_observations",
    "supply_availability", "listing_depth_liquidity", "historical_comparable_products",
    "sealed_collectible_premium", "collector_ip_demand", "reprint_risk"})
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceSnapshot:
    source_id: str
    provider: str
    record_identity: str
    content_digest: str
    retrieved_at: datetime
    evidence_state: str = "known"
    locator: str | None = None
    published_at: datetime | None = None
    canonical_references: tuple[str, ...] = ()

    def __post_init__(self):
        for name in ("source_id", "provider", "record_identity"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if not isinstance(self.content_digest, str) or not _DIGEST.fullmatch(self.content_digest):
            raise ProductValidationError("source content_digest must be sha256:<64 lowercase hex>")
        if self.evidence_state not in EVIDENCE_STATES: raise ProductValidationError("invalid source evidence_state")
        object.__setattr__(self, "retrieved_at", _stamp(self.retrieved_at, "retrieved_at"))
        if self.published_at is not None: object.__setattr__(self, "published_at", _stamp(self.published_at, "published_at"))
        if self.locator is not None: object.__setattr__(self, "locator", _text(self.locator, "locator"))
        object.__setattr__(self, "canonical_references", tuple(sorted(_text(x, "canonical_reference") for x in self.canonical_references)))

    def to_dict(self):
        return {"source_id": self.source_id, "provider": self.provider, "record_identity": self.record_identity,
            "content_digest": self.content_digest, "evidence_state": self.evidence_state, "locator": self.locator,
            "published_at": _plain(self.published_at), "retrieved_at": _plain(self.retrieved_at),
            "canonical_references": list(self.canonical_references)}


@dataclass(frozen=True)
class SinglesTransactionCosts:
    currency: str
    shipping: Decimal
    marketplace_fees: Decimal
    other_costs: Decimal
    completeness: str
    evidence_source_ids: tuple[str, ...]
    seller_order_assumptions: tuple[str, ...] = ()

    def __post_init__(self):
        currency = _text(self.currency, "currency").upper()
        if len(currency) != 3 or not currency.isalpha(): raise ProductValidationError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        for name in ("shipping", "marketplace_fees", "other_costs"):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if self.completeness not in {"complete", "incomplete", "unknown"}: raise ProductValidationError("invalid transaction-cost completeness")
        object.__setattr__(self, "evidence_source_ids", tuple(sorted(_text(x, "evidence_source_id") for x in self.evidence_source_ids)))
        object.__setattr__(self, "seller_order_assumptions", tuple(sorted(_text(x, "seller_order_assumption") for x in self.seller_order_assumptions)))

    @property
    def total(self): return self.shipping + self.marketplace_fees + self.other_costs
    def to_dict(self):
        return {"currency": self.currency, "shipping": _plain(self.shipping), "marketplace_fees": _plain(self.marketplace_fees),
            "other_costs": _plain(self.other_costs), "total": _plain(self.total), "completeness": self.completeness,
            "evidence_source_ids": list(self.evidence_source_ids), "seller_order_assumptions": list(self.seller_order_assumptions)}


@dataclass(frozen=True)
class FixedContentAcquisitionEvidencePacket:
    manifest: FixedContentProductManifest
    sealed_offer: ProductAcquisitionOffer
    valuations: tuple[ComponentValuationInput, ...]
    unpriced_component_ids: tuple[str, ...]
    sources: tuple[SourceSnapshot, ...]
    transaction_costs: SinglesTransactionCosts
    assembled_at: datetime
    sealed_cost_input_states: Mapping[str, str]
    availability_state: str = "unknown"
    availability_source_ids: tuple[str, ...] = ()
    future_evidence: Mapping[str, tuple[str, ...]] | None = None
    schema_version: str = PACKET_SCHEMA

    def __post_init__(self):
        if self.schema_version != PACKET_SCHEMA: raise ProductValidationError("unsupported packet schema")
        if not isinstance(self.manifest, FixedContentProductManifest) or not isinstance(self.sealed_offer, ProductAcquisitionOffer): raise ProductValidationError("packet requires typed manifest and sealed offer")
        if self.sealed_offer.product_id != self.manifest.product_id: raise ProductValidationError("packet product identities conflict")
        object.__setattr__(self, "assembled_at", _stamp(self.assembled_at, "assembled_at"))
        sources = tuple(sorted(self.sources, key=lambda x: x.source_id))
        if not sources or len({x.source_id for x in sources}) != len(sources): raise ProductValidationError("packet requires unique sources")
        object.__setattr__(self, "sources", sources); source_ids = {x.source_id for x in sources}
        valuations = tuple(sorted(self.valuations, key=lambda x: (x.component_id, x.valuation_id)))
        if any(not isinstance(x, ComponentValuationInput) for x in valuations): raise ProductValidationError("typed valuations are required")
        if len({x.component_id for x in valuations}) != len(valuations): raise ProductValidationError("conflicting component valuation replay")
        object.__setattr__(self, "valuations", valuations)
        unpriced = tuple(sorted(_text(x, "unpriced_component_id") for x in self.unpriced_component_ids))
        if len(set(unpriced)) != len(unpriced): raise ProductValidationError("duplicate unpriced component")
        object.__setattr__(self, "unpriced_component_ids", unpriced)
        component_ids = {x.component_id for x in self.manifest.components}; valued_ids = {x.component_id for x in valuations}
        if valued_ids & set(unpriced) or valued_ids | set(unpriced) != component_ids: raise ProductValidationError("every guaranteed component must be exactly valued or explicitly unpriced")
        if not isinstance(self.transaction_costs, SinglesTransactionCosts): raise ProductValidationError("typed transaction costs are required")
        if not set(self.transaction_costs.evidence_source_ids) <= source_ids: raise ProductValidationError("transaction costs reference absent source")
        states = dict(self.sealed_cost_input_states)
        if set(states) != {"shipping", "tax", "fees", "discounts"} or any(x not in EVIDENCE_STATES for x in states.values()): raise ProductValidationError("sealed cost states must exactly cover shipping, tax, fees, and discounts")
        object.__setattr__(self, "sealed_cost_input_states", states)
        if self.availability_state not in {"available", "unavailable", "unknown"}: raise ProductValidationError("invalid availability state")
        availability_ids = tuple(sorted(_text(x, "availability_source_id") for x in self.availability_source_ids))
        if not set(availability_ids) <= source_ids: raise ProductValidationError("availability references absent source")
        if self.availability_state != "unknown" and not availability_ids: raise ProductValidationError("evidenced availability requires provenance")
        object.__setattr__(self, "availability_source_ids", availability_ids)
        future = {} if self.future_evidence is None else {str(k): tuple(sorted(v)) for k, v in self.future_evidence.items()}
        if not set(future) <= FUTURE_EVIDENCE_CLASSES: raise ProductValidationError("unsupported inference/evidence field")
        if any(not set(v) <= source_ids for v in future.values()): raise ProductValidationError("future evidence references absent source")
        object.__setattr__(self, "future_evidence", future)
        governed = {(x.provider, x.content_digest) for x in sources}
        references = (*self.manifest.evidence, *self.sealed_offer.evidence)
        if any(not _DIGEST.fullmatch(x.content_digest) for x in references): raise ProductValidationError("material evidence digest is invalid")
        if any((x.source_identity, x.content_digest) not in governed for x in references): raise ProductValidationError("material evidence lacks governed source snapshot")
        for value in valuations:
            digest = value.observation.provenance.get("source_digest")
            if not isinstance(digest, str) or not _DIGEST.fullmatch(digest): raise ProductValidationError("market observation source digest is invalid")
            if (value.observation.provider, digest) not in governed: raise ProductValidationError("market observation lacks governed source snapshot")

    def content_dict(self):
        return {"schema_version": self.schema_version, "assembled_at": _plain(self.assembled_at), "manifest": self.manifest.to_dict(),
            "sealed_offer": self.sealed_offer.to_dict(), "sealed_cost_input_states": dict(sorted(self.sealed_cost_input_states.items())),
            "availability_state": self.availability_state, "availability_source_ids": list(self.availability_source_ids),
            "valuations": [x.to_dict() for x in self.valuations], "unpriced_component_ids": list(self.unpriced_component_ids),
            "transaction_costs": self.transaction_costs.to_dict(), "sources": [x.to_dict() for x in self.sources],
            "future_evidence": {k: list(v) for k, v in sorted(self.future_evidence.items())}}
    @property
    def packet_id(self): return _identity("fixed-content-evidence-sha256:", self.content_dict())
    def to_dict(self): return {"packet_id": self.packet_id, **self.content_dict()}
    def to_json(self): return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True)
class EvidencePacketReview:
    packet_id: str
    reviewer_identity: str
    reviewed_at: datetime
    status: str
    issues: tuple[str, ...]
    schema_version: str = REVIEW_SCHEMA
    def __post_init__(self):
        if self.status not in {READY_FOR_EVALUATION, NOT_READY_FOR_EVALUATION}: raise ProductValidationError("invalid review status")
        object.__setattr__(self, "reviewer_identity", _text(self.reviewer_identity, "reviewer_identity"))
        object.__setattr__(self, "reviewed_at", _stamp(self.reviewed_at, "reviewed_at"))
        object.__setattr__(self, "issues", tuple(sorted(set(self.issues))))
        if (self.status == READY_FOR_EVALUATION) == bool(self.issues): raise ProductValidationError("READY requires no issues; NOT_READY requires issues")
    def to_dict(self): return {"schema_version": self.schema_version, "packet_id": self.packet_id, "reviewer_identity": self.reviewer_identity,
        "reviewed_at": _plain(self.reviewed_at), "status": self.status, "issues": list(self.issues)}


def review_evidence_packet(packet, reviewer_identity, reviewed_at, *, acceptable_observed_after=None):
    """Apply current-cost gates without running a recommendation policy."""
    if not isinstance(packet, FixedContentAcquisitionEvidencePacket): raise ProductValidationError("typed packet required")
    issues = []
    if packet.manifest.completeness != "complete": issues.append("manifest_not_complete")
    if packet.manifest.unknowns or any(x.unknowns for x in packet.manifest.components): issues.append("decision_critical_manifest_unknowns")
    if packet.unpriced_component_ids or any(x.observation.price is None for x in packet.valuations): issues.append("unpriced_components")
    if packet.transaction_costs.completeness != "complete": issues.append("transaction_costs_not_complete")
    if packet.transaction_costs.currency != packet.sealed_offer.currency: issues.append("incompatible_currencies")
    if any(x in {"unknown", "incomplete"} for x in packet.sealed_cost_input_states.values()): issues.append("sealed_effective_cost_inputs_incomplete")
    if packet.availability_state == "unavailable": issues.append("sealed_offer_unavailable")
    expected = None; components = {x.component_id: x for x in packet.manifest.components}
    for value in packet.valuations:
        obs = value.observation; dims = (obs.provider, obs.currency, obs.price_type)
        if expected is None: expected = dims
        elif dims != expected: issues.append("incompatible_market_dimensions")
        if obs.currency != packet.sealed_offer.currency: issues.append("incompatible_currencies")
        component = components[value.component_id]
        if (component.printing_id, component.finish, component.language, component.treatment) != (value.printing_id, value.finish, value.language, value.treatment): issues.append("incompatible_component_dimensions")
        if acceptable_observed_after is not None and obs.observed_at < acceptable_observed_after: issues.append("singles_timestamp_not_acceptable")
    if acceptable_observed_after is not None and packet.sealed_offer.observed_at < acceptable_observed_after: issues.append("sealed_timestamp_not_acceptable")
    material_pairs = {(x.source_identity, x.content_digest) for x in (*packet.manifest.evidence, *packet.sealed_offer.evidence)}
    material_pairs.update((x.observation.provider, x.observation.provenance["source_digest"]) for x in packet.valuations)
    material_ids = set(packet.transaction_costs.evidence_source_ids) | set(packet.availability_source_ids)
    material_ids.update(x.source_id for x in packet.sources if (x.provider, x.content_digest) in material_pairs)
    if any(x.evidence_state != "known" for x in packet.sources if x.source_id in material_ids): issues.append("provenance_not_sufficient")
    issues = tuple(sorted(set(issues)))
    return EvidencePacketReview(packet.packet_id, reviewer_identity, reviewed_at,
        READY_FOR_EVALUATION if not issues else NOT_READY_FOR_EVALUATION, issues)


class EvidencePacketReplayRepository:
    """Append-only bytes: identical replay is idempotent; identity conflicts fail closed."""
    def __init__(self): self._bytes = {}
    def retain(self, packet):
        if not isinstance(packet, FixedContentAcquisitionEvidencePacket): raise ProductValidationError("typed packet required")
        encoded = packet.to_json().encode("utf-8"); existing = self._bytes.get(packet.packet_id)
        if existing is not None and existing != encoded: raise ProductValidationError("packet identity exists with conflicting bytes")
        self._bytes[packet.packet_id] = encoded
        return encoded
    def replay(self, packet_id):
        try: encoded = self._bytes[packet_id]
        except KeyError as error: raise ProductValidationError("unknown packet identity") from error
        data = json.loads(encoded); content = {k: v for k, v in data.items() if k != "packet_id"}
        if _identity("fixed-content-evidence-sha256:", content) != packet_id: raise ProductValidationError("packet digest validation failed")
        return encoded
