"""Offline proofs for five bounded, non-executable casting source units.

Synthetic locator material is project-authored. Official bytes are supplied
only by an optional owner-controlled test, never retained as a test fixture.
Preservation digests bind all source and review files at canonical main
eacfe1ebd641966681797bd4647daa254900d178 independently of Git availability.
"""
import ast
from contextlib import ExitStack
from dataclasses import FrozenInstanceError
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from activated_ability_preservation import is_design_addition
from query_attachment_performance_preservation import historical_inventory_row
from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.errors import GameplayContractError


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / "gameplay-rules-bounded-casting-projection"
CODE = ROOT / "src/gameplay_rules/projection"
CANONICAL = "eacfe1ebd641966681797bd4647daa254900d178"
EXPECTED = ("601.2", "601.2b", "601.2f", "601.2g", "601.2h")
SIBLINGS = ("601.2a", "601.2c", "601.2d", "601.2e", "601.2i")
FRONTIER = {"601.3", "733", "700.2", "702.47", "118.8", "118.9", "107.3", "605"}
OLD_BLOCKERS = {"613", "603", "603.7d", "603.7e", "603.7f", "114", "901.6", "902.6", "904.7", "905.5"}
ARTIFACT = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
POLICY = "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR"
HISTORICAL = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER = "sha256:" + "f" * 64
EXTERNAL_ARTIFACT = os.environ.get("MTGLAB_BOUNDED_CASTING_ARTIFACT")
FILES = {"projection.json", "design-source-correspondence.json", "casting-stage-matrix.json",
         "madness-readiness-reassessment.json", "casting-readiness-reassessment.json",
         "composite-coverage.json", "manifest.json"}
SOURCE_ROOTS = {
    "artifact_review_root": REVIEWS / "gameplay-rules-artifact-verification",
    "source_root": REVIEWS / "gameplay-rules-source-versioning",
    "discovery_root": REVIEWS / "gameplay-rules-release-discovery-closure",
}
PRIOR_PACKAGES = {
    "gameplay-rules-foundational-projection": "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea",
    "gameplay-rules-execution-profile-design": "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687",
    "gameplay-rules-foundational-dependencies": "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a",
    "gameplay-rules-object-control-exceptions": "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab",
    "gameplay-rules-zone-change-exceptions": "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875",
    "gameplay-rules-zone-change-direct-dependencies": "sha256:d51fab1425f6aa9b82e4621ac8c88d4b83d736c6906a4f4c589c41ff1aeadba4",
    "gameplay-rules-madness-casting-design": "sha256:06cd012d08d204f10337d834f312bcf19b060a3569ef3cf879c46714d30944c8",
}
EXPLICIT = {
    "601.2": ("601.2a", "601.2b", "601.2c", "601.2d", "601.2f", "601.2g", "601.2h", "601.3", "733"),
    "601.2b": ("700.2", "702.47", "118.8", "118.9", "601.2f", "107.3"),
    "601.2f": ("601.2b",), "601.2g": ("605",), "601.2h": (),
}


def inventory(paths):
    result = []
    for path in sorted(set(paths)):
        if path.is_symlink():
            raise AssertionError("Protected file must be a regular file")
        raw = path.read_bytes()
        result.append(historical_inventory_row({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()}, ROOT))
    return result


def regular_files(root):
    # Later append-only milestones are outside this historical inventory.
    # The successor preservation guard pins their exact four-file namespaces.
    return [p for p in _historical_regular_files(root) if not is_design_addition(p)
            and not (p.parent == ROOT / "src/gameplay_rules/projection" and p.name.startswith("mana_classification_"))
            and "gameplay-rules-bounded-mana-classification-projection" not in p.parts
            and not (p.parent == ROOT / "src/gameplay_rules/projection" and p.name in {
                "mana_stack_exception_source.py", "mana_stack_exception_pins.py",
                "mana_stack_exception_reports.py", "mana_stack_exception_package.py"})
            and "gameplay-rules-bounded-mana-stack-exception-projection" not in p.parts]


def _historical_regular_files(root):
    return [path for path in root.rglob("*") if path.is_file()
            and "__pycache__" not in path.parts and path.suffix != ".pyc"]


def body(record):
    return {key: value for key, value in record.to_dict().items()
            if key not in {"schema_version", record.ID_FIELD}}


def prior_rules():
    result = {}
    for package in PRIOR_PACKAGES:
        path = REVIEWS / package / "projection.json"
        if path.is_file():
            for rule in json.loads(path.read_bytes())["rules"]:
                if rule["rule_reference"] in result:
                    raise AssertionError("Retained projections must remain separate and disjoint")
                result[rule["rule_reference"]] = rule
    return result


class BoundedCastingPreservationTests(unittest.TestCase):
    def test_292_historical_source_rows_and_current_successors_match_exact_pins(self):
        paths = [path for path in regular_files(ROOT / "src")
                 if not (path.parent == CODE and path.name.startswith(("bounded_casting", "bounded_mana")))
                 and "mana_ability_design" not in path.parts
                 and "mana_dependency_design" not in path.parts]
        values = inventory(paths)
        self.assertEqual(len(values), 292)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "ed132d7edd573efb2abee47729da8fce7d987ea2553def83bbaf8a2de7fa014b")

    def test_all_162_prior_evidence_files_and_seven_packages_remain_byte_identical(self):
        values = inventory(path for path in regular_files(REVIEWS) if PACKAGE not in path.parents
                           and "gameplay-rules-mana-ability-design" not in path.parts
                           and "gameplay-rules-bounded-mana-ability-projection" not in path.parts
                           and "gameplay-rules-mana-direct-dependency-design" not in path.parts)
        self.assertEqual(len(values), 162)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "e11dae638659061a4496a236c0f0d0b0b82b90383171f1073d8542562e4362b4")
        for name, identity in PRIOR_PACKAGES.items():
            with self.subTest(package=name):
                self.assertEqual(json.loads((REVIEWS / name / "manifest.json").read_bytes())["package_id"], identity)

    def test_historical_single_line_anchors_and_madness_lookup_identities_preserved(self):
        rules = prior_rules()
        self.assertEqual(len(rules), 63)
        self.assertTrue(set(EXPECTED).isdisjoint(rules))
        for rule in rules.values():
            self.assertEqual(rule["source_anchor"]["span_policy"], "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")
        for ref, identity in {
            "702.35a": "sha256:48da52c60c006aaae9a752b23155581474244b4a7b3a050b588fb2f51c1b6534",
            "702.35b": "sha256:884e5ecb63b242196785a1d38f8a3014896342a6d4b738e6005430c1ac22d5ae",
            "702.35c": "sha256:79b507ab353539b0d1166876f25c279a2171f860f69ab40b53cc2d942f198fb4",
            "400.7k": "sha256:5fd728b81834e50cc3555e61fd9cf9f9cb6e3cce172618d23cfcd0649efe21c5",
        }.items():
            self.assertEqual(rules[ref]["rule_id"], identity)

    def test_architecture_v13_and_decision_017_remain_byte_identical(self):
        values = inventory(ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md"))
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")

    def test_historical_acquisition_identity_and_protected_fixture_bytes_unchanged(self):
        root = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((root / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL)
        for name, expected in manifest["files"].items():
            raw = (root / name).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, expected)

    def test_fictional_profile_and_simulation_unchanged(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_new_projection_layer_has_no_network_card_ingestion_runtime_or_general_parser(self):
        imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation", "random", "secrets",
                   "providers", "external_ingestion", "production_evidence", "market"}
        runtime = {"GameplayRulesEngine", "GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                   "LegalityResult", "GameTransition", "RawSnapshotStore"}
        functions = {"cast_spell", "pay_cost", "pay_mana", "calculate_total_cost", "execute_madness", "move_object",
                     "activate_mana_ability", "rollback", "to_rules_snapshot", "to_execution_profile", "activate_profile",
                     "parse_comprehensive_rules", "build_rule_inventory", "parse_rule_tree"}
        files = list(CODE.glob("bounded_casting*.py"))
        self.assertGreaterEqual(len(files), 5)
        for path in files:
            for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
                with self.subTest(file=path.name, kind=type(node).__name__):
                    if isinstance(node, ast.Import):
                        self.assertTrue(imports.isdisjoint(alias.name.split(".")[0] for alias in node.names))
                    elif isinstance(node, ast.ImportFrom):
                        self.assertNotIn((node.module or "").split(".")[0], imports)
                        self.assertTrue(runtime.isdisjoint(alias.name for alias in node.names))
                    elif isinstance(node, ast.Name):
                        self.assertNotIn(node.id, runtime)
                    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertNotIn(node.name, functions)


class BoundedCastingSourceTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.projection.bounded_casting_source import locate_bounded_casting_anchors
        self.locate = locate_bounded_casting_anchors

    def fixture(self, ending=b"\n"):
        lines = ["Authored locator header ☃".encode(), b"601.2. Authored parent sentinel.",
                 b"  Authored parent continuation.", "\u00a0".encode(), b"601.2a Authored omitted stage.",
                 b"601.2b Authored choices sentinel.", b"  Authored choices continuation.", "\u00a0".encode(),
                 b"601.2c Authored omitted stage.", b"601.2f Authored cost sentinel.",
                 b"  Authored cost continuation.", "\u00a0".encode(), b"601.2g Authored window sentinel.",
                 "\u00a0".encode(), b"601.2h Authored payment sentinel.",
                 b"Example: Authored ownership sentinel.", "\u00a0".encode(), b"601.2i Authored omitted stage."]
        return ending.join(lines) + ending

    def test_only_five_markers_and_complete_raw_blocks_are_located_deterministically(self):
        data = self.fixture(b"\r\n")
        first = self.locate(data)
        self.assertEqual(first, self.locate(data))
        self.assertEqual(tuple(anchor["rule_reference"] for anchor in first), EXPECTED)
        self.assertEqual([anchor["line_count"] for anchor in first], [2, 2, 2, 1, 2])
        for anchor in first:
            span = data[anchor["byte_start"]:anchor["byte_end"]]
            self.assertEqual(anchor["anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
            self.assertEqual(anchor["span_policy"], POLICY)
            self.assertEqual(anchor["artifact_hash"], "sha256:" + hashlib.sha256(data).hexdigest())
            self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(span).hexdigest())
            self.assertEqual(anchor["ending_physical_line"] - anchor["starting_physical_line"] + 1,
                             anchor["line_count"])
            self.assertFalse(span.endswith((b"\r", b"\n")))
            self.assertNotIn("Authored", json.dumps(anchor))
        self.assertEqual(first[0]["starting_physical_line"], 2)
        self.assertEqual(first[0]["byte_start"], len("Authored locator header ☃\r\n".encode()))

    def test_internal_line_terminator_is_hashed_and_final_terminator_excluded(self):
        original = self.fixture(b"\r\n")
        first = self.locate(original)
        changed_internal = original.replace(b"parent sentinel.\r\n", b"parent sentinel.\n")
        changed_final = original.replace(b"parent continuation.\r\n", b"parent continuation.\n")
        self.assertNotEqual(first[0]["span_sha256"], self.locate(changed_internal)[0]["span_sha256"])
        self.assertEqual(first[0]["span_sha256"], self.locate(changed_final)[0]["span_sha256"])
        self.assertNotEqual(first[0]["artifact_hash"], self.locate(changed_final)[0]["artifact_hash"])

    def test_selected_h_example_belongs_to_h_and_following_i_body_does_not(self):
        data = self.fixture()
        anchors = self.locate(data)
        h = anchors[-1]
        span = data[h["byte_start"]:h["byte_end"]]
        self.assertIn(b"Authored ownership sentinel.", span)
        self.assertNotIn(b"601.2i", span)
        self.assertEqual(h["line_count"], 2)

    def test_each_missing_duplicate_or_prefix_substituted_selected_start_is_rejected(self):
        for reference in EXPECTED:
            marker = (reference + (". " if reference == "601.2" else " ")).encode()
            for mutation in ("missing", "duplicate", "prefix"):
                data = self.fixture()
                line = next(line for line in data.splitlines() if line.startswith(marker))
                if mutation == "missing":
                    data = data.replace(line + b"\n", b"", 1)
                elif mutation == "duplicate":
                    data += line + b"\n"
                else:
                    data = data.replace(marker, reference.encode() + b"z ", 1)
                with self.subTest(reference=reference, mutation=mutation), self.assertRaises(GameplayContractError):
                    self.locate(data)

    def test_ambiguous_continuation_numbering_and_termination_are_rejected(self):
        base = self.fixture()
        changes = {
            "unindented-continuation": (b"  Authored parent continuation.", b"Authored unexplained continuation."),
            "malformed-number": (b"601.2b Authored", b"601.2bb Authored"),
            "wrong-next-unit": (b"601.2c Authored", b"601.2d Authored"),
            "missing-termination": (b"601.2i Authored omitted stage.\n", b""),
            "numbered-indented-continuation": (b"  Authored parent continuation.", b"  601.2c Authored hidden boundary."),
        }
        for kind, (old, new) in changes.items():
            with self.subTest(kind=kind), self.assertRaises(GameplayContractError):
                self.locate(base.replace(old, new, 1))

    def test_example_after_separator_or_multiple_examples_fails_closed(self):
        base = self.fixture()
        example = b"Example: Authored ownership sentinel."
        for data in (base.replace(example, "\u00a0".encode() + b"\n" + example, 1),
                     base.replace(example, example + b"\nExample: Authored second illustration.", 1)):
            with self.assertRaises(GameplayContractError) as caught:
                self.locate(data)
            self.assertIn("AMBIGUOUS_EXAMPLE_OWNERSHIP", str(caught.exception))

    def test_overlapping_selected_spans_rejected_independently(self):
        from gameplay_rules.projection.bounded_casting_source import validate_bounded_casting_spans
        anchors = self.locate(self.fixture())
        anchors[1]["byte_start"] = anchors[0]["byte_start"]
        with self.assertRaises(GameplayContractError):
            validate_bounded_casting_spans(anchors)

    def test_wrong_artifact_bytes_rejected_before_structural_projection(self):
        from gameplay_rules.projection.bounded_casting_source import verify_bounded_casting_bytes
        for value in (self.fixture(), b"x" * 977752, b"", "not bytes", None):
            with self.subTest(kind=type(value).__name__), self.assertRaises(GameplayContractError):
                verify_bounded_casting_bytes(value)

    def test_missing_wrong_sha_and_linked_source_artifacts_fail_without_network_or_retention(self):
        from gameplay_rules.projection.bounded_casting_source import build_bounded_casting_projection
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "authored-wrong.txt"
            wrong.write_bytes(b"x" * 977752)
            linked = root / "linked.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing.txt", wrong, linked):
                with self.subTest(kind=path.name), patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                     patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")), \
                     self.assertRaises(GameplayContractError) as caught:
                    build_bounded_casting_projection(path, **SOURCE_ROOTS)
                self.assertNotIn(str(root), str(caught.exception))
                if path.name == "missing.txt":
                    self.assertIn("MISSING_VERIFIED_SOURCE_ARTIFACT", str(caught.exception))


class BoundedCastingProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_casting_contracts import BoundedCastingProjection
        cls.projection = BoundedCastingProjection.from_json((PACKAGE / "projection.json").read_bytes())
        cls.value = cls.projection.to_dict()
        cls.rules = {rule["rule_reference"]: rule for rule in cls.value["rules"]}

    def test_canonical_base_exact_allowlist_no_sixth_unit_and_68_total(self):
        from gameplay_rules.projection.bounded_casting_scope import SELECTED_REFERENCES
        self.assertEqual(self.value["canonical_base"], CANONICAL)
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED)
        self.assertEqual(tuple(self.rules), EXPECTED)
        self.assertEqual(self.value["selected_rule_count"], 5)
        self.assertEqual(self.value["new_source_units_projected"], 5)
        self.assertEqual(self.value["total_projected_rule_count"], 68)
        self.assertTrue((set(SIBLINGS) | FRONTIER | OLD_BLOCKERS).isdisjoint(self.rules))
        self.assertEqual(self.value["milestone_status"], "BOUNDED_CASTING_RULES_PROJECTED")
        self.assertEqual(self.value["projection_kind"], "NON_EXECUTABLE")

    def test_each_rule_retains_authored_semantics_unique_identity_and_exact_direct_references(self):
        self.assertEqual(len({rule["rule_id"] for rule in self.rules.values()}), 5)
        for reference, rule in self.rules.items():
            with self.subTest(reference=reference):
                for key in ("topic", "paraphrase", "semantic_category", "concept_tags", "limitations",
                            "subsystem_boundaries", "required_future_semantic_primitives", "sibling_stage_relationships"):
                    self.assertTrue(rule[key], key)
                self.assertEqual(tuple(rule["direct_dependency_references"]), EXPLICIT[reference])
                self.assertEqual(rule["coverage_state"], "BOUNDED_CASTING_SOURCE_PROJECTED")
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")
                self.assertEqual(rule["semantic_closure_state"], "OPEN")
                self.assertEqual(rule["execution_readiness"], "BLOCKED")
                self.assertFalse(rule["execution_ready"])
                self.assertTrue(rule["semantic_distinctions"]["descriptive_only"])
                self.assertEqual(rule["semantic_distinctions"]["runtime_operations_implemented"], [])
                self.assertFalse(rule["semantic_distinctions"]["complete_casting_procedure_represented"])
                self.assertRegex(rule["rule_id"], r"^sha256:[0-9a-f]{64}$")

    def test_exact_artifact_lineage_and_full_anchor_schema_for_all_five_units(self):
        binding = self.value["source_binding"]
        self.assertEqual(binding["artifact_hash"], ARTIFACT)
        self.assertEqual(binding["byte_length"], 977752)
        self.assertEqual(binding["effective_date"], "2026-09-25")
        self.assertEqual(binding["verification_result_id"],
                         "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3")
        self.assertEqual(binding["correspondence_review_id"],
                         "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def")
        previous_end = 0
        for reference, (start, end) in zip(EXPECTED, ((2461, 2461), (2465, 2465), (2474, 2474),
                                                               (2476, 2476), (2478, 2479))):
            anchor = self.rules[reference]["source_anchor"]
            with self.subTest(reference=reference):
                self.assertEqual(set(anchor), {"rule_reference", "artifact_hash", "effective_date", "anchor_type",
                    "starting_physical_line", "ending_physical_line", "line_count", "byte_start", "byte_end",
                    "span_sha256", "span_policy"})
                self.assertEqual(anchor["rule_reference"], reference)
                self.assertEqual(anchor["artifact_hash"], ARTIFACT)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertEqual(anchor["anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
                self.assertEqual(anchor["span_policy"], POLICY)
                self.assertEqual((anchor["starting_physical_line"], anchor["ending_physical_line"]), (start, end))
                self.assertEqual(anchor["line_count"], end - start + 1)
                self.assertGreater(anchor["byte_start"], previous_end)
                self.assertGreater(anchor["byte_end"], anchor["byte_start"])
                self.assertLessEqual(anchor["byte_end"], 977752)
                self.assertRegex(anchor["span_sha256"], r"^sha256:[0-9a-f]{64}$")
            previous_end = anchor["byte_end"]

    def test_projection_rejects_reidentified_extra_missing_duplicate_or_unselected_units(self):
        from gameplay_rules.projection.bounded_casting_contracts import BoundedCastingProjection
        for mutation in ("count", "extra", "missing", "duplicate", *SIBLINGS, *sorted(FRONTIER)):
            value = body(self.projection)
            if mutation == "count":
                value["selected_rule_count"] = 6
            elif mutation == "extra":
                value["rules"].append(value["rules"][-1])
            elif mutation == "missing":
                value["rules"].pop()
            elif mutation == "duplicate":
                value["rules"][1] = value["rules"][0]
            else:
                value["rules"][0]["rule_reference"] = mutation
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                BoundedCastingProjection.create(value)

    def test_pinned_source_spans_cannot_be_forged_or_reidentified_offline(self):
        from gameplay_rules.projection.bounded_casting_contracts import BoundedCastingProjection
        for field, value in (("artifact_hash", OTHER), ("span_sha256", OTHER), ("byte_start", 0),
                             ("line_count", 99), ("anchor_type", "SINGLE_LINE_RULE_ANCHOR"),
                             ("span_policy", "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")):
            changed = body(self.projection)
            changed["rules"][0]["source_anchor"][field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                BoundedCastingProjection.create(changed)

    def test_parent_ordered_procedure_does_not_satisfy_sibling_stages_or_rollback(self):
        value = self.rules["601.2"]["semantic_distinctions"]
        self.assertEqual(value["movement_description"], {"origin": "previous_location", "destination": "stack",
                                                          "subject_kinds": ["spell", "card", "copy"]})
        self.assertTrue(value["cost_payment_required"])
        self.assertTrue(value["legal_permission_to_begin_required"])
        self.assertEqual(value["required_step_failure"], "ROLLBACK_BOUNDARY")
        self.assertEqual(value["selected_stage_references"], list(EXPECTED[1:]))
        self.assertEqual(value["unprojected_stage_references"], list(SIBLINGS))
        self.assertEqual(value["legality_stage_boundary"], "601.2e")
        self.assertEqual(value["structural_siblings_without_parent_direct_citation"], ["601.2e", "601.2i"])
        self.assertFalse(value["parent_projection_satisfies_unselected_stages"])
        self.assertFalse(value["five_units_establish_complete_casting"])
        unresolved = {row["reference"] for row in self.rules["601.2"]["unresolved_dependencies"]}
        self.assertEqual(unresolved, {"601.2a", "601.2c", "601.2d", "601.3", "733"})

    def test_choice_declarations_cover_mode_splice_variable_hybrid_phyrexian_and_constraints(self):
        value = self.rules["601.2b"]["semantic_distinctions"]
        self.assertEqual(value["mode_choice"], "DESCRIPTIVE_ONLY")
        self.assertEqual(value["splice_declaration"], "DESCRIPTIVE_ONLY")
        self.assertEqual(value["splice_cards_revealed_from"], "HAND")
        self.assertFalse(value["splice_reveal_implemented"])
        self.assertEqual(value["alternative_cost_declaration"], "DESCRIPTIVE_ONLY")
        self.assertEqual(value["additional_cost_declaration"], "DESCRIPTIVE_ONLY")
        self.assertEqual(value["variable_values"], "DECLARED_WITH_REQUIRED_DEPENDENT_CHOICES")
        self.assertEqual(value["normally_later_choice_needed_for_variable"], "BRING_CHOICE_FORWARD_TO_THIS_STAGE")
        self.assertTrue(value["hybrid_choice"])
        self.assertTrue(value["phyrexian_choice"])
        self.assertTrue(value["prior_choices_may_restrict_current_choices"])
        self.assertEqual(value["later_total_cost_stage"], "601.2f")

    def test_alternative_base_cost_is_not_a_discount_or_unrestricted_stacking(self):
        choices = self.rules["601.2b"]["semantic_distinctions"]
        total = self.rules["601.2f"]["semantic_distinctions"]
        for value in (choices, total):
            self.assertEqual(value["base_cost_basis"], ["NORMAL_MANA_COST", "SELECTED_ALTERNATIVE_COST"])
            self.assertFalse(value["madness_cost_as_mana_cost_discount"])
        self.assertTrue(choices["alternative_cost_replaces_normal_mana_cost_basis"])
        self.assertFalse(choices["multiple_alternative_casting_methods_per_spell"])
        self.assertFalse(choices["multiple_alternative_costs_per_spell"])
        self.assertFalse(choices["alternative_interactions_fully_resolved"])
        self.assertEqual(total["selected_base_count"], 1)

    def test_choice_and_total_cost_stages_bind_each_other_without_recursive_projection(self):
        self.assertIn("601.2f", self.rules["601.2b"]["direct_dependency_references"])
        self.assertEqual(self.rules["601.2f"]["direct_dependency_references"], ["601.2b"])
        for source, target in (("601.2b", "601.2f"), ("601.2f", "601.2b")):
            rows = [row for row in self.rules[source]["dependencies"] if row["reference"] == target]
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "PROJECTED_IN_THIS_MILESTONE")
        unresolved = {row["reference"] for row in self.rules["601.2b"]["unresolved_dependencies"]}
        self.assertEqual(unresolved, {"700.2", "702.47", "118.8", "118.9", "107.3"})

    def test_cost_components_order_zero_floor_direct_modifiers_and_lock_are_descriptive(self):
        value = self.rules["601.2f"]["semantic_distinctions"]
        self.assertEqual(value["ordinary_components"],
                         ["selected_base", "all_additional_costs", "cost_increases", "cost_reductions"])
        self.assertTrue(value["reduction_order_may_matter"])
        self.assertEqual(value["reduction_application_order"], "PLAYER_CHOOSES_ANY_ORDER")
        self.assertEqual(value["mana_portion_lower_bound"], 0)
        self.assertTrue(value["direct_total_cost_modifiers_after_ordinary_components"])
        self.assertEqual(value["cost_lock"], "FINAL_TOTAL_LOCKED_AFTER_DETERMINATION")
        self.assertFalse(value["later_changes_alter_locked_total"])
        self.assertFalse(value["cost_calculation_implemented"])

    def test_mana_window_requires_mana_payment_and_real_605_remains_unresolved(self):
        rule = self.rules["601.2g"]
        value = rule["semantic_distinctions"]
        self.assertEqual(value["condition"], "DETERMINED_TOTAL_COST_CONTAINS_MANA_PAYMENT")
        self.assertTrue(value["opportunity_before_cost_payment"])
        self.assertEqual(value["mana_ability_dependency"], "605")
        self.assertFalse(value["real_605_satisfied_by_fictional_mana"])
        self.assertFalse(value["mana_ability_execution_implemented"])
        self.assertEqual(rule["unresolved_dependencies"][0]["reference"], "605")
        self.assertEqual(rule["unresolved_dependencies"][0]["coverage_state"], "UNPROJECTED")

    def test_payment_groups_preserve_ordinary_then_random_or_library_public_order(self):
        value = self.rules["601.2h"]["semantic_distinctions"]
        first, later = value["payment_groups"]
        self.assertEqual((first["order"], later["order"]), (1, 2))
        self.assertEqual(first["name"], "ORDINARY")
        self.assertEqual(first["excludes"], ["random_element", "library_to_public_zone_movement"])
        self.assertEqual(later["includes"], first["excludes"])
        self.assertEqual((first["component_order"], later["component_order"]), ("ANY_ORDER", "ANY_ORDER"))
        self.assertFalse(value["partial_payment_allowed"])
        self.assertFalse(value["unpayable_cost_may_be_paid"])
        self.assertFalse(value["payment_execution_implemented"])
        self.assertFalse(value["example_content_retained"])
        self.assertEqual(self.rules["601.2h"]["direct_dependency_references"], [])

    def test_sibling_stage_matrix_keeps_legality_stage_and_other_unselected_stages_open(self):
        from gameplay_rules.projection.bounded_casting_scope import SIBLING_STAGE_MATRIX
        rows = {row["reference"]: dict(row) for row in SIBLING_STAGE_MATRIX}
        self.assertEqual(list(rows), ["601.2", *("601.2" + suffix for suffix in "abcdefghi")])
        self.assertEqual(rows["601.2"]["status"], "PARENT_CONTEXT_PROJECTED")
        self.assertFalse(rows["601.2"]["satisfies_unprojected_stages"])
        for reference in EXPECTED[1:]:
            self.assertEqual(rows[reference]["status"], "SELECTED_AND_PROJECTED")
        for reference in SIBLINGS:
            self.assertEqual(rows[reference]["status"], "UNPROJECTED_CASTING_STAGE")
            self.assertEqual(rows[reference]["execution_relevance"], "UNKNOWN_OR_INCOMPLETE")
            self.assertFalse(rows[reference]["satisfied_by_parent_projection"])
            self.assertFalse(rows[reference]["execution_ready"])
        self.assertFalse(rows["601.2e"]["parent_explicitly_cites_stage"])


class BoundedCastingPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_casting_package import (
            build_bounded_casting_package, load_bounded_casting_package, write_bounded_casting_package,
            package_manifest, rebuild_bounded_casting_package,
        )
        cls.build = staticmethod(build_bounded_casting_package)
        cls.load = staticmethod(load_bounded_casting_package)
        cls.write = staticmethod(write_bounded_casting_package)
        cls.manifest = staticmethod(package_manifest)
        cls.rebuild = staticmethod(rebuild_bounded_casting_package)
        cls.records = cls.load(PACKAGE, review_root=REVIEWS)

    def test_exact_seven_json_files_and_six_distinct_records_bound_to_one_projection(self):
        self.assertEqual(set(self.records), FILES - {"manifest.json"})
        self.assertEqual({path.name for path in PACKAGE.iterdir()}, FILES)
        self.assertEqual(len({record.identity for record in self.records.values()}), 6)
        projection = self.records["projection.json"]
        for name, record in self.records.items():
            self.assertEqual(record.to_dict()["canonical_base"], CANONICAL)
            if name != "projection.json":
                self.assertEqual(record.to_dict()["bounded_casting_projection_id"], projection.identity)

    def test_record_identity_roundtrips_and_flags_cannot_be_shadowed_or_mutated(self):
        for record in self.records.values():
            with self.subTest(record=record.to_dict().get("review_kind", "projection")):
                self.assertIs(record.verify(), record)
                self.assertEqual(type(record).from_json(record.serialize()), record)
                self.assertEqual(type(record).create(body(record)), record)
                self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
                for name, value in (("status", "EXECUTABLE"), ("boundary_flags", {}),
                                    ("execution_authorized", True), ("unknown_authority", True)):
                    with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                        setattr(record, name, value)
                with self.assertRaises(TypeError):
                    record._payload["boundary_flags"]["real_rules_executable"] = True
                detached = record.to_dict()
                detached["boundary_flags"]["real_rules_executable"] = True
                self.assertFalse(record.to_dict()["boundary_flags"]["real_rules_executable"])

    def test_strict_json_schema_identity_and_duplicate_fields_rejected(self):
        for record in self.records.values():
            for field, value in ((record.ID_FIELD, OTHER), ("schema_version", "unknown-schema"),
                                 ("canonical_base", "0" * 40), ("status", "EXECUTABLE")):
                changed = record.to_dict()
                changed[field] = value
                with self.subTest(field=field), self.assertRaises(GameplayContractError):
                    type(record).from_dict(changed)
            for invalid in (record.serialize()[:-1] + ',"canonical_base":"' + CANONICAL + '"}',
                            record.serialize()[:-1] + ',"unapproved":NaN}', b"\xff", "[]"):
                with self.assertRaises(GameplayContractError):
                    type(record).from_json(invalid)

    def test_execution_permission_source_and_snapshot_authority_stay_absent(self):
        for record in self.records.values():
            flags = record.to_dict()["boundary_flags"]
            self.assertTrue(flags["non_executable"])
            for field in ("execution_authorized", "real_rules_executable", "admission_eligible", "source_body_retained",
                          "oracle_ingested", "real_snapshot_created", "real_profile_activated"):
                self.assertFalse(flags[field])
            self.assertEqual(flags["owner_execution_approval"], "NOT_GRANTED")
            self.assertEqual(flags["source_policy_clearance"], "not_granted")
            for field in ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export"):
                self.assertEqual(flags[field], "NOT_ESTABLISHED")

    def test_reidentified_promotions_source_prose_or_unknown_envelope_fields_rejected(self):
        for record in self.records.values():
            for mutation in ("execution", "permission", "source-prose", "unknown"):
                changed = body(record)
                if mutation == "execution":
                    changed["boundary_flags"]["real_rules_executable"] = True
                elif mutation == "permission":
                    changed["boundary_flags"]["source_policy_clearance"] = "granted"
                elif mutation == "source-prose":
                    changed["source_text"] = "Authored forbidden source field sentinel."
                else:
                    changed["unapproved"] = True
                with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                    type(record).create(changed)
        review = self.records["casting-readiness-reassessment.json"]
        for field, value in (("execution_ready", True), ("required_primitives_available", True),
                             ("real_execution_primitives_available", ["authored-false-primitive"]),
                             ("implies_complete_spell_casting", True), ("authorized", True), ("semantic_closure", "CLOSED"),
                             ("source_body_retained", True), ("source_text", "Authored forbidden field sentinel.")):
            changed = body(review)
            changed["findings"][field] = value
            with self.subTest(finding=field), self.assertRaises(GameplayContractError):
                type(review).create(changed)

    def test_offline_load_rebuild_requires_no_artifact_network_source_parser_or_raw_retention(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")))
            for module in ("source", "dependency_source", "object_control_source", "zone_change_source",
                           "zone_change_dependency_source", "bounded_casting_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + "._verified_bytes",
                                          side_effect=AssertionError("external source access forbidden")))
            stack.enter_context(patch("gameplay_rules.projection.bounded_casting_source.locate_bounded_casting_anchors",
                                      side_effect=AssertionError("fresh source parse forbidden")))
            self.assertEqual(self.load(PACKAGE, review_root=REVIEWS), self.records)
            self.assertEqual(self.rebuild(self.records["projection.json"], review_root=REVIEWS), self.records)

    def test_source_required_for_new_construction_not_replaced_by_retained_anchor_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            absent = Path(tmp) / "not-present.txt"
            with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                 self.assertRaises(GameplayContractError):
                self.build(absent, review_root=REVIEWS)
        with self.assertRaises(GameplayContractError):
            self.rebuild(self.records["projection.json"].to_dict(), review_root=REVIEWS)

    def test_records_cannot_be_loaded_as_real_gameplay_snapshots_or_execution_profiles(self):
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

    def test_manifest_binds_68_units_seven_prior_packages_and_historical_identity(self):
        value = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(value, self.manifest(self.records))
        self.assertEqual(value["canonical_base"], CANONICAL)
        self.assertEqual((value["projected_rule_count_before"], value["new_source_units_projected"],
                          value["projected_rule_count_after"]), (63, 5, 68))
        self.assertEqual(value["selected_references"], list(EXPECTED))
        self.assertEqual(value["additional_rules_projected"], [])
        self.assertEqual(set(value["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL)
        self.assertFalse(value["historical_anchors_changed"])
        self.assertFalse(value["real_profile_activated"])

    def test_package_has_no_source_txt_official_prose_examples_or_external_paths(self):
        forbidden = {"source_prose", "source_text", "official_text", "official_examples", "examples", "oracle_text",
                     "source_excerpt", "raw_source", "attachment_path", "source_path", "artifact_path", "raw_bytes"}
        def check(value):
            if isinstance(value, dict):
                self.assertTrue(forbidden.isdisjoint(value))
                for item in value.values():
                    check(item)
            elif isinstance(value, list):
                for item in value:
                    check(item)
            elif isinstance(value, str):
                for prefix in ("/workspace/", "/tmp/", "file://", "sediment://"):
                    self.assertNotIn(prefix, value)
        for path in PACKAGE.iterdir():
            self.assertEqual(path.suffix, ".json")
            check(json.loads(path.read_bytes()))

    def test_tampered_missing_extra_txt_extra_source_or_directory_rejected(self):
        for mutation in ("tamper", "missing", "txt", "source", "directory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                if mutation == "tamper":
                    path = root / "projection.json"
                    path.write_bytes(path.read_bytes().replace(b'"selected_rule_count":5', b'"selected_rule_count":6'))
                elif mutation == "missing":
                    (root / "casting-stage-matrix.json").unlink()
                elif mutation == "directory":
                    (root / "extra").mkdir()
                else:
                    (root / ("source.txt" if mutation == "txt" else "source.json")).write_text("Authored extra sentinel.")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_symlink_hardlink_package_root_and_ancestor_links_rejected(self):
        for kind in ("symlink", "hardlink", "root", "ancestor"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as tmp:
                parent = Path(tmp)
                root = parent / "real" / "package"
                shutil.copytree(PACKAGE, root)
                if kind in {"root", "ancestor"}:
                    alias = parent / "alias"
                    alias.symlink_to(root if kind == "root" else root.parent, target_is_directory=True)
                    root = alias if kind == "root" else alias / "package"
                else:
                    path = root / "casting-stage-matrix.json"
                    held = parent / "held.json"
                    path.rename(held)
                    path.symlink_to(held) if kind == "symlink" else os.link(held, path)
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_noncanonical_record_and_manifest_serializations_rejected(self):
        for name in ("projection.json", "manifest.json"):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / name
                path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2) + "\n")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_coherently_reidentified_rehashed_findings_still_require_offline_reproduction(self):
        changed = dict(self.records)
        review = changed["casting-readiness-reassessment.json"]
        value = body(review)
        value["findings"]["unapproved_review_note"] = "Authored changed conclusion sentinel."
        changed["casting-readiness-reassessment.json"] = type(review).create(value)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "rehashed"
            self.write(root, changed)
            with self.assertRaises(GameplayContractError):
                self.load(root, review_root=REVIEWS)

    def test_deterministic_relocation_rebuild_and_append_only_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "relocated-reviews"
            shutil.copytree(REVIEWS, reviews)
            rebuilt = self.rebuild(self.records["projection.json"], review_root=reviews)
            self.assertEqual(rebuilt, self.records)
            root = Path(tmp) / "fresh"
            value = self.write(root, rebuilt)
            self.assertEqual(value, self.manifest(self.records))
            self.assertEqual(self.load(root, review_root=reviews), self.records)
            for name in FILES:
                self.assertEqual((root / name).read_bytes(), (PACKAGE / name).read_bytes())
            with self.assertRaises(GameplayContractError):
                self.write(root, rebuilt)

    @unittest.skipUnless(EXTERNAL_ARTIFACT, "external owner-controlled artifact not configured")
    def test_owner_artifact_reproduces_exact_package_and_no_selected_source_line_is_retained(self):
        from gameplay_rules.projection.bounded_casting_source import verify_bounded_casting_bytes
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")):
            rebuilt = self.build(EXTERNAL_ARTIFACT, review_root=REVIEWS)
            source = Path(EXTERNAL_ARTIFACT).read_bytes()
            verify_bounded_casting_bytes(source)
        self.assertEqual(rebuilt, self.records)
        retained = [path.read_bytes() for path in PACKAGE.iterdir()]
        retained.extend(path.read_bytes() for path in CODE.glob("bounded_casting*.py"))
        retained.append(Path(__file__).read_bytes())
        doc = ROOT / "docs/GAMEPLAY_RULES_BOUNDED_CASTING_PROJECTION.md"
        if doc.is_file():
            retained.append(doc.read_bytes())
        for rule in rebuilt["projection.json"].to_dict()["rules"]:
            anchor = rule["source_anchor"]
            span = source[anchor["byte_start"]:anchor["byte_end"]]
            self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(span).hexdigest())
            for line in span.splitlines():
                if len(line) > 20:
                    for target in retained:
                        self.assertNotIn(line, target)


class BoundedCastingReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_casting_package import load_bounded_casting_package
        cls.records = load_bounded_casting_package(PACKAGE, review_root=REVIEWS)
        cls.rules = {rule["rule_reference"]: rule for rule in cls.records["projection.json"].to_dict()["rules"]}
        cls.correspondence = cls.records["design-source-correspondence.json"].to_dict()["findings"]
        cls.matrix = cls.records["casting-stage-matrix.json"].to_dict()["findings"]
        cls.madness = cls.records["madness-readiness-reassessment.json"].to_dict()["findings"]
        cls.casting = cls.records["casting-readiness-reassessment.json"].to_dict()["findings"]
        cls.composite = cls.records["composite-coverage.json"].to_dict()["findings"]

    def test_correspondence_separates_old_design_input_from_new_verified_evidence(self):
        value = self.correspondence
        self.assertEqual(value["historical_design_package_id"], PRIOR_PACKAGES["gameplay-rules-madness-casting-design"])
        self.assertEqual(value["historical_design_id"],
                         "sha256:ca2acabb2fbca0e958165ef4cc4d48d3736885458053219507cddd58c5eb611a")
        self.assertEqual(value["historical_design_authority_unchanged"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
        self.assertEqual(value["new_evidence_authority"], "EXACT_ARTIFACT_AND_SELECTED_BLOCKS_VERIFIED")
        self.assertFalse(value["historical_design_package_mutated"])
        for row in value["observations"]:
            self.assertEqual(row["historical_authority"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
            rule = self.rules[row["rule_reference"]]
            self.assertEqual(row["rule_id"], rule["rule_id"])
            self.assertEqual(row["source_anchor"], rule["source_anchor"])

    def test_source_observations_verified_refined_and_additional_boundary_classified(self):
        rows = {row["observation"]: row for row in self.correspondence["observations"]}
        expected = {"mode_choice", "splice_declaration", "alternative_cost_basis", "additional_costs", "variable_values",
                    "hybrid_choices", "phyrexian_choices", "multiple_alternative_cost_exclusion", "prior_choice_restrictions",
                    "total_cost_composition", "cost_lock", "mana_ability_window", "payment_ordering",
                    "partial_payment_prohibition", "unpayable_costs", "parent_permission_and_rollback"}
        self.assertEqual(set(rows), expected)
        for name in ("variable_values", "total_cost_composition", "cost_lock"):
            self.assertEqual(rows[name]["finding"], "VERIFIED_WITH_REFINEMENT")
        self.assertEqual(rows["parent_permission_and_rollback"]["finding"], "FOUND_ADDITIONAL_BOUNDARY")
        self.assertEqual(self.correspondence["semantic_observation_counts"], {
            "VERIFIED": 12, "VERIFIED_WITH_REFINEMENT": 3, "DID_NOT_VERIFY": 0, "FOUND_ADDITIONAL_BOUNDARY": 1})
        self.assertEqual(self.correspondence["semantic_observations_contradicted"], [])

    def test_actual_physical_shape_refines_expectations_without_padding_or_policy_weakening(self):
        rows = {row["rule_reference"]: row for row in self.correspondence["physical_shape_observations"]}
        for reference in ("601.2", "601.2b", "601.2f"):
            self.assertTrue(rows[reference]["expected_multiline"])
            self.assertEqual(rows[reference]["actual_line_count"], 1)
            self.assertEqual(rows[reference]["finding"], "DID_NOT_VERIFY")
            self.assertTrue(rows[reference]["reviewed_contract_compatible"])
        self.assertEqual(rows["601.2g"]["actual_line_count"], 1)
        self.assertEqual(rows["601.2h"]["actual_line_count"], 2)
        ownership = self.correspondence["example_ownership"]
        self.assertEqual(ownership["rule_reference"], "601.2h")
        self.assertEqual(ownership["state"], "UNAMBIGUOUS_SELECTED_RULE_OWNERSHIP")
        self.assertTrue(ownership["included_in_block_hash"])
        self.assertFalse(ownership["example_prose_retained"])

    def test_verified_frontier_exactly_matches_selected_block_citations_and_does_not_invent_e_i(self):
        rows = self.matrix["explicit_numbered_dependency_findings"]
        expected = {(reference, target) for reference, targets in EXPLICIT.items() for target in targets}
        self.assertEqual({(row["from_reference"], row["target_reference"]) for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        for row in rows:
            selected = row["target_reference"] in EXPECTED
            self.assertEqual(row["reference_state"], "DIRECT_REFERENCE_RESOLVED" if selected else "UNRESOLVED")
            self.assertEqual(row["coverage_state"], "PROJECTED_IN_THIS_MILESTONE" if selected else "UNPROJECTED")
            self.assertEqual(row["evidence_basis"], "VERIFIED_SELECTED_SOURCE_BLOCK_CITATION")
        self.assertEqual(set(self.matrix["verified_unresolved_direct_references"]), FRONTIER | {"601.2a", "601.2c", "601.2d"})
        self.assertEqual(self.matrix["structural_only_unprojected_stages"], ["601.2e", "601.2i"])

    def test_retained_stage_matrix_is_deterministic_and_parent_never_satisfies_missing_stages(self):
        rows = self.matrix["rows"]
        self.assertEqual([row["reference"] for row in rows], ["601.2", *("601.2" + suffix for suffix in "abcdefghi")])
        self.assertFalse(self.matrix["parent_projection_satisfies_siblings"])
        self.assertEqual(self.matrix["selected_stage_references"], list(EXPECTED[1:]))
        self.assertEqual(self.matrix["unprojected_stage_references"], list(SIBLINGS))
        for row in rows:
            if row["reference"] in EXPECTED:
                self.assertEqual(row["rule_id"], self.rules[row["reference"]]["rule_id"])
            else:
                self.assertEqual(row["status"], "UNPROJECTED_CASTING_STAGE")
                self.assertNotIn("rule_id", row)
                self.assertFalse(row["execution_ready"])
        legality = self.matrix["legality_stage_boundary"]
        self.assertEqual(legality["reference"], "601.2e")
        self.assertEqual(legality["coverage_state"], "UNPROJECTED_CASTING_STAGE")
        self.assertEqual(legality["role_basis"], "OWNER_SUPPLIED_STRUCTURAL_DESIGN_BOUNDARY_NOT_PROJECTED_SOURCE")

    def test_madness_reassessment_binds_old_four_rule_ids_and_new_five_without_duplication(self):
        old = prior_rules()
        for row in self.madness["retained_madness_rules"]:
            self.assertEqual(row["rule_id"], old[row["rule_reference"]]["rule_id"])
        self.assertEqual([row["rule_reference"] for row in self.madness["retained_madness_rules"]],
                         ["702.35a", "702.35b", "702.35c"])
        lookup = self.madness["retained_zone_change_lookup"]
        self.assertEqual(lookup, {"rule_reference": "400.7k", "rule_id": old["400.7k"]["rule_id"]})
        self.assertEqual(self.madness["new_selected_casting_rules"],
                         [{"rule_reference": ref, "rule_id": self.rules[ref]["rule_id"]} for ref in EXPECTED])
        self.assertEqual(self.madness["alternative_cost_source_coverage"], "REPRESENTED_WITH_OPEN_DEPENDENCIES")
        self.assertFalse(self.madness["fictional_mana_satisfies_real_605"])

    def test_all_fourteen_madness_dimensions_stay_open_and_non_executable(self):
        rows = self.madness["dimensions"]
        self.assertEqual([row["dimension"] for row in rows], ["discard_replacement", "exile", "trigger", "optional_cast_choice",
            "alternative_cost_selection", "cost_determination", "mana_ability_window", "payment", "casting_legality",
            "target_and_mode_requirements", "stack_placement", "casting_completion", "rollback", "public_zone_fallback"])
        for row in rows:
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
        self.assertEqual(self.madness["dependency_closure"], "OPEN")
        self.assertEqual(self.madness["semantic_closure"], "OPEN")
        self.assertEqual(self.madness["execution_readiness"], "EXECUTION_BLOCKED")
        self.assertFalse(self.madness["execution_ready"])

    def test_alternative_cost_subprocedure_coverage_does_not_imply_semantic_closure_or_complete_casting(self):
        rows = {row["capability_id"]: row for row in self.casting["capabilities"]}
        self.assertEqual(set(rows), {"alternative_cost_casting_subprocedure", "complete_spell_casting"})
        subprocedure = rows["alternative_cost_casting_subprocedure"]
        self.assertEqual(subprocedure["source_coverage"], "REPRESENTED_WITH_OPEN_DEPENDENCIES")
        self.assertEqual(subprocedure["selected_stages"], list(EXPECTED[1:]))
        self.assertFalse(subprocedure["implies_complete_spell_casting"])
        for row in rows.values():
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["dependency_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
            self.assertFalse(row["required_primitives_available"])
            self.assertEqual(row["real_execution_primitives_available"], [])
            self.assertFalse(row["runtime_implemented"])

    def test_complete_casting_preserves_missing_stages_permission_rollback_and_major_gaps(self):
        rows = {row["capability_id"]: row for row in self.casting["capabilities"]}
        complete = rows["complete_spell_casting"]
        self.assertEqual(complete["source_coverage"], "INCOMPLETE")
        self.assertEqual(complete["missing_stages"], list(SIBLINGS))
        self.assertEqual(complete["unresolved_permission_and_rollback"], ["601.3", "733"])
        self.assertTrue({"initial_spell_movement_and_stack_proposal", "target_declaration", "division_and_distribution",
                         "legality_checking", "casting_completion", "cast_triggers", "stack_semantics",
                         "casting_permission_and_prohibition", "illegal_action_rollback", "priority"}
                        <= set(self.casting["complete_casting_gaps"]))
        self.assertFalse(self.casting["payment_executed"])
        self.assertFalse(self.casting["cost_calculation_implemented"])
        self.assertEqual(self.casting["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")

    def test_old_and_new_numbered_blockers_remain_unprojected_and_no_longer_count_b_f_g_h_open(self):
        remaining = set(self.casting["remaining_unresolved_rules"])
        self.assertEqual(remaining, OLD_BLOCKERS | FRONTIER | set(SIBLINGS))
        self.assertTrue(set(EXPECTED).isdisjoint(remaining))
        self.assertEqual(set(self.composite["remaining_unresolved_rules"]), remaining)
        self.assertEqual(set(self.madness["unresolved_numbered_references"]), remaining)
        for blocker in ("unresolved_direct_numbered_dependencies", "unprojected_casting_stages", "real_card_and_effect_semantics",
                        "real_605_semantics", "casting_legality", "illegal_action_rollback", "real_semantic_primitives",
                        "deterministic_runtime_vectors", "owner_activation"):
            self.assertIn(blocker, self.casting["blockers"])

    def test_readonly_composite_preserves_six_projection_and_six_package_identities_exactly_68(self):
        from gameplay_rules.projection.bounded_casting_package import composite_coverage_view, package_manifest
        value = self.composite
        self.assertEqual(value["view_kind"], "READ_ONLY_SIX_PROJECTION_COMPOSITE")
        self.assertEqual((value["previous_projected_rule_count"], value["new_projected_rule_count"],
                          value["total_projected_rule_count"]), (63, 5, 68))
        self.assertEqual(value["component_rule_counts"], [20, 12, 7, 12, 12, 5])
        refs = value["projected_references"]
        self.assertEqual(len(refs), 68)
        self.assertEqual(len(set(refs)), 68)
        self.assertEqual(refs[-5:], list(EXPECTED))
        self.assertEqual(refs.count("400.7"), 1)
        self.assertEqual(refs.count("400.7k"), 1)
        self.assertTrue((OLD_BLOCKERS | FRONTIER | set(SIBLINGS)).isdisjoint(refs))
        components = value["projection_components"]
        self.assertEqual(len({row["projection_id"] for row in components}), 6)
        self.assertTrue(all(not row["mutated"] for row in components))
        self.assertTrue(value["component_identities_preserved"])
        before = {name: record.serialize() for name, record in self.records.items()}
        manifest = package_manifest(self.records)
        view = composite_coverage_view(self.records, manifest)
        self.assertEqual(len({row["package_id"] for row in view["projection_components"]}), 6)
        self.assertEqual(view["projection_components"][-1]["package_id"], manifest["package_id"])
        self.assertEqual(view["total_projected_rule_count"], 68)
        self.assertEqual(before, {name: record.serialize() for name, record in self.records.items()})
        with self.assertRaises(GameplayContractError):
            composite_coverage_view(self.records, dict(manifest, package_id=OTHER))

    def test_exactly_one_next_milestone_is_recommended_not_authorized_or_started(self):
        value = self.casting["next_milestone"]
        self.assertEqual(value["candidate"], "Mana Ability Dependency Design")
        self.assertEqual(value["center_reference"], "605")
        self.assertEqual(value["exact_proposed_scope"], ["605 dependency and authority boundary design"])
        self.assertFalse(value["source_txt_required"])
        self.assertTrue(value["future_source_projection_requires_verified_artifact"])
        self.assertEqual(value["new_source_units_authorized"], 0)
        self.assertFalse(value["authorized"])
        self.assertFalse(value["started"])
        self.assertEqual(value["source_basis"], "RETAINED_VERIFIED_FRONTIER_ONLY_NOT_NEW_605_SOURCE_KNOWLEDGE")


if __name__ == "__main__":
    unittest.main()
