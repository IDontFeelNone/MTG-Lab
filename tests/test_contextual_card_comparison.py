from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from card_intelligence import (ContextualCardComparisonPilot, ContextualComparisonDossier,
                              ContextualComparisonError)
from card_intelligence.cli import main
from card_intelligence.comparison import MAXIMUM_BYTES, comparison_explanation
from card_intelligence.mechanics import content_identity, stable_json
from card_intelligence.models import KnowledgeValidationError
from card_intelligence.repository import KnowledgeRepository
from decision_intelligence import AcquisitionDecisionOrchestrator, AnalysisMetric, DomainAnalysisEnvelope
from jsonschema import Draft202012Validator
from scripts.build_contextual_card_comparison import build_artifacts
from scripts.build_functional_role_pilot import build_artifacts as role_artifacts
from scripts.build_mechanical_cohort import build_artifacts as mechanical_artifacts
from scripts.build_two_card_demo import build_artifacts as demo_artifacts


from historical_catalog import historical_repository

# This module replays the retained original catalog, not the current catalog.
ROOT = historical_repository()
REVIEW = ROOT / "data/review/contextual-card-comparison"
EXPECTED_IDS = {"Ponder": "02090581-61aa-4348-ad57-451be8ee91c2",
                "Faithless Looting": "3d6fa57a-aa53-4b5c-b8af-a7612c823117",
                "Greater Good": "dc0593c2-ccb4-4648-a592-c5bcd121dc72"}


def rehash(document):
    body = copy.deepcopy(document)
    body.pop("comparison_id", None)
    return {**body, "comparison_id": content_identity(body)}


def protected_inventory():
    files = [p for p in (ROOT / "data").rglob("*") if p.is_file() and not p.is_relative_to(REVIEW)]
    files += [ROOT / p for p in ("docs/ARCHITECTURE.md", "docs/DECISIONS.md", "docs/ENGINEERING_STANDARDS.md")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


class ContextualCardComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from historical_catalog import bind_replay_builder
        from scripts import build_contextual_card_comparison
        bind_replay_builder(cls, build_contextual_card_comparison)
        from scripts import build_functional_role_pilot
        bind_replay_builder(cls, build_functional_role_pilot)
        from scripts import build_mechanical_cohort
        bind_replay_builder(cls, build_mechanical_cohort)
        from scripts import build_two_card_demo
        bind_replay_builder(cls, build_two_card_demo)
        cls.protected = protected_inventory()
        cls.pilot = ContextualCardComparisonPilot(ROOT / "data")
        cls.document = cls.pilot.dossier().to_dict()
        cls.by_name = {c["card_identity"]["name"]: c for c in cls.document["candidates"]}

    def altered_plan(self, change):
        plan = copy.deepcopy(self.pilot.plan)
        change(plan)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with patch("card_intelligence.comparison.FunctionalRolePilot", return_value=self.pilot.roles):
                return ContextualCardComparisonPilot(ROOT / "data", plan_path=path)

    def test_exact_production_subjects_and_no_name_or_seed_fallback(self):
        self.assertEqual({name: c["card_identity"]["card_id"] for name, c in self.by_name.items()}, EXPECTED_IDS)
        canonical = json.loads((ROOT / "data/canonical/state.json").read_bytes())
        for name, identity in EXPECTED_IDS.items():
            self.assertEqual(canonical["card"][identity]["values"]["name"], name)
        for identity in ("Ponder", "magic.ponder", "36cd2364-d113-47d1-b2c4-b088d9eb88dd"):
            with self.assertRaises(ContextualComparisonError):
                self.altered_plan(lambda p: p["cards"][0].update(card_id=identity))
        with self.assertRaises(ContextualComparisonError):
            self.altered_plan(lambda p: p["cards"].append(copy.deepcopy(p["cards"][0])))

    def test_hypothetical_assumptions_legality_and_no_invented_deck(self):
        context = self.document["context"]
        self.assertEqual(context["kind"], "hypothetical_deck_context")
        self.assertEqual(context["format_legality"]["status"], "unknown")
        self.assertIsNone(context["format_legality"]["value"])
        self.assertTrue(all(a["state"] == "supplied_assumption" for a in context["assumptions"]))
        self.assertEqual(self.pilot.assumptions["sacrificed_creature_power"]["value"], 4)
        self.assertEqual(content_identity(context), self.document["context_identity"])
        for change in (lambda p: p["context"]["format_legality"].update(status="known", value=True),
                       lambda p: p["context"]["assumptions"][0].update(state="verified_fact"),
                       lambda p: p["context"]["assumptions"][1].update(value=False)):
            with self.assertRaises(ContextualComparisonError): self.altered_plan(change)

    def test_exact_mechanical_and_pending_evidence_bindings(self):
        for c in self.document["candidates"]:
            identity = c["card_identity"]["card_id"]
            mechanical = self.pilot.roles.mechanical.dossier(identity).to_dict()
            original_roles = self.pilot.roles.dossier(identity)
            self.assertEqual(c["mechanical_dossier_id"], mechanical["dossier_id"])
            self.assertEqual(c["role_dossier_id"], original_roles["dossier_id"])
            self.assertEqual(c["pending_roles"], original_roles["role_candidates"])
            self.assertEqual(c["canonical_provenance"], mechanical["canonical_provenance"])
            self.assertEqual(c["source"], mechanical["source"])
            source = c["source"]
            raw = (ROOT / source["retained_source_reference"]).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source["retained_source_sha256"])
            row = json.loads(raw)[source["source_record_index"]]
            self.assertEqual(row["oracle_id"], identity)
            self.assertEqual(content_identity(row), source["record_content_identity"])
            self.assertEqual(c["mechanical_facts"]["oracle_text"]["value"], row["oracle_text"])
            self.assertEqual(c["mechanical_facts"]["mana_cost"]["value"], row["mana_cost"])
            self.assertEqual(c["mechanical_facts"]["type_line"]["value"], row["type_line"])

    def test_eight_roles_remain_pending_with_two_incomplete_selection_proposals(self):
        roles = [r for c in self.document["candidates"] for r in c["pending_roles"]]
        self.assertEqual(len(roles), 8)
        self.assertEqual(sum(r["value"]["status"] == "known" for r in roles), 6)
        self.assertEqual(sum(r["value"]["status"] == "incomplete" for r in roles), 2)
        self.assertTrue(all(r["review"] == self.document["review"] for r in roles))
        self.assertTrue(all(c["literal_instruction_annotation"]["review_status"] == "requires_review" for c in self.document["candidates"]))
        self.assertTrue(all(c["selection_weight"] is None for c in self.document["criteria"]))

    def test_cost_routes_and_restrictions_remain_distinct(self):
        facts = {n: c["mechanical_facts"] for n, c in self.by_name.items()}
        self.assertEqual({n: f["mana_cost"]["value"] for n, f in facts.items()},
                         {"Ponder": "{U}", "Faithless Looting": "{R}", "Greater Good": "{2}{G}{G}"})
        self.assertIn("Flashback {2}{R}", facts["Faithless Looting"]["oracle_text"]["value"])
        self.assertIn("Then exile it.", facts["Faithless Looting"]["oracle_text"]["value"])
        self.assertEqual(facts["Greater Good"]["type_line"]["value"], "Enchantment")
        greater_roles = self.by_name["Greater Good"]["pending_roles"]
        self.assertTrue(all("Sacrifice a creature" in " ".join(r["qualifiers"]["costs"]) for r in greater_roles))
        self.assertTrue(all(r["qualifiers"]["timing"]["status"] == "unknown" for c in self.document["candidates"] for r in c["pending_roles"]))
        mana = [c for c in self.document["deterministic_comparisons"] if c["unit"] == "mana_value"]
        self.assertEqual([c["value"] for c in mana], ["0", "-3", "-3"])
        self.assertTrue(all("not actual payment" in c["limitations"] for c in mana))

    def test_conditional_instruction_arithmetic_is_not_card_advantage(self):
        rows = {c["card_ids"][0]: c for c in self.document["deterministic_comparisons"] if c["unit"] == "instruction_count_difference"}
        self.assertEqual({n: rows[i]["value"] for n, i in EXPECTED_IDS.items()},
                         {"Ponder": 1, "Faithless Looting": 0, "Greater Good": 1})
        self.assertEqual(rows[EXPECTED_IDS["Greater Good"]]["inputs"], {"draw_count": 4, "mandatory_discard_count": 3})
        for row in rows.values():
            self.assertIn("Not net card advantage", row["limitations"])
            self.assertIn("resolved_instructions", row["assumption_ids"])
            self.assertEqual(row["category"], "conditional_instruction_arithmetic")
        for power, expected in ((0, -3), (3, 0), (6, 3)):
            pilot = self.altered_plan(lambda p: p["context"]["assumptions"][2].update(value=power))
            row = next(c for c in pilot.dossier().to_dict()["deterministic_comparisons"] if c["calculation_id"] == "draw-minus-discard:" + EXPECTED_IDS["Greater Good"])
            self.assertEqual(row["value"], expected)
            self.assertEqual(pilot.dossier().to_dict()["decision_intelligence"]["reasoning_context"]["recommendation"]["outcome"], "abstain")

    def test_missing_values_are_unknown_and_never_replaced_with_zero(self):
        pilot = self.altered_plan(lambda p: p["cards"][0]["literal_instruction_annotation"].update(mandatory_discard_count=None))
        row = next(c for c in pilot.dossier().to_dict()["deterministic_comparisons"] if c["calculation_id"] == "draw-minus-discard:" + EXPECTED_IDS["Ponder"])
        self.assertEqual((row["state"], row["value"]), ("unknown", None))
        for value in (None, True, -1, "4"):
            with self.assertRaises(ContextualComparisonError):
                self.altered_plan(lambda p: p["context"]["assumptions"][2].update(value=value))

    def test_source_snapshot_and_required_fields_fail_closed(self):
        for change in (lambda p: p.update(canonical_snapshot_id="sha256:" + "0" * 64),
                       lambda p: p["cards"][0].update(oracle_text="Draw one."),
                       lambda p: p["cards"][0].update(role_dossier_id="sha256:" + "0" * 64),
                       lambda p: p["cards"][0].update(mechanical_dossier_id="sha256:" + "0" * 64),
                       lambda p: p.update(prepared_at="2026-08-01T00:00:00Z")):
            with self.assertRaises(ContextualComparisonError): self.altered_plan(change)
        original = self.pilot.roles.mechanical.dossier
        def unknown(identity):
            document = original(identity).to_dict()
            document["fields"]["mana_cost"] = {"status": "unknown", "source_pointer": "/mana_cost"}
            result = unittest.mock.Mock(); result.to_dict.return_value = document
            return result
        with patch.object(self.pilot.roles.mechanical, "dossier", side_effect=unknown):
            with self.assertRaisesRegex(ContextualComparisonError, "unknown"):
                self.altered_plan(lambda p: None)

    def test_existing_decision_engine_owns_abstention_and_contradiction_handling(self):
        decision = {**self.pilot.decision_inputs(), "reasoning_context": self.document["decision_intelligence"]["reasoning_context"]}
        self.assertEqual(decision["request"]["schema_version"], "decision-request-v1")
        self.assertTrue(all(a["schema_version"] == "decision-analysis-v1" for a in decision["analyses"]))
        self.assertEqual(decision["reasoning_context"]["schema_version"], "decision-reasoning-context-v1")
        result = decision["reasoning_context"]["recommendation"]
        self.assertEqual(result["outcome"], "abstain")
        self.assertIsNone(result["selected_alternative_id"])
        self.assertEqual(len(result["abstention_reasons"]), 3)
        self.assertTrue(all("required_metric_unknown" in r for r in result["abstention_reasons"]))
        original = AcquisitionDecisionOrchestrator.evaluate
        def contradict(engine, request, analyses, policy):
            first = analyses[0]
            conflict = DomainAnalysisEnvelope(first.domain_id, first.domain_version, first.alternative_id,
                (AnalysisMetric("human_reviewed_context_match", "known", 1),), state="incomplete")
            return original(engine, request, [*analyses, conflict], policy)
        with patch("card_intelligence.comparison.AcquisitionDecisionOrchestrator.evaluate", new=contradict):
            result = self.altered_plan(lambda p: None).dossier().to_dict()["decision_intelligence"]["reasoning_context"]["recommendation"]
        self.assertEqual(result["outcome"], "abstain")
        self.assertTrue(any("contradictory_evidence" in r for r in result["abstention_reasons"]))

    def test_unverified_hypotheses_counterarguments_and_evidence_references(self):
        for c in self.document["candidates"]:
            self.assertTrue(c["counterarguments"])
            for h in c["strategic_hypotheses"]:
                self.assertEqual(h["state"], "unverified_hypothesis")
                self.assertTrue(h["counterargument"])
                self.assertTrue(h["evidence_ids"])
        changed = copy.deepcopy(self.document)
        changed["candidates"][0]["strategic_hypotheses"][0]["evidence_ids"] = ["invented-evidence"]
        with self.assertRaises(ContextualComparisonError): ContextualComparisonDossier(rehash(changed))

    def test_no_self_approval_selection_or_canonical_admission(self):
        for change in (lambda d: d["review"].update(status="approved"),
                       lambda d: d["review"].update(canonical_admission=True),
                       lambda d: d["review"].update(human_attestation={"actor": "model"}),
                       lambda d: d["decision_intelligence"]["reasoning_context"]["recommendation"].update(outcome="selected", selected_alternative_id=EXPECTED_IDS["Ponder"]),
                       lambda d: d["candidates"][0]["literal_instruction_annotation"].update(review_status="approved"),
                       lambda d: d["candidates"][0]["pending_roles"][0]["review"].update(status="approved")):
            document = copy.deepcopy(self.document); change(document)
            with self.assertRaises(ValueError): ContextualComparisonDossier(rehash(document))
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(KnowledgeValidationError):
                KnowledgeRepository(Path(directory)).append(self.pilot.dossier())
            self.assertEqual(list(Path(directory).rglob("*")), [])

    def test_content_id_deep_immutability_and_game_neutral_envelope(self):
        dossier = self.pilot.dossier()
        self.assertEqual(content_identity({k: v for k, v in self.document.items() if k != "comparison_id"}), self.document["comparison_id"])
        with self.assertRaises(TypeError): dossier.payload["context"]["assumptions"][0]["value"] = "changed"
        changed = dossier.to_dict(); changed["context"]["description"] = "changed"
        with self.assertRaisesRegex(ContextualComparisonError, "identity"): ContextualComparisonDossier(changed)
        schema = json.loads((ROOT / "src/schemas/v1/contextual-card-comparison-v1.schema.json").read_bytes())
        Draft202012Validator.check_schema(schema)
        self.assertNotIn("enum", schema["properties"]["candidates"]["items"]["properties"]["card_identity"]["properties"]["game_id"])
        self.assertEqual(stable_json(self.document), dossier.to_json())

    def test_bounded_manual_handoff_uses_unmodified_exact_query_contracts(self):
        context = self.pilot.reasoning_context()
        self.assertEqual(context, self.pilot.reasoning_context())
        self.assertFalse(context["live_model_or_transport"])
        self.assertLessEqual(len(stable_json(context).encode()), 65536)
        self.assertEqual(context["comparison"], self.document)
        self.assertEqual(len(context["canonical_contexts"]), 3)
        for c in context["canonical_contexts"]:
            self.assertEqual(c["schema_version"], "canonical-reasoning-context-v1")
            self.assertIsNone(c["analytics_snapshot_id"])
            self.assertEqual(c["canonical_snapshot_id"], self.document["canonical_snapshot_id"])
            request = c["normalized_request"]["semantic_request"]
            self.assertEqual(request["operation"], "find_identifier")
            self.assertIn(request["parameters"]["identifier"], EXPECTED_IDS.values())
            self.assertEqual(c["entities"], [])
            self.assertEqual(c["omitted_item_counts"]["entities"], 1)
            self.assertTrue(c["truncation"]["occurred"])
            self.assertGreater(c["omitted_item_counts"]["evidence"], 0)
        with patch("card_intelligence.comparison.MAXIMUM_BYTES", 10):
            with self.assertRaisesRegex(ContextualComparisonError, "byte bound"): self.pilot.reasoning_context()

    def test_example_contains_only_supplied_facts_proposals_arithmetic_and_unknowns(self):
        text = comparison_explanation(self.pilot.dossier())
        self.assertIn("**ABSTAIN**", text)
        for c in self.document["candidates"]:
            self.assertIn(c["card_identity"]["card_id"], text)
            for line in c["mechanical_facts"]["oracle_text"]["value"].splitlines(): self.assertIn(line, text)
            for h in c["strategic_hypotheses"]:
                self.assertIn("Unverified strategic hypothesis: " + h["statement"], text)
                self.assertIn(h["counterargument"], text)
        self.assertIn("Not net card advantage", text)
        for claim in ("Ponder is best", "Greater Good is superior", "wins games", "instant-speed activation", "verified combo"):
            self.assertNotIn(claim, text)

    def test_cli_structured_stdout_matches_retained_payload_and_is_deterministic(self):
        for flags, artifact in (([], "comparison.json"), (["--reasoning-context"], "reasoning-context.json")):
            expected = (REVIEW / artifact).read_bytes()
            outputs = []
            for _ in range(2):
                stream = io.StringIO()
                with patch("card_intelligence.cli.ContextualCardComparisonPilot", return_value=self.pilot), contextlib.redirect_stdout(stream):
                    self.assertEqual(main(["contextual-comparison", *flags]), 0)
                raw = stream.getvalue().encode("utf-8")
                self.assertLessEqual(len(raw), MAXIMUM_BYTES)
                self.assertTrue(raw.endswith(b"\n"))
                self.assertFalse(raw.endswith(b"\n\n"))
                # Normalize exactly one documented LF, not arbitrary whitespace.
                self.assertEqual(raw.removesuffix(b"\n"), expected.removesuffix(b"\n"))
                self.assertEqual(raw, (stable_json(json.loads(expected)) + "\n").encode("utf-8"))
                outputs.append(raw)
            self.assertEqual(outputs[0], outputs[1])

    def test_cli_byte_limit_includes_newline_and_multibyte_utf8_and_fails_closed(self):
        prefix_bytes = len(stable_json({"synthetic_payload": ""}).encode("utf-8"))
        for flags in ([], ["--reasoning-context"]):
            for body_bytes, expected_code in ((MAXIMUM_BYTES - 1, 0), (MAXIMUM_BYTES, 2)):
                payload = {"synthetic_payload": "é" + "x" * (body_bytes - prefix_bytes - len("é".encode("utf-8")))}
                body = stable_json(payload)
                self.assertEqual(len(body.encode("utf-8")), body_bytes)
                self.assertLessEqual(len(body + "\n"), MAXIMUM_BYTES)
                pilot = Mock()
                pilot.reasoning_context.return_value = payload
                pilot.dossier.return_value.to_json.return_value = body
                stream = io.StringIO()
                with patch("card_intelligence.cli.ContextualCardComparisonPilot", return_value=pilot), contextlib.redirect_stdout(stream):
                    self.assertEqual(main(["contextual-comparison", *flags]), expected_code)
                raw = stream.getvalue().encode("utf-8")
                if expected_code == 0:
                    self.assertEqual(len(raw), MAXIMUM_BYTES)
                    self.assertEqual(raw, body.encode("utf-8") + b"\n")
                    self.assertEqual(json.loads(raw), payload)
                else:
                    error = json.loads(raw)
                    self.assertFalse(error["valid"])
                    self.assertIn("trailing newline", error["error"])
                    self.assertLess(len(raw), MAXIMUM_BYTES)
                    self.assertNotIn(b"synthetic_payload", raw)
                    self.assertNotIn(b"x" * 100, raw)

    def test_retained_replay_cli_previous_demos_and_protected_data(self):
        artifacts = build_artifacts()
        self.assertEqual(len(artifacts), 5)
        self.assertEqual({p.name: p.read_bytes() for p in REVIEW.iterdir() if p.is_file()}, artifacts)
        manifest = json.loads(artifacts["manifest.json"])
        for name, metadata in manifest["files"].items():
            self.assertEqual(metadata, {"bytes": len(artifacts[name]), "sha256": hashlib.sha256(artifacts[name]).hexdigest()})
        for builder, directory, count in ((role_artifacts, "functional-role-pilot", 8),
                                          (mechanical_artifacts, "mechanical-card-cohort", 11),
                                          (demo_artifacts, "two-card-chatgpt-demo", 7)):
            retained = ROOT / "data/review" / directory
            replay = builder()
            self.assertEqual(len(replay), count)
            self.assertEqual({p.name: p.read_bytes() for p in retained.iterdir() if p.is_file()}, replay)
        for flag in ([], ["--reasoning-context"], ["--human-readable"]):
            stream = io.StringIO()
            with patch("card_intelligence.cli.ContextualCardComparisonPilot", return_value=self.pilot), contextlib.redirect_stdout(stream):
                self.assertEqual(main(["contextual-comparison", *flag]), 0)
            self.assertTrue(stream.getvalue())
        self.assertEqual(self.protected, protected_inventory())


if __name__ == "__main__":
    unittest.main()
