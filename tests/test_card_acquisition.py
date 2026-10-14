from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.acquisition import (CardAcquisitionAdapter, CardAcquisitionDossier,
    CardAcquisitionError, CardAcquisitionInput)
from card_intelligence.mechanics import content_identity, stable_json
from decision_intelligence.models import identity as decision_identity


from historical_catalog import historical_repository

# This module replays the retained original catalog, not the current catalog.
ROOT = historical_repository()
PRINTINGS = ("5c8d3bc4-32fc-5b26-84bf-9921e5884d43",
             "72783a15-4847-5448-8f1d-0c40379594d3",
             "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade")


class CardAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapter = CardAcquisitionAdapter(ROOT / "data")
        cls.protected = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "data").rglob("*") if p.is_file()}

    def fixture(self):
        buyer = {"buyer_id": "fictional-buyer", "destination_country": "US", "postal_code": "00000",
            "purchase_method": "synthetic_guest", "discount_basis": "fictional explicit discounts",
            "order_assumption": "one_copy_independent_order"}
        context = {"objective": "Demonstrate supplied personal collecting priorities, not competitive suitability.",
            "objective_id": "synthetic-collecting-objective", "budget": "10.00", "currency": "USD", "money_scale": 2,
            "buyer_context": buyer, "priority_order": [PRINTINGS[0], PRINTINGS[2], PRINTINGS[1]],
            "hard_constraints": {"condition": "near_mint"}, "freshness_policy": {"max_age_seconds": 86400},
            "eligibility_required": False}
        dimensions = {"finish": "nonfoil", "language": "English", "treatment": None}
        ownership = {"buyer_id": buyer["buyer_id"], "scope_complete": True, "scope_printing_ids": list(PRINTINGS),
            "lots": [{"lot_id": "owned-physical-copy", "printing_id": PRINTINGS[0], "quantity": 1,
                      **dimensions, "condition": "near_mint"}]}
        requirements, offers, candidates = [], [], []
        values = (("3.00", "1.00", "0.25", "0.10", "0.15"),
                  ("1.00", "1.00", "0.10", "0.10", "0.20"),
                  ("7.00", "1.00", "0.70", "0.10", "0.80"))
        for index, pid in enumerate(PRINTINGS):
            card = self.adapter.printings[pid].canonical_values["card_id"]
            req = {"card_id": card, "printing_id": pid, "acceptable_printing_ids": [pid],
                "desired_quantity": 1, "preferred_dimensions": dimensions.copy()}
            offer = {"offer_id": f"fictional-offer-{index}", "printing_id": pid, "currency": "USD",
                "buyer_id": buyer["buyer_id"], "buyer_context_identity": content_identity(buyer),
                "order_assumption": buyer["order_assumption"], "seller_id": "fictional-seller", "market": "US",
                **dimensions, "condition": "near_mint", "quantity": 1, "available": True, "available_quantity": 1,
                "observed_at": "2026-10-12T19:00:00Z", "retrieved_at": "2026-10-12T19:01:00Z",
                "valid_until": "2026-10-12T20:00:00Z",
                "costs": {name: {"amount": amount, "basis": "Explicit fictional transaction term; not a market observation."}
                    for name, amount in zip(("unit_price", "shipping", "taxes", "fees", "discounts"), values[index])}}
            requirements.append(req)
            offers.append(offer)
            candidates.append({**copy.deepcopy(req),
                "requirements_binding": {"source_id": "synthetic-input", "pointer": f"/requirements/{index}"},
                "offer": {"value": copy.deepcopy(offer), "binding": {"source_id": "synthetic-input", "pointer": f"/offers/{index}"}},
                "eligibility": None})
        source = {"mode": "synthetic_demonstration", "kind": "synthetic_fixture", "provider_identity": "synthetic-fixture",
            "seller_identity": "fictional-seller", "captured_at": "2026-10-12T19:01:00Z",
            "context": context, "ownership": ownership, "requirements": requirements, "offers": offers}
        packet = {"schema_version": "card-acquisition-input-v1", "mode": "synthetic_demonstration",
            "as_of": "2026-10-12T19:02:00Z", "canonical_snapshot_id": self.adapter.mechanical.snapshot_id,
            "sources": [{"source_id": "synthetic-input", "relative_path": "source.json", "content_digest": "",
                "kind": source["kind"], "provider_identity": source["provider_identity"], "seller_identity": source["seller_identity"],
                "captured_at": source["captured_at"], "review": {"status": "not_applicable"}}],
            "context": {"value": copy.deepcopy(context), "binding": {"source_id": "synthetic-input", "pointer": "/context"}},
            "ownership": {"value": copy.deepcopy(ownership), "binding": {"source_id": "synthetic-input", "pointer": "/ownership"}},
            "candidates": candidates}
        return packet, source

    def evaluate(self, change=None, *, bind=True):
        packet, source = self.fixture()
        if change:
            change(packet)
        if bind:
            source["context"] = packet["context"]["value"]
            source["ownership"] = packet["ownership"]["value"]
            source["requirements"] = [{k: c[k] for k in ("card_id", "printing_id", "acceptable_printing_ids", "desired_quantity", "preferred_dimensions")}
                                      for c in packet["candidates"]]
            source["offers"] = [c["offer"]["value"] if c["offer"] else None for c in packet["candidates"]]
        raw = stable_json(source).encode()
        packet["sources"][0]["content_digest"] = "sha256:" + hashlib.sha256(raw).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "source.json").write_bytes(raw)
            return self.adapter.evaluate(packet, source_root=Path(directory))

    def assert_abstains(self, dossier, phrase):
        value = dossier.to_dict()
        self.assertEqual(value["decision"]["recommendation"]["outcome"], "abstain")
        self.assertFalse(value["actual_purchase_advice"])
        self.assertIn(phrase, " ".join(value["blockers"]))

    @staticmethod
    def rehash(document):
        recommendation = document["decision"]["recommendation"]
        recommendation["recommendation_id"] = decision_identity("recommendation-sha256:",
            {k: v for k, v in recommendation.items() if k != "recommendation_id"})
        document["dossier_id"] = content_identity({k: v for k, v in document.items() if k != "dossier_id"})
        return document

    def real_unit_evaluate(self, change=None):
        # Fabricated temporary unit records verify the real-world gate. They
        # are never retained as offers, review attestations, or purchase advice.
        packet, source = self.fixture()
        packet.update(mode="real_world", sources=[])
        packet["context"]["value"]["eligibility_required"] = True
        eligibility = []
        for index, candidate in enumerate(packet["candidates"]):
            candidate["requirements_binding"]["source_id"] = "buyer"
            candidate["offer"]["binding"]["source_id"] = "offers"
            value = {"status": "reviewed", "eligible": True, "card_id": candidate["card_id"],
                "printing_id": candidate["printing_id"], "objective_id": packet["context"]["value"]["objective_id"],
                "mechanical_dossier_id": self.adapter.mechanical.dossier(candidate["card_id"]).to_dict()["dossier_id"],
                "basis_category": "reviewed_mechanical_objective", "basis": "Fictional scoped unit test review."}
            candidate["eligibility"] = {"value": value,
                "binding": {"source_id": "eligibility", "pointer": f"/eligibility/{index}"}}
            eligibility.append(value)
        packet["context"]["binding"]["source_id"] = "buyer"
        packet["ownership"]["binding"]["source_id"] = "buyer"
        metadata = {k: source[k] for k in ("provider_identity", "seller_identity", "captured_at")}
        documents = {
            "buyer": {**metadata, "mode": "real_world", "kind": "buyer_declaration",
                "context": packet["context"]["value"], "ownership": packet["ownership"]["value"],
                "requirements": [{k: c[k] for k in ("card_id", "printing_id", "acceptable_printing_ids", "desired_quantity", "preferred_dimensions")}
                    for c in packet["candidates"]]},
            "offers": {**metadata, "mode": "real_world", "kind": "reviewed_offer",
                "offers": [c["offer"]["value"] for c in packet["candidates"]]},
            "eligibility": {**metadata, "mode": "real_world", "kind": "objective_eligibility_review",
                "eligibility": eligibility}}
        reviews = {sid: {"status": "reviewed", "reviewer": "fictional-unit-only-reviewer",
            "reviewed_at": packet["as_of"]} for sid in documents}
        if change:
            change(packet, documents, reviews)
        with tempfile.TemporaryDirectory() as directory:
            for sid, document in documents.items():
                raw = stable_json(document).encode()
                digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                Path(directory, sid + ".json").write_bytes(raw)
                reviews[sid].setdefault("content_digest", digest)
                packet["sources"].append({"source_id": sid, "relative_path": sid + ".json",
                    "content_digest": digest, "kind": document["kind"], **metadata, "review": reviews[sid]})
            return self.adapter.evaluate(packet, source_root=Path(directory))

    def test_exact_production_selection_and_existing_decision_engine(self):
        dossier = self.evaluate().to_dict()
        result = dossier["decision"]["recommendation"]
        self.assertEqual(result["outcome"], "selected")
        self.assertEqual(result["selected_alternative_id"], PRINTINGS[2])
        self.assertFalse(dossier["actual_purchase_advice"])
        rows = {r["printing_id"]: r for r in dossier["candidates"]}
        self.assertEqual(rows[PRINTINGS[2]]["complete_cost"], "8.00")
        self.assertEqual(rows[PRINTINGS[2]]["remaining_budget"], "2.00")
        self.assertEqual(rows[PRINTINGS[0]]["owned_acceptable_quantity"], 1)
        self.assertEqual(rows[PRINTINGS[0]]["missing_quantity"], 0)
        self.assertIn("already_owned", rows[PRINTINGS[0]]["exclusion_reasons"][0])
        self.assertTrue(result["counterarguments"])
        self.assertTrue(result["decision_change_conditions"])
        self.assertEqual(result["policy"]["policy_id"], "collection-aware-card-acquisition")

    def test_affordability_is_enforced_not_merely_stored_in_request(self):
        dossier = self.evaluate(lambda p: p["context"]["value"].update(budget="3.00")).to_dict()
        self.assertEqual(dossier["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[1])
        self.assertIn("over_budget", next(r for r in dossier["candidates"] if r["printing_id"] == PRINTINGS[2])["exclusion_reasons"])
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"].update(budget="1.00")), "no_missing")

    def test_missing_offer_for_known_owned_copy_remains_null_not_zero(self):
        dossier = self.evaluate(lambda p: p["candidates"][0].update(offer=None)).to_dict()
        owned = next(r for r in dossier["candidates"] if r["printing_id"] == PRINTINGS[0])
        self.assertIsNone(owned["complete_cost"])
        self.assertEqual(dossier["decision"]["recommendation"]["outcome"], "selected")

    def test_unknown_ownership_scope_or_physical_dimensions_abstain(self):
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"].update(scope_complete=False)), "ownership scope")
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"]["lots"][0].pop("finish")), "finish")
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"]["lots"][0].pop("condition")), "condition is unknown")
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"].update(buyer_id="another-person")), "different or unknown buyer")

    def test_unknown_sentinels_cannot_establish_owned_condition_or_buyer_context(self):
        for sentinel in ("unknown", " NULL ", "Incomplete", "unsupported", "unresolved", "missing"):
            self.assert_abstains(self.evaluate(lambda p, s=sentinel:
                p["ownership"]["value"]["lots"][0].update(condition=s)), "condition is unknown")
            self.assert_abstains(self.evaluate(lambda p, s=sentinel:
                p["context"]["value"]["hard_constraints"].update(condition=s)), "physical condition is required")
        for field in ("buyer_id", "destination_country", "postal_code", "purchase_method", "discount_basis"):
            self.assert_abstains(self.evaluate(lambda p, f=field:
                p["context"]["value"]["buyer_context"].update({f: " UNKNOWN "})), f"buyer {field}")
        for field in ("objective", "objective_id"):
            self.assert_abstains(self.evaluate(lambda p, f=field:
                p["context"]["value"].update({f: "null"})), "objective")
        # A known but unacceptable copy is distinct from unknown ownership.
        known = self.evaluate(lambda p: p["ownership"]["value"]["lots"][0].update(condition="damaged")).to_dict()
        self.assertEqual(known["decision"]["recommendation"]["outcome"], "selected")
        self.assertEqual(next(r for r in known["candidates"] if r["printing_id"] == PRINTINGS[0])["owned_acceptable_quantity"], 0)
        def no_discount(packet):
            buyer = packet["context"]["value"]["buyer_context"]
            buyer["discount_basis"] = "none"
            for candidate in packet["candidates"]:
                offer = candidate["offer"]["value"]
                offer["buyer_context_identity"] = content_identity(buyer)
                offer["costs"]["discounts"] = {"amount": "0.00", "basis": "Explicit fictional no discount applies."}
        self.assertEqual(self.evaluate(no_discount).to_dict()["decision"]["recommendation"]["outcome"], "selected")

    def test_duplicate_lots_are_not_counted_twice(self):
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"]["lots"].append(
            copy.deepcopy(p["ownership"]["value"]["lots"][0]))), "duplicate")

    def test_foil_canonical_variant_cannot_satisfy_nonfoil_preference(self):
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["offer"]["value"].update(finish="foil")), "exact preferred")

    def test_owned_other_finish_does_not_satisfy_desired_copy(self):
        def change(packet):
            lot = packet["ownership"]["value"]["lots"][0]
            lot.update(printing_id=PRINTINGS[2], finish="foil")
        result = self.evaluate(change).to_dict()
        greater = next(r for r in result["candidates"] if r["printing_id"] == PRINTINGS[2])
        self.assertEqual(greater["owned_acceptable_quantity"], 0)
        self.assertEqual(greater["missing_quantity"], 1)

    def test_unknown_costs_and_unevidenced_zeros_abstain(self):
        for change in (lambda p: p["candidates"][1]["offer"]["value"]["costs"].pop("shipping"),
                       lambda p: p["candidates"][1]["offer"]["value"]["costs"]["taxes"].update(amount=None),
                       lambda p: p["candidates"][1]["offer"]["value"]["costs"]["fees"].update(amount="0.00", basis=""),
                       lambda p: p["candidates"][1]["offer"]["value"]["costs"]["fees"].update(amount="0.00", basis="unknown")):
            self.assertEqual(self.evaluate(change).to_dict()["decision"]["recommendation"]["outcome"], "abstain")

    def test_discount_cannot_create_negative_acquisition_cost(self):
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][1]["offer"]["value"]["costs"]["discounts"].update(amount="100.00")), "discount exceeds")

    def test_exact_precision_rejects_float_exponential_and_overprecision(self):
        for amount in (0.1, "NaN", "1e3", "-1.00", "1.001"):
            self.assert_abstains(self.evaluate(lambda p, a=amount: p["context"]["value"].update(budget=a)), "context:")

    def test_stale_future_and_invalid_timestamp_inputs_fail_closed(self):
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][1]["offer"]["value"].update(valid_until="2026-10-12T19:01:00Z")), "stale")
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][1]["offer"]["value"].update(observed_at="2026-10-12T19:03:00Z")), "future-dated")
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][1]["offer"]["value"].update(observed_at="2026-10-12Z")), "timestamp")

    def test_unavailable_offer_is_excluded_and_unknown_availability_abstains(self):
        result = self.evaluate(lambda p: p["candidates"][2]["offer"]["value"].update(available=False, available_quantity=0)).to_dict()
        self.assertEqual(result["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[1])
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["offer"]["value"].update(available=None)), "availability is unknown")
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["offer"]["value"].update(available=True, available_quantity=0)), "availability contradicts")

    def test_offer_currency_and_buyer_context_must_match(self):
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["offer"]["value"].update(currency="EUR")), "incomparable")
        for field in ("postal_code", "purchase_method", "discount_basis"):
            self.assert_abstains(self.evaluate(lambda p, f=field: p["context"]["value"]["buyer_context"].update({f: "changed"})), "incomparable")

    def test_source_bound_payload_cannot_be_changed_without_source(self):
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"].update(budget="100.00"), bind=False), "payload differs")
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["offer"]["value"]["costs"]["unit_price"].update(amount="0.00"), bind=False), "payload differs")

    def test_retained_bytes_digest_and_path_escape_are_rejected(self):
        packet, source = self.fixture()
        raw = stable_json(source).encode()
        packet["sources"][0]["content_digest"] = "sha256:" + "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "source.json").write_bytes(raw)
            self.assert_abstains(self.adapter.evaluate(packet, source_root=Path(directory)), "digest mismatch")
            packet["sources"][0]["relative_path"] = "../source.json"
            self.assert_abstains(self.adapter.evaluate(packet, source_root=Path(directory)), "escapes")

    def test_pending_roles_cannot_establish_required_objective_eligibility(self):
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"].update(eligibility_required=True)), "required supplied evidence is missing")

    def test_unknown_hard_constraint_or_preference_abstains(self):
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"]["hard_constraints"].update(competitive_win_rate=60)), "unsupported hard")
        self.assert_abstains(self.evaluate(lambda p: p["candidates"][2]["preferred_dimensions"].update(frame="future")), "unsupported or missing")

    def test_exact_card_id_no_name_seed_or_unlinked_printing_fallback(self):
        for identity in ("Ponder", "magic.ponder", self.adapter.printings[PRINTINGS[1]].canonical_values["card_id"]):
            with self.assertRaises(CardAcquisitionError):
                self.evaluate(lambda p, i=identity: p["candidates"][0].update(card_id=i))

    def test_real_incomplete_inputs_and_synthetic_source_cannot_be_purchase_advice(self):
        packet, _ = self.fixture()
        packet.update(mode="real_world", sources=[])
        packet["context"] = {"value": None, "binding": None}
        packet["ownership"] = {"value": None, "binding": None}
        for candidate in packet["candidates"]:
            candidate.update(offer=None, eligibility=None, requirements_binding=None, desired_quantity=None)
        with tempfile.TemporaryDirectory() as directory:
            self.assert_abstains(self.adapter.evaluate(packet, source_root=Path(directory)), "required supplied evidence is missing")
        self.assert_abstains(self.evaluate(lambda p: p.update(mode="real_world")), "source metadata or mode")

    def test_fictional_unit_only_real_review_gates_reject_incomplete_attestations(self):
        # These fabricated temporary records exercise rejection only. They are
        # never retained as real offers or used for a real purchase example.
        for mutation in (lambda r: r.update(status="requires_review"),
                         lambda r: r.update(status="READY_FOR_EVALUATION"),
                         lambda r: r.update(content_digest="sha256:" + "0" * 64),
                         lambda r: r.update(reviewed_at="2026-10-12T19:00:30Z"),
                         lambda r: r.update(reviewed_at="2026-10-12T19:03:00Z")):
            packet, source = self.fixture()
            packet.update(mode="real_world", sources=[])
            with tempfile.TemporaryDirectory() as directory:
                for sid, kind in (("buyer", "buyer_declaration"), ("offers", "reviewed_offer")):
                    document = {**source, "mode": "real_world", "kind": kind}
                    raw = stable_json(document).encode()
                    digest = "sha256:" + hashlib.sha256(raw).hexdigest()
                    Path(directory, sid + ".json").write_bytes(raw)
                    review = {"status": "reviewed", "reviewer": "fictional-unit-only-reviewer",
                        "reviewed_at": "2026-10-12T19:01:30Z", "content_digest": digest}
                    if sid == "offers":
                        mutation(review)
                    packet["sources"].append({"source_id": sid, "relative_path": sid + ".json",
                        "content_digest": digest, "kind": kind, "provider_identity": source["provider_identity"],
                        "seller_identity": source["seller_identity"], "captured_at": source["captured_at"], "review": review})
                packet["context"]["binding"]["source_id"] = "buyer"
                packet["ownership"]["binding"]["source_id"] = "buyer"
                for candidate in packet["candidates"]:
                    candidate["requirements_binding"]["source_id"] = "buyer"
                    candidate["offer"]["binding"]["source_id"] = "offers"
                self.assert_abstains(self.adapter.evaluate(packet, source_root=Path(directory)), "scoped human review")

    def test_malformed_input_shapes_reject_or_abstain_without_attribute_errors(self):
        for value in (None, {}, [None]):
            packet, _ = self.fixture()
            packet["sources"] = value
            with self.assertRaises(CardAcquisitionError):
                CardAcquisitionInput(packet)
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"].update(buyer_context=[])), "buyer context")
        self.assert_abstains(self.evaluate(lambda p: p["context"]["value"].update(freshness_policy=None)), "freshness policy")
        self.assert_abstains(self.evaluate(lambda p: p["ownership"]["value"].update(lots=[None])), "missing ownership lot")

    def test_deterministic_deep_immutable_replay_and_bounded_handoff(self):
        first, second = self.evaluate(), self.evaluate()
        self.assertEqual(first.to_json(), second.to_json())
        self.assertEqual(first.reasoning_context(), second.reasoning_context())
        self.assertLess(len(stable_json(first.reasoning_context()).encode()), 65536)
        self.assertEqual(CardAcquisitionDossier(first.to_dict()).to_json(), first.to_json())
        with self.assertRaises(TypeError):
            first.payload["review"]["canonical_admission"] = True
        packet, _ = self.fixture()
        immutable = CardAcquisitionInput(packet)
        packet["context"]["value"]["budget"] = "500.00"
        self.assertEqual(immutable.to_dict()["context"]["value"]["budget"], "10.00")

    def test_rehashed_dossier_cannot_change_decision_or_review_boundary(self):
        for mutation in (lambda p: p.update(actual_purchase_advice=True),
                         lambda p: p["review"].update(canonical_admission=True),
                         lambda p: p["decision"]["recommendation"].update(selected_alternative_id=PRINTINGS[0]),
                         lambda p: p.update(canonical_snapshot_id="sha256:changed")):
            document = self.evaluate().to_dict()
            mutation(document)
            document["dossier_id"] = content_identity({k: v for k, v in document.items() if k != "dossier_id"})
            with self.assertRaises(CardAcquisitionError):
                CardAcquisitionDossier(document)

    def test_reported_rehashed_mode_cost_and_owned_copy_mutations_are_rejected(self):
        original = self.evaluate().to_dict()
        winner = original["decision"]["recommendation"]["selected_alternative_id"]
        def chosen(document):
            return next(row for row in document["candidates"] if row["printing_id"] == winner)
        mutations = (
            lambda d: d.update(mode="real_world", actual_purchase_advice=True),
            lambda d: chosen(d).update(complete_cost="0.00", complete_cost_units=0, remaining_budget="10.00"),
            lambda d: chosen(d).update(desired_quantity=1, owned_acceptable_quantity=1,
                missing_quantity=1, acquisition_eligible=True))
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(original)
                mutation(document)
                self.assertEqual(document["input_id"], original["input_id"])
                self.assertEqual(document["decision_request_id"], original["decision_request_id"])
                with self.assertRaises(CardAcquisitionError):
                    CardAcquisitionDossier(self.rehash(document))

    def test_rehashed_cross_field_money_and_quantity_mutations_are_rejected(self):
        original = self.evaluate().to_dict()
        winner = original["decision"]["recommendation"]["selected_alternative_id"]
        for field, value in (("complete_cost_units", -1), ("complete_cost_units", True),
                ("desired_quantity", True), ("owned_acceptable_quantity", -1),
                ("owned_acceptable_quantity", True), ("missing_quantity", True),
                ("acquisition_quantity", True), ("acquisition_quantity", 2),
                ("declared_priority", False), ("money_scale", True), ("money_scale", 3),
                ("currency", "EUR"), ("complete_cost", "8.0"), ("remaining_budget", "10.00"),
                ("acquisition_eligible", False), ("objective_eligibility", "reviewed")):
            with self.subTest(field=field, value=value):
                document = copy.deepcopy(original)
                next(row for row in document["candidates"] if row["printing_id"] == winner)[field] = value
                with self.assertRaises(CardAcquisitionError):
                    CardAcquisitionDossier(self.rehash(document))
        document = copy.deepcopy(original)
        next(row for row in document["candidates"] if row["printing_id"] == winner)["costs"]["shipping"] = {
            "amount": "0.00", "basis": "unknown"}
        with self.assertRaises(CardAcquisitionError):
            CardAcquisitionDossier(self.rehash(document))

    def test_rehashed_eligible_winner_rationale_actions_and_analysis_are_replayed(self):
        original = self.evaluate().to_dict()
        def action(document):
            request = document["reconstruction"]["decision_request"]
            request["alternatives"][0]["action"] = "BUY_ALL_COPIES"
            request["request_id"] = decision_identity("request-sha256:",
                {k: v for k, v in request.items() if k != "request_id"})
            document["decision_request_id"] = request["request_id"]
            document["decision"]["recommendation"]["request_id"] = request["request_id"]
        mutations = (
            lambda d: d["decision"]["recommendation"].update(selected_alternative_id=PRINTINGS[1]),
            lambda d: d["decision"]["recommendation"]["rationale"][0].update(selected_value=99),
            lambda d: d["decision"]["recommendation"]["supporting_factors"][0].update(statement="Altered justification."),
            lambda d: d["reconstruction"]["analyses"][0]["metrics"][0].update(value=0),
            action)
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(original)
                mutation(document)
                with self.assertRaises(CardAcquisitionError):
                    CardAcquisitionDossier(self.rehash(document))

    def test_original_input_and_retained_source_snapshots_are_required_for_reconstruction(self):
        original = self.evaluate().to_dict()
        self.assertEqual(content_identity(original["reconstruction"]["input_packet"]), original["input_id"])
        request = original["reconstruction"]["decision_request"]
        self.assertEqual(decision_identity("request-sha256:", {k: v for k, v in request.items() if k != "request_id"}),
            original["decision_request_id"])
        mutations = (
            lambda d: d.pop("reconstruction"),
            lambda d: d["reconstruction"].update(input_packet=None),
            lambda d: d["reconstruction"]["input_packet"].update(mode="real_world"),
            lambda d: d["reconstruction"]["input_packet"]["context"]["value"].update(budget="500.00"),
            lambda d: d["reconstruction"]["sources"][0].update(source_text="{}"),
            lambda d: d["reconstruction"].update(sources=[]),
            lambda d: d["reconstruction"].update(analysis_shared=[]),
            lambda d: d.update(unbound_alternate_action="EXECUTE_PURCHASE"))
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                document = copy.deepcopy(original)
                mutation(document)
                with self.assertRaises(CardAcquisitionError):
                    CardAcquisitionDossier(self.rehash(document))
        # Reconstruction remains valid after temporary sources are gone and
        # requires no file reads or implicit access to the production store.
        with patch.object(Path, "read_bytes", side_effect=AssertionError("unexpected source read")):
            self.assertEqual(CardAcquisitionDossier(original).to_dict(), original)

    def test_fictional_unit_complete_real_review_and_eligibility_reconstruction(self):
        original = self.real_unit_evaluate().to_dict()
        self.assertEqual(original["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[2])
        self.assertTrue(original["actual_purchase_advice"])
        self.assertEqual(CardAcquisitionDossier(original).to_dict(), original)
        for kind in ("buyer", "offers", "eligibility"):
            self.assert_abstains(self.real_unit_evaluate(lambda p, d, r, k=kind:
                r[k].update(status="READY_FOR_EVALUATION")), "scoped human review")
        for field, value in (("status", "requires_review"), ("basis_category", "pending_role"),
                ("basis", "unknown"), ("eligible", 1), ("mechanical_dossier_id", "sha256:unbound")):
            self.assert_abstains(self.real_unit_evaluate(lambda p, d, r, f=field, v=value:
                d["eligibility"]["eligibility"][2].update({f: v})), "objective eligibility")
        for mutation in (
                lambda d: d["reconstruction"]["input_packet"]["sources"][0]["review"].update(status="READY_FOR_EVALUATION"),
                lambda d: d["reconstruction"]["input_packet"]["candidates"][2]["eligibility"]["value"].update(status="requires_review"),
                lambda d: d["reconstruction"]["sources"][2].update(source_text="{}")):
            document = copy.deepcopy(original)
            mutation(document)
            with self.assertRaises(CardAcquisitionError):
                CardAcquisitionDossier(self.rehash(document))

    def test_exact_budget_missing_quantity_and_result_byte_boundaries(self):
        document = self.evaluate(lambda p: p["context"]["value"].update(budget="8.00")).to_dict()
        self.assertEqual(document["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[2])
        self.assertEqual(next(r for r in document["candidates"] if r["printing_id"] == PRINTINGS[2])["remaining_budget"], "0.00")
        document = self.evaluate(lambda p: p["context"]["value"].update(budget="7.99")).to_dict()
        self.assertEqual(document["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[1])
        document = self.evaluate(lambda p: p["candidates"][0].update(desired_quantity=2)).to_dict()
        self.assertEqual(document["decision"]["recommendation"]["selected_alternative_id"], PRINTINGS[0])
        row = next(r for r in document["candidates"] if r["printing_id"] == PRINTINGS[0])
        self.assertEqual((row["desired_quantity"], row["owned_acceptable_quantity"], row["missing_quantity"], row["acquisition_quantity"]),
            (2, 1, 1, 1))
        for value in (True, -1):
            self.assert_abstains(self.evaluate(lambda p, v=value:
                p["ownership"]["value"]["lots"][0].update(quantity=v)), "nonnegative integer")
        document = self.evaluate().to_dict()
        document["reconstruction"]["canonical"]["scope"] += "x" * 65536
        with self.assertRaisesRegex(CardAcquisitionError, "byte bound"):
            CardAcquisitionDossier(self.rehash(document))

    def test_protected_production_and_retained_evidence_are_not_mutated(self):
        self.evaluate()
        after = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (ROOT / "data").rglob("*") if p.is_file()}
        self.assertEqual(after, self.protected)


if __name__ == "__main__":
    unittest.main()
