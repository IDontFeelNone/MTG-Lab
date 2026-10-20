"""Offline design proofs; no official source, card text, or gameplay execution.

Preservation digests were captured independently from canonical main
ccf408904f682d9b2e49ba6d25ade335d80d61fb before this milestone added files.
They bind all 282 prior source files and all 156 retained evidence files.
"""
import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from activated_ability_preservation import is_design_addition
from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.errors import GameplayContractError


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "reference-reviews/gameplay-rules-madness-casting-design"
CODE = ROOT / "src/gameplay_rules/casting_design"
CANONICAL = "ccf408904f682d9b2e49ba6d25ade335d80d61fb"
HISTORICAL = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
FRONTIER = ("601.2b", "601.2f", "601.2g", "601.2h")
CANDIDATES = {"700.2", "702.47", "118.8", "118.9", "107.3", "605"}
PRIOR_PACKAGES = {
    "gameplay-rules-foundational-projection": "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea",
    "gameplay-rules-execution-profile-design": "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687",
    "gameplay-rules-foundational-dependencies": "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a",
    "gameplay-rules-object-control-exceptions": "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab",
    "gameplay-rules-zone-change-exceptions": "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875",
    "gameplay-rules-zone-change-direct-dependencies": "sha256:d51fab1425f6aa9b82e4621ac8c88d4b83d736c6906a4f4c589c41ff1aeadba4",
}
FILES = {"source-anchor-design.json", "casting-subprocedure-design.json", "cost-design.json",
         "madness-readiness.json", "projection-frontier.json", "manifest.json"}


def inventory(paths):
    files = set()
    for path in paths:
        files.update([path] if path.is_file() else [item for item in path.rglob("*")
                     if item.is_file() and "__pycache__" not in item.parts and item.suffix != ".pyc"])
    result = []
    for path in sorted(files):
        # The successor guard independently pins every inherited byte.
        if is_design_addition(path):
            continue
        if path.is_symlink():
            raise AssertionError("Protected artifact must not be a symlink")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


def retained_projection_rules():
    result = {}
    for name in PRIOR_PACKAGES:
        path = ROOT / "reference-reviews" / name / "projection.json"
        if path.exists():
            value = json.loads(path.read_bytes())
            for rule in value["rules"]:
                reference = rule["rule_reference"]
                if reference in result:
                    raise AssertionError("Prior real rule must be represented only once")
                result[reference] = rule
    return result


class MadnessCastingPreservationTests(unittest.TestCase):
    def assert_inventory(self, paths, count, digest):
        value = inventory(paths)
        self.assertEqual(len(value), count)
        self.assertEqual(hashlib.sha256(deterministic_json(value).encode()).hexdigest(), digest)

    def test_all_prior_runtime_product_policy_admission_intelligence_and_projection_code_byte_identical(self):
        paths = [path for path in (ROOT / "src").iterdir() if path.name != "gameplay_rules"]
        paths.extend(path for path in (ROOT / "src/gameplay_rules").iterdir()
                     if path.name not in {"projection", "casting_design", "mana_ability_design", "mana_dependency_design", "__pycache__"})
        paths.extend(path for path in (ROOT / "src/gameplay_rules/projection").glob("*.py")
                     if not path.name.startswith(("bounded_casting_", "bounded_mana_", "mana_classification_"))
                     # The successor guard keeps all historical digests and
                     # permits only these four append-only source files.
                     and path.name not in {"mana_stack_exception_source.py", "mana_stack_exception_pins.py",
                         "mana_stack_exception_reports.py", "mana_stack_exception_package.py"})
        self.assert_inventory(paths, 282, "16e1125ab591a3bf2c5e503a5c3b1eda854dfcbb56d5e1a7e99a1fcbce173a20")

    def test_all_156_prior_retained_evidence_and_design_files_byte_identical(self):
        paths = [path for path in (ROOT / "reference-reviews").iterdir()
                 if path != PACKAGE and path.name not in {"gameplay-rules-bounded-casting-projection", "gameplay-rules-mana-ability-design", "gameplay-rules-bounded-mana-ability-projection", "gameplay-rules-mana-direct-dependency-design", "gameplay-rules-bounded-mana-classification-projection",
                     "gameplay-rules-bounded-mana-stack-exception-projection"}]
        self.assert_inventory(paths, 156, "29b7e1fe080bc49bfdf68f39f7b1fec783c7447bac72d2d7f261778a77a9e509")

    def test_exact_six_prior_package_identities_remain(self):
        for name, identity in PRIOR_PACKAGES.items():
            with self.subTest(package=name):
                manifest = json.loads((ROOT / "reference-reviews" / name / "manifest.json").read_bytes())
                self.assertEqual(manifest["package_id"], identity)

    def test_historical_single_line_anchor_and_evidence_identities_are_byte_identical(self):
        paths = [path for path in (ROOT / "reference-reviews").iterdir()
                 if path.name.startswith("gameplay-rules-") and path != PACKAGE
                 and path.name not in {"gameplay-rules-bounded-casting-projection", "gameplay-rules-mana-ability-design", "gameplay-rules-bounded-mana-ability-projection", "gameplay-rules-mana-direct-dependency-design", "gameplay-rules-bounded-mana-classification-projection",
                     "gameplay-rules-bounded-mana-stack-exception-projection"}]
        self.assert_inventory(paths, 51, "66b80a9883ad434ff778d528cbc938f3804c6f9b4355b9fff0e6e63f8808c0f4")
        for rule in retained_projection_rules().values():
            self.assertEqual(rule["source_anchor"]["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")

    def test_exact_sixty_three_prior_projected_units_and_no_601_source_rules(self):
        rules = retained_projection_rules()
        self.assertEqual(len(rules), 63)
        self.assertFalse(any(reference.startswith("601.") for reference in rules))
        self.assertTrue(set(FRONTIER).isdisjoint(rules))
        self.assertTrue(CANDIDATES.isdisjoint(rules))
        self.assertTrue({"613", "603", "603.7d", "603.7e", "603.7f", "114",
                         "901.6", "902.6", "904.7", "905.5"}.isdisjoint(rules))

    def test_architecture_v13_and_decision_017_are_unchanged(self):
        self.assert_inventory([ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md")],
            5, "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")

    def test_historical_card_acquisition_identity_and_file_bytes_are_unchanged(self):
        root = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((root / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL)
        for name, binding in manifest["files"].items():
            raw = (root / name).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, binding)

    def test_fictional_profile_and_simulation_are_unchanged(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_design_namespace_has_no_runtime_network_ingestion_or_payment_implementation(self):
        forbidden_imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation",
                             "providers", "external_ingestion", "market", "production_evidence",
                             "repository", "random", "secrets"}
        forbidden_runtime = {"GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                             "LegalityResult", "GameTransition", "GameplayRulesEngine", "RawSnapshotStore"}
        forbidden_functions = {"to_rules_snapshot", "to_execution_profile", "activate_profile", "move_object",
                               "execute_trigger", "cast_spell", "play_land", "apply_continuous_effect",
                               "perform_state_based_actions", "execute_madness", "pay_cost", "pay_mana",
                               "calculate_total_cost", "activate_mana_ability", "resolve_spell", "rollback"}
        paths = list(CODE.glob("*.py"))
        self.assertGreater(len(paths), 1)
        for path in paths:
            tree = ast.parse(path.read_text(), filename=str(path))
            for node in ast.walk(tree):
                with self.subTest(module=path.name, node=type(node).__name__):
                    if isinstance(node, ast.Import):
                        self.assertTrue(forbidden_imports.isdisjoint(alias.name.split(".")[0] for alias in node.names))
                    elif isinstance(node, ast.ImportFrom):
                        self.assertNotIn((node.module or "").split(".")[0], forbidden_imports)
                        self.assertTrue(forbidden_runtime.isdisjoint(alias.name for alias in node.names))
                    elif isinstance(node, ast.Name):
                        self.assertNotIn(node.id, forbidden_runtime)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertNotIn(node.name, forbidden_functions)


class MultiLineAnchorDesignTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.casting_design.anchors import (
            build_source_anchor_design, verify_fictional_rule_blocks, validate_fictional_block_spans,
        )
        self.design = build_source_anchor_design()
        self.verify = verify_fictional_rule_blocks
        self.validate_spans = validate_fictional_block_spans
        self.fixture = b"FIC.1a. Authored opening\r\n  Authored continuation\nFIC.1b. Authored following\r\n[[FIC_END]]\n"

    def test_historical_single_line_policy_is_supported_without_anchor_conversion(self):
        value = self.design.to_dict()["compatibility"]
        self.assertEqual(value["historical_anchor_type"], "SINGLE_LINE_RULE_ANCHOR")
        self.assertEqual(value["historical_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")
        self.assertEqual(value["historical_anchor_conversion"], "FORBIDDEN")
        self.assertFalse(value["historical_anchor_identity_changes"])
        self.assertEqual(value["supported_anchor_types"],
                         ["SINGLE_LINE_RULE_ANCHOR", "MULTI_LINE_RULE_BLOCK_ANCHOR"])

    def test_future_anchor_contract_contains_complete_span_metadata_and_no_actual_cr_anchor(self):
        value = self.design.to_dict()["future_anchor_contract"]
        self.assertEqual(value["anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
        self.assertEqual(value["span_policy"], "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR")
        self.assertEqual(set(value["fields"]), {"rule_reference", "artifact_identity", "effective_date",
            "starting_physical_line", "ending_physical_line", "byte_start", "byte_end", "line_count", "span_sha256"})
        self.assertEqual(value["concrete_real_source_anchors_created"], 0)
        self.assertFalse(value["real_source_verification_implemented"])
        self.assertFalse(value["source_prose_retained"])

    def test_fictional_complete_multiline_span_and_lines_are_deterministic(self):
        first, second = self.verify(self.fixture, ("FIC.1a", "FIC.1b"))
        expected = b"FIC.1a. Authored opening\r\n  Authored continuation"
        self.assertEqual((first.starting_physical_line, first.ending_physical_line, first.line_count), (1, 2, 2))
        self.assertEqual((first.byte_start, first.byte_end), (0, len(expected)))
        self.assertEqual(first.span_sha256, "sha256:" + hashlib.sha256(expected).hexdigest())
        self.assertEqual(first.artifact_identity, "sha256:" + hashlib.sha256(self.fixture).hexdigest())
        self.assertEqual((second.starting_physical_line, second.ending_physical_line, second.line_count), (3, 3, 1))
        self.assertLess(first.byte_end, second.byte_start)
        self.assertEqual((first, second), self.verify(self.fixture, ("FIC.1a", "FIC.1b")))
        self.assertNotIn("Authored", repr(first.to_dict()))
        self.assertFalse(first.real_source_verified)
        self.assertFalse(first.source_body_retained)
        with self.assertRaises(FrozenInstanceError):
            first.byte_end = 1

    def test_internal_line_terminators_are_included_exactly_in_span_hash(self):
        one = self.verify(self.fixture, ("FIC.1a",))[0]
        two = self.verify(self.fixture.replace(b"opening\r\n", b"opening\n"), ("FIC.1a",))[0]
        self.assertNotEqual(one.span_sha256, two.span_sha256)
        self.assertEqual(one.byte_end, two.byte_end + 1)

    def test_final_line_terminator_is_excluded_but_full_artifact_identity_changes(self):
        one = self.verify(self.fixture, ("FIC.1b",))[0]
        changed = self.fixture.replace(b"following\r\n", b"following\n")
        two = self.verify(changed, ("FIC.1b",))[0]
        self.assertEqual(one.span_sha256, two.span_sha256)
        self.assertEqual((one.byte_start, one.byte_end), (two.byte_start, two.byte_end))
        self.assertNotEqual(one.artifact_identity, two.artifact_identity)

    def test_following_rules_example_is_not_swallowed(self):
        fixture = b"FIC.1a. Earlier\nFIC.1b. Later\nFIC_EXAMPLE[FIC.1b]: Later illustration\n[[FIC_END]]\n"
        first, second = self.verify(fixture, ("FIC.1a", "FIC.1b"))
        self.assertEqual(first.byte_end, len(b"FIC.1a. Earlier"))
        self.assertEqual(second.line_count, 2)
        self.assertNotIn("Later illustration", repr((first, second)))

    def test_missing_duplicate_malformed_and_ambiguous_boundaries_fail_closed(self):
        cases = [
            (self.fixture, ("FIC.9",)),
            (self.fixture, ("FIC.1a", "FIC.1a")),
            (self.fixture.replace(b"FIC.1b.", b"FIC.1a."), ("FIC.1a",)),
            (self.fixture.replace(b"FIC.1b.", b"FIC.01b."), ("FIC.1a",)),
            (self.fixture.replace(b"[[FIC_END]]\n", b""), ("FIC.1a",)),
            (self.fixture.replace(b"  Authored continuation", b"Ambiguous ownership"), ("FIC.1a",)),
            (self.fixture.replace(b"  Authored continuation", b"FIC_EXAMPLE[FIC.1b]: Following example"), ("FIC.1a",)),
            (self.fixture + b"  Trailing bytes", ("FIC.1a",)),
        ]
        for fixture, references in cases:
            with self.subTest(fixture=fixture, references=references):
                with self.assertRaises(GameplayContractError):
                    self.verify(fixture, references)

    def test_overlapping_selected_spans_and_mixed_fixture_identity_fail(self):
        first, second = self.verify(self.fixture, ("FIC.1a", "FIC.1b"))
        overlap = replace(second, byte_start=first.byte_start)
        different = replace(second, artifact_identity="sha256:" + "f" * 64)
        for rows in ((first, overlap), (first, different), (first, first)):
            with self.subTest(rows=rows):
                with self.assertRaises(GameplayContractError):
                    self.validate_spans(rows)

    def test_real_rule_labels_and_real_numbered_source_grammar_are_rejected(self):
        with self.assertRaises(GameplayContractError):
            self.verify(self.fixture, FRONTIER)
        with self.assertRaises(GameplayContractError):
            self.verify(b"601.2b. Synthetic text\n[[FIC_END]]\n", ("FIC.1a",))
        value = self.design.to_dict()["fictional_proof_contract"]
        self.assertEqual(value["authority"], "FICTIONAL_FIXTURE_ONLY")
        self.assertFalse(value["real_rule_labels_accepted"])
        self.assertFalse(value["real_source_bytes_read"])
        self.assertTrue(value["no_general_real_source_parser"])


class CastingAndCostDesignTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.casting_design.stages import build_casting_subprocedure_design
        from gameplay_rules.casting_design.costs import build_cost_design
        self.build_casting = build_casting_subprocedure_design
        self.build_cost = build_cost_design
        self.casting = self.build_casting()
        self.cost = self.build_cost(self.casting)
        self.value = self.casting.to_dict()
        self.cost_value = self.cost.to_dict()

    def test_four_frontier_refs_are_unprojected_and_stage_order_is_deterministic(self):
        self.assertEqual(tuple(self.value["current_casting_frontier"]), FRONTIER)
        self.assertEqual([row["future_rule_reference"] for row in self.value["stages"]], list(FRONTIER))
        self.assertEqual([row["stage_id"] for row in self.value["stages"]], ["CASTING_CHOICES",
            "TOTAL_COST_DETERMINATION", "MANA_ABILITY_WINDOW", "TOTAL_COST_PAYMENT"])
        self.assertEqual([row["sequence"] for row in self.value["stages"]], [1, 2, 3, 4])
        self.assertTrue(all(row["projection_status"] == "UNPROJECTED" for row in self.value["stages"]))
        self.assertTrue(all(row["execution_supported"] is False for row in self.value["stages"]))
        self.assertTrue(self.value["semantic_sequence_only"])
        self.assertFalse(self.value["executable_state_machine"])
        self.assertEqual(self.casting, self.build_casting())

    def test_subprocedure_does_not_imply_complete_casting_structurally(self):
        capabilities = self.value["capabilities"]
        self.assertEqual(set(capabilities), {"alternative_cost_casting_subprocedure", "complete_spell_casting"})
        self.assertEqual(capabilities["alternative_cost_casting_subprocedure"]["implied_capabilities"], [])
        full = capabilities["complete_spell_casting"]
        self.assertEqual(full["representation"], "OUTSIDE_DESIGN")
        self.assertEqual(full["execution_readiness"], "BLOCKED")
        self.assertTrue(full["requires_independent_closure"])
        self.assertFalse(full["satisfied_by_subprocedure"])

    def test_choice_declarations_include_unknown_and_unsupported_cost_families(self):
        choice = self.value["stages"][0]
        self.assertTrue({"synthetic_spell_reference", "chosen_casting_method", "base_cost_basis",
            "additional_costs_selected", "variable_values", "modal_choices", "splice_choices",
            "hybrid_payment_declarations", "phyrexian_payment_declarations",
            "prior_casting_choice_restrictions", "knowledge_state", "unsupported_choice_families"
        }.issubset(choice["declaration_fields"]))
        self.assertEqual(choice["knowledge_states"], ["KNOWN", "UNKNOWN", "UNSUPPORTED"])
        self.assertEqual(self.value["evidence_status"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")

    def test_madness_selects_alternative_basis_and_cannot_be_modeled_as_discount(self):
        choice = self.value["stages"][0]
        self.assertEqual(choice["base_cost_basis"], ["NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"])
        madness = choice["madness_case"]
        self.assertEqual(madness["base_cost_basis"], "SELECTED_ALTERNATIVE_COST")
        self.assertEqual(madness["alternative_cost_source"], "madness")
        self.assertFalse(madness["mana_cost_discount"])
        self.assertFalse(madness["legal_cast_established"])
        self.assertTrue(madness["candidate_cost_only"])
        expression = self.cost_value["expression_contract"]
        self.assertEqual(expression["basis_cardinality"], "EXACTLY_ONE")
        self.assertFalse(expression["alternative_cost_is_discount"])
        body = {key: self.value[key] for key in self.casting.BODY_FIELDS}
        body["stages"][0]["madness_case"]["mana_cost_discount"] = True
        with self.assertRaises(GameplayContractError):
            type(self.casting).create(body)

    def test_multiple_alternative_cost_conflict_has_unknown_and_unsupported_states(self):
        conflict = self.value["stages"][0]["alternative_cost_conflict"]
        self.assertEqual(conflict["selected_alternative_cost"], "SINGLE_CANDIDATE_OR_NONE")
        self.assertEqual(conflict["interaction_states"], ["MUTUALLY_EXCLUSIVE", "UNKNOWN", "UNSUPPORTED"])
        self.assertEqual(conflict["selection_algorithm"], "ABSENT")
        self.assertFalse(conflict["interaction_semantics_complete"])

    def test_cost_model_is_unevaluated_ordered_expression_and_taxonomy(self):
        expression = self.cost_value["expression_contract"]
        self.assertEqual(expression["ordered_expression_terms"], ["selected_base_cost", "additional_costs",
            "cost_increases", "cost_reductions", "direct_total_cost_modifiers", "locked_total_cost"])
        self.assertEqual(expression["component_taxonomy"], ["MANA", "TAPPING", "SACRIFICING", "DISCARDING",
            "LIFE", "GENERIC_NONMANA", "UNKNOWN", "UNSUPPORTED"])
        self.assertEqual(expression["calculation"], "ABSENT")
        self.assertEqual(expression["real_card_input"], "FORBIDDEN")
        self.assertEqual(expression["layers"], "UNIMPLEMENTED")
        self.assertEqual(self.cost_value["casting_design_id"], self.casting.identity)

    def test_cost_lock_and_payment_must_bind_exact_locked_identity(self):
        lock = self.cost_value["lock_contract"]
        self.assertEqual(lock["states"], ["UNDETERMINED", "DETERMINED", "LOCKED"])
        self.assertEqual(lock["payment_required_state"], "LOCKED")
        self.assertEqual(lock["payment_identity_binding"], "EXACT_IDENTITY_EQUALITY")
        self.assertEqual(lock["recompute_during_payment"], "FORBIDDEN")
        self.assertFalse(lock["state_machine"])
        self.assertEqual(lock["runtime_locking"], "ABSENT")
        self.assertEqual(self.value["stages"][3]["input"], "EXACT_LOCKED_COST_IDENTITY")
        self.assertEqual(self.value["stages"][3]["silent_cost_recomputation"], "FORBIDDEN")

    def test_payment_contract_has_no_partial_payment_and_explicit_unpayable_condition(self):
        payment = self.cost_value["payment_contract"]
        self.assertIn("locked_total_cost_identity", payment["fields"])
        self.assertIn("unpayable_cost_condition", payment["fields"])
        self.assertEqual(payment["partial_payment"], "FORBIDDEN")
        self.assertEqual(payment["unpayable_cost"], "CANNOT_BE_PAID")
        self.assertEqual(payment["component_states"], ["PAID", "UNPAID", "UNKNOWN", "UNSUPPORTED"])
        self.assertEqual(payment["payment_execution"], "ABSENT")
        self.assertEqual(self.cost_value["runtime_operations"], [])

    def test_payment_order_groups_separate_ordinary_from_random_or_library_movement(self):
        groups = self.cost_value["payment_contract"]["ordered_groups"]
        self.assertEqual([row["sequence"] for row in groups], [1, 2])
        self.assertEqual([row["group"] for row in groups], ["ORDINARY", "RANDOM_OR_LIBRARY_TO_PUBLIC_ZONE"])
        self.assertEqual(groups[1]["components"], ["RANDOM_ELEMENTS", "LIBRARY_TO_PUBLIC_ZONE"])
        for name in ("randomization", "library_inspection", "object_movement", "game_state_mutation"):
            self.assertEqual(self.cost_value["payment_contract"][name], "ABSENT")

    def test_mana_window_keeps_605_unresolved_and_fictional_authority_separate(self):
        mana = self.value["stages"][2]
        self.assertEqual(mana["condition"], "TOTAL_COST_CONTAINS_MANA_PAYMENT")
        self.assertEqual(mana["direct_dependency_design_input"], "605")
        self.assertEqual(mana["dependency_state"], "UNRESOLVED_UNPROJECTED")
        self.assertEqual(mana["fictional_mana_authority"], "DOES_NOT_SATISFY_REAL_605")
        self.assertFalse(mana["mana_abilities_available"])
        self.assertFalse(mana["mana_pool_available"])
        self.assertFalse(mana["priority_available"])

    def test_unmodeled_relevant_branches_fail_closed_in_synthetic_design_proofs(self):
        policy = self.value["branch_policy"]
        self.assertEqual(policy["alternative_cost_selection"], "CENTRAL")
        self.assertEqual(policy["total_cost_determination"], "CENTRAL")
        self.assertEqual(policy["payment"], "CENTRAL")
        self.assertEqual(policy["unmodeled_relevant_branch"], ["INDETERMINATE", "UNSUPPORTED"])
        self.assertEqual(policy["confident_executable_outcome"], "FORBIDDEN")
        rows = self.cost_value["synthetic_proofs"]
        unknown = next(row for row in rows if row.get("alternative_interaction") == "UNKNOWN")
        self.assertEqual(unknown["result"], "INDETERMINATE")
        self.assertFalse(unknown["legal_cast_established"])
        conditional = next(row for row in rows if row.get("relevance") == "UNKNOWN")
        self.assertEqual(conditional["result"], "UNSUPPORTED")
        self.assertFalse(conditional["legal_cast_established"])
        for row in rows:
            self.assertFalse(row.get("cost_calculated", False))
            self.assertFalse(row.get("payment_performed", False))

    def test_general_casting_proposal_targets_legality_stack_priority_rollback_are_unsupported(self):
        boundaries = set(self.value["general_casting_boundaries"])
        self.assertTrue({"move_or_propose_spell", "targeting", "legality_check", "stack_semantics", "priority",
            "illegal_action_rollback", "casting_permission_and_prohibition", "completion_of_casting",
            "trigger_consequences"}.issubset(boundaries))
        self.assertEqual(self.value["boundary_support"], "UNSUPPORTED")

    def test_changed_review_input_changes_casting_and_bound_cost_design_identity(self):
        changed = self.build_casting(design_notes=["A revised synthetic branch requires another review."])
        self.assertNotEqual(changed.identity, self.casting.identity)
        changed_cost = self.build_cost(changed)
        self.assertEqual(changed_cost.to_dict()["casting_design_id"], changed.identity)
        self.assertNotEqual(changed_cost.identity, self.cost.identity)
        self.assertEqual(changed, self.build_casting(design_notes=["A revised synthetic branch requires another review."]))


class SyntheticDeclarationDesignTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.casting_design.stages import build_casting_choice_declaration
        from gameplay_rules.casting_design.costs import build_cost_expression_declaration, build_payment_plan
        self.choice = build_casting_choice_declaration
        self.cost = build_cost_expression_declaration
        self.payment = build_payment_plan

    def body(self, record):
        return {key: record.to_dict()[key] for key in record.BODY_FIELDS}

    def test_normal_and_alternative_cost_declarations_have_exclusive_basis(self):
        alternative = self.choice()
        normal = self.choice(base_cost_basis="NORMAL_MANA_COST", selected_alternative_cost_reference=None,
                             alternative_cost_source=None)
        self.assertNotEqual(alternative.identity, normal.identity)
        self.assertEqual(alternative.base_cost_basis, "SELECTED_ALTERNATIVE_COST")
        self.assertEqual(alternative.alternative_cost_source, "madness")
        self.assertIsNone(normal.selected_alternative_cost_reference)
        self.assertFalse(alternative.legal_cast_established)
        with self.assertRaises(GameplayContractError):
            self.choice(base_cost_basis="NORMAL_MANA_COST")
        with self.assertRaises(GameplayContractError):
            self.choice(selected_alternative_cost_reference=None)
        body = self.body(alternative)
        body["mana_cost_discount"] = True
        with self.assertRaises(GameplayContractError):
            type(alternative).create(body)

    def test_unmodeled_mode_splice_variable_hybrid_phyrexian_choices_reject_confident_outcome(self):
        for branch in ("MODES", "SPLICE", "VARIABLE_VALUES", "HYBRID", "PHYREXIAN", "PRIOR_CHOICE_RESTRICTIONS"):
            with self.subTest(branch=branch):
                with self.assertRaises(GameplayContractError):
                    self.choice(relevant_unmodeled_branches=[branch])
                declaration = self.choice(relevant_unmodeled_branches=[branch], declaration_outcome="INDETERMINATE")
                self.assertEqual(declaration.declaration_outcome, "INDETERMINATE")
                self.assertFalse(declaration.legal_cast_established)
                cost = self.cost(declaration)
                with self.assertRaises(GameplayContractError):
                    self.payment(cost)
                self.assertEqual(self.payment(cost, result_state="UNSUPPORTED").result_state, "UNSUPPORTED")

    def test_populated_choice_families_cannot_bypass_fail_closed_branch_declarations(self):
        for field in ("modal_choices", "splice_choices", "variable_values", "hybrid_payment_declarations",
                      "phyrexian_payment_declarations", "prior_casting_choice_restrictions"):
            with self.subTest(field=field):
                args = {field: ["synthetic-branch-declaration"]}
                with self.assertRaises(GameplayContractError):
                    self.choice(**args)
                declaration = self.choice(**args, declaration_outcome="UNSUPPORTED")
                self.assertEqual(declaration.declaration_outcome, "UNSUPPORTED")
                self.assertFalse(declaration.legal_cast_established)

    def test_unknown_or_unsupported_alternative_cost_interaction_fails_closed(self):
        for state in ("UNKNOWN", "UNSUPPORTED"):
            with self.subTest(interaction=state):
                args = {"other_candidate_alternatives": ["synthetic-other-cost"], "alternative_interaction": state}
                with self.assertRaises(GameplayContractError):
                    self.choice(**args)
                declaration = self.choice(**args, declaration_outcome="INDETERMINATE")
                self.assertEqual(declaration.declaration_outcome, "INDETERMINATE")
        with self.assertRaises(GameplayContractError):
            self.choice(other_candidate_alternatives=["synthetic-madness-cost-alpha"])

    def test_only_locked_cost_declarations_can_bind_payment_and_cannot_recompute(self):
        for state in ("UNDETERMINED", "DETERMINED"):
            with self.subTest(state=state):
                declaration = self.cost(state=state)
                self.assertEqual(declaration.state, state)
                with self.assertRaises(GameplayContractError):
                    self.payment(declaration)
        locked = self.cost(state="LOCKED")
        plan = self.payment(locked)
        self.assertEqual(plan.locked_total_cost_identity, locked.identity)
        self.assertFalse(plan.payment_executed)
        self.assertFalse(plan.cost_recomputed)
        with self.assertRaises(GameplayContractError):
            self.payment(locked, locked_total_cost_identity="sha256:" + "f" * 64)
        body = self.body(plan)
        body["cost_recomputed"] = True
        with self.assertRaises(GameplayContractError):
            type(plan).create(body)

    def test_partial_payment_and_unpayable_paid_cost_are_rejected(self):
        locked = self.cost()
        components = [row["synthetic_component_id"] for row in locked.to_dict()["components"]]
        with self.assertRaises(GameplayContractError):
            self.payment(locked, payment_states={components[0]: "PAID", components[1]: "UNPAID"})
        with self.assertRaises(GameplayContractError):
            self.payment(locked, payment_states={key: "PAID" for key in components}, unpayable=True, result_state="UNPAYABLE")
        plan = self.payment(locked, unpayable=True, result_state="UNPAYABLE")
        self.assertTrue(plan.unpayable_cost_condition)
        self.assertEqual(plan.result_state, "UNPAYABLE")
        self.assertFalse(plan.payment_executed)

    def test_payment_inventory_requires_exact_components_and_fail_closed_unknown_states(self):
        locked = self.cost()
        components = [row["synthetic_component_id"] for row in locked.to_dict()["components"]]
        for states in ({components[0]: "UNPAID"}, {**{key: "UNPAID" for key in components}, "synthetic-extra": "UNPAID"}):
            with self.subTest(states=states):
                with self.assertRaises(GameplayContractError):
                    self.payment(locked, payment_states=states)
        unknown = {key: "UNKNOWN" for key in components}
        with self.assertRaises(GameplayContractError):
            self.payment(locked, payment_states=unknown)
        plan = self.payment(locked, payment_states=unknown, result_state="INDETERMINATE")
        self.assertEqual(plan.result_state, "INDETERMINATE")
        self.assertFalse(plan.payment_executed)

    def test_random_and_library_public_zone_components_are_later_and_unsupported(self):
        components = [
            {"synthetic_component_id": "synthetic-ordinary", "cost_type": "MANA", "symbolic_obligation": "synthetic-mana", "payment_order_class": "ORDINARY"},
            {"synthetic_component_id": "synthetic-random", "cost_type": "DISCARDING", "symbolic_obligation": "synthetic-random-item", "payment_order_class": "RANDOM"},
            {"synthetic_component_id": "synthetic-library", "cost_type": "GENERIC_NONMANA", "symbolic_obligation": "synthetic-library-item", "payment_order_class": "LIBRARY_TO_PUBLIC_ZONE"},
        ]
        locked = self.cost(components=components)
        with self.assertRaises(GameplayContractError):
            self.payment(locked)
        plan = self.payment(locked, result_state="UNSUPPORTED")
        groups = plan.to_dict()["ordered_payment_groups"]
        self.assertEqual(groups[0]["component_ids"], ["synthetic-ordinary"])
        self.assertEqual(groups[1]["component_ids"], ["synthetic-random", "synthetic-library"])
        self.assertEqual(plan.random_element_boundary, "PRESENT_UNSUPPORTED")
        self.assertEqual(plan.library_to_public_zone_boundary, "PRESENT_UNSUPPORTED")
        body = self.body(plan)
        body["ordered_payment_groups"].reverse()
        with self.assertRaises(GameplayContractError):
            type(plan).create(body)
        self.assertFalse(plan.gameplay_executed)

    def test_taxonomy_accepts_symbolic_mana_and_nonmana_but_no_real_card_references(self):
        for cost_type in ("MANA", "TAPPING", "SACRIFICING", "DISCARDING", "LIFE", "GENERIC_NONMANA", "UNKNOWN", "UNSUPPORTED"):
            with self.subTest(cost_type=cost_type):
                row = {"synthetic_component_id": "synthetic-component", "cost_type": cost_type,
                       "symbolic_obligation": "synthetic-obligation", "payment_order_class": "ORDINARY"}
                declaration = self.cost(components=[row])
                self.assertFalse(declaration.cost_calculated)
                self.assertFalse(declaration.runtime_lock_performed)
        with self.assertRaises(GameplayContractError):
            self.choice(synthetic_spell_reference="real-card-reference")

    def test_all_paid_declaration_is_metadata_without_execution_or_legality(self):
        locked = self.cost()
        states = {row["synthetic_component_id"]: "PAID" for row in locked.to_dict()["components"]}
        plan = self.payment(locked, payment_states=states)
        self.assertEqual(plan.result_state, "DECLARATION_ONLY")
        self.assertFalse(plan.payment_executed)
        self.assertFalse(plan.gameplay_executed)
        self.assertFalse(plan.real_rules_executable)
        self.assertFalse(plan.real_profile_activated)
        self.assertFalse(plan.execution_authorized)


class ProjectionFrontierDesignTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.casting_design.frontier import build_projection_frontier_design
        self.record = build_projection_frontier_design()
        self.value = self.record.to_dict()

    def test_exact_four_current_casting_frontier_refs_come_from_design_input(self):
        self.assertEqual(tuple(self.value["current_casting_frontier"]), FRONTIER)
        self.assertEqual(self.value["design_input_authority"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
        observations = self.value["observations"]
        self.assertEqual([row["rule_reference"] for row in observations], list(FRONTIER))
        for row in observations:
            self.assertEqual(row["authority"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
            self.assertNotIn("source_anchor", row)
            self.assertNotIn("artifact_identity", row)
            self.assertNotIn("source_text", row)

    def test_candidate_edges_are_unverified_unprojected_and_exactly_pm_observations(self):
        edges = self.value["candidate_direct_references"]
        self.assertEqual([(row["from_reference"], row["to_reference"]) for row in edges], [
            ("601.2b", "700.2"), ("601.2b", "702.47"), ("601.2b", "118.8"),
            ("601.2b", "118.9"), ("601.2b", "601.2f"), ("601.2b", "107.3"),
            ("601.2f", "601.2b"), ("601.2g", "605")])
        for row in edges:
            self.assertEqual(row["status"], "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_PROJECTION")
            self.assertEqual(row["projection_status"], "UNPROJECTED")
            self.assertFalse(row["source_verified"])
            self.assertNotIn("source_anchor", row)
        self.assertEqual(set(self.value["outside_candidate_references"]), CANDIDATES)

    def test_no_new_source_projection_and_all_existing_frontier_blockers_remain(self):
        value = self.value["current_projection"]
        self.assertEqual((value["before"], value["new_real_source_units"], value["after"]), (63, 0, 63))
        self.assertTrue(set(FRONTIER).issubset(value["unprojected_references"]))
        self.assertTrue(CANDIDATES.issubset(value["unprojected_references"]))
        self.assertTrue({"601.2", "613", "603", "603.7d", "603.7e", "603.7f", "114",
            "901.6", "902.6", "904.7", "905.5"}.issubset(value["unprojected_references"]))

    def test_madness_central_conditional_and_incidental_branches_do_not_assume_absence(self):
        value = self.value["madness_minimal_frontier"]
        self.assertEqual(value["central"], ["alternative_cost_selection", "total_cost_determination", "payment"])
        self.assertIn("mana_ability_access", value["conditional"])
        self.assertEqual(value["incidental_but_not_assumed_absent"], ["splice"])
        self.assertEqual(value["relevance_evidence"], "SYNTHETIC_DECLARATIONS_ONLY")
        self.assertEqual(value["unmodeled_relevant_branch_outcomes"], ["INDETERMINATE", "UNSUPPORTED"])
        self.assertEqual(value["confident_executable_outcome"], "FORBIDDEN")

    def test_exactly_one_recommendation_adds_immediate_parent_context_but_no_other_stages(self):
        next_milestone = self.value["next_milestone"]
        self.assertIsInstance(next_milestone, dict)
        self.assertEqual(next_milestone["candidate"], "Bounded Casting Rules Projection")
        self.assertEqual(next_milestone["exact_proposed_source_allowlist"], ["601.2", *FRONTIER])
        self.assertEqual(next_milestone["proposed_source_unit_count"], 5)
        self.assertEqual(set(next_milestone["rationale_by_reference"]), {"601.2", *FRONTIER})
        self.assertTrue(all(next_milestone["rationale_by_reference"].values()))
        self.assertEqual(next_milestone["parent_context_authority"], "DESIGN_HIERARCHY_JUDGMENT_NOT_SOURCE_OBSERVATION")
        self.assertEqual(next_milestone["parent_body_and_direct_reference_frontier"], "UNKNOWN_REQUIRES_SOURCE_VERIFICATION")
        self.assertFalse(next_milestone["unselected_casting_stage_numbered_allowlist_claimed"])
        self.assertFalse(next_milestone["complete_casting_implied"])

    def test_recommendation_is_not_authorized_requires_source_and_preserves_large_frontiers(self):
        value = self.value["next_milestone"]
        self.assertFalse(value["authorized"])
        self.assertTrue(value["source_txt_required"])
        self.assertTrue(value["verified_source_required_before_any_projection"])
        self.assertEqual(value["expected_anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
        self.assertEqual(value["expected_anchor_policy"], "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR")
        self.assertEqual(value["one_line_future_units"], "PERMITTED_AS_BLOCK_WITH_LINE_COUNT_ONE")
        self.assertEqual(set(value["deliberately_unresolved_candidate_references"]), CANDIDATES)
        self.assertEqual(value["scope_insufficiency"], "STOP_FOR_SEPARATE_SCOPE_REVIEW_NEVER_AUTO_EXPAND")
        self.assertIn("mana_abilities_605", value["larger_separate_milestones"])
        self.assertIn("complete_casting_legality_stack_and_permissions", value["larger_separate_milestones"])


class MadnessCastingReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.casting_design.builder import build_design_package
        cls.records = build_design_package(review_root=ROOT / "reference-reviews")
        cls.value = cls.records["madness-readiness.json"].to_dict()

    def test_existing_madness_family_and_400_7k_bind_exact_existing_rule_identities(self):
        binding = self.value["retained_evidence"]
        rules = retained_projection_rules()
        self.assertEqual(binding["madness_rules"], [{"rule_reference": reference, "rule_id": rules[reference]["rule_id"]}
                         for reference in ("702.35a", "702.35b", "702.35c")])
        self.assertEqual(binding["zone_change_lookup"], {"rule_reference": "400.7k", "rule_id": rules["400.7k"]["rule_id"]})
        self.assertEqual(binding["projected_real_source_units"], 63)
        self.assertEqual(set(binding["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(binding["closure_review_id"], "sha256:b8958164e53a1fe4d76888b28e9c164a9615a69bad217bcd18669e808548d2f7")
        self.assertEqual(binding["zone_change_readiness_id"], "sha256:df7f9ad6c4949f7dec55839a4009c639e0ae6d7e377f076d97788dab8fe3aae3")
        self.assertEqual(self.value["binding_policy"], "IMMUTABLE_EXISTING_RULE_IDENTITIES_NO_REPROJECTION")

    def test_conceptual_madness_path_is_not_executable_and_ends_before_later_casting(self):
        self.assertEqual(self.value["conceptual_madness_path"], ["DISCARD_REPLACEMENT_AND_EXILE", "MADNESS_TRIGGER",
            "OWNER_OPTIONAL_CAST_CHOICE", "CANDIDATE_MADNESS_ALTERNATIVE_COST", "CASTING_CHOICES",
            "TOTAL_COST_DETERMINATION", "CONDITIONAL_MANA_ABILITY_WINDOW", "TOTAL_COST_PAYMENT",
            "LATER_CASTING_STAGES_OUTSIDE_DESIGN"])
        self.assertFalse(self.value["conceptual_path_execution"])

    def test_eleven_distinct_madness_subsystems_remain_open_and_unimplemented(self):
        dimensions = self.value["dimensions"]
        self.assertEqual([row["dimension"] for row in dimensions], ["discard_replacement_semantics", "exile_semantics",
            "madness_trigger_semantics", "casting_permission", "alternative_cost_selection", "total_cost_determination",
            "mana_ability_window", "payment", "full_spell_casting_legality", "public_zone_fallback_if_not_cast", "zone_change_lookup"])
        for row in dimensions:
            self.assertEqual(row["dependency_closure"], "OPEN")
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertFalse(row["implementation_available"])
            self.assertFalse(row["execution_supported"])
            self.assertEqual(row["execution_status"], "EXECUTION_BLOCKED")
            self.assertTrue(row["required_unimplemented_primitives"])
        lookup = dimensions[-1]
        self.assertEqual(lookup["supporting_existing_projected_rules"], ["702.35c", "400.7k"])
        self.assertIn("object_history_execution", lookup["required_unimplemented_primitives"])

    def test_madness_subprocedure_and_complete_casting_are_three_independent_blocked_capabilities(self):
        rows = {row["capability_id"]: row for row in self.value["capabilities"]}
        self.assertEqual(set(rows), {"madness", "alternative_cost_casting_subprocedure", "complete_spell_casting"})
        self.assertTrue(all(row["execution_status"] == "EXECUTION_BLOCKED" for row in rows.values()))
        self.assertFalse(rows["alternative_cost_casting_subprocedure"]["complete_casting_implied"])
        self.assertFalse(rows["alternative_cost_casting_subprocedure"]["satisfied_by_fictional_runtime"])
        self.assertFalse(rows["complete_spell_casting"]["satisfied_by_alternative_cost_subprocedure"])
        self.assertEqual(self.value["overall_readiness"], "EXECUTION_BLOCKED")
        self.assertEqual(self.value["real_execution_profile_readiness"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(self.value["real_execution_primitives_available"], [])
        self.assertFalse(self.value["fictional_mana_satisfies_real_605"])
        self.assertEqual(self.value["605_status"], "UNRESOLVED_UNPROJECTED")

    def test_readiness_builder_requires_typed_design_contracts_not_identity_shaped_runtime_objects(self):
        from gameplay_rules.casting_design.readiness import build_madness_readiness
        class IdentityShapedObject:
            identity = "sha256:" + "f" * 64
            def verify(self):
                return self
        arguments = [self.records[name] for name in ("casting-subprocedure-design.json", "cost-design.json",
                     "source-anchor-design.json", "projection-frontier.json")]
        for index in range(4):
            changed = list(arguments)
            changed[index] = IdentityShapedObject()
            with self.subTest(argument=index), self.assertRaises(GameplayContractError):
                build_madness_readiness(self.value["retained_evidence"], *changed)

    def test_source_projection_runtime_activation_card_semantics_and_owner_blockers_are_preserved(self):
        self.assertEqual((self.value["projected_rule_count_before"], self.value["source_projections_added"],
                          self.value["projected_rule_count_after"]), (63, 0, 63))
        self.assertEqual(self.value["blockers"], ["SOURCE_PROJECTION_FRONTIER_OPEN", "COMPLETE_CASTING_SEMANTICS_OPEN",
            "REQUIRED_PRIMITIVES_ABSENT", "REAL_CARD_EFFECT_SEMANTICS_ABSENT", "DETERMINISTIC_RUNTIME_VECTORS_ABSENT",
            "OWNER_ACTIVATION_NOT_GRANTED"])
        self.assertTrue(set(FRONTIER).issubset(self.value["remaining_unprojected_numbered_boundaries"]))
        self.assertTrue(CANDIDATES.issubset(self.value["remaining_unprojected_numbered_boundaries"]))


class MadnessCastingPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.casting_design.builder import build_design_package
        from gameplay_rules.casting_design.package import load_design_package, write_design_package, package_manifest
        cls.build = staticmethod(build_design_package)
        cls.load = staticmethod(load_design_package)
        cls.write = staticmethod(write_design_package)
        cls.manifest = staticmethod(package_manifest)
        cls.review_root = ROOT / "reference-reviews"
        cls.records = cls.load(PACKAGE, review_root=cls.review_root)

    def test_exact_canonical_base_and_all_five_records_are_design_only_without_source_authority(self):
        self.assertEqual(set(self.records), FILES - {"manifest.json"})
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, FILES)
        for record in self.records.values():
            value = record.to_dict()
            self.assertEqual(value["canonical_base"], CANONICAL)
            self.assertEqual(value["release_date"], "2026-09-25")
            self.assertEqual(value["status"], "DESIGN_ONLY")
            self.assertTrue(value["design_only"])
            self.assertTrue(value["non_executable"])
            self.assertEqual(value["new_source_units_projected"], 0)
            for name in ("execution_authorized", "projection_authorized", "source_verification_claimed", "source_body_retained",
                         "real_rules_executable", "oracle_ingested", "real_snapshot_created", "real_profile_activated"):
                self.assertFalse(value[name])

    def test_source_policy_and_all_permission_states_are_unchanged(self):
        for record in self.records.values():
            value = record.to_dict()
            self.assertEqual(value["source_policy_clearance"], "not_granted")
            self.assertEqual(value["owner_execution_approval"], "NOT_GRANTED")
            self.assertEqual(value["permissions"], {name: "NOT_ESTABLISHED" for name in
                ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})

    def test_five_record_identities_roundtrip_deterministically_and_are_deeply_immutable(self):
        self.assertEqual(len({record.identity for record in self.records.values()}), 5)
        for record in self.records.values():
            with self.subTest(record=type(record).__name__):
                self.assertEqual(type(record).from_json(record.serialize()), record)
                self.assertEqual(type(record).create({key: record.to_dict()[key] for key in record.BODY_FIELDS}), record)
                self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
                self.assertEqual(record.verify(), record)
                self.assertRegex(record.identity, r"^sha256:[0-9a-f]{64}$")
                with self.assertRaises(FrozenInstanceError):
                    record._payload = {}
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    record.execution_authorized = True
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    record.status = "EXECUTABLE"
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    record.unreviewed_attribute = True
                with self.assertRaises(TypeError):
                    record._payload["execution_authorized"] = True
                with self.assertRaises(TypeError):
                    record._payload["permissions"]["ai_export"] = "GRANTED"
                detached = record.to_dict()
                detached["permissions"]["ai_export"] = "GRANTED"
                self.assertEqual(record.to_dict()["permissions"]["ai_export"], "NOT_ESTABLISHED")

    def test_record_tampered_identity_flags_schema_duplicate_json_and_nonfinite_values_rejected(self):
        record = self.records["casting-subprocedure-design.json"]
        for field, value in ((record.ID_FIELD, "sha256:" + "f" * 64), ("schema_version", "other-schema"),
            ("execution_authorized", True), ("source_verification_claimed", True), ("new_source_units_projected", 1),
            ("real_profile_activated", True), ("source_policy_clearance", "granted")):
            with self.subTest(field=field):
                body = record.to_dict()
                body[field] = value
                with self.assertRaises(GameplayContractError):
                    type(record).from_dict(body)
        duplicate = record.serialize()[:-1] + ',"status":"DESIGN_ONLY"}'
        with self.assertRaises(GameplayContractError):
            type(record).from_json(duplicate)
        with self.assertRaises(GameplayContractError):
            type(record).from_json(record.serialize()[:-1] + ',"bad":NaN}')
        body = {key: record.to_dict()[key] for key in record.BODY_FIELDS}
        body["source_anchor"] = {"rule_reference": "601.2b"}
        with self.assertRaises(GameplayContractError):
            type(record).create(body)

    def test_offline_rebuild_needs_no_external_txt_network_or_source_parser(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")))
            for module in ("source", "dependency_source", "object_control_source", "zone_change_source", "zone_change_dependency_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + "._verified_bytes",
                                          side_effect=AssertionError("external source access forbidden")))
            rebuilt = self.build(review_root=self.review_root)
            loaded = self.load(PACKAGE, review_root=self.review_root)
        self.assertEqual(rebuilt, self.records)
        self.assertEqual(loaded, self.records)

    def test_design_records_cannot_be_loaded_as_real_gameplay_snapshots(self):
        from gameplay_rules.models import GameplayRulesSnapshot
        from gameplay_rules.snapshots import load_rules_snapshot
        for name, record in self.records.items():
            with self.subTest(record=name):
                with self.assertRaises(GameplayContractError):
                    GameplayRulesSnapshot.from_dict(record.to_dict())
                with self.assertRaises(GameplayContractError):
                    load_rules_snapshot(PACKAGE / name)
                self.assertFalse(hasattr(record, "to_rules_snapshot"))
                self.assertFalse(hasattr(record, "to_execution_profile"))

    def test_manifest_preserves_63_rule_coverage_and_six_package_identities(self):
        value = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(value["canonical_base"], CANONICAL)
        self.assertEqual((value["projected_rule_count_before"], value["new_source_units_projected"], value["projected_rule_count_after"]), (63, 0, 63))
        self.assertEqual(value["additional_rules_projected"], [])
        self.assertFalse(value["source_artifact_required"])
        self.assertFalse(value["source_anchors_created"])
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL)
        self.assertEqual(set(value["retained_evidence_binding"]["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(value["record_ids"], {record.ID_FIELD: record.identity for record in self.records.values()})
        self.assertEqual(value, self.manifest(self.records, {name: (record.serialize() + "\n").encode()
                                                            for name, record in self.records.items()}))

    def test_package_contains_no_txt_source_prose_actual_source_anchors_or_external_paths(self):
        forbidden = {"source_anchor", "source_text", "official_text", "oracle_text", "raw_source", "source_excerpt", "examples"}
        def check(value):
            if isinstance(value, dict):
                self.assertTrue(forbidden.isdisjoint(value))
                for item in value.values():
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)
            elif isinstance(value, str):
                self.assertNotIn("/workspace/", value)
                self.assertNotIn("/tmp/", value)
                self.assertNotIn("file://", value)
                self.assertNotIn("sediment://", value)
        for path in PACKAGE.iterdir():
            self.assertEqual(path.suffix, ".json")
            check(json.loads(path.read_bytes()))
        self.assertFalse((PACKAGE / "projection.json").exists())

    def test_modified_missing_or_extra_source_and_txt_package_files_are_rejected(self):
        for mutation in ("tamper", "missing", "txt", "source", "directory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                if mutation == "tamper":
                    path = root / "cost-design.json"
                    path.write_bytes(path.read_bytes().replace(b'"LOCKED"', b'"CHANGED"', 1))
                elif mutation == "missing":
                    (root / "cost-design.json").unlink()
                elif mutation == "directory":
                    (root / "unexpected").mkdir()
                else:
                    (root / ("source.txt" if mutation == "txt" else "source.json")).write_text("synthetic extra data")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=self.review_root)

    def test_symlink_hardlink_or_symlink_ancestor_package_is_rejected(self):
        for link in ("symlink", "hardlink", "root-symlink"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                if link == "root-symlink":
                    alias = Path(tmp) / "alias"
                    alias.symlink_to(root, target_is_directory=True)
                    root = alias
                else:
                    path = root / "cost-design.json"
                    held = Path(tmp) / "held.json"
                    path.rename(held)
                    if link == "symlink":
                        path.symlink_to(held)
                    else:
                        os.link(held, path)
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=self.review_root)

    def test_noncanonical_record_or_manifest_bytes_are_rejected(self):
        for name in ("cost-design.json", "manifest.json"):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / name
                path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2) + "\n")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=self.review_root)

    def test_reidentified_and_rehashed_findings_cannot_replace_reviewed_reproduction(self):
        records = dict(self.records)
        changed = records["projection-frontier.json"]
        body = {key: changed.to_dict()[key] for key in changed.BODY_FIELDS}
        body["design_notes"] = ["A changed synthetic review conclusion needs another retained review."]
        changed = type(changed).create(body)
        records["projection-frontier.json"] = changed
        readiness = records["madness-readiness.json"]
        body = {key: readiness.to_dict()[key] for key in readiness.BODY_FIELDS}
        body["projection_frontier_id"] = changed.identity
        records["madness-readiness.json"] = type(readiness).create(body)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "changed"
            self.write(root, records)
            with self.assertRaises(GameplayContractError):
                self.load(root, review_root=self.review_root)

    def test_relocation_rebuild_and_append_only_writing_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "relocated-reviews"
            shutil.copytree(self.review_root, reviews)
            records = self.build(review_root=reviews)
            self.assertEqual(records, self.records)
            root = Path(tmp) / "fresh-package"
            manifest = self.write(root, records)
            self.assertEqual(self.load(root, review_root=reviews), records)
            for name in FILES:
                self.assertEqual((root / name).read_bytes(), (PACKAGE / name).read_bytes())
            self.assertEqual(manifest["package_id"], json.loads((PACKAGE / "manifest.json").read_bytes())["package_id"])
            with self.assertRaises(GameplayContractError):
                self.write(root, records)


if __name__ == "__main__":
    unittest.main()
