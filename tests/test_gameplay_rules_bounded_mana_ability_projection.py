"""Offline and owner-artifact proofs for the bounded thirteen-unit 605 family.

Source locator fixtures below are invented text. Canonical preservation digests
are independent of Git availability; optional official bytes are never retained.
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

from evidence.contracts import deterministic_json
from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.errors import GameplayContractError

ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / "gameplay-rules-bounded-mana-ability-projection"
CODE = ROOT / "src/gameplay_rules/projection"
CANONICAL = "6d7542f7d375e6c75e3de7bf6ce3010868ca04ad"
EXPECTED = ("605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b", "605.3c",
            "605.4", "605.4a", "605.5", "605.5a", "605.5b")
FRONTIER = {"115.6", "606", "602.2", "405.6c", "603"}
OLD_BLOCKERS = {"603.7d", "603.7e", "603.7f", "114", "901.6", "902.6", "904.7", "905.5", "613",
                "601.2a", "601.2c", "601.2d", "601.2e", "601.2i", "601.3", "733", "700.2", "702.47",
                "118.8", "118.9", "107.3"}
ARTIFACT = "sha256:8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca"
POLICY = "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR"
HISTORICAL = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
OTHER = "sha256:" + "f" * 64
EXTERNAL_ARTIFACT = os.environ.get("MTGLAB_BOUNDED_MANA_ARTIFACT")
FILES = {"projection.json", "design-source-correspondence.json", "family-closure-review.json",
         "consumer-reassessment.json", "classification-readiness.json", "behavior-readiness.json",
         "overall-readiness.json", "composite-coverage.json", "manifest.json"}
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
    "gameplay-rules-bounded-casting-projection": "sha256:d2b1832f170d1bbd6ef21efe3d3452923880cc47c57dad523f7aefff4bc427d7",
    "gameplay-rules-mana-ability-design": "sha256:6b1d0165bc0fab488ff7fd4aa84aa5bf5ccdb0e991c99a989d1ef6d3a6a09ce1",
}
EXPLICIT = {
    "605.1": (), "605.1a": ("115.6", "606"), "605.1b": ("115.6", "605.1a"), "605.2": (),
    "605.3": ("602.2",), "605.3a": (), "605.3b": ("405.6c",), "605.3c": (), "605.4": ("603",),
    "605.4a": (), "605.5": ("605.1a", "605.1b"), "605.5a": (), "605.5b": (),
}


def inventory(paths):
    values = []
    for path in sorted(set(paths)):
        if path.is_symlink():
            raise AssertionError("Protected file must be regular")
        raw = path.read_bytes()
        values.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return values


def regular_files(root):
    # This later append-only milestone is outside the historical inventory.
    return [p for p in _historical_regular_files(root)
            if not (p.parent == ROOT / "src/gameplay_rules/projection" and p.name.startswith("mana_classification_"))
            and "gameplay-rules-bounded-mana-classification-projection" not in p.parts]


def _historical_regular_files(root):
    return [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]


def body(record):
    return {k: v for k, v in record.to_dict().items() if k not in {"schema_version", record.ID_FIELD}}


def prior_rules():
    rules = {}
    for package in PRIOR_PACKAGES:
        path = REVIEWS / package / "projection.json"
        if path.is_file():
            for rule in json.loads(path.read_bytes())["rules"]:
                if rule["rule_reference"] in rules:
                    raise AssertionError("Prior source-unit projections must remain disjoint")
                rules[rule["rule_reference"]] = rule
    return rules


class BoundedManaPreservationTests(unittest.TestCase):
    def test_all_308_prior_source_files_preserve_engine_profiles_policy_products_writer_and_simulation(self):
        values = inventory(p for p in regular_files(ROOT / "src")
                           if not (p.parent == CODE and p.name.startswith("bounded_mana"))
                           and "mana_dependency_design" not in p.parts)
        self.assertEqual(len(values), 308)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "745d737bbd8fb53f97d5d599b807255cd29adca63dc9a2c6baf3debc219cde50")

    def test_all_176_prior_review_files_and_nine_package_identities_are_byte_identical(self):
        values = inventory(p for p in regular_files(REVIEWS) if PACKAGE not in p.parents
                           and "gameplay-rules-mana-direct-dependency-design" not in p.parts)
        self.assertEqual(len(values), 176)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "5cf537091af0a56b12d6f1e14679faab64a373a46d66936389d51ba02741136e")
        for package, identity in PRIOR_PACKAGES.items():
            with self.subTest(package=package):
                self.assertEqual(json.loads((REVIEWS / package / "manifest.json").read_bytes())["package_id"], identity)

    def test_all_68_old_rules_and_historical_anchor_policies_preserved_without_synthetic_605(self):
        rules = prior_rules()
        self.assertEqual(len(rules), 68)
        self.assertNotIn("605", rules)
        self.assertTrue(set(EXPECTED).isdisjoint(rules))
        for ref, rule in rules.items():
            expected = POLICY if ref in {"601.2", "601.2b", "601.2f", "601.2g", "601.2h"} else "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR"
            self.assertEqual(rule["source_anchor"]["span_policy"], expected)
        for ref, identity in {
            "601.2g": "sha256:7c01241cb591680e28dd16dd3c97b88b28ebcdaca80af8c153a5891e1363a662",
            "109.4a": "sha256:7793b14d8f2af5916dd02316ff0ea817d77b0bf656284c0f56d86b3f743fcea1",
            "702.35a": "sha256:48da52c60c006aaae9a752b23155581474244b4a7b3a050b588fb2f51c1b6534",
            "702.35b": "sha256:884e5ecb63b242196785a1d38f8a3014896342a6d4b738e6005430c1ac22d5ae",
            "702.35c": "sha256:79b507ab353539b0d1166876f25c279a2171f860f69ab40b53cc2d942f198fb4",
            "400.7k": "sha256:5fd728b81834e50cc3555e61fd9cf9f9cb6e3cce172618d23cfcd0649efe21c5",
        }.items():
            self.assertEqual(rules[ref]["rule_id"], identity)
        for ref in ("601.2g", "109.4a"):
            self.assertIn("605", rules[ref]["direct_dependency_references"])
            self.assertIn("605", [row["reference"] for row in rules[ref]["unresolved_dependencies"]])

    def test_architecture_v13_decision_017_and_protected_historical_fixture_remain_unchanged(self):
        values = inventory(ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md"))
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")
        fixture = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((fixture / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL)
        for name, expected in manifest["files"].items():
            raw = (fixture / name).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, expected)

    def test_fictional_authority_constants_and_empty_simulation_unchanged(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({p.name for p in (ROOT / "src/simulation").iterdir() if p.name != "__pycache__"}, {".gitkeep"})

    def test_new_projection_layer_has_no_runtime_network_card_ingestion_or_general_parser(self):
        imports = {"socket", "http", "urllib", "requests", "subprocess", "simulation", "random", "secrets",
                   "providers", "external_ingestion", "production_evidence", "market"}
        runtime = {"GameplayRulesEngine", "GameplayRulesSnapshot", "CardGameplaySemantics", "GameState", "GameAction",
                   "LegalityResult", "GameTransition", "RawSnapshotStore"}
        functions = {"classify_mana_ability", "activate_mana_ability", "resolve_mana_ability", "produce_mana", "add_mana",
                     "pay_mana", "pay_cost", "assign_controller", "detect_trigger", "to_rules_snapshot", "activate_profile",
                     "parse_comprehensive_rules", "build_rule_inventory", "parse_rule_tree", "import_section"}
        paths = list(CODE.glob("bounded_mana*.py"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
                if isinstance(node, ast.Import):
                    self.assertTrue(imports.isdisjoint(a.name.split(".")[0] for a in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or "").split(".")[0], imports)
                    self.assertTrue(runtime.isdisjoint(a.name for a in node.names))
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, runtime)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertNotIn(node.name, functions)


class BoundedManaSourceTests(unittest.TestCase):
    def setUp(self):
        from gameplay_rules.projection.bounded_mana_source import locate_bounded_mana_anchors
        self.locate = locate_bounded_mana_anchors

    def fixture(self, ending=b"\n"):
        lines = ["Invented locator header ☃".encode(), b"605. Mana Abilities", "\u00a0".encode()]
        for ref in EXPECTED:
            lines.append((ref + (". " if ref[-1].isdigit() else " ") + "Invented source-unit sentinel.").encode())
            if ref == "605.1":
                lines.append(b"  Invented indented continuation.")
            if ref in {"605.2", "605.4a"}:
                lines.append(b"Example: Invented ownership sentinel.")
            lines.append("\u00a0".encode())
        lines.append(b"606. Loyalty Abilities")
        return ending.join(lines) + ending

    def test_complete_fixed_family_located_in_order_without_retaining_text(self):
        data = self.fixture(b"\r\n")
        values = self.locate(data)
        self.assertEqual(values, self.locate(data))
        self.assertEqual(tuple(a["rule_reference"] for a in values), EXPECTED)
        self.assertEqual([a["line_count"] for a in values], [2, 1, 1, 2, 1, 1, 1, 1, 1, 2, 1, 1, 1])
        for anchor in values:
            span = data[anchor["byte_start"]:anchor["byte_end"]]
            self.assertEqual(anchor["anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
            self.assertEqual(anchor["span_policy"], POLICY)
            self.assertEqual(anchor["artifact_hash"], "sha256:" + hashlib.sha256(data).hexdigest())
            self.assertEqual(anchor["span_sha256"], "sha256:" + hashlib.sha256(span).hexdigest())
            self.assertEqual(anchor["line_count"], anchor["ending_physical_line"] - anchor["starting_physical_line"] + 1)
            self.assertFalse(span.endswith((b"\r", b"\n")))
            self.assertNotIn("Invented", json.dumps(anchor))
        self.assertEqual(values[0]["starting_physical_line"], 4)
        self.assertEqual(values[0]["byte_start"], len("Invented locator header ☃\r\n605. Mana Abilities\r\n\u00a0\r\n".encode()))

    def test_internal_terminator_changes_span_hash_but_final_terminator_does_not(self):
        raw = self.fixture(b"\r\n")
        original = self.locate(raw)[0]
        internal = raw.replace(b"source-unit sentinel.\r\n  Invented", b"source-unit sentinel.\n  Invented", 1)
        final = raw.replace(b"indented continuation.\r\n", b"indented continuation.\n", 1)
        self.assertNotEqual(original["span_sha256"], self.locate(internal)[0]["span_sha256"])
        self.assertEqual(original["span_sha256"], self.locate(final)[0]["span_sha256"])
        self.assertNotEqual(original["artifact_hash"], self.locate(final)[0]["artifact_hash"])

    def test_only_adjacent_unambiguous_examples_belong_to_605_2_and_605_4a(self):
        raw = self.fixture()
        for anchor in self.locate(raw):
            span = raw[anchor["byte_start"]:anchor["byte_end"]]
            self.assertEqual(b"Example: Invented" in span, anchor["rule_reference"] in {"605.2", "605.4a"})
            self.assertNotIn(b"606.", span)
            self.assertNotIn("\u00a0".encode(), span)

    def test_every_missing_duplicate_or_prefix_substituted_selected_marker_fails(self):
        for ref in EXPECTED:
            marker = (ref + (". " if ref[-1].isdigit() else " ")).encode()
            base = self.fixture()
            line = next(line for line in base.splitlines() if line.startswith(marker))
            for kind, data in {
                "missing": base.replace(line + b"\n", b"", 1),
                "duplicate": base + line + b"\n",
                "prefix": base.replace(marker, ref.encode() + b"z ", 1),
            }.items():
                with self.subTest(ref=ref, kind=kind), self.assertRaises(GameplayContractError):
                    self.locate(data)

    def test_incomplete_extra_reordered_or_malformed_family_fails(self):
        raw = self.fixture()
        cases = {
            "heading-absent": raw.replace(b"605. Mana Abilities\n", b"", 1),
            "end-absent": raw.replace(b"606. Loyalty Abilities\n", b"", 1),
            "extra-unit": raw.replace(b"606. Loyalty", b"605.6. Invented extra unit.\n606. Loyalty", 1),
            "reordered-unit": raw.replace(b"605.1a Invented", b"605.1b Invented", 1),
            "malformed-number": raw.replace(b"605.1a Invented", b"605.1aa Invented", 1),
            "indented-number": raw.replace(b"  Invented indented continuation.", b"  605.1a Invented hidden boundary.", 1),
            "unexplained-continuation": raw.replace(b"  Invented indented continuation.", b"Invented unexplained continuation.", 1),
        }
        for kind, data in cases.items():
            with self.subTest(kind=kind), self.assertRaises(GameplayContractError):
                self.locate(data)

    def test_separator_or_repeated_or_unexpected_example_ownership_is_rejected(self):
        raw = self.fixture()
        sample = b"Example: Invented ownership sentinel."
        cases = (
            raw.replace(sample, "\u00a0\n".encode() + sample, 1),
            raw.replace(sample, sample + b"\nExample: Invented repeated illustration.", 1),
            raw.replace(b"  Invented indented continuation.", sample, 1),
            raw.replace(sample, b"  " + sample, 1),
        )
        for data in cases:
            with self.assertRaises(GameplayContractError) as caught:
                self.locate(data)
            self.assertIn("AMBIGUOUS_EXAMPLE_OWNERSHIP", str(caught.exception))

    def test_overlapping_span_metadata_fails_independently(self):
        from gameplay_rules.projection.bounded_mana_source import validate_bounded_mana_spans
        anchors = self.locate(self.fixture())
        anchors[1]["byte_start"] = anchors[0]["byte_start"]
        with self.assertRaises(GameplayContractError):
            validate_bounded_mana_spans(anchors)

    def test_artifact_hash_is_required_before_synthetic_structure_can_gain_projection_authority(self):
        from gameplay_rules.projection.bounded_mana_source import verify_bounded_mana_bytes
        for value in (self.fixture(), b"x" * 977752, b"", "not bytes", None):
            with self.subTest(kind=type(value).__name__), self.assertRaises(GameplayContractError):
                verify_bounded_mana_bytes(value)

    def test_missing_wrong_or_symlink_source_fails_without_network_or_raw_snapshot_retention(self):
        from gameplay_rules.projection.bounded_mana_source import build_bounded_mana_projection
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            wrong = root / "invented-wrong.txt"
            wrong.write_bytes(b"x" * 977752)
            linked = root / "linked.txt"
            linked.symlink_to(wrong)
            for path in (root / "missing.txt", wrong, linked):
                with self.subTest(kind=path.name), patch("socket.socket", side_effect=AssertionError("network forbidden")), \
                     patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")), \
                     self.assertRaises(GameplayContractError) as caught:
                    build_bounded_mana_projection(path, **SOURCE_ROOTS)
                self.assertNotIn(str(root), str(caught.exception))
                if path.name == "missing.txt":
                    self.assertIn("MISSING_VERIFIED_SOURCE_ARTIFACT", str(caught.exception))


class BoundedManaProjectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_mana_contracts import BoundedManaProjection
        cls.projection = BoundedManaProjection.from_json((PACKAGE / "projection.json").read_bytes())
        cls.value = cls.projection.to_dict()
        cls.rules = {rule["rule_reference"]: rule for rule in cls.value["rules"]}

    def test_exact_canonical_base_allowlist_thirteen_new_and_81_total(self):
        from gameplay_rules.projection.bounded_mana_scope import SELECTED_REFERENCES
        self.assertEqual(self.value["canonical_base"], CANONICAL)
        self.assertEqual(tuple(SELECTED_REFERENCES), EXPECTED)
        self.assertEqual(tuple(self.rules), EXPECTED)
        self.assertEqual(self.value["selected_rule_count"], 13)
        self.assertEqual(self.value["new_source_units_projected"], 13)
        self.assertEqual(self.value["total_projected_rule_count"], 81)
        self.assertEqual(self.value["milestone_status"], "BOUNDED_MANA_ABILITY_RULES_PROJECTED")
        self.assertEqual(self.value["projection_kind"], "NON_EXECUTABLE")
        self.assertNotIn("605", self.rules)
        self.assertTrue((FRONTIER | OLD_BLOCKERS).isdisjoint(self.rules))

    def test_every_rule_has_immutable_authored_semantics_and_exact_explicit_citations(self):
        self.assertEqual(len({r["rule_id"] for r in self.rules.values()}), 13)
        for ref, rule in self.rules.items():
            with self.subTest(reference=ref):
                for key in ("topic", "paraphrase", "semantic_category", "concept_tags", "limitations", "subsystem_boundaries",
                            "required_future_semantic_primitives", "semantic_distinctions"):
                    self.assertTrue(rule[key], key)
                self.assertEqual(tuple(rule["direct_dependency_references"]), EXPLICIT[ref])
                self.assertEqual(rule["review_state"], "PROJECTED_FOR_REVIEW")
                self.assertEqual(rule["semantic_closure_state"], "OPEN")
                self.assertEqual(rule["execution_readiness"], "BLOCKED")
                self.assertFalse(rule["execution_ready"])
                self.assertRegex(rule["rule_id"], r"^sha256:[0-9a-f]{64}$")

    def test_exact_source_artifact_lineage_and_complete_anchor_schema(self):
        binding = self.value["source_binding"]
        self.assertEqual(binding["artifact_hash"], ARTIFACT)
        self.assertEqual(binding["byte_length"], 977752)
        self.assertEqual(binding["effective_date"], "2026-09-25")
        self.assertEqual(binding["verification_result_id"],
                         "sha256:6289f9e138c248f33b950842fd079f9dc9d4be431a9ac8dc1effb4a18ec502b3")
        self.assertEqual(binding["correspondence_review_id"],
                         "sha256:7332e6517b1b28085bbee1fa76b8ecbc9cbe4148e261452449a308ba348d9def")
        last_end = 0
        for ref in EXPECTED:
            anchor = self.rules[ref]["source_anchor"]
            with self.subTest(reference=ref):
                self.assertEqual(set(anchor), {"rule_reference", "artifact_hash", "effective_date", "anchor_type",
                    "starting_physical_line", "ending_physical_line", "line_count", "byte_start", "byte_end",
                    "span_sha256", "span_policy"})
                self.assertEqual(anchor["rule_reference"], ref)
                self.assertEqual(anchor["artifact_hash"], ARTIFACT)
                self.assertEqual(anchor["effective_date"], "2026-09-25")
                self.assertEqual(anchor["anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
                self.assertEqual(anchor["span_policy"], POLICY)
                self.assertEqual(anchor["line_count"], 2 if ref in {"605.2", "605.4a"} else 1)
                self.assertEqual(anchor["ending_physical_line"] - anchor["starting_physical_line"] + 1, anchor["line_count"])
                self.assertGreater(anchor["byte_start"], last_end)
                self.assertGreater(anchor["byte_end"], anchor["byte_start"])
                self.assertLessEqual(anchor["byte_end"], 977752)
                self.assertRegex(anchor["span_sha256"], r"^sha256:[0-9a-f]{64}$")
            last_end = anchor["byte_end"]

    def test_reidentified_fourteenth_missing_duplicate_or_unselected_rule_is_rejected(self):
        from gameplay_rules.projection.bounded_mana_contracts import BoundedManaProjection
        for mutation in ("count", "extra", "missing", "duplicate", "605", *sorted(FRONTIER | OLD_BLOCKERS)):
            value = body(self.projection)
            if mutation == "count":
                value["selected_rule_count"] = 14
            elif mutation == "extra":
                value["rules"].append(value["rules"][-1])
            elif mutation == "missing":
                value["rules"].pop()
            elif mutation == "duplicate":
                value["rules"][1] = value["rules"][0]
            else:
                value["rules"][0]["rule_reference"] = mutation
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                BoundedManaProjection.create(value)

    def test_anchor_hash_span_policy_and_physical_bounds_cannot_be_forged_offline(self):
        from gameplay_rules.projection.bounded_mana_contracts import BoundedManaProjection
        for field, value in (("artifact_hash", OTHER), ("span_sha256", OTHER), ("byte_start", 0), ("line_count", 99),
                             ("anchor_type", "SINGLE_LINE_RULE_ANCHOR"),
                             ("span_policy", "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR")):
            changed = body(self.projection)
            changed["rules"][0]["source_anchor"][field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                BoundedManaProjection.create(changed)

    def test_selected_internal_dependencies_and_external_frontier_do_not_recurse(self):
        for ref, rule in self.rules.items():
            deps = {row["reference"]: row for row in rule["dependencies"]}
            self.assertEqual(set(deps), set(EXPLICIT[ref]) & set(EXPECTED))
            self.assertEqual({row["reference"] for row in rule["unresolved_dependencies"]}, set(EXPLICIT[ref]) - set(EXPECTED))
            for target, row in deps.items():
                if target in EXPECTED:
                    self.assertEqual(row["status"], "PROJECTED_IN_THIS_MILESTONE")
                else:
                    self.assertEqual(row["coverage_state"], "UNPROJECTED")
        self.assertEqual({target for refs in EXPLICIT.values() for target in refs if target not in EXPECTED}, FRONTIER)
        for ref in ("605.5a", "605.5b"):
            self.assertEqual(self.rules[ref]["direct_dependency_references"], [])


class BoundedManaPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_mana_package import (
            build_bounded_mana_package, load_bounded_mana_package, write_bounded_mana_package,
            package_manifest, rebuild_bounded_mana_package,
        )
        cls.build = staticmethod(build_bounded_mana_package)
        cls.load = staticmethod(load_bounded_mana_package)
        cls.write = staticmethod(write_bounded_mana_package)
        cls.manifest = staticmethod(package_manifest)
        cls.rebuild = staticmethod(rebuild_bounded_mana_package)
        cls.records = cls.load(PACKAGE, review_root=REVIEWS)

    def test_exact_nine_json_files_bind_eight_distinct_records_to_one_projection(self):
        self.assertEqual(set(self.records), FILES - {"manifest.json"})
        self.assertEqual({p.name for p in PACKAGE.iterdir()}, FILES)
        self.assertEqual(len({r.identity for r in self.records.values()}), 8)
        projection = self.records["projection.json"]
        for name, record in self.records.items():
            self.assertEqual(record.to_dict()["canonical_base"], CANONICAL)
            if name != "projection.json":
                self.assertEqual(record.to_dict()["bounded_mana_projection_id"], projection.identity)

    def test_records_roundtrip_canonical_identity_and_cannot_mutate_nested_flags(self):
        for record in self.records.values():
            self.assertIs(record.verify(), record)
            self.assertEqual(type(record).from_json(record.serialize()), record)
            self.assertEqual(type(record).create(body(record)), record)
            self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
            for name, value in (("status", "EXECUTABLE"), ("boundary_flags", {}), ("execution_authorized", True)):
                with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                    setattr(record, name, value)
            with self.assertRaises(TypeError):
                record._payload["boundary_flags"]["real_rules_executable"] = True
            detached = record.to_dict()
            detached["boundary_flags"]["real_rules_executable"] = True
            self.assertFalse(record.to_dict()["boundary_flags"]["real_rules_executable"])

    def test_identity_schema_duplicates_nonfinite_and_unknown_fields_rejected(self):
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

    def test_all_execution_permission_snapshot_and_profile_authority_remain_absent(self):
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

    def test_reidentified_execution_or_permission_promotions_source_prose_and_unknown_envelope_rejected(self):
        for record in self.records.values():
            for mutation in ("execution", "permission", "source-prose", "unknown"):
                changed = body(record)
                if mutation == "execution":
                    changed["boundary_flags"]["real_rules_executable"] = True
                elif mutation == "permission":
                    changed["boundary_flags"]["source_policy_clearance"] = "granted"
                elif mutation == "source-prose":
                    changed["source_text"] = "Invented forbidden source-field sentinel."
                else:
                    changed["unapproved"] = True
                with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                    type(record).create(changed)
        review = self.records["overall-readiness.json"]
        for field, value in (("execution_ready", True), ("required_primitives_available", True),
                             ("authorized", True), ("semantic_closure", "CLOSED"),
                             ("source_body_retained", True), ("source_text", "Invented prohibited field.")):
            changed = body(review)
            changed["findings"][field] = value
            with self.subTest(finding=field), self.assertRaises(GameplayContractError):
                type(review).create(changed)

    def test_offline_load_and_rebuild_need_no_network_artifact_locator_or_raw_retention(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")))
            for module in ("source", "dependency_source", "object_control_source", "zone_change_source",
                           "zone_change_dependency_source", "bounded_casting_source", "bounded_mana_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + "._verified_bytes",
                                          side_effect=AssertionError("external source access forbidden")))
            stack.enter_context(patch("gameplay_rules.projection.bounded_mana_source.locate_bounded_mana_anchors",
                                      side_effect=AssertionError("fresh source location forbidden")))
            self.assertEqual(self.load(PACKAGE, review_root=REVIEWS), self.records)
            self.assertEqual(self.rebuild(self.records["projection.json"], review_root=REVIEWS), self.records)

    def test_new_construction_requires_artifact_instead_of_retained_anchor_hashes(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch("socket.socket", side_effect=AssertionError("network forbidden")), self.assertRaises(GameplayContractError):
                self.build(Path(tmp) / "missing.txt", review_root=REVIEWS)
        with self.assertRaises(GameplayContractError):
            self.rebuild(self.records["projection.json"].to_dict(), review_root=REVIEWS)

    def test_no_record_can_load_as_a_real_snapshot_or_execution_profile(self):
        from gameplay_rules.models import GameplayRulesSnapshot
        from gameplay_rules.snapshots import load_rules_snapshot
        for name, record in self.records.items():
            with self.subTest(record=name), self.assertRaises(GameplayContractError):
                GameplayRulesSnapshot.from_dict(record.to_dict())
            with self.assertRaises(GameplayContractError):
                load_rules_snapshot(PACKAGE / name)
            self.assertFalse(hasattr(record, "to_rules_snapshot"))
            self.assertFalse(hasattr(record, "to_execution_profile"))

    def test_manifest_binds_all_nine_prior_packages_81_units_and_historical_replay(self):
        value = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(value, self.manifest(self.records))
        self.assertEqual(value["canonical_base"], CANONICAL)
        self.assertEqual((value["projected_rule_count_before"], value["new_source_units_projected"],
                          value["projected_rule_count_after"]), (68, 13, 81))
        self.assertEqual(value["selected_references"], list(EXPECTED))
        self.assertEqual(value["additional_rules_projected"], [])
        self.assertEqual(set(value["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL)
        self.assertFalse(value["historical_anchors_changed"])
        self.assertFalse(value["real_profile_activated"])

    def test_package_contains_no_prose_examples_txt_or_external_paths(self):
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

    def test_tamper_missing_extra_txt_source_or_directory_rejected(self):
        for mutation in ("tamper", "missing", "txt", "source", "directory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                if mutation == "tamper":
                    path = root / "projection.json"
                    path.write_bytes(path.read_bytes().replace(b'"selected_rule_count":13', b'"selected_rule_count":14'))
                elif mutation == "missing":
                    (root / "family-closure-review.json").unlink()
                elif mutation == "directory":
                    (root / "extra").mkdir()
                else:
                    (root / ("source.txt" if mutation == "txt" else "source.json")).write_text("Invented extra sentinel.")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_symlink_hardlink_root_and_ancestor_links_rejected(self):
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
                    path = root / "family-closure-review.json"
                    held = parent / "held.json"
                    path.rename(held)
                    path.symlink_to(held) if kind == "symlink" else os.link(held, path)
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_noncanonical_record_or_manifest_serialization_rejected(self):
        for name in ("projection.json", "manifest.json"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / name
                path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2) + "\n")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_coherently_rehashed_false_review_cannot_bypass_independent_rebuild(self):
        changed = dict(self.records)
        review = changed["overall-readiness.json"]
        value = body(review)
        value["findings"]["unapproved_review_note"] = "Invented changed conclusion sentinel."
        changed["overall-readiness.json"] = type(review).create(value)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "rehashed"
            self.write(root, changed)
            with self.assertRaises(GameplayContractError):
                self.load(root, review_root=REVIEWS)

    def test_deterministic_offline_relocation_rebuild_and_append_only_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "relocated-reviews"
            shutil.copytree(REVIEWS, reviews)
            rebuilt = self.rebuild(self.records["projection.json"], review_root=reviews)
            self.assertEqual(rebuilt, self.records)
            root = Path(tmp) / "fresh"
            self.assertEqual(self.write(root, rebuilt), self.manifest(self.records))
            self.assertEqual(self.load(root, review_root=reviews), self.records)
            for name in FILES:
                self.assertEqual((root / name).read_bytes(), (PACKAGE / name).read_bytes())
            with self.assertRaises(GameplayContractError):
                self.write(root, rebuilt)

    @unittest.skipUnless(EXTERNAL_ARTIFACT, "external owner-controlled artifact not configured")
    def test_owner_artifact_reproduces_exact_package_and_no_selected_source_line_is_retained(self):
        from gameplay_rules.projection.bounded_mana_source import verify_bounded_mana_bytes
        with patch("socket.socket", side_effect=AssertionError("network forbidden")), \
             patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")):
            rebuilt = self.build(EXTERNAL_ARTIFACT, review_root=REVIEWS)
            source = Path(EXTERNAL_ARTIFACT).read_bytes()
            verify_bounded_mana_bytes(source)
        self.assertEqual(rebuilt, self.records)
        retained = [p.read_bytes() for p in PACKAGE.iterdir()]
        retained.extend(p.read_bytes() for p in CODE.glob("bounded_mana*.py"))
        retained.append(Path(__file__).read_bytes())
        doc = ROOT / "docs/GAMEPLAY_RULES_BOUNDED_MANA_ABILITY_PROJECTION.md"
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


class BoundedManaSemanticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value = json.loads((PACKAGE / "projection.json").read_bytes())
        cls.rules = {row["rule_reference"]: row for row in value["rules"]}
        cls.semantics = {ref: rule["semantic_distinctions"] for ref, rule in cls.rules.items()}

    def test_two_rule_defined_criteria_families_do_not_reduce_to_mana_output_heuristic(self):
        value = self.semantics["605.1"]
        self.assertEqual(value["classification_basis"], "ONE_COMPLETE_RULE_DEFINED_CRITERIA_SET")
        self.assertEqual(value["criteria_family_references"], ["605.1a", "605.1b"])
        self.assertFalse(value["produces_mana_alone_is_sufficient"])
        self.assertFalse(value["other_generated_effects_alone_remove_classification"])
        self.assertFalse(value["timing_restrictions_alone_remove_classification"])
        self.assertFalse(value["classification_implies_execution"])

    def test_structural_parent_child_relationships_are_separate_from_explicit_citations(self):
        children = {"605.1": ["605.1a", "605.1b"], "605.3": ["605.3a", "605.3b", "605.3c"],
                    "605.4": ["605.4a"], "605.5": ["605.5a", "605.5b"]}
        for parent, refs in children.items():
            found = [row["reference"] for row in self.rules[parent]["family_relationships"]
                     if row["relation"] == "STRUCTURAL_SELECTED_CHILD"]
            self.assertEqual(found, refs)
            for child in refs:
                parents = [row["reference"] for row in self.rules[child]["family_relationships"]
                           if row["relation"] == "STRUCTURAL_SELECTED_PARENT"]
                self.assertEqual(parents, [parent])
        self.assertEqual(self.rules["605.2"]["family_relationships"], [])
        self.assertEqual(self.rules["605.1"]["direct_dependency_references"], [])

    def test_activated_criteria_all_required_and_replacement_distinction_explicit(self):
        value = self.semantics["605.1a"]
        self.assertEqual(value["ability_kind"], "ACTIVATED")
        self.assertTrue(value["all_criteria_required"])
        self.assertFalse(value["requires_target"])
        self.assertTrue(value["could_add_mana_to_player_pool_on_resolution"])
        for field in ("is_loyalty_ability", "cost_moves_card_to_or_from_library", "effect_moves_card_to_or_from_library"):
            self.assertFalse(value[field])
        self.assertEqual(value["applicable_replacement_effects_considered"], "SELF_REPLACEMENT_ONLY")
        self.assertTrue(value["other_applicable_replacement_effects_ignored_for_classification"])
        self.assertTrue(value["classification_distinct_from_current_mana_output"])
        self.assertTrue(value["classification_distinct_from_activation_eligibility"])

    def test_triggered_criteria_preserve_three_qualifying_relationships_and_activated_backlink(self):
        value = self.semantics["605.1b"]
        self.assertEqual(value["ability_kind"], "TRIGGERED")
        self.assertTrue(value["all_criteria_required"])
        self.assertFalse(value["requires_target"])
        self.assertTrue(value["could_add_mana_to_player_pool_on_resolution"])
        self.assertEqual(value["qualifying_trigger_relationships"], ["ACTIVATED_MANA_ABILITY_ACTIVATION",
                         "ACTIVATED_MANA_ABILITY_RESOLUTION", "MANA_ADDED_TO_POOL"])
        self.assertEqual(value["activated_mana_classification_reference"], "605.1a")
        self.assertTrue(value["activated_and_triggered_classification_are_distinct"])
        self.assertFalse(value["trigger_detection_implemented"])

    def test_persistent_classification_does_not_claim_current_output_or_eligibility(self):
        value = self.semantics["605.2"]
        self.assertEqual(value["classification"], "MANA_ABILITY")
        self.assertEqual(value["current_activation_eligibility"], "SEPARATE_UNKNOWN_DIMENSION")
        self.assertEqual(value["current_productive_output"], "SEPARATE_UNKNOWN_DIMENSION")
        self.assertFalse(value["inability_to_produce_mana_alone_removes_classification"])
        self.assertFalse(value["classification_implies_current_output"])
        self.assertFalse(value["classification_implies_current_activation_eligibility"])
        self.assertFalse(value["example_content_retained"])

    def test_activated_parent_retains_general_activation_and_five_opportunity_categories(self):
        parent = self.semantics["605.3"]
        self.assertEqual(parent["ordinary_activation_dependency"], "602.2")
        self.assertEqual(parent["special_exception_references"], ["605.3a", "605.3b", "605.3c"])
        self.assertFalse(parent["selected_exceptions_satisfy_general_activation"])
        value = self.semantics["605.3a"]
        self.assertEqual(value["activation_opportunity_categories"], ["ORDINARY_PRIORITY", "SPELL_CASTING_MANA_PAYMENT",
                         "ABILITY_ACTIVATION_MANA_PAYMENT", "RULE_REQUESTED_MANA_PAYMENT", "EFFECT_REQUESTED_MANA_PAYMENT"])
        self.assertEqual(value["request_may_occur_during"], ["SPELL_CASTING", "SPELL_RESOLUTION", "ABILITY_ACTIVATION",
                         "ABILITY_RESOLUTION"])
        self.assertTrue(value["eligibility_categories_only"])
        self.assertFalse(value["priority_implemented"])
        self.assertFalse(value["activation_window_evaluation_implemented"])

    def test_activated_immediate_behavior_and_same_ability_reactivation_boundary_are_descriptive(self):
        value = self.semantics["605.3b"]
        self.assertFalse(value["actual_stack_entry"])
        self.assertEqual(value["resolution_sequence"], "IMMEDIATELY_AFTER_ACTIVATION")
        for key in ("targetable_as_stack_object", "counterable_as_stack_object", "respondable_as_stack_object",
                    "stack_bypass_runtime_implemented"):
            self.assertFalse(value[key])
        self.assertEqual(value["stack_exception_reference"], "405.6c")
        repeat = self.semantics["605.3c"]
        self.assertEqual(repeat["restriction_begins"], "ACTIVATION_START")
        self.assertEqual(repeat["restricted_subject"], "SAME_ABILITY")
        self.assertEqual(repeat["restriction_ends"], "THAT_ACTIVATION_RESOLVED")
        self.assertFalse(repeat["same_ability_reactivation_before_resolution"])
        self.assertFalse(repeat["general_activation_sequence_supplied"])
        self.assertFalse(repeat["activation_lock_implemented"])

    def test_triggered_immediate_exception_does_not_supply_general_trigger_priority_or_stack_runtime(self):
        parent = self.semantics["605.4"]
        self.assertEqual(parent["ordinary_trigger_dependency"], "603")
        self.assertFalse(parent["selected_exception_satisfies_general_trigger_semantics"])
        value = self.semantics["605.4a"]
        self.assertEqual(value["resolution_sequence"], "IMMEDIATELY_AFTER_CAUSING_MANA_ABILITY")
        for key in ("actual_stack_entry", "waits_for_priority", "targetable_as_stack_object", "counterable_as_stack_object",
                    "respondable_as_stack_object", "trigger_sequence_runtime_implemented", "example_content_retained"):
            self.assertFalse(value[key])

    def test_criteria_failure_targeted_wrong_trigger_and_no_output_exclusions_are_present(self):
        parent = self.semantics["605.5"]
        self.assertEqual(parent["criteria_references"], ["605.1a", "605.1b"])
        self.assertEqual(parent["neither_criteria_set_satisfied"], "NOT_MANA_ABILITY")
        value = self.semantics["605.5a"]
        for key in ("target_required", "wrong_trigger_relationship", "mana_activation_trigger_without_possible_mana_output"):
            self.assertEqual(value[key], "NOT_MANA_ABILITY")
        self.assertEqual(value["qualifying_trigger_criteria_reference"], "605.1b")
        self.assertFalse(value["exclusions_override_selected_complete_trigger_criteria"])
        self.assertTrue(value["ordinary_procedure_is_semantic_boundary_not_numbered_citation"])
        self.assertEqual(self.rules["605.5a"]["direct_dependency_references"], [])

    def test_spell_with_mana_effect_is_excluded_without_oracle_or_real_card_ingestion(self):
        value = self.semantics["605.5b"]
        self.assertFalse(value["spell_is_mana_ability"])
        self.assertFalse(value["spell_that_adds_mana_equals_mana_ability"])
        self.assertTrue(value["spell_casting_and_resolution_remain_separate"])
        self.assertEqual(value["historical_context"], "HISTORICAL_ORACLE_CONTEXT_NOT_INGESTED")

    def test_all_semantics_are_descriptive_without_classification_execution_or_authority_inheritance(self):
        for value in self.semantics.values():
            self.assertTrue(value["descriptive_only"])
            self.assertEqual(value["runtime_operations_implemented"], [])
            self.assertFalse(value["classification_execution_implemented"])
            self.assertFalse(value["source_coverage_implies_semantic_closure"])
            self.assertFalse(value["source_coverage_implies_execution"])
            self.assertFalse(value["fictional_mana_satisfies_real_605_execution"])


class BoundedManaReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.projection.bounded_mana_package import load_bounded_mana_package
        cls.records = load_bounded_mana_package(PACKAGE, review_root=REVIEWS)
        cls.rules = {r["rule_reference"]: r for r in cls.records["projection.json"].to_dict()["rules"]}
        cls.findings = {name: record.to_dict()["findings"] for name, record in cls.records.items()
                        if name != "projection.json"}

    def test_correspondence_keeps_prior_design_authority_historical_and_binds_verified_rule_identities(self):
        value = self.findings["design-source-correspondence.json"]
        self.assertEqual(value["historical_design_package_id"], PRIOR_PACKAGES["gameplay-rules-mana-ability-design"])
        self.assertEqual(value["historical_design_authority_unchanged"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
        self.assertEqual(value["new_evidence_authority"], "EXACT_ARTIFACT_AND_SELECTED_BLOCKS_VERIFIED")
        self.assertFalse(value["historical_design_package_mutated"])
        for row in value["observations"]:
            self.assertEqual(row["historical_authority"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
            self.assertTrue(row["source_rule_bindings"])
            for binding in row["source_rule_bindings"]:
                self.assertEqual(binding["rule_id"], self.rules[binding["rule_reference"]]["rule_id"])

    def test_all_requested_observations_verified_or_refined_and_new_boundaries_kept_explicit(self):
        value = self.findings["design-source-correspondence.json"]
        rows = {row["observation"]: row for row in value["observations"]}
        required = {
            "activated_vs_triggered_classification", "no_target_requirements", "could_add_mana", "loyalty_exclusion",
            "library_movement_exclusion", "replacement_effect_distinction", "triggered_qualifying_relationships",
            "classification_persistence", "priority_activation_window", "spell_payment_activation_window",
            "ability_payment_activation_window", "rule_or_effect_payment_request", "activated_no_stack_behavior",
            "activated_immediate_resolution", "reactivation_prohibition", "triggered_no_stack_behavior",
            "triggered_immediate_sequencing", "triggered_no_priority_wait", "explicit_non_mana_cases", "spell_exclusion",
        }
        self.assertTrue(required <= set(rows))
        self.assertEqual(value["semantic_observation_counts"], {
            "VERIFIED": 17, "VERIFIED_WITH_REFINEMENT": 3, "DID_NOT_VERIFY": 0, "FOUND_ADDITIONAL_BOUNDARY": 5})
        self.assertEqual(value["semantic_observations_contradicted"], [])
        for name in ("replacement_effect_distinction", "rule_or_effect_payment_request", "explicit_non_mana_cases"):
            self.assertEqual(rows[name]["finding"], "VERIFIED_WITH_REFINEMENT")
        for name in ("general_activated_procedure", "general_triggered_procedure", "historical_oracle_context",
                     "exclusion_trigger_wording_requires_family_context"):
            self.assertEqual(rows[name]["finding"], "FOUND_ADDITIONAL_BOUNDARY")

    def test_verified_examples_are_hash_only_and_owned_by_exactly_two_selected_rules(self):
        rows = self.findings["design-source-correspondence.json"]["example_ownership"]
        self.assertEqual([row["rule_reference"] for row in rows], ["605.2", "605.4a"])
        for row in rows:
            self.assertEqual(row["state"], "UNAMBIGUOUS_SELECTED_RULE_OWNERSHIP")
            self.assertEqual(row["source_anchor"], self.rules[row["rule_reference"]]["source_anchor"])
            self.assertTrue(row["included_in_block_hash"])
            self.assertFalse(row["example_prose_retained"])

    def test_fixed_family_completeness_resolves_section_reference_without_creating_a_605_rule(self):
        value = self.findings["family-closure-review.json"]
        self.assertEqual(value["section_reference"], "605")
        self.assertEqual(value["selected_family_references"], list(EXPECTED))
        self.assertEqual(value["rule_count"], 13)
        self.assertEqual(value["section_reference_state"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertTrue(value["complete_relevant_local_family"])
        self.assertEqual(value["family_completeness_evidence"], "EXACT_ARTIFACT_RELEASE_SPECIFIC_FAMILY_SHAPE_VERIFIED")
        for key in ("section_heading_is_source_unit", "synthetic_real_605_rule_created",
                    "section_resolution_is_concrete_rule_projection", "section_coverage_implies_semantic_closure",
                    "section_coverage_implies_execution"):
            self.assertFalse(value[key])
        rows = value["family_rows"]
        self.assertEqual([row["rule_reference"] for row in rows], list(EXPECTED))
        self.assertEqual(len({row["rule_id"] for row in rows}), 13)
        for row in rows:
            self.assertEqual(row["rule_id"], self.rules[row["rule_reference"]]["rule_id"])
            self.assertEqual(row["coverage_state"], "SELECTED_AND_PROJECTED")

    def test_verified_frontier_matches_only_actual_numbered_citations_and_leaves_five_external_targets_open(self):
        value = self.findings["family-closure-review.json"]
        rows = value["verified_numbered_dependency_findings"]
        expected = {(source, target) for source, targets in EXPLICIT.items() for target in targets}
        self.assertEqual({(row["from_reference"], row["target_reference"]) for row in rows}, expected)
        self.assertEqual(len(rows), len(expected))
        self.assertEqual(set(value["verified_unresolved_direct_references"]), FRONTIER)
        for row in rows:
            self.assertEqual(row["from_rule_id"], self.rules[row["from_reference"]]["rule_id"])
            self.assertEqual(row["evidence_basis"], "VERIFIED_SELECTED_SOURCE_BLOCK_CITATION")
            selected = row["target_reference"] in EXPECTED
            self.assertEqual(row["reference_state"], "DIRECT_REFERENCE_RESOLVED" if selected else "UNRESOLVED")
            self.assertEqual(row["coverage_state"], "PROJECTED_IN_THIS_MILESTONE" if selected else "UNPROJECTED")

    def test_both_consumer_section_reassessments_preserve_historical_dependency_arrays_and_block_execution(self):
        old = prior_rules()
        family = self.findings["family-closure-review.json"]
        consumers = self.findings["consumer-reassessment.json"]
        self.assertEqual([r["rule_reference"] for r in family["broad_dependency_reassessments"]], ["601.2g", "109.4a"])
        for rows in (family["broad_dependency_reassessments"], consumers["consumer_reassessments"]):
            for row in rows:
                ref = row["rule_reference"]
                self.assertEqual(row["previous_explicit_dependency"], "605")
                self.assertEqual(row["historical_consumer_binding"]["rule_id"], old[ref]["rule_id"])
                self.assertEqual(row["new_section_reference_state"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
                self.assertEqual(row["new_dependency_evidence"],
                                 [{"rule_reference": ref, "rule_id": self.rules[ref]["rule_id"]} for ref in EXPECTED])
                for key in ("concrete_source_unit_named_605_created", "historical_direct_dependency_array_rewritten",
                            "historical_rule_reprojected", "historical_rule_mutated", "section_coverage_implies_semantic_closure",
                            "section_coverage_implies_execution", "execution_ready", "runtime_implemented"):
                    self.assertFalse(row[key])
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")

    def test_casting_consumer_gains_source_coverage_while_production_pool_payment_and_general_casting_remain_open(self):
        value = self.findings["consumer-reassessment.json"]["consumer_reassessments"][0]
        self.assertEqual(value["rule_reference"], "601.2g")
        self.assertEqual(set(value["source_coverage_improvements"]), {
            "mana_ability_classification", "special_activation_windows", "activated_no_stack_and_immediate_behavior"})
        self.assertEqual(set(value["remaining_unresolved_numbered_dependencies"]), FRONTIER)
        self.assertTrue({"mana_production_semantics", "mana_pool_semantics", "payment_integration", "overall_casting_gaps",
                         "real_ability_and_card_semantics"} <= set(value["remaining_semantic_boundaries"]))

    def test_controller_consumer_keeps_as_if_stack_attribution_separate_from_actual_stack_presence(self):
        value = self.findings["consumer-reassessment.json"]["consumer_reassessments"][1]
        self.assertEqual(value["rule_reference"], "109.4a")
        self.assertIn("hypothetical_stack_controller_attribution", value["required_future_primitives"])
        self.assertIn("general_ability_controller_semantics", value["remaining_semantic_boundaries"])
        self.assertFalse(value["actual_stack_presence_required_for_attribution"])
        self.assertFalse(value["hypothetical_stack_attribution_supplied_by_605"])
        self.assertTrue(value["controller_attribution_separate_from_casting"])

    def test_madness_path_is_indirect_and_preserves_existing_madness_and_zone_lookup_identities(self):
        value = self.findings["consumer-reassessment.json"]
        self.assertEqual(value["madness_indirect_path"], ["702.35b", "BOUNDED_CASTING_PROJECTION", "601.2g", "605"])
        self.assertEqual(value["madness_flow_kind"], "INDIRECT_DEPENDENCY_FLOW")
        self.assertFalse(value["madness_direct_605_citation_created"])
        old = prior_rules()
        for row in value["retained_madness_rules"]:
            self.assertEqual(row["rule_id"], old[row["rule_reference"]]["rule_id"])
        lookup = value["retained_zone_change_lookup"]
        self.assertEqual(lookup["rule_id"], old["400.7k"]["rule_id"])
        self.assertEqual(value["fictional_authority_finding"], "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605")

    def test_classification_coverage_remains_open_for_target_loyalty_library_replacements_and_card_semantics(self):
        value = self.findings["classification-readiness.json"]
        self.assertEqual(value["capability_id"], "mana_ability_classification")
        self.assertEqual(value["source_coverage"], "REPRESENTED_WITH_OPEN_DEPENDENCIES")
        self.assertEqual([r["rule_reference"] for r in value["selected_source_bindings"]],
                         ["605.1", "605.1a", "605.1b", "605.2", "605.5", "605.5a", "605.5b"])
        self.assertTrue(value["activated_and_triggered_criteria_distinct"])
        self.assertTrue(value["classification_current_output_and_activation_separate"])
        for key in ("produces_mana_alone_is_sufficient", "classification_implies_current_output",
                    "classification_implies_current_activation", "classification_implies_execution",
                    "spell_that_adds_mana_is_mana_ability", "runtime_implemented", "execution_ready"):
            self.assertFalse(value[key])
        self.assertEqual(value["semantic_closure"], "OPEN")
        self.assertEqual(value["execution_readiness"], "EXECUTION_BLOCKED")

    def test_activated_and_triggered_behavior_source_coverage_have_separate_nonexecutable_capabilities(self):
        value = self.findings["behavior-readiness.json"]
        rows = {row["capability_id"]: row for row in value["capabilities"]}
        self.assertEqual(set(rows), {"activated_mana_ability_activation_window",
                         "activated_mana_ability_immediate_resolution", "triggered_mana_ability_immediate_resolution"})
        for row in rows.values():
            self.assertEqual(row["source_coverage"], "REPRESENTED_WITH_OPEN_DEPENDENCIES")
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["implementation_status"], "NOT_IMPLEMENTED")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
            self.assertFalse(row["runtime_implemented"])
        self.assertEqual(value["activated_behavior_source_references"], ["605.3", "605.3a", "605.3b", "605.3c"])
        self.assertEqual(value["triggered_behavior_source_references"], ["605.4", "605.4a"])
        for field in ("activated_uses_stack", "triggered_uses_stack", "triggered_waits_for_priority",
                      "same_ability_reactivation_before_resolution_permitted", "general_activated_abilities_covered",
                      "general_triggered_abilities_covered"):
            self.assertFalse(value[field])

    def test_all_eight_capabilities_retain_independent_requirements_primitives_and_execution_blockers(self):
        value = self.findings["overall-readiness.json"]
        rows = {row["capability_id"]: row for row in value["capabilities"]}
        self.assertEqual(set(rows), {"mana_ability_classification", "activated_mana_ability_activation_window",
                         "activated_mana_ability_immediate_resolution", "triggered_mana_ability_immediate_resolution",
                         "mana_ability_controller_attribution", "mana_payment_opportunity", "mana_production_semantics",
                         "mana_pool_semantics"})
        for row in rows.values():
            self.assertTrue(row["evidence_requirements"])
            self.assertTrue(row["semantic_dependencies"])
            self.assertTrue(row["required_future_primitives"])
            self.assertTrue(row["unsupported_boundaries"])
            self.assertEqual(row["implementation_status"], "NOT_IMPLEMENTED")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
            self.assertFalse(row["source_coverage_implies_execution"])
            self.assertFalse(row["required_primitives_available"])
            self.assertEqual(row["real_execution_primitives_available"], [])
        self.assertFalse(value["one_capability_readiness_implies_another"])
        for field in ("source_coverage_implies_execution", "source_coverage_implies_general_activated_abilities",
                      "source_coverage_implies_general_triggered_abilities"):
            self.assertFalse(value[field])

    def test_source_coverage_does_not_erase_external_or_controller_evidence_requirements(self):
        value = self.findings["overall-readiness.json"]
        rows = {row["capability_id"]: row for row in value["capabilities"]}
        self.assertIn("FUTURE_TARGET_LOYALTY_LIBRARY_REPLACEMENT_SCOPE_EVIDENCE",
                      rows["mana_ability_classification"]["evidence_requirements"])
        self.assertIn("REAL_ABILITY_AND_EFFECT_SEMANTICS",
                      rows["mana_ability_classification"]["evidence_requirements"])
        self.assertIn("SEPARATE_GENERAL_ABILITY_CONTROLLER_SOURCE_REVIEW",
                      rows["mana_ability_controller_attribution"]["evidence_requirements"])
        self.assertIn("FUTURE_GENERAL_ACTIVATED_PROCEDURE_REVIEW",
                      rows["activated_mana_ability_immediate_resolution"]["evidence_requirements"])
        self.assertIn("FUTURE_STACK_EXCEPTION_REVIEW",
                      rows["activated_mana_ability_immediate_resolution"]["evidence_requirements"])
        self.assertIn("FUTURE_GENERAL_TRIGGERED_ABILITY_REVIEW",
                      rows["triggered_mana_ability_immediate_resolution"]["evidence_requirements"])
        for row in rows.values():
            self.assertTrue(row["prior_design_evidence_requirements"])
            self.assertEqual(row["implied_ready_capabilities"], [])
            self.assertFalse(row["fictional_runtime_authority_inherited"])

    def test_production_pool_and_payment_remain_outside_source_family_execution_and_fictional_authority(self):
        value = self.findings["overall-readiness.json"]
        rows = {row["capability_id"]: row for row in value["capabilities"]}
        for name in ("mana_production_semantics", "mana_pool_semantics"):
            self.assertEqual(rows[name]["source_coverage"], "OUTSIDE_605_FAMILY_COVERAGE")
            self.assertEqual(rows[name]["selected_source_bindings"], [])
            self.assertFalse(rows[name]["source_verified"])
        text = json.dumps(value["production_pool_payment_boundaries"])
        self.assertIn("BLOCKED", text)
        self.assertIn("mana_production", text)
        self.assertIn("mana_pool", text)
        self.assertIn("payment", text)
        self.assertFalse(value["fictional_mana_satisfies_real_605"])
        self.assertIn("FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605", json.dumps(value["fictional_authority"]))

    def test_five_capability_reassessments_and_real_execution_profile_stay_blocked(self):
        value = self.findings["overall-readiness.json"]
        rows = value["readiness_reassessments"]
        self.assertEqual([row["capability_id"] for row in rows], ["mana_abilities", "alternative_cost_casting_subprocedure",
                         "complete_spell_casting", "object_control", "madness"])
        for row in rows:
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
            self.assertFalse(row["execution_ready"])
            self.assertFalse(row["runtime_implemented"])
            self.assertTrue(row["blockers"])
        self.assertEqual(value["readiness_code"], "REAL_EXECUTION_PROFILE_NOT_READY")
        self.assertEqual(value["target_profile_id"], "magic-comprehensive-rules-20260925-v1")
        self.assertEqual(value["unprojected_casting_stages"], ["601.2a", "601.2c", "601.2d", "601.2e", "601.2i"])
        self.assertEqual(value["unresolved_permission_and_rollback"], ["601.3", "733"])

    def test_old_blockers_plus_five_new_external_targets_remain_unprojected_without_unresolved_broad_605(self):
        value = self.findings["overall-readiness.json"]
        remaining = set(value["remaining_unprojected_numbered_boundaries"])
        self.assertEqual(remaining, OLD_BLOCKERS | FRONTIER)
        self.assertNotIn("605", remaining)
        self.assertTrue(set(EXPECTED).isdisjoint(remaining))
        self.assertEqual(set(self.findings["composite-coverage.json"]["remaining_unresolved_rules"]), remaining)

    def test_readonly_composite_preserves_seven_distinct_projection_and_package_identities_exactly_81(self):
        from gameplay_rules.projection.bounded_mana_package import composite_coverage_view, package_manifest
        value = self.findings["composite-coverage.json"]
        self.assertEqual(value["view_kind"], "READ_ONLY_SEVEN_PROJECTION_COMPOSITE")
        self.assertEqual((value["previous_projected_rule_count"], value["new_projected_rule_count"],
                          value["total_projected_rule_count"]), (68, 13, 81))
        self.assertEqual(value["component_rule_counts"], [20, 12, 7, 12, 12, 5, 13])
        refs = value["projected_references"]
        self.assertEqual(len(refs), 81)
        self.assertEqual(len(set(refs)), 81)
        self.assertEqual(refs[-13:], list(EXPECTED))
        self.assertNotIn("605", refs)
        self.assertTrue((OLD_BLOCKERS | FRONTIER).isdisjoint(refs))
        self.assertEqual(value["resolved_section_references"], ["605"])
        components = value["projection_components"]
        self.assertEqual(len({row["projection_id"] for row in components}), 7)
        self.assertTrue(all(not row["mutated"] for row in components))
        self.assertTrue(value["component_identities_preserved"])
        before = {name: record.serialize() for name, record in self.records.items()}
        manifest = package_manifest(self.records)
        view = composite_coverage_view(self.records, manifest)
        self.assertEqual(len({row["package_id"] for row in view["projection_components"]}), 7)
        self.assertEqual(view["projection_components"][-1]["package_id"], manifest["package_id"])
        self.assertEqual(before, {name: record.serialize() for name, record in self.records.items()})
        with self.assertRaises(GameplayContractError):
            composite_coverage_view(self.records, dict(manifest, package_id=OTHER))

    def test_exactly_one_next_milestone_is_design_of_verified_frontier_not_authorized_or_started(self):
        value = self.findings["overall-readiness.json"]["next_milestone"]
        self.assertEqual(value["candidate"], "Mana Ability Direct Dependency Design")
        self.assertEqual(set(value["exact_proposed_scope"]), FRONTIER)
        self.assertEqual(len(value["exact_proposed_scope"]), 5)
        self.assertFalse(value["source_txt_required"])
        self.assertTrue(value["future_source_projection_requires_verified_artifact"])
        self.assertEqual(value["new_source_units_authorized"], 0)
        self.assertFalse(value["authorized"])
        self.assertFalse(value["started"])
        self.assertEqual(value["source_basis"], "RETAINED_VERIFIED_FRONTIER_ONLY_NOT_NEW_TARGET_SOURCE_KNOWLEDGE")


if __name__ == "__main__":
    unittest.main()
