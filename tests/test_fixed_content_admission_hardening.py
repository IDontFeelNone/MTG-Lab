"""Admission regressions; synthetic inputs only, with no domain evaluation."""
from dataclasses import FrozenInstanceError, replace
from datetime import timedelta, timezone
import hashlib
import json
from pathlib import Path
import unittest

from jsonschema import Draft202012Validator, ValidationError
from product_intelligence import (
    EvidencePacketReview, EvidencePacketReplayRepository, ProductValidationError,
    READY_FOR_EVALUATION, NOT_READY_FOR_EVALUATION, REVIEW_SCHEMA,
    assess_evidence_packet, require_ready_evidence_review, review_evidence_packet,
)
from tests.test_fixed_content_evidence_packet import NOW, packet
from product_intelligence.evidence_packet import _format_checker

ROOT = Path(__file__).resolve().parents[1]
CUTOFF = NOW - timedelta(days=1)


def complete_packet():
    base = packet(unpriced=("token-sheet",))
    return replace(base, manifest=replace(base.manifest, components=(base.manifest.components[0],)),
                   unpriced_component_ids=())


def approved_review(p, **changes):
    args = {"acceptable_observed_after": CUTOFF, "human_approved": True,
            "reviewed_packet_id": p.packet_id, "review_reference": "review:synthetic-approval-1"}
    args.update(changes)
    return review_evidence_packet(p, "synthetic-reviewer", NOW, **args)


def eligibility(p, *, as_of=NOW, cutoff=CUTOFF):
    return assess_evidence_packet(p, as_of=as_of, acceptable_observed_after=cutoff)


def packet_schema():
    schema = json.loads((ROOT / "src/schemas/v1/fixed-content-acquisition-evidence-v1.schema.json").read_text())
    return Draft202012Validator(schema, format_checker=_format_checker())


class FixedContentAdmissionHardeningTests(unittest.TestCase):
    def test_packet_mappings_and_observation_provenance_are_deeply_immutable(self):
        base = complete_packet()
        states = dict(base.sealed_cost_input_states)
        future_refs = [base.sources[0].source_id]
        future = {"reprint_risk": future_refs}
        provenance = dict(base.valuations[0].observation.provenance)
        provenance["nested"] = {"items": ["original"]}
        obs = replace(base.valuations[0].observation, provenance=provenance)
        p = replace(base, sealed_cost_input_states=states, future_evidence=future,
                    valuations=(replace(base.valuations[0], observation=obs),))
        before = (p.packet_id, p.to_json())
        states["tax"] = "unknown"
        future_refs.append("changed")
        future["reprint_risk"] = []
        provenance["nested"]["items"].append("changed")
        exported = p.to_dict()
        exported["sealed_cost_input_states"]["tax"] = "unknown"
        exported["valuations"][0]["market_observation"]["provenance"]["nested"]["items"].append("changed")
        with self.assertRaises(TypeError):
            p.sealed_cost_input_states["tax"] = "unknown"
        with self.assertRaises(TypeError):
            p.future_evidence["reprint_risk"] = ()
        with self.assertRaises(TypeError):
            p.valuations[0].observation.provenance["nested"]["items"][0] = "changed"
        with self.assertRaises(FrozenInstanceError):
            p.transaction_costs.shipping = 999
        self.assertEqual(before, (p.packet_id, p.to_json()))

    def test_original_v1_packet_identity_and_bytes_remain_compatible(self):
        p = packet(unpriced=("token-sheet",))
        self.assertEqual(p.packet_id, "fixed-content-evidence-sha256:766c6acafbdea8f1eb9ed13a72e5da11ac39c3992993ab614998051dc8d66765")
        self.assertEqual(p.to_json(), json.dumps(p.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        packet_schema().validate(p.to_dict())

    def test_reordered_inputs_replay_identically_without_aliases(self):
        p = complete_packet()
        copy = replace(p, sources=list(reversed(p.sources)),
                       sealed_cost_input_states=dict(reversed(list(p.sealed_cost_input_states.items()))))
        repo = EvidencePacketReplayRepository()
        encoded = repo.retain(p)
        self.assertEqual(encoded, repo.retain(copy))
        self.assertEqual(encoded, repo.replay(p.packet_id))
        repo._bytes[p.packet_id] = encoded + b" "
        with self.assertRaisesRegex(ProductValidationError, "canonical"):
            repo.replay(p.packet_id)

    def test_replay_rejects_wrong_embedded_identity_and_nested_contract_drift(self):
        p = complete_packet()
        repo = EvidencePacketReplayRepository()
        repo.retain(p)
        data = p.to_dict()
        data["packet_id"] = "fixed-content-evidence-sha256:" + "0" * 64
        repo._bytes[p.packet_id] = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        with self.assertRaisesRegex(ProductValidationError, "digest"):
            repo.replay(p.packet_id)
        data = p.to_dict()
        data["manifest"]["components"][0]["quantity"] = 0
        repo._bytes[p.packet_id] = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        with self.assertRaisesRegex(ProductValidationError, "contract"):
            repo.replay(p.packet_id)

    def test_positive_cost_bundle_requires_known_referenced_provenance(self):
        p = complete_packet()
        self.assertTrue(eligibility(p).eligible)
        no_refs = replace(p, transaction_costs=replace(p.transaction_costs, evidence_source_ids=()))
        self.assertIn("transaction_cost_provenance_missing", eligibility(no_refs).issues)
        for state in ("unknown", "incomplete", "not_applicable"):
            with self.subTest(state=state):
                sources = tuple(replace(x, evidence_state=state) if x.source_id == "transaction-policy" else x for x in p.sources)
                self.assertIn("provenance_not_sufficient", eligibility(replace(p, sources=sources)).issues)
        with self.assertRaisesRegex(ProductValidationError, "absent source"):
            replace(p, transaction_costs=replace(p.transaction_costs, evidence_source_ids=("absent",)))
        with self.assertRaisesRegex(ProductValidationError, "duplicate"):
            replace(p.transaction_costs, evidence_source_ids=("transaction-policy", "transaction-policy"))

    def test_zero_costs_require_evidence_and_explicit_seller_order_basis(self):
        p = complete_packet()
        costs = replace(p.transaction_costs, shipping="0", marketplace_fees="0", other_costs="0",
                        seller_order_assumptions=("Single pickup order; no buyer fees or other charges.",))
        zero = replace(p, transaction_costs=costs)
        self.assertEqual(zero.transaction_costs.total, 0)
        self.assertTrue(eligibility(zero).eligible)
        self.assertEqual(approved_review(zero).status, READY_FOR_EVALUATION)
        signed_zero = replace(zero, transaction_costs=replace(costs, shipping="-0.00"))
        self.assertTrue(eligibility(signed_zero).eligible)
        packet_schema().validate(signed_zero.to_dict())
        self.assertIn("zero_transaction_cost_basis_missing", eligibility(replace(zero,
            transaction_costs=replace(costs, seller_order_assumptions=()))).issues)
        self.assertIn("transaction_cost_provenance_missing", eligibility(replace(zero,
            transaction_costs=replace(costs, evidence_source_ids=()))).issues)

    def test_unknown_cost_is_null_not_zero_and_never_ready(self):
        p = complete_packet()
        for state in ("unknown", "incomplete"):
            with self.subTest(state=state):
                costs = replace(p.transaction_costs, shipping=None, completeness=state)
                unknown = replace(p, transaction_costs=costs)
                self.assertIsNone(costs.shipping)
                self.assertIsNone(costs.total)
                self.assertIsNone(unknown.to_dict()["transaction_costs"]["total"])
                packet_schema().validate(unknown.to_dict())
                self.assertIn("transaction_costs_not_complete", eligibility(unknown).issues)
                self.assertEqual(approved_review(unknown).status, NOT_READY_FOR_EVALUATION)
        with self.assertRaisesRegex(ProductValidationError, "all amounts"):
            replace(p.transaction_costs, shipping=None)
        for amount in ("-1", "NaN", "Infinity", True):
            with self.subTest(amount=amount), self.assertRaises(ProductValidationError):
                replace(p.transaction_costs, shipping=amount)

    def test_freshness_is_explicit_deterministic_and_inclusive(self):
        p = complete_packet()
        self.assertTrue(eligibility(p, cutoff=NOW).eligible)
        self.assertEqual(eligibility(p), eligibility(p))
        self.assertIn("freshness_policy_missing", eligibility(p, cutoff=None).issues)
        review = approved_review(p, acceptable_observed_after=None)
        self.assertEqual(review.status, NOT_READY_FOR_EVALUATION)
        self.assertEqual(review.acceptable_observed_after, None)
        # Equivalent time-zone representations produce the same review policy.
        shifted = NOW.astimezone(timezone(timedelta(hours=-4)))
        self.assertEqual(review_evidence_packet(p, "synthetic-reviewer", shifted,
            acceptable_observed_after=CUTOFF, human_approved=True, reviewed_packet_id=p.packet_id,
            review_reference="review:synthetic-approval-1"), approved_review(p))
        with self.assertRaises(ProductValidationError):
            eligibility(p, cutoff=NOW + timedelta(seconds=1))
        with self.assertRaises(ProductValidationError):
            eligibility(p, cutoff=CUTOFF.replace(tzinfo=None))
        with self.assertRaises(ProductValidationError):
            eligibility(p, as_of=NOW.replace(tzinfo=None))

    def test_stale_sealed_and_singles_observations_fail_independently(self):
        p = complete_packet()
        stale = CUTOFF - timedelta(seconds=1)
        sealed = replace(p, sealed_offer=replace(p.sealed_offer, observed_at=stale))
        self.assertIn("sealed_timestamp_not_acceptable", eligibility(sealed).issues)
        self.assertNotIn("singles_timestamp_not_acceptable", eligibility(sealed).issues)
        value = p.valuations[0]
        singles = replace(p, valuations=(replace(value, observation=replace(value.observation, observed_at=stale)),))
        self.assertIn("singles_timestamp_not_acceptable", eligibility(singles).issues)
        self.assertNotIn("sealed_timestamp_not_acceptable", eligibility(singles).issues)
        at_boundary = replace(p, sealed_offer=replace(p.sealed_offer, observed_at=CUTOFF),
            valuations=(replace(value, observation=replace(value.observation, observed_at=CUTOFF)),))
        self.assertTrue(eligibility(at_boundary).eligible)

    def test_future_sealed_and_singles_observations_fail(self):
        p = complete_packet()
        future = NOW + timedelta(seconds=1)
        sealed = replace(p, sealed_offer=replace(p.sealed_offer, observed_at=future))
        self.assertIn("sealed_timestamp_in_future", eligibility(sealed).issues)
        value = p.valuations[0]
        singles = replace(p, valuations=(replace(value, observation=replace(value.observation,
            observed_at=future, recorded_at=future)),))
        self.assertIn("singles_timestamp_in_future", eligibility(singles).issues)
        self.assertEqual(approved_review(singles).status, NOT_READY_FOR_EVALUATION)

    def test_future_recording_retrieval_effective_and_assembly_times_fail(self):
        p = complete_packet()
        future = NOW + timedelta(seconds=1)
        value = p.valuations[0]
        cases = [replace(p, assembled_at=future),
                 replace(p, sealed_offer=replace(p.sealed_offer, effective_at=future)),
                 replace(p, manifest=replace(p.manifest, effective_at=future)),
                 replace(p, valuations=(replace(value, observation=replace(value.observation, recorded_at=future)),)),
                 replace(p, sources=tuple(replace(x, retrieved_at=future) if x.source_id == "transaction-policy" else x for x in p.sources))]
        for candidate in cases:
            with self.subTest(packet=candidate.packet_id):
                self.assertIn("evidence_timestamp_in_future", eligibility(candidate).issues)
        later = NOW + timedelta(hours=1)
        self.assertIn("evidence_timestamp_after_assembly", eligibility(cases[-1], as_of=later).issues)
        sources = tuple(replace(x, published_at=NOW, retrieved_at=CUTOFF) if x.source_id == "transaction-policy" else x for x in p.sources)
        self.assertIn("source_timestamp_order_invalid", eligibility(replace(p, sources=sources)).issues)

    def test_unknown_or_unavailable_sealed_availability_never_qualifies(self):
        p = complete_packet()
        for state, issue in (("unknown", "sealed_availability_unknown"), ("unavailable", "sealed_offer_unavailable")):
            with self.subTest(state=state):
                candidate = replace(p, availability_state=state)
                self.assertIn(issue, eligibility(candidate).issues)
                self.assertEqual(approved_review(candidate).status, NOT_READY_FOR_EVALUATION)
        with self.assertRaisesRegex(ProductValidationError, "provenance"):
            replace(p, availability_source_ids=())
        sources = tuple(replace(x, evidence_state="unknown") if x.source_id == "offer-source" else x for x in p.sources)
        self.assertIn("provenance_not_sufficient", eligibility(replace(p, sources=sources)).issues)

    def test_not_applicable_sealed_cost_cannot_contradict_nonzero_amount(self):
        p = complete_packet()
        states = dict(p.sealed_cost_input_states, shipping="not_applicable")
        with self.assertRaisesRegex(ProductValidationError, "must be zero"):
            replace(p, sealed_cost_input_states=states)
        zero = replace(p, sealed_offer=replace(p.sealed_offer, shipping="0"), sealed_cost_input_states=states)
        self.assertTrue(eligibility(zero).eligible)

    def test_automated_eligibility_does_not_create_affirmative_human_approval(self):
        p = complete_packet()
        automatic = eligibility(p)
        self.assertTrue(automatic.eligible)
        self.assertFalse(hasattr(automatic, "status"))
        self.assertFalse(hasattr(automatic, "human_approved"))
        review = review_evidence_packet(p, "automation", NOW, acceptable_observed_after=CUTOFF)
        self.assertEqual(review.status, NOT_READY_FOR_EVALUATION)
        self.assertFalse(review.human_approved)
        self.assertIn("human_approval_missing", review.issues)
        with self.assertRaisesRegex(ProductValidationError, "affirmative"):
            require_ready_evidence_review(p, review, as_of=NOW, acceptable_observed_after=CUTOFF)

    def test_affirmative_review_requires_exact_packet_and_durable_reference(self):
        p = complete_packet()
        review = approved_review(p)
        require_ready_evidence_review(p, review, as_of=NOW, acceptable_observed_after=CUTOFF)
        self.assertEqual(review.schema_version, REVIEW_SCHEMA)
        self.assertEqual(review.packet_id, p.packet_id)
        self.assertEqual(review.acceptable_observed_after, CUTOFF)
        restored = EvidencePacketReview.from_dict(json.loads(json.dumps(review.to_dict(), sort_keys=True)))
        self.assertEqual(restored, review)
        require_ready_evidence_review(p, restored, as_of=NOW, acceptable_observed_after=CUTOFF)
        for changes, issue in [({"human_approved": False}, "human_approval_missing"),
                               ({"reviewed_packet_id": "wrong"}, "human_review_packet_mismatch"),
                               ({"review_reference": None}, "human_review_reference_missing")]:
            with self.subTest(changes=changes):
                result = approved_review(p, **changes)
                self.assertIn(issue, result.issues)
                self.assertEqual(result.status, NOT_READY_FOR_EVALUATION)
        for changes in ({"human_approved": "true"}, {"review_reference": " "}):
            with self.subTest(changes=changes), self.assertRaises(ProductValidationError):
                approved_review(p, **changes)

    def test_review_reuse_rejects_packet_policy_and_version_changes(self):
        p = complete_packet()
        review = approved_review(p)
        changed = replace(p, sealed_offer=replace(p.sealed_offer, listed_price="21"))
        with self.assertRaisesRegex(ProductValidationError, "bind"):
            require_ready_evidence_review(changed, review, as_of=NOW, acceptable_observed_after=CUTOFF)
        for as_of, cutoff in ((NOW + timedelta(seconds=1), CUTOFF), (NOW, NOW)):
            with self.subTest(as_of=as_of, cutoff=cutoff), self.assertRaisesRegex(ProductValidationError, "new human review"):
                require_ready_evidence_review(p, review, as_of=as_of, acceptable_observed_after=cutoff)
        with self.assertRaisesRegex(ProductValidationError, "unsupported review schema"):
            replace(review, schema_version="fixed-content-acquisition-evidence-review-v1")
        for changes in ({"human_approved": False}, {"review_reference": None}, {"acceptable_observed_after": None}):
            with self.subTest(changes=changes), self.assertRaises(ProductValidationError):
                replace(review, **changes)
        # A manually constructed READY record cannot bypass packet eligibility.
        incomplete = replace(p, availability_state="unknown")
        forged = replace(review, packet_id=incomplete.packet_id)
        with self.assertRaisesRegex(ProductValidationError, "not eligible"):
            require_ready_evidence_review(incomplete, forged, as_of=NOW, acceptable_observed_after=CUTOFF)

    def test_nested_schema_rejects_wrong_versions_extra_fields_and_invalid_types(self):
        p = complete_packet()
        validator = packet_schema()
        validator.check_schema(validator.schema)
        mutations = [lambda d: d["manifest"].update(schema_version="future"),
                     lambda d: d["sealed_offer"].update(schema_version="future"),
                     lambda d: d["valuations"][0].update(schema_version="future"),
                     lambda d: d["valuations"][0]["market_observation"].update(schema_version="future"),
                     lambda d: d["manifest"]["components"][0].update(quantity=True),
                     lambda d: d["manifest"]["components"][0].update(price_forecast="1"),
                     lambda d: d["sealed_offer"].update(observed_at="not-a-time"),
                     lambda d: d["valuations"][0]["market_observation"].update(price=-1),
                     lambda d: d["sources"][0].update(content_digest="sha256:bad")]
        for index, mutate in enumerate(mutations):
            d = p.to_dict()
            mutate(d)
            with self.subTest(mutation=index), self.assertRaises(ValidationError):
                validator.validate(d)

    def test_typed_packet_rejects_invalid_nested_structures(self):
        p = complete_packet()
        for changes in ({"sources": ({},)}, {"valuations": ({},)}):
            with self.subTest(changes=changes), self.assertRaises(ProductValidationError):
                replace(p, **changes)
        # Same component ID with different dimensions must not collapse to one map key.
        duplicate = replace(p.manifest.components[0], printing_id="other-printing")
        manifest = replace(p.manifest, components=p.manifest.components + (duplicate,))
        with self.assertRaisesRegex(ProductValidationError, "duplicate guaranteed component ID"):
            replace(p, manifest=manifest)
        with self.assertRaises(ProductValidationError):
            replace(p, future_evidence={"reprint_risk": "manifest-source"})
        with self.assertRaises(ProductValidationError):
            replace(p, manifest=replace(p.manifest, release_date={"mutable": []}))
        with self.assertRaises(ProductValidationError):
            replace(p, manifest=replace(p.manifest, evidence=(replace(p.manifest.evidence[0], locator=[]),)))

    def test_review_schema_enforces_approval_and_missing_policy_is_not_ready(self):
        p = complete_packet()
        path = ROOT / "src/schemas/v1/fixed-content-acquisition-evidence-review-v2.schema.json"
        schema = json.loads(path.read_text())
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema, format_checker=_format_checker())
        ready = approved_review(p).to_dict()
        validator.validate(ready)
        validator.validate(review_evidence_packet(p, "automation", NOW).to_dict())
        for key, value in (("human_approved", False), ("review_reference", None),
                           ("acceptable_observed_after", None), ("schema_version", "fixed-content-acquisition-evidence-review-v1")):
            with self.subTest(key=key), self.assertRaises(ValidationError):
                validator.validate(dict(ready, **{key: value}))
            with self.subTest(reader_key=key), self.assertRaises(ProductValidationError):
                EvidencePacketReview.from_dict(dict(ready, **{key: value}))
        with self.assertRaises(ProductValidationError):
            EvidencePacketReview("bad-id", "reviewer", NOW, NOT_READY_FOR_EVALUATION, ("issue",))

    def test_critical_missing_provenance_and_dimension_mismatch_remain_fail_closed(self):
        p = complete_packet()
        manifest = replace(p.manifest, components=(replace(p.manifest.components[0], evidence_ids=()),))
        self.assertIn("manifest_provenance_missing", eligibility(replace(p, manifest=manifest)).issues)
        dimension = replace(p.manifest.components[0], treatment="different")
        candidate = replace(p, manifest=replace(p.manifest, components=(dimension,)))
        self.assertIn("incompatible_component_dimensions", eligibility(candidate).issues)
        self.assertEqual(approved_review(candidate).status, NOT_READY_FOR_EVALUATION)

    def test_admission_and_replay_leave_all_protected_data_unchanged(self):
        def inventory():
            return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in sorted((ROOT / "data").rglob("*")) if p.is_file()}
        before = inventory()
        p = complete_packet()
        repo = EvidencePacketReplayRepository()
        repo.retain(p)
        repo.replay(p.packet_id)
        review = approved_review(p)
        require_ready_evidence_review(p, review, as_of=NOW, acceptable_observed_after=CUTOFF)
        self.assertEqual(before, inventory())


if __name__ == "__main__":
    unittest.main()
