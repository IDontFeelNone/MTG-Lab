from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence.acquisition import CardAcquisitionDossier, CardAcquisitionError
from card_intelligence.cli import main as card_cli
from card_intelligence.mechanics import content_identity, stable_json
from decision_intelligence.models import identity as decision_identity
from scripts import build_card_acquisition_pilot as pilot


EXPECTED = {
    "Ponder": ("02090581-61aa-4348-ad57-451be8ee91c2", "5c8d3bc4-32fc-5b26-84bf-9921e5884d43"),
    "Faithless Looting": ("3d6fa57a-aa53-4b5c-b8af-a7612c823117", "72783a15-4847-5448-8f1d-0c40379594d3"),
    "Greater Good": ("dc0593c2-ccb4-4648-a592-c5bcd121dc72", "46c0ae9f-b64a-528f-aab6-f1ceff9f0ade"),
}


class CardAcquisitionPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = pilot.protected_inventory()
        cls.artifacts = pilot.build_artifacts()
        cls.dossier = json.loads(cls.artifacts["acquisition-dossier.json"])
        cls.context = json.loads(cls.artifacts["reasoning-context.json"])
        cls.by_name = {s["card_identity"]["name"]: s for s in cls.dossier["subjects"]}

    def test_exact_three_production_card_and_printing_bindings(self):
        self.assertEqual({name: (s["card_identity"]["card_id"], s["printing_identity"]["printing_id"])
            for name, s in self.by_name.items()}, EXPECTED)
        canonical = json.loads((pilot.ROOT / "data/canonical/state.json").read_bytes())
        for name, (card_id, printing_id) in EXPECTED.items():
            self.assertEqual(canonical["card"][card_id]["values"]["name"], name)
            self.assertEqual(canonical["printing"][printing_id]["values"]["card_id"], card_id)
            self.assertEqual(self.by_name[name]["printing_identity"]["canonical_language"], "English")
            self.assertEqual(self.by_name[name]["printing_identity"]["canonical_treatment"]["status"], "unknown")

    def test_retained_source_identity_oracle_text_and_field_provenance(self):
        shared = copy.deepcopy(self.dossier["mechanical_source"])
        shared_id = shared.pop("content_identity")
        self.assertEqual(content_identity(shared), shared_id)
        for subject in self.dossier["subjects"]:
            source = subject["source"]
            self.assertEqual(source["shared_source_identity"], shared_id)
            raw = (pilot.ROOT / source["retained_source_reference"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["retained_source_sha256"])
            row = json.loads(raw)[source["source_record_index"]]
            self.assertEqual(content_identity(row), source["record_content_identity"])
            self.assertEqual(row["oracle_id"], subject["card_identity"]["card_id"])
            self.assertEqual(subject["mechanical_fields"]["oracle_text"]["value"], row["oracle_text"])
            self.assertEqual(subject["mechanical_fields"]["mana_cost"]["value"], row["mana_cost"])
            self.assertTrue(subject["canonical_provenance"]["promotion_audit_references"])
            self.assertTrue(all(a["audit_reference"] and a["entity_binding"]
                for a in subject["canonical_provenance"]["promotion_audit_references"]))

    def test_eight_role_proposals_remain_pending_and_original_dossiers_unchanged(self):
        dossiers = [json.loads(line) for line in
            (pilot.ROOT / "data/review/functional-role-pilot/dossiers.jsonl").read_text().splitlines()]
        by_id = {d["card_identity"]["card_id"]: d for d in dossiers}
        copied = []
        for subject in self.dossier["subjects"]:
            roles = subject["pending_role_evidence"]
            original = by_id[subject["card_identity"]["card_id"]]
            self.assertEqual(roles["dossier_id"], original["dossier_id"])
            self.assertEqual({r["candidate_id"] for r in roles["candidates"]},
                {r["candidate_id"] for r in original["role_candidates"]})
            copied.extend(roles["candidates"])
        self.assertEqual(len(copied), 8)
        self.assertEqual(sum(r["value_state"] == "known" for r in copied), 6)
        self.assertEqual(sum(r["value_state"] == "incomplete" for r in copied), 2)
        self.assertTrue(all(r["review"]["status"] == "requires_review" and
            r["review"]["human_attestation"] is None and not r["review"]["canonical_admission"] for r in copied))

    def test_synthetic_personal_preference_selection_and_duplicate_prevention(self):
        scenario = self.dossier["synthetic_demonstration"]
        self.assertEqual(scenario["mode"], "synthetic_demonstration")
        self.assertFalse(scenario["actual_purchase_advice"])
        self.assertEqual(scenario["decision"]["schema_version"], "decision-reasoning-context-v1")
        self.assertEqual(scenario["decision"]["recommendation"]["outcome"], "selected")
        self.assertEqual(scenario["decision"]["recommendation"]["selected_alternative_id"], EXPECTED["Greater Good"][1])
        by_name = {c["card_name"]: c for c in scenario["candidates"]}
        ponder = by_name["Ponder"]
        self.assertEqual((ponder["owned_acceptable_quantity"], ponder["missing_quantity"]), (1, 0))
        self.assertFalse(ponder["acquisition_eligible"])
        self.assertIn("already_owned_desired_acceptable_copies", ponder["exclusion_reasons"])
        self.assertLess(by_name["Faithless Looting"]["complete_cost_units"], by_name["Greater Good"]["complete_cost_units"])
        self.assertTrue(all(c["objective_eligibility"] == "user_preference_only_not_strategic_suitability"
            for c in scenario["candidates"]))

    def test_exact_transaction_costs_and_remaining_budget_are_not_recalculated_by_ai(self):
        rows = {c["card_name"]: c for c in self.dossier["synthetic_demonstration"]["candidates"]}
        self.assertEqual({n: (c["complete_cost"], c["remaining_budget"]) for n, c in rows.items()},
            {"Ponder": ("4.20", "5.80"), "Faithless Looting": ("2.00", "8.00"), "Greater Good": ("8.00", "2.00")})
        for row in rows.values():
            self.assertEqual(set(row["costs"]), {"unit_price", "shipping", "taxes", "fees", "discounts"})
            self.assertTrue(all(term["basis"] for term in row["costs"].values()))
        explanation = self.artifacts["explanation.md"].decode()
        self.assertIn("7.00 + 1.00 + 0.70 + 0.10 - 0.80 = 8.00 USD", explanation)
        self.assertIn("Cost counterargument: Faithless Looting", explanation)
        self.assertIn("not a mechanical superiority or competitive ranking", explanation)

    def test_real_world_gaps_abstain_without_inventing_buyer_or_owned_zero(self):
        synthetic, real = pilot.build_packets()
        self.assertEqual(real["mode"], "real_world")
        self.assertEqual(real["sources"], [])
        self.assertIsNone(real["context"]["value"])
        self.assertIsNone(real["ownership"]["value"])
        self.assertTrue(all(c["desired_quantity"] is None and c["offer"] is None for c in real["candidates"]))
        scenario = self.dossier["real_evidence_assessment"]
        recommendation = scenario["decision"]["recommendation"]
        self.assertEqual(recommendation["outcome"], "abstain")
        self.assertIsNone(recommendation["selected_alternative_id"])
        self.assertTrue(scenario["blockers"])
        self.assertTrue(all(c["owned_acceptable_quantity"] is None and c["complete_cost"] is None
            for c in scenario["candidates"]))
        for field in ("buyer_context", "budget", "currency", "ownership", "shipping", "taxes", "fees", "discounts",
                      "availability", "offer_source_integrity", "reviewed_objective_eligibility"):
            self.assertIn(field, self.dossier["real_input_inventory"])
        self.assertNotEqual(synthetic["as_of"], real["as_of"])

    def test_all_fictional_inputs_have_byte_bound_source_bindings(self):
        synthetic, _ = pilot.build_packets()
        plan, source, raw = pilot.load_inputs()
        ref = synthetic["sources"][0]
        self.assertEqual(ref["content_digest"], "sha256:" + hashlib.sha256(raw).hexdigest())
        self.assertEqual(ref["kind"], source["kind"])
        self.assertEqual(synthetic["context"]["value"], source["context"])
        self.assertEqual(synthetic["ownership"]["value"], source["ownership"])
        for i, candidate in enumerate(synthetic["candidates"]):
            self.assertEqual(candidate["requirements_binding"]["pointer"], f"/requirements/{i}")
            self.assertEqual(candidate["offer"]["value"], source["offers"][i])
            self.assertEqual(candidate["preferred_dimensions"]["treatment"], None)
        self.assertEqual(plan["prepared_at"], "2026-10-12T19:28:27Z")
        self.assertIn("fictional", source["notice"])

    def test_changed_retained_synthetic_source_is_rejected_before_evaluation(self):
        source_path = pilot.ROOT / "data/review/card-acquisition-pilot/synthetic-inputs.json"
        original = Path.read_bytes
        def corrupted(path):
            raw = original(path)
            return raw + b" " if path == source_path else raw
        with patch.object(Path, "read_bytes", corrupted):
            with self.assertRaisesRegex(ValueError, "source integrity mismatch"):
                pilot.load_inputs()

    def test_content_identities_context_byte_bounds_and_explicit_omissions(self):
        body = copy.deepcopy(self.dossier); identity = body.pop("dossier_id")
        self.assertEqual(content_identity(body), identity)
        body = copy.deepcopy(self.context); identity = body.pop("handoff_id")
        self.assertEqual(content_identity(body), identity)
        for name in ("acquisition-dossier.json", "reasoning-context.json", "packet-synthetic.json", "packet-real.json"):
            raw = self.artifacts[name]
            self.assertLessEqual(len(raw), 65536)
            self.assertTrue(raw.endswith(b"\n"))
            self.assertFalse(raw.endswith(b"\n\n"))
            self.assertEqual(raw[:-1].decode(), stable_json(json.loads(raw)))
        self.assertEqual(self.context["dossier"], self.dossier)
        self.assertEqual(len(self.context["canonical_contexts"]), 3)
        originals = json.loads(self.artifacts["canonical-contexts.json"])
        self.assertTrue(all(c["canonical_snapshot_id"] == self.dossier["canonical_snapshot_id"] and
            c["entities"] == [] and c["relationships"] == [] for c in originals))
        self.assertEqual([c["context_id"] for c in self.context["canonical_contexts"]],
            [c["context_id"] for c in originals])
        self.assertEqual(self.context["canonical_contexts_reference"]["sha256"],
            hashlib.sha256(self.artifacts["canonical-contexts.json"]).hexdigest())
        self.assertEqual(self.context["omissions"]["pilot_subjects_omitted"], 0)
        self.assertLessEqual(len(self.artifacts["reasoning-context.json"]), 65536)
        for key in ("synthetic_demonstration", "real_evidence_assessment"):
            scenario = self.dossier[key]
            reference = scenario["validated_acquisition_reference"]
            raw = self.artifacts[Path(reference["relative_path"]).name]
            self.assertEqual(reference["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertEqual(reference["bytes"], len(raw))
            self.assertEqual(json.loads(raw)["dossier_id"], scenario["validated_acquisition_dossier_id"])
            self.assertEqual(scenario["decision"], json.loads(raw)["decision"])
            self.assertEqual(scenario["omissions"]["decision_values_omitted"], 0)
        with self.assertRaisesRegex(ValueError, "including trailing LF"):
            pilot.compact_payload("x" * 65534)

    def test_full_reconstruction_proofs_bind_packets_and_project_with_explicit_accounting(self):
        for mode, key in (("synthetic", "synthetic_demonstration"), ("real", "real_evidence_assessment")):
            full = json.loads(self.artifacts[mode + "-result.json"])
            proof = full["reconstruction"]
            scenario = self.dossier[key]
            omitted = scenario["omissions"]["reconstruction_proof"]
            self.assertNotIn("reconstruction", scenario)
            self.assertEqual(proof["input_packet"], json.loads(self.artifacts["packet-" + mode + ".json"]))
            self.assertEqual(content_identity(proof["input_packet"]), full["input_id"])
            self.assertEqual(proof["decision_request"]["request_id"], full["decision_request_id"])
            self.assertEqual(proof["canonical"]["snapshot_id"], self.dossier["canonical_snapshot_id"])
            self.assertEqual(omitted["retained_field"], "reconstruction")
            self.assertEqual(omitted["content_identity"], content_identity(proof))
            self.assertEqual(omitted["input_id"], full["input_id"])
            self.assertEqual(omitted["decision_request_id"], full["decision_request_id"])
            self.assertEqual(omitted["analysis_count"], 2 if mode == "synthetic" else 3)
            self.assertEqual(omitted["analysis_content_identities"],
                [content_identity({**proof["analysis_shared"], **analysis}) for analysis in proof["analyses"]])
            self.assertEqual(omitted["source_snapshot_count"], len(proof["sources"]))
            self.assertEqual(omitted["canonical_card_count"], 3)
            self.assertEqual(omitted["canonical_printing_count"], 3)
            self.assertEqual(CardAcquisitionDossier(full).to_dict(), full)
            if mode == "synthetic":
                self.assertEqual(len(proof["sources"]), 1)
                self.assertEqual(proof["sources"][0]["source_text"].encode("utf-8"),
                    (pilot.REVIEW / "synthetic-inputs.json").read_bytes())
            else:
                self.assertEqual(proof["sources"], [])

    def test_projection_validates_full_proof_before_omitting_it(self):
        full = json.loads(self.artifacts["synthetic-result.json"])
        full["reconstruction"]["input_packet"]["ownership"]["value"]["scope_complete"] = False
        full["dossier_id"] = content_identity({k: v for k, v in full.items() if k != "dossier_id"})
        with self.assertRaises(CardAcquisitionError):
            pilot._scenario_projection(full, "synthetic-result.json")

    def test_manual_handoff_and_explanation_reject_rehashed_aggregate_contradictions(self):
        changes = {
            "ownership": lambda d: next(c for c in d["synthetic_demonstration"]["candidates"]
                if c["card_name"] == "Ponder").update(owned_acceptable_quantity=0, missing_quantity=1),
            "cost": lambda d: next(c for c in d["synthetic_demonstration"]["candidates"]
                if c["card_name"] == "Greater Good").update(
                    complete_cost="0.00", complete_cost_units=0, remaining_budget="10.00"),
            "status": lambda d: d["real_evidence_assessment"]["decision"]["recommendation"].update(
                outcome="selected", selected_alternative_id=EXPECTED["Greater Good"][1], abstention_reasons=[]),
        }
        for label, change in changes.items():
            forged = copy.deepcopy(self.dossier)
            change(forged)
            for key in ("synthetic_demonstration", "real_evidence_assessment"):
                scenario = forged[key]
                recommendation = scenario["decision"]["recommendation"]
                recommendation["recommendation_id"] = decision_identity("recommendation-sha256:",
                    {k: v for k, v in recommendation.items() if k != "recommendation_id"})
                scenario["projection_id"] = content_identity(
                    {k: v for k, v in scenario.items() if k != "projection_id"})
            forged["dossier_id"] = content_identity({k: v for k, v in forged.items() if k != "dossier_id"})
            for renderer in (pilot.pilot_reasoning_context, pilot.pilot_explanation):
                with self.subTest(change=label, renderer=renderer.__name__):
                    with self.assertRaisesRegex(ValueError, "bound input/result replay"):
                        renderer(forged)

    def test_cli_actual_stdout_matches_retained_adapter_payload_after_one_lf(self):
        for mode in ("synthetic", "real"):
            raw = self.artifacts[mode + "-result.json"]
            result = CardAcquisitionDossier(json.loads(raw))
            argv = [sys.executable, "-m", "card_intelligence.cli", "--data-root",
                str(pilot.ROOT / "data"), "acquisition", "--input",
                str(pilot.REVIEW / ("packet-" + mode + ".json")), "--source-root", str(pilot.ROOT)]
            expected_context = (stable_json(result.reasoning_context()) + "\n").encode("utf-8")
            for arguments, expected in ((argv, raw), (argv + ["--reasoning-context"], expected_context)):
                completed = subprocess.run(arguments, cwd=pilot.ROOT,
                    env={**os.environ, "PYTHONPATH": str(pilot.ROOT / "src")},
                    capture_output=True, check=False)
                self.assertEqual(completed.returncode, 0, completed.stderr.decode("utf-8"))
                self.assertEqual(completed.stderr, b"")
                self.assertEqual(completed.stdout, expected)
                self.assertLessEqual(len(completed.stdout), 65536)
                self.assertTrue(completed.stdout.endswith(b"\n"))
                self.assertFalse(completed.stdout.endswith(b"\n\n"))
                self.assertEqual(completed.stdout[:-1].decode(), stable_json(json.loads(completed.stdout)))
                document = json.loads(completed.stdout)
                reconstructed = document["dossier"] if "dossier" in document else document
                self.assertEqual(CardAcquisitionDossier(reconstructed).to_json(), result.to_json())

    def test_cli_oversize_output_fails_closed_before_payload(self):
        argv = ["acquisition", "--input", str(pilot.REVIEW / "packet-synthetic.json"),
            "--source-root", str(pilot.ROOT)]
        with patch("card_intelligence.cli.CardAcquisitionAdapter") as adapter:
            result = adapter.return_value.evaluate.return_value
            for reasoning in (False, True):
                result.to_json.return_value = stable_json("x" * 65534)
                result.reasoning_context.return_value = "x" * 65534
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(card_cli(argv + (["--reasoning-context"] if reasoning else [])), 2)
                raw = output.getvalue().encode("utf-8")
                self.assertIn(b"including the trailing newline", raw)
                self.assertLess(len(raw), 1000)
                self.assertNotIn(b"xxxx", raw)
                result.to_json.return_value = stable_json("x" * 65533)
                result.reasoning_context.return_value = "x" * 65533
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(card_cli(argv + (["--reasoning-context"] if reasoning else [])), 0)
                self.assertEqual(len(output.getvalue().encode("utf-8")), 65536)

    def test_retained_artifacts_exact_replay_manifest_and_protected_boundaries(self):
        actual = {p.name: p.read_bytes() for p in pilot.REVIEW.iterdir() if p.is_file()
            and p.name not in {"plan.json", "synthetic-inputs.json"}}
        self.assertEqual(actual, self.artifacts)
        manifest = json.loads(self.artifacts["manifest.json"])
        for name, meta in manifest["files"].items():
            self.assertEqual(len(actual[name]), meta["bytes"])
            self.assertEqual(hashlib.sha256(actual[name]).hexdigest(), meta["sha256"])
        self.assertEqual(manifest["protected_inventory"]["content_identity"], content_identity(self.before))
        self.assertEqual(pilot.protected_inventory(), self.before)
        self.assertTrue(all(value is False for value in self.dossier["protection_boundary"].values()))

    def test_collection_growth_preserves_original_protection_and_detects_canonical_edits(self):
        inventory = pilot.protected_inventory()
        retained = json.loads((pilot.REVIEW / "manifest.json").read_bytes())["protected_inventory"]
        self.assertEqual(len(inventory), retained["file_count"])
        self.assertEqual(content_identity(inventory), retained["content_identity"])
        self.assertFalse(any(path.startswith(("data/collections/", "data/review/collection-audit-pilot/"))
                             for path in inventory))
        original = Path.read_bytes
        target = pilot.ROOT / "data/canonical/state.json"
        def altered(path):
            return original(path) + b"tampered" if path == target else original(path)
        with patch.object(Path, "read_bytes", altered):
            changed = pilot.protected_inventory()
        self.assertNotEqual(inventory["data/canonical/state.json"], changed["data/canonical/state.json"])

    def test_generator_refuses_to_overwrite_conflicting_review_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory)
            (destination / "acquisition-dossier.json").write_bytes(b"conflicting review bytes\n")
            with patch.object(pilot, "REVIEW", destination), patch.object(pilot, "build_artifacts", return_value=self.artifacts), \
                    patch("sys.argv", ["build_card_acquisition_pilot.py"]):
                with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                    pilot.main()
            self.assertEqual((destination / "acquisition-dossier.json").read_bytes(), b"conflicting review bytes\n")


if __name__ == "__main__":
    unittest.main()
