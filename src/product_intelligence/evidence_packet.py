"""Governed evidence and human-review boundary for fixed-content acquisition."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError
from decision_intelligence import EvidenceReference

from .models import (ComponentValuationInput, FixedContentProductManifest,
                     ProductAcquisitionOffer, ProductValidationError, _decimal,
                     GuaranteedComponent, _freeze, _identity, _plain, _stamp, _text)

PACKET_SCHEMA = "fixed-content-acquisition-evidence-v1"
REVIEW_SCHEMA = "fixed-content-acquisition-evidence-review-v2"
READY_FOR_EVALUATION = "READY_FOR_EVALUATION"
NOT_READY_FOR_EVALUATION = "NOT_READY_FOR_EVALUATION"
EVIDENCE_STATES = frozenset({"known", "unknown", "incomplete", "not_applicable"})
FUTURE_EVIDENCE_CLASSES = frozenset({"presale_observations", "post_release_observations",
    "supply_availability", "listing_depth_liquidity", "historical_comparable_products",
    "sealed_collectible_premium", "collector_ip_demand", "reprint_risk"})
_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_PACKET_ID = re.compile(r"^fixed-content-evidence-sha256:[0-9a-f]{64}$")
_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$")


def _format_checker():
    checker = FormatChecker()

    # jsonschema's optional date-time dependency is not in requirements.txt.
    @checker.checks("date-time", raises=(ValueError, TypeError))
    def aware_timestamp(value):
        if not isinstance(value, str):
            return True
        return bool(_TIMESTAMP.fullmatch(value)) and datetime.fromisoformat(value.replace("z", "+00:00").replace("Z", "+00:00")).tzinfo is not None

    return checker


def _references(values, label):
    if not isinstance(values, (tuple, list)):
        raise ProductValidationError(f"{label} must be a list or tuple of references")
    result = tuple(sorted(_text(x, label) for x in values))
    if len(set(result)) != len(result):
        raise ProductValidationError(f"duplicate {label}")
    return result


@lru_cache(maxsize=2)
def _validator(schema_name):
    path = Path(__file__).resolve().parents[1] / "schemas" / "v1" / f"{schema_name}.schema.json"
    return Draft202012Validator(json.loads(path.read_text(encoding="utf-8")), format_checker=_format_checker())


def _validate_packet_document(document):
    try:
        _validator(PACKET_SCHEMA).validate(document)
    except ValidationError as error:
        location = ".".join(str(x) for x in error.absolute_path) or "<root>"
        raise ProductValidationError(f"packet contract failed at {location}: {error.message}") from error


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
        if not isinstance(self.evidence_state, str) or self.evidence_state not in EVIDENCE_STATES: raise ProductValidationError("invalid source evidence_state")
        object.__setattr__(self, "retrieved_at", _stamp(self.retrieved_at, "retrieved_at"))
        if self.published_at is not None: object.__setattr__(self, "published_at", _stamp(self.published_at, "published_at"))
        if self.locator is not None: object.__setattr__(self, "locator", _text(self.locator, "locator"))
        object.__setattr__(self, "canonical_references", _references(self.canonical_references, "canonical_reference"))

    def to_dict(self):
        return {"source_id": self.source_id, "provider": self.provider, "record_identity": self.record_identity,
            "content_digest": self.content_digest, "evidence_state": self.evidence_state, "locator": self.locator,
            "published_at": _plain(self.published_at), "retrieved_at": _plain(self.retrieved_at),
            "canonical_references": list(self.canonical_references)}


@dataclass(frozen=True)
class SinglesTransactionCosts:
    currency: str
    shipping: Decimal | None
    marketplace_fees: Decimal | None
    other_costs: Decimal | None
    completeness: str
    evidence_source_ids: tuple[str, ...]
    seller_order_assumptions: tuple[str, ...] = ()

    def __post_init__(self):
        currency = _text(self.currency, "currency").upper()
        if len(currency) != 3 or not currency.isalpha(): raise ProductValidationError("currency must be a three-letter code")
        object.__setattr__(self, "currency", currency)
        for name in ("shipping", "marketplace_fees", "other_costs"):
            value = getattr(self, name)
            object.__setattr__(self, name, None if value is None else _decimal(value, name))
        if self.completeness not in {"complete", "incomplete", "unknown"}: raise ProductValidationError("invalid transaction-cost completeness")
        if self.completeness == "complete" and any(getattr(self, name) is None for name in ("shipping", "marketplace_fees", "other_costs")):
            raise ProductValidationError("complete transaction costs require all amounts")
        object.__setattr__(self, "evidence_source_ids", _references(self.evidence_source_ids, "evidence_source_id"))
        object.__setattr__(self, "seller_order_assumptions", _references(self.seller_order_assumptions, "seller_order_assumption"))

    @property
    def total(self):
        values = (self.shipping, self.marketplace_fees, self.other_costs)
        return None if any(x is None for x in values) else self.shipping + self.marketplace_fees + self.other_costs
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
        if any(not isinstance(x, GuaranteedComponent) for x in self.manifest.components):
            raise ProductValidationError("typed guaranteed components are required")
        if any(not isinstance(x, EvidenceReference) for x in (*self.manifest.evidence, *self.sealed_offer.evidence)):
            raise ProductValidationError("typed material evidence references are required")
        if self.sealed_offer.product_id != self.manifest.product_id: raise ProductValidationError("packet product identities conflict")
        object.__setattr__(self, "assembled_at", _stamp(self.assembled_at, "assembled_at"))
        if any(not isinstance(x, SourceSnapshot) for x in self.sources):
            raise ProductValidationError("typed source snapshots are required")
        sources = tuple(sorted(self.sources, key=lambda x: x.source_id))
        if not sources or len({x.source_id for x in sources}) != len(sources): raise ProductValidationError("packet requires unique sources")
        object.__setattr__(self, "sources", sources); source_ids = {x.source_id for x in sources}
        if any(not isinstance(x, ComponentValuationInput) for x in self.valuations): raise ProductValidationError("typed valuations are required")
        valuations = tuple(sorted(self.valuations, key=lambda x: (x.component_id, x.valuation_id)))
        if len({x.component_id for x in valuations}) != len(valuations): raise ProductValidationError("conflicting component valuation replay")
        object.__setattr__(self, "valuations", valuations)
        unpriced = tuple(sorted(_text(x, "unpriced_component_id") for x in self.unpriced_component_ids))
        if len(set(unpriced)) != len(unpriced): raise ProductValidationError("duplicate unpriced component")
        object.__setattr__(self, "unpriced_component_ids", unpriced)
        component_ids = {x.component_id for x in self.manifest.components}; valued_ids = {x.component_id for x in valuations}
        if len(component_ids) != len(self.manifest.components):
            raise ProductValidationError("duplicate guaranteed component ID")
        if valued_ids & set(unpriced) or valued_ids | set(unpriced) != component_ids: raise ProductValidationError("every guaranteed component must be exactly valued or explicitly unpriced")
        if not isinstance(self.transaction_costs, SinglesTransactionCosts): raise ProductValidationError("typed transaction costs are required")
        if not set(self.transaction_costs.evidence_source_ids) <= source_ids: raise ProductValidationError("transaction costs reference absent source")
        if not isinstance(self.sealed_cost_input_states, Mapping):
            raise ProductValidationError("sealed cost states must be a mapping")
        states = dict(self.sealed_cost_input_states)
        if set(states) != {"shipping", "tax", "fees", "discounts"} or any(not isinstance(x, str) or x not in EVIDENCE_STATES for x in states.values()): raise ProductValidationError("sealed cost states must exactly cover shipping, tax, fees, and discounts")
        sealed_amounts = {"shipping": self.sealed_offer.shipping, "tax": self.sealed_offer.tax,
                         "fees": self.sealed_offer.transaction_fees, "discounts": self.sealed_offer.discounts}
        if any(states[key] == "not_applicable" and amount != 0 for key, amount in sealed_amounts.items()):
            raise ProductValidationError("not_applicable sealed cost must be zero")
        object.__setattr__(self, "sealed_cost_input_states", _freeze(states))
        if self.availability_state not in {"available", "unavailable", "unknown"}: raise ProductValidationError("invalid availability state")
        availability_ids = _references(self.availability_source_ids, "availability_source_id")
        if not set(availability_ids) <= source_ids: raise ProductValidationError("availability references absent source")
        if self.availability_state != "unknown" and not availability_ids: raise ProductValidationError("evidenced availability requires provenance")
        object.__setattr__(self, "availability_source_ids", availability_ids)
        if self.future_evidence is not None and not isinstance(self.future_evidence, Mapping):
            raise ProductValidationError("future evidence must be a mapping")
        future = {} if self.future_evidence is None else {k: _references(v, "future evidence source ID") for k, v in self.future_evidence.items()}
        if not set(future) <= FUTURE_EVIDENCE_CLASSES: raise ProductValidationError("unsupported inference/evidence field")
        if any(not set(v) <= source_ids for v in future.values()): raise ProductValidationError("future evidence references absent source")
        object.__setattr__(self, "future_evidence", _freeze(future))
        governed = {(x.provider, x.content_digest) for x in sources}
        references = (*self.manifest.evidence, *self.sealed_offer.evidence)
        if any(not _DIGEST.fullmatch(x.content_digest) for x in references): raise ProductValidationError("material evidence digest is invalid")
        if any((x.source_identity, x.content_digest) not in governed for x in references): raise ProductValidationError("material evidence lacks governed source snapshot")
        for value in valuations:
            digest = value.observation.provenance.get("source_digest")
            if not isinstance(digest, str) or not _DIGEST.fullmatch(digest): raise ProductValidationError("market observation source digest is invalid")
            if (value.observation.provider, digest) not in governed: raise ProductValidationError("market observation lacks governed source snapshot")
        _validate_packet_document(self.to_dict())

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
class EvidencePacketEligibility:
    """Automated findings only; eligibility is never human approval."""

    packet_id: str
    as_of: datetime
    acceptable_observed_after: datetime | None
    issues: tuple[str, ...]

    @property
    def eligible(self):
        return not self.issues


@dataclass(frozen=True)
class EvidencePacketReview:
    packet_id: str
    reviewer_identity: str
    reviewed_at: datetime
    status: str
    issues: tuple[str, ...]
    schema_version: str = REVIEW_SCHEMA
    acceptable_observed_after: datetime | None = None
    human_approved: bool = False
    review_reference: str | None = None

    def __post_init__(self):
        if self.schema_version != REVIEW_SCHEMA:
            raise ProductValidationError("unsupported review schema; v1 is not affirmative approval")
        if not isinstance(self.packet_id, str) or not _PACKET_ID.fullmatch(self.packet_id):
            raise ProductValidationError("invalid reviewed packet identity")
        if self.status not in {READY_FOR_EVALUATION, NOT_READY_FOR_EVALUATION}:
            raise ProductValidationError("invalid review status")
        object.__setattr__(self, "reviewer_identity", _text(self.reviewer_identity, "reviewer_identity"))
        object.__setattr__(self, "reviewed_at", _stamp(self.reviewed_at, "reviewed_at"))
        object.__setattr__(self, "issues", _references(self.issues, "review issue"))
        if type(self.human_approved) is not bool:
            raise ProductValidationError("human_approved must be an explicit boolean")
        if self.acceptable_observed_after is not None:
            cutoff = _stamp(self.acceptable_observed_after, "acceptable_observed_after")
            if cutoff > self.reviewed_at:
                raise ProductValidationError("freshness cutoff cannot follow review time")
            object.__setattr__(self, "acceptable_observed_after", cutoff)
        if self.review_reference is not None:
            object.__setattr__(self, "review_reference", _text(self.review_reference, "review_reference"))
        if (self.status == READY_FOR_EVALUATION) == bool(self.issues):
            raise ProductValidationError("READY requires no issues; NOT_READY requires issues")
        if self.status == READY_FOR_EVALUATION and (
            not self.human_approved or not self.review_reference or self.acceptable_observed_after is None
        ):
            raise ProductValidationError("READY requires explicit human approval, review reference, and freshness policy")
        try:
            _validator(REVIEW_SCHEMA).validate(self.to_dict())
        except ValidationError as error:
            raise ProductValidationError(f"review contract failed: {error.message}") from error

    def to_dict(self):
        return {"schema_version": self.schema_version, "packet_id": self.packet_id,
                "reviewer_identity": self.reviewer_identity, "reviewed_at": _plain(self.reviewed_at),
                "status": self.status, "issues": list(self.issues),
                "acceptable_observed_after": _plain(self.acceptable_observed_after),
                "human_approved": self.human_approved, "review_reference": self.review_reference}

    @classmethod
    def from_dict(cls, document):
        """Read v2 only; historical machine-generated v1 READY is not approval."""
        try:
            _validator(REVIEW_SCHEMA).validate(document)
        except ValidationError as error:
            raise ProductValidationError(f"review contract failed: {error.message}") from error
        cutoff = document["acceptable_observed_after"]
        return cls(document["packet_id"], document["reviewer_identity"],
                   datetime.fromisoformat(document["reviewed_at"].replace("z", "+00:00").replace("Z", "+00:00")),
                   document["status"], tuple(document["issues"]), document["schema_version"],
                   None if cutoff is None else datetime.fromisoformat(cutoff.replace("z", "+00:00").replace("Z", "+00:00")),
                   document["human_approved"], document["review_reference"])


def assess_evidence_packet(packet, *, as_of, acceptable_observed_after):
    """Check an explicit inclusive observation window, without approving anything."""
    if not isinstance(packet, FixedContentAcquisitionEvidencePacket):
        raise ProductValidationError("typed packet required")
    as_of = _stamp(as_of, "as_of")
    cutoff = None if acceptable_observed_after is None else _stamp(acceptable_observed_after, "acceptable_observed_after")
    if cutoff is not None and cutoff > as_of:
        raise ProductValidationError("freshness cutoff cannot follow as_of")
    issues = []
    if cutoff is None:
        issues.append("freshness_policy_missing")
    if packet.manifest.completeness != "complete":
        issues.append("manifest_not_complete")
    if packet.manifest.unknowns or any(x.unknowns for x in packet.manifest.components):
        issues.append("decision_critical_manifest_unknowns")
    if packet.unpriced_component_ids or any(x.observation.price is None for x in packet.valuations):
        issues.append("unpriced_components")
    costs = packet.transaction_costs
    if costs.completeness != "complete" or costs.total is None:
        issues.append("transaction_costs_not_complete")
    # These references attest the entire stated cost bundle, including every zero.
    if not costs.evidence_source_ids:
        issues.append("transaction_cost_provenance_missing")
    if any(x == 0 for x in (costs.shipping, costs.marketplace_fees, costs.other_costs)) and not costs.seller_order_assumptions:
        issues.append("zero_transaction_cost_basis_missing")
    if costs.currency != packet.sealed_offer.currency:
        issues.append("incompatible_currencies")
    if any(x in {"unknown", "incomplete"} for x in packet.sealed_cost_input_states.values()):
        issues.append("sealed_effective_cost_inputs_incomplete")
    if packet.availability_state != "available":
        issues.append("sealed_offer_unavailable" if packet.availability_state == "unavailable" else "sealed_availability_unknown")
    if not packet.manifest.evidence or any(not x.evidence_ids for x in packet.manifest.components):
        issues.append("manifest_provenance_missing")

    expected = None
    components = {x.component_id: x for x in packet.manifest.components}
    for value in packet.valuations:
        obs = value.observation
        dims = (obs.provider, obs.currency, obs.price_type, obs.observed_at)
        if expected is None:
            expected = dims
        elif dims != expected:
            issues.append("incompatible_market_dimensions")
        if obs.currency != packet.sealed_offer.currency:
            issues.append("incompatible_currencies")
        component = components[value.component_id]
        if (component.printing_id, component.finish, component.language, component.treatment) != (value.printing_id, value.finish, value.language, value.treatment):
            issues.append("incompatible_component_dimensions")
        if cutoff is not None and obs.observed_at < cutoff:
            issues.append("singles_timestamp_not_acceptable")
        if obs.observed_at > as_of:
            issues.append("singles_timestamp_in_future")
    if cutoff is not None and packet.sealed_offer.observed_at < cutoff:
        issues.append("sealed_timestamp_not_acceptable")
    if packet.sealed_offer.observed_at > as_of:
        issues.append("sealed_timestamp_in_future")

    material_pairs = {(x.source_identity, x.content_digest) for x in (*packet.manifest.evidence, *packet.sealed_offer.evidence)}
    material_pairs.update((x.observation.provider, x.observation.provenance["source_digest"]) for x in packet.valuations)
    material_ids = set(costs.evidence_source_ids) | set(packet.availability_source_ids)
    material_ids.update(x.source_id for x in packet.sources if (x.provider, x.content_digest) in material_pairs)
    material_sources = tuple(x for x in packet.sources if x.source_id in material_ids)
    if any(x.evidence_state != "known" for x in material_sources):
        issues.append("provenance_not_sufficient")

    stamps = [packet.assembled_at, packet.manifest.effective_at, packet.sealed_offer.observed_at,
              packet.sealed_offer.effective_at]
    for value in packet.valuations:
        stamps.extend((value.observation.observed_at, value.observation.recorded_at))
    for source in material_sources:
        stamps.extend((source.published_at, source.retrieved_at))
        if source.published_at is not None and source.published_at > source.retrieved_at:
            issues.append("source_timestamp_order_invalid")
    for ref in (*packet.manifest.evidence, *packet.sealed_offer.evidence):
        if ref.recorded_at is not None:
            stamps.append(_stamp(datetime.fromisoformat(ref.recorded_at.replace("z", "+00:00").replace("Z", "+00:00")), "evidence recorded_at"))
    if any(stamp is not None and stamp > as_of for stamp in stamps):
        issues.append("evidence_timestamp_in_future")
    if any(stamp is not None and stamp > packet.assembled_at for stamp in stamps):
        issues.append("evidence_timestamp_after_assembly")
    return EvidencePacketEligibility(packet.packet_id, as_of, cutoff, tuple(sorted(set(issues))))


def review_evidence_packet(packet, reviewer_identity, reviewed_at, *, acceptable_observed_after=None,
                           human_approved=False, reviewed_packet_id=None, review_reference=None):
    """Record a caller-supplied human attestation; never infer approval from eligibility.

    The trusted human-review caller owns authentication and the durable review reference.
    This function neither authenticates a human nor signs or publishes a review.
    """
    eligibility = assess_evidence_packet(packet, as_of=reviewed_at,
                                         acceptable_observed_after=acceptable_observed_after)
    if type(human_approved) is not bool:
        raise ProductValidationError("human_approved must be an explicit boolean")
    issues = list(eligibility.issues)
    if not human_approved:
        issues.append("human_approval_missing")
    if reviewed_packet_id != packet.packet_id:
        issues.append("human_review_packet_mismatch")
    if review_reference is None:
        issues.append("human_review_reference_missing")
    else:
        review_reference = _text(review_reference, "review_reference")
    issues = tuple(sorted(set(issues)))
    return EvidencePacketReview(packet.packet_id, reviewer_identity, eligibility.as_of,
        READY_FOR_EVALUATION if not issues else NOT_READY_FOR_EVALUATION, issues,
        acceptable_observed_after=eligibility.acceptable_observed_after,
        human_approved=human_approved, review_reference=review_reference)


def require_ready_evidence_review(packet, review, *, as_of, acceptable_observed_after):
    """Verify exact packet, explicit human attestation, and the approved as-of policy.

    This admission guard does not call Product or Decision Intelligence. Changing the
    packet or observation window requires another human review, not approval replay.
    """
    if not isinstance(packet, FixedContentAcquisitionEvidencePacket) or not isinstance(review, EvidencePacketReview):
        raise ProductValidationError("typed packet and review required")
    as_of = _stamp(as_of, "as_of")
    cutoff = _stamp(acceptable_observed_after, "acceptable_observed_after")
    if review.packet_id != packet.packet_id:
        raise ProductValidationError("review does not bind this packet")
    if review.status != READY_FOR_EVALUATION or not review.human_approved or not review.review_reference:
        raise ProductValidationError("affirmative human review required")
    if review.reviewed_at != as_of or review.acceptable_observed_after != cutoff:
        raise ProductValidationError("freshness policy changed; a new human review is required")
    eligibility = assess_evidence_packet(packet, as_of=as_of, acceptable_observed_after=cutoff)
    if not eligibility.eligible:
        raise ProductValidationError("packet is not eligible: " + ", ".join(eligibility.issues))


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
        _validate_packet_document(data)
        if data["packet_id"] != packet_id or _identity("fixed-content-evidence-sha256:", content) != packet_id: raise ProductValidationError("packet digest validation failed")
        if json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8") != encoded:
            raise ProductValidationError("packet replay bytes are not canonical")
        return encoded
