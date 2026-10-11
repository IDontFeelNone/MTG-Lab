"""Governed production fixed-content evidence packet contract tests."""
from dataclasses import FrozenInstanceError, replace
from datetime import date, datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator

from decision_intelligence import EvidenceReference
from market.intelligence import MarketObservation
from product_intelligence import (ComponentValuationInput, EvidencePacketReplayRepository,
    FixedContentAcquisitionEvidencePacket, FixedContentProductManifest, GuaranteedComponent,
    NOT_READY_FOR_EVALUATION, ProductAcquisitionOffer, ProductValidationError,
    READY_FOR_EVALUATION, SinglesTransactionCosts, SourceSnapshot, review_evidence_packet)

NOW=datetime(2026,8,16,12,tzinfo=timezone.utc)
D1="sha256:"+"a"*64; D2="sha256:"+"b"*64; D3="sha256:"+"c"*64
MANIFEST_REF=EvidenceReference("manifest-doc","publisher",D1,NOW.isoformat(),"https://example.invalid/manifest")
OFFER_REF=EvidenceReference("offer-record","seller",D2,NOW.isoformat(),"seller:offer-1")


def source(sid, provider, digest, **kw):
    return SourceSnapshot(sid,provider,sid+"-record",digest,NOW,canonical_references=("product:generic-1",),**kw)

def observation(cid="printing-1", price="3.00", currency="USD", provider="market", finish="foil", language="en", observed=NOW):
    return MarketObservation("printing",cid,provider,observed,NOW,price,currency,"market",finish,
        provenance={"language":language,"source_record_id":"market-record-1","source_digest":D3})

def packet(*, completeness="complete", unpriced=(), currency="USD", market_currency="USD",
           market_provider="market", tx_complete="complete", states=None, component_unknowns=(),
           future=None, second=False):
    components=[GuaranteedComponent("card-1","card",2,"printing-1","foil","en","showcase",("manifest-doc",),component_unknowns),
        GuaranteedComponent("token-sheet","printed-accessory",1,evidence_ids=("manifest-doc",))]
    manifest=FixedContentProductManifest("generic-1","generic-collectible-game","gift-collection",tuple(components),completeness,
        (MANIFEST_REF,),date(2026,8,1),NOW,unknowns=() if completeness=="complete" else ("contents not fully published",))
    offer=ProductAcquisitionOffer("offer-1","generic-1","seller",NOW,currency,Decimal("20"),(OFFER_REF,),
        Decimal("2"),Decimal("1"),Decimal("0.50"),Decimal("3"),NOW)
    values=[] if "card-1" in unpriced else [ComponentValuationInput("card-1",observation(currency=market_currency,provider=market_provider),"printing-1","foil","en","showcase")]
    if "token-sheet" not in unpriced:
        # Non-card components are explicitly unpriced in the normal fixture; a valuation binding is card/Printing-only by design.
        unpriced=tuple(unpriced)+("token-sheet",)
    costs=SinglesTransactionCosts(currency,Decimal("4"),Decimal("0.25"),Decimal("1"),tx_complete,("transaction-policy",),("one consolidated order",))
    sources=(source("manifest-source","publisher",D1,published_at=NOW),source("offer-source","seller",D2),
        source("market-source",market_provider,D3),source("transaction-policy","policy-owner",D3))
    return FixedContentAcquisitionEvidencePacket(manifest,offer,tuple(values),tuple(unpriced),sources,costs,NOW,
        states or {"shipping":"known","tax":"known","fees":"known","discounts":"known"},"available",("offer-source",),future)

class EvidencePacketTests(unittest.TestCase):
    def test_schema_determinism_identity_and_preservation(self):
        p=packet(unpriced=("token-sheet",))
        schema=json.loads(Path("src/schemas/v1/fixed-content-acquisition-evidence-v1.schema.json").read_text())
        Draft202012Validator(schema).validate(p.to_dict())
        self.assertEqual(p.to_json(),p.to_json()); self.assertTrue(p.packet_id.startswith("fixed-content-evidence-sha256:"))
        card=p.to_dict()["manifest"]["components"][0]
        self.assertEqual((card["quantity"],card["printing_id"],card["finish"],card["language"],card["treatment"]),(2,"printing-1","foil","en","showcase"))
        self.assertEqual(p.to_dict()["manifest"]["components"][1]["component_type"],"printed-accessory")
        self.assertEqual(p.sealed_offer.effective_cost,Decimal("20.50")); self.assertEqual(p.transaction_costs.total,Decimal("5.25"))
        self.assertEqual(p.sources[0].retrieved_at,NOW); self.assertEqual(p.manifest.effective_at,NOW)

    def test_replay_byte_identity_digest_and_conflict(self):
        p=packet(unpriced=("token-sheet",)); repo=EvidencePacketReplayRepository(); first=repo.retain(p)
        self.assertEqual(first,repo.retain(p)); self.assertEqual(first,repo.replay(p.packet_id))
        repo._bytes[p.packet_id]=first+b" "
        with self.assertRaises(ProductValidationError): repo.retain(p)
        repo._bytes[p.packet_id]=first.replace(b'"generic-1"',b'"generic-X"',1)
        with self.assertRaises(ProductValidationError): repo.replay(p.packet_id)

    def test_complete_mapping_and_explicit_unknown(self):
        p=packet(unpriced=("card-1","token-sheet"))
        self.assertEqual(p.unpriced_component_ids,("card-1","token-sheet"))
        self.assertEqual(review_evidence_packet(p,"human",NOW).status,NOT_READY_FOR_EVALUATION)
        with self.assertRaises(ProductValidationError):
            replace(p,unpriced_component_ids=())

    def test_ready_requires_all_valued_including_non_card(self):
        # A generic non-MTG collectible component can be valued when represented by a compatible Printing observation.
        base=packet(unpriced=("token-sheet",)); component=GuaranteedComponent("piece","collectible-piece",1,"piece-edition","standard","xx","numbered",("manifest-doc",))
        manifest=FixedContentProductManifest("generic-1","non-mtg-game","collection",(component,),"complete",(MANIFEST_REF,),effective_at=NOW)
        value=ComponentValuationInput("piece",observation("piece-edition","18",finish="standard",language="xx"),"piece-edition","standard","xx","numbered")
        ready=FixedContentAcquisitionEvidencePacket(manifest,base.sealed_offer,(value,),(),base.sources,base.transaction_costs,NOW,base.sealed_cost_input_states,"available",("offer-source",))
        review=review_evidence_packet(ready,"human-reviewer",NOW)
        self.assertEqual(review.status,READY_FOR_EVALUATION); self.assertEqual(review.issues,())

    def test_not_ready_gates(self):
        cases=[packet(completeness="incomplete",unpriced=("token-sheet",)),
            packet(unpriced=("card-1","token-sheet")),packet(unpriced=("token-sheet",),tx_complete="unknown"),
            packet(unpriced=("token-sheet",),market_currency="EUR"),
            packet(unpriced=("token-sheet",),states={"shipping":"known","tax":"unknown","fees":"known","discounts":"known"})]
        expected=("manifest_not_complete","unpriced_components","transaction_costs_not_complete","incompatible_currencies","sealed_effective_cost_inputs_incomplete")
        for p,issue in zip(cases,expected): self.assertIn(issue,review_evidence_packet(p,"human",NOW).issues)

    def test_market_dimension_and_timestamp_gates(self):
        p=packet(unpriced=("token-sheet",))
        cutoff=datetime(2026,8,17,tzinfo=timezone.utc)
        issues=review_evidence_packet(p,"human",NOW,acceptable_observed_after=cutoff).issues
        self.assertIn("singles_timestamp_not_acceptable",issues); self.assertIn("sealed_timestamp_not_acceptable",issues)
        # Two differently sourced observations fail the packet review's same-market comparison dimension.
        c2=GuaranteedComponent("card-2","card",1,"printing-2","foil","en","showcase",("manifest-doc",))
        m=FixedContentProductManifest("generic-1","game","collection",p.manifest.components+(c2,),"complete",(MANIFEST_REF,),effective_at=NOW)
        v2=ComponentValuationInput("card-2",observation("printing-2",provider="other-market"),"printing-2","foil","en","showcase")
        mixed=FixedContentAcquisitionEvidencePacket(m,p.sealed_offer,p.valuations+(v2,),p.unpriced_component_ids,
            p.sources+(source("other-market-source","other-market",D3),),p.transaction_costs,NOW,p.sealed_cost_input_states,"available",("offer-source",))
        self.assertIn("incompatible_market_dimensions",review_evidence_packet(mixed,"human",NOW).issues)

    def test_validation_provenance_digest_future_fields_and_immutability(self):
        with self.assertRaises(ProductValidationError): source("bad","publisher","sha256:xyz")
        with self.assertRaises(ProductValidationError): packet(unpriced=("token-sheet",),future={"price_forecast":()})
        p=packet(unpriced=("token-sheet",),future={"presale_observations":()})
        with self.assertRaises((FrozenInstanceError,AttributeError)): p.manifest.product_id="changed"
        self.assertEqual(p.future_evidence["presale_observations"],())

    def test_no_named_product_special_cases(self):
        source_text=Path("src/product_intelligence/evidence_packet.py").read_text().lower()
        for forbidden in ("crack the plates","hobbit","secret lair","commander deck"):
            self.assertNotIn(forbidden,source_text)

if __name__ == "__main__": unittest.main()
