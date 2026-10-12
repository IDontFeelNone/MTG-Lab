"""Production-source role proposals stay bounded, deterministic and unapproved."""
import copy
from contextlib import redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from card_intelligence import FunctionalRoleCandidate, FunctionalRoleError, FunctionalRolePilot
from card_intelligence.cli import main
from card_intelligence.mechanics import content_identity, stable_json
from card_intelligence.models import KnowledgeValidationError
from card_intelligence.repository import KnowledgeRepository
from card_intelligence.roles import validate_role_supersession
from scripts.build_functional_role_pilot import build_artifacts, comparison_text
from scripts.build_mechanical_cohort import build_artifacts as mechanical_artifacts
from scripts.build_two_card_demo import build_artifacts as two_card_artifacts


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"
REVIEW = DATA / "review/functional-role-pilot"


def protected_inventory():
    files = [p for p in DATA.rglob("*") if p.is_file() and not p.is_relative_to(REVIEW)]
    files += [ROOT / p for p in ("docs/ARCHITECTURE.md", "docs/DECISIONS.md", "docs/ENGINEERING_STANDARDS.md")]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def rehash(document):
    body = copy.deepcopy(document)
    body.pop("candidate_id", None)
    return {**body, "candidate_id": content_identity(body)}


class FunctionalRolePilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.protected = protected_inventory()
        cls.pilot = FunctionalRolePilot(DATA)
        cls.documents = {i: cls.pilot.dossier(i) for i in cls.pilot.cards}
        cls.by_name = {d["card_identity"]["name"]: d for d in cls.documents.values()}
        cls.source = json.loads((ROOT / cls.pilot.mechanical.source["retained_source_reference"]).read_bytes())

    def candidate(self, name, role):
        return next(c for c in self.by_name[name]["role_candidates"] if c["role_reference"]["role_id"] == role)

    def altered_plan(self, change):
        plan = copy.deepcopy(self.pilot.plan)
        change(plan)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            with patch("card_intelligence.roles.MechanicalCardIntelligence", return_value=self.pilot.mechanical):
                return FunctionalRolePilot(DATA, plan_path=path)

    def test_exact_production_selection_and_no_cohort_classifier(self):
        canonical = json.loads((DATA / "canonical/state.json").read_bytes())
        self.assertEqual(len(self.documents), 15)
        self.assertTrue(set(self.documents) <= set(canonical["card"]))
        self.assertEqual(len(self.pilot.mechanical.cards), 384)
        self.assertEqual(self.pilot.mechanical.reconciliation["source_row_count"], 385)
        for identity, d in self.documents.items():
            self.assertEqual(d["card_identity"]["name"], canonical["card"][identity]["values"]["name"])
            self.assertEqual(d["source"]["oracle_id"], identity)
        for invalid in ("Sol Ring", "magic.sol-ring", "36cd2364-d113-47d1-b2c4-b088d9eb88dd"):
            with self.assertRaises(FunctionalRoleError): self.pilot.dossier(invalid)
        with self.assertRaisesRegex(FunctionalRoleError, "limited"):
            self.altered_plan(lambda p: p["cards"].extend(copy.deepcopy(p["cards"])))

    def test_multi_role_functions_and_state_census(self):
        report = self.pilot.report()
        self.assertEqual(report["candidate_count"], 30)
        self.assertEqual(report["candidate_state_counts"], {"known": 20, "incomplete": 4, "unknown": 2, "unsupported": 4})
        for name, roles in {
            "Veil of Summer": {"protection", "card_draw"},
            "Greater Good": {"sacrifice_outlet", "card_draw"},
            "Faithless Looting": {"card_draw", "recursion"},
            "Pitiless Plunderer": {"event_payoff", "mana_acceleration"},
            "Ponder": {"card_draw", "card_selection"},
        }.items():
            known = {c["role_reference"]["role_id"] for c in self.by_name[name]["role_candidates"] if c["value"]["status"] == "known"}
            self.assertEqual(known, roles)
        self.assertEqual(report["pilot_card_count"], 15)
        self.assertEqual(report["production_cohort_card_count"], 384)

    def test_conditions_costs_targeting_and_beneficiaries(self):
        wish = self.candidate("Wishclaw Talisman", "tutoring")
        self.assertEqual(wish["qualifiers"]["timing"]["description"], "Activate only during your turn.")
        self.assertIn("An opponent gains control of this artifact.", wish["qualifiers"]["restrictions"])
        self.assertTrue(any("wish counter" in x and "{T}" in x for x in wish["qualifiers"]["costs"]))
        veil = self.candidate("Veil of Summer", "card_draw")
        self.assertEqual(veil["qualifiers"]["conditions"], ["An opponent must have cast a blue or black spell this turn."])
        giver = self.candidate("Giver of Runes", "protection")
        self.assertIn("The target must be another creature you control.", giver["qualifiers"]["restrictions"])
        standstill = self.candidate("Standstill", "card_draw")
        self.assertTrue(any("not always" in x for x in standstill["qualifiers"]["restrictions"]))
        greater = self.candidate("Greater Good", "card_draw")
        self.assertIn("The discard-three instruction follows the draw.", greater["qualifiers"]["restrictions"])
        self.assertTrue(any("power" in x for x in greater["qualifiers"]["conditions"]))

    def test_false_positive_controls_and_no_keyword_classifier(self):
        for name, role in (("Underworld Breach", "sacrifice_outlet"),
                           ("Standstill", "sacrifice_outlet"),
                           ("Pitiless Plunderer", "sacrifice_outlet"),
                           ("Noxious Revival", "card_draw")):
            candidate = self.candidate(name, role)
            self.assertEqual(candidate["value"], {"status": "unsupported", "data": None})
        cruise = self.by_name["Treasure Cruise"]
        self.assertEqual([c["role_reference"]["role_id"] for c in cruise["role_candidates"]], ["card_draw"])
        self.assertIn("Delve", self.candidate("Treasure Cruise", "card_draw")["mechanical_binding"]["source_field_value"])
        basalt = self.candidate("Basalt Monolith", "combo_enabling")
        self.assertEqual(basalt["value"], {"status": "unknown", "data": None})
        self.assertTrue(any("{3}" in x for x in basalt["qualifiers"]["costs"]))
        def assign_combo(plan):
            card = next(c for c in plan["cards"] if c["name"] == "Basalt Monolith")
            role = next(c for c in card["roles"] if c["role_id"] == "combo_enabling")
            role.update(state="known", basis="direct_mechanical", function="A verified loop")
        with self.assertRaisesRegex(FunctionalRoleError, "basis"):
            self.altered_plan(assign_combo)

    def test_every_source_reference_resolves_and_complete_ability_text_is_preserved(self):
        for identity, d in self.documents.items():
            mechanical = self.pilot.mechanical.dossier(identity).to_dict()
            self.assertEqual(d["mechanical_dossier_id"], mechanical["dossier_id"])
            row = self.source[d["source"]["source_record_index"]]
            self.assertEqual(row["oracle_id"], identity)
            for c in d["role_candidates"]:
                binding = c["mechanical_binding"]
                self.assertEqual(binding["source_field_value"], row["oracle_text"])
                self.assertEqual(binding["record_content_identity"], content_identity(row))
                self.assertEqual(binding["ability_lines"], row["oracle_text"].splitlines())
                self.assertEqual(c["evidence"][0]["observed_at"], d["source"]["source_timestamp"])
                ref, fragment = c["evidence"][0]["reference"].split("#", 1)
                value = json.loads((ROOT / ref).read_bytes())
                for part in fragment[1:].split("/"): value = value[int(part)] if isinstance(value, list) else value[part]
                self.assertEqual(value, row["oracle_text"])
                self.assertIn("\n".join(binding["ability_lines"]), c["evidence"][0]["claim"])

    def test_missing_snapshot_or_exact_mechanical_binding_fails_closed(self):
        for change in (
            lambda p: p.update(canonical_snapshot_id="sha256:" + "0" * 64),
            lambda p: p["cards"][0].update(mechanical_dossier_id="sha256:" + "0" * 64),
            lambda p: p["cards"][0].update(oracle_text="Draw"),
            lambda p: p["cards"][0]["roles"][0].update(evidence_lines=[999]),
            lambda p: p["cards"][0]["roles"][0].update(role_id="universal_power"),
        ):
            with self.assertRaises(FunctionalRoleError): self.altered_plan(change)

    def test_unknown_incomplete_and_unsupported_states_cannot_become_known_by_relabeling(self):
        incomplete = self.candidate("Counterspell", "protection")
        self.assertEqual(incomplete["value"]["status"], "incomplete")
        self.assertTrue(incomplete["context_dependencies"])
        for name, role, change in (
            ("Counterspell", "protection", lambda c: c["value"].update(status="known")),
            ("Basalt Monolith", "combo_enabling", lambda c: c["value"].update(data="A loop")),
            ("Noxious Revival", "card_draw", lambda c: c["value"].update(status="known", data="Draw a card")),
            ("Counterspell", "protection", lambda c: c.update(context_dependencies=[])),
        ):
            c = copy.deepcopy(self.candidate(name, role)); change(c)
            with self.assertRaises(FunctionalRoleError): FunctionalRoleCandidate(rehash(c))

    def test_review_boundary_rejects_self_approval_and_knowledge_admission(self):
        original = self.candidate("Sol Ring", "mana_acceleration")
        for change in (lambda c: c["review"].update(status="approved"),
                       lambda c: c["review"].update(canonical_admission=True),
                       lambda c: c["review"].update(human_attestation={"actor": "model"})):
            c = copy.deepcopy(original); change(c)
            with self.assertRaises(FunctionalRoleError): FunctionalRoleCandidate(rehash(c))
        with tempfile.TemporaryDirectory() as temporary:
            repository = KnowledgeRepository(Path(temporary))
            with self.assertRaises(KnowledgeValidationError): repository.append(FunctionalRoleCandidate(original))
            self.assertEqual(list(Path(temporary).rglob("*")), [])
        self.assertFalse(self.pilot.report()["human_review"]["canonical_admission_eligible"])

    def test_prominence_requires_context_and_shared_envelope_is_game_neutral(self):
        original = copy.deepcopy(self.candidate("Sol Ring", "mana_acceleration"))
        self.assertEqual(original["prominence"]["status"], "unknown")
        original["prominence"].update(status="known", designation="primary")
        with self.assertRaises(FunctionalRoleError): FunctionalRoleCandidate(rehash(original))
        original["prominence"]["context_evidence"] = [{"source_id": "synthetic-deck-objective",
            "source_type": "synthetic_fixture", "reference": "fixture:objective", "observed_at": "2026-10-12T16:00:00Z",
            "claim": "Synthetic objective used only to test the generic pending contract."}]
        original["subject"] = {"game_id": "synthetic-game", "card_id": "synthetic-card"}
        original["mechanical_binding"]["source_field_name"] = "ability_text"
        original["mechanical_binding"]["context_metadata"] = {"resource_system": "synthetic"}
        for designation in ("primary", "secondary"):
            original["prominence"]["designation"] = designation
            self.assertEqual(FunctionalRoleCandidate(rehash(original)).to_dict()["review"]["status"], "requires_review")
        self.assertTrue(all(c["prominence"]["status"] == "unknown" for d in self.documents.values() for c in d["role_candidates"]))

    def test_supersession_preserves_subject_role_and_forward_time_without_promotion(self):
        old = FunctionalRoleCandidate(self.candidate("Sol Ring", "mana_acceleration"))
        document = old.to_dict(); document["prepared_at"] = "2026-10-12T16:08:12Z"
        document["supersedes"] = [old.to_dict()["candidate_id"]]
        replacement = FunctionalRoleCandidate(rehash(document))
        validate_role_supersession(replacement, (old,))
        with self.assertRaises(FunctionalRoleError): validate_role_supersession(replacement, ())
        for change in (lambda c: c["subject"].update(card_id="other-card"),
                       lambda c: c["role_reference"].update(role_id="other-role"),
                       lambda c: c.update(prepared_at=old.to_dict()["prepared_at"])):
            c = copy.deepcopy(document); change(c)
            with self.assertRaises(FunctionalRoleError): validate_role_supersession(FunctionalRoleCandidate(rehash(c)), (old,))

    def test_immutable_candidate_content_identity_and_no_hidden_truncation(self):
        candidate = FunctionalRoleCandidate(self.candidate("Sol Ring", "mana_acceleration"))
        with self.assertRaises(TypeError): candidate.payload["review"]["status"] = "approved"
        with self.assertRaises(TypeError): candidate.payload["qualifiers"]["costs"][0] = "No cost"
        changed = candidate.to_dict(); changed["value"]["data"] = "Changed"
        with self.assertRaisesRegex(FunctionalRoleError, "content identity"): FunctionalRoleCandidate(changed)
        for i, d in self.documents.items():
            self.assertEqual(stable_json(d), stable_json(self.pilot.dossier(i)))
            body = copy.deepcopy(d); identity = body.pop("dossier_id")
            self.assertEqual(content_identity(body), identity)
            self.assertEqual(d["omissions"]["pilot_role_candidates_omitted"], 0)
            self.assertLessEqual(len(stable_json(d).encode()), 65536)

    def test_existing_reasoning_contract_and_bounded_manual_supplements(self):
        for i in self.pilot.plan["comparison_card_ids"]:
            context = self.pilot.reasoning_context(i).to_dict()
            self.assertEqual(context["schema_version"], "canonical-reasoning-context-v1")
            self.assertEqual(context["entities"][0]["canonical_identity"], i)
            self.assertEqual(context["canonical_snapshot_id"], self.pilot.mechanical.snapshot_id)
            self.assertEqual(context["analytics_results"][0]["dossier"], self.pilot.mechanical.dossier(i).to_dict())
            self.assertEqual(context["analytics_results"][1]["dossier"], self.pilot.dossier(i))
            self.assertEqual(context["analytics_results"][1]["projection"], "functional_role_review_pilot_manual_handoff")
            self.assertIsNone(context["analytics_snapshot_id"])
            self.assertEqual(context["truncation"]["role_supplement"]["role_candidates_omitted"], 0)
            self.assertLessEqual(len(stable_json(context).encode()), 65536)
            hashed = {"canonical_snapshot_id": context["canonical_snapshot_id"], "analytics_snapshot_id": None,
                "request": context["normalized_request"], "entities": context["entities"], "relationships": context["relationships"],
                "analytics": context["analytics_results"], "provenance": context["provenance_references"], "evidence": context["evidence_references"],
                "omitted": context["omitted_item_counts"], "truncation": context["truncation"], "warnings": context["warnings"]}
            self.assertEqual(context["context_id"], content_identity(hashed))
        with patch("card_intelligence.roles.MAXIMUM_BYTES", 100):
            with self.assertRaises(FunctionalRoleError): self.pilot.reasoning_context(self.pilot.plan["comparison_card_ids"][0])

    def test_three_card_comparison_renders_only_supplied_proposals(self):
        comparison = self.pilot.comparison()
        self.assertEqual({r["card_identity"]["name"] for r in comparison["cards"]}, {"Ponder", "Faithless Looting", "Greater Good"})
        self.assertEqual(comparison["shared_known_function_roles"], ["card_draw"])
        text = comparison_text(comparison)
        for row in comparison["cards"]:
            for c in row["role_candidates"]:
                self.assertIn(c["candidate_id"], text)
                self.assertIn(c["value"]["data"] or c["basis_explanation"], text)
                for line in c["mechanical_binding"]["ability_lines"]: self.assertIn(line, text)
        self.assertIn("discard", text)
        self.assertIn("requires_review", text)
        self.assertNotIn("better than", text)
        for d in self.documents.values():
            for claim in ("verified_combos", "competitive_rankings", "best_in_slot", "net_card_advantage"):
                self.assertIn(claim, d["unsupported_dimensions"])
            for field in ("power_score", "recommendation", "rankings", "verified_combo"):
                self.assertNotIn(field, d)

    def test_cli_rejects_name_seed_and_nonpilot_ids(self):
        card_id = self.by_name["Sol Ring"]["card_identity"]["card_id"]
        for argv, code in ((["roles", "--card-id", card_id], 0), (["roles-pilot"], 0),
                           (["roles-comparison"], 0), (["roles", "--card-id", "magic.sol-ring"], 2)):
            output = StringIO()
            with patch("card_intelligence.cli.FunctionalRolePilot", return_value=self.pilot), redirect_stdout(output):
                self.assertEqual(main(argv), code)
            self.assertIn("schema_version", json.loads(output.getvalue()))

    def test_retained_replay_and_all_protected_production_evidence_unchanged(self):
        expected = build_artifacts()
        self.assertEqual(len(expected), 8)
        self.assertEqual(expected, {p.name: p.read_bytes() for p in REVIEW.iterdir() if p.is_file()})
        manifest = json.loads(expected["manifest.json"])
        self.assertEqual(len(manifest["dossiers"]), 15)
        for name, meta in manifest["files"].items():
            self.assertEqual(meta["sha256"], hashlib.sha256(expected[name]).hexdigest())
            self.assertEqual(meta["bytes"], len(expected[name]))
        for producer, directory in ((mechanical_artifacts, "mechanical-card-cohort"), (two_card_artifacts, "two-card-chatgpt-demo")):
            self.assertEqual(producer(), {p.name: p.read_bytes() for p in (DATA / "review" / directory).iterdir() if p.is_file()})
        self.assertEqual(self.protected, protected_inventory())


if __name__ == "__main__":
    unittest.main()
