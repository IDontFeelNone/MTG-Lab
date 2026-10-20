"""Design contracts and canonical preservation; no gameplay execution.

The optional external-artifact test is the only fresh source-inspection proof.
Offline reproduction verifies retained metadata and must never substitute for it.
"""
import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

from activated_ability_preservation import (
    NEW_REVIEW_PATHS, NEW_SOURCE_PATHS, is_design_addition,
)
from evidence.contracts import deterministic_json
from gameplay_rules.activated_ability_design import inspection
from gameplay_rules.activated_ability_design import package as pkg
from gameplay_rules.errors import GameplayContractError


ROOT = Path(__file__).resolve().parents[1]
REVIEWS = ROOT / "reference-reviews"
PACKAGE = REVIEWS / "gameplay-rules-activated-ability-procedure-design"
CODE = ROOT / "src/gameplay_rules/activated_ability_design"
CANONICAL_MAIN = "9e1335d53458913dec1907e2922b9e99339cc3c5"
RECORD_NAMES = {
    "source-correspondence.json", "local-scope.json",
    "procedure-responsibilities.json", "casting-import.json",
    "mana-relationships.json", "consumer-bindings.json", "readiness.json",
}
SOURCE_ENV = "MTG_ACTIVATED_ABILITY_SOURCE"


def canonical_bytes(value):
    return (deterministic_json(value) + "\n").encode("utf-8")


def inherited_projections():
    """Inspect retained projection records without modifying their evidence."""
    return [json.loads(p.read_bytes()) for p in sorted(REVIEWS.glob("gameplay-rules-*/projection.json"))]


def paths_to(value, predicate, prefix=()):
    if predicate(value):
        yield prefix
    if type(value) is dict:
        for key, item in value.items():
            yield from paths_to(item, predicate, (*prefix, key))
    elif type(value) is list:
        for index, item in enumerate(value):
            yield from paths_to(item, predicate, (*prefix, index))


def replace_at(value, path, replacement):
    target = value
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = replacement


class SourceInspectionTests(unittest.TestCase):
    def test_candidate_scope_and_import_members_are_exact(self):
        self.assertEqual(inspection.CANDIDATE_REFERENCES, ("602.2", "602.2a", "602.2b"))
        self.assertEqual(inspection.IMPORTED_STAGES, tuple("601.2" + s for s in "bcdefghi"))
        self.assertNotIn("601.2a", inspection.IMPORTED_STAGES)

    def test_missing_or_invalid_source_has_no_metadata_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            absent = Path(td) / "absent.txt"
            invalid = Path(td) / "invalid.txt"
            invalid.write_bytes(b"Project-authored invalid source fixture.\n")
            for path in (None, absent, invalid):
                with self.subTest(kind="missing" if path != invalid else "invalid"):
                    with self.assertRaises(GameplayContractError):
                        pkg.build_package(path, review_root=REVIEWS)
            with self.assertRaises(GameplayContractError):
                inspection.verify_bytes(invalid.read_bytes())

    def test_configured_invalid_source_cannot_be_a_skip(self):
        with tempfile.TemporaryDirectory() as td:
            invalid = Path(td) / "invalid.txt"
            invalid.write_bytes(b"Project-authored invalid artifact.\n")
            with self.assertRaises(GameplayContractError):
                inspection.inspect_source(invalid)

    def test_actual_external_source_inspection(self):
        configured = os.environ.get(SOURCE_ENV)
        if configured is None:
            self.skipTest("external TXT unavailable: no fresh activated-procedure source verification")
        # Empty, missing and mismatched configured paths fail instead of skip.
        result = inspection.inspect_source(configured)
        self.assertEqual(canonical_bytes(result), canonical_bytes(inspection.expected_inspection()))
        records = pkg.build_package(configured, review_root=REVIEWS)
        self.assertEqual(canonical_bytes(records), canonical_bytes(pkg.rebuild_package(review_root=REVIEWS)))
        pkg.verify_source(records, configured, review_root=REVIEWS)


class PackageBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = pkg.rebuild_package(review_root=REVIEWS)

    def test_seven_records_have_content_bound_distinct_identities(self):
        self.assertEqual(set(self.records), RECORD_NAMES)
        identities = []
        for name, record in self.records.items():
            with self.subTest(record=name):
                body = {key: value for key, value in record.items() if key != "review_id"}
                self.assertEqual(record, pkg.identify_record(body))
                self.assertEqual(record["record_kind"], name)
                identities.append(record["review_id"])
        self.assertEqual(len(set(identities)), 7)

    def test_valid_write_load_rebuild_and_relocation_are_canonical(self):
        original = copy.deepcopy(self.records)
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "new-package"
            manifest = pkg.write_package(target, self.records, review_root=REVIEWS)
            self.assertEqual(set(p.name for p in target.iterdir()), RECORD_NAMES | {"manifest.json"})
            self.assertEqual(manifest, pkg.manifest(self.records))
            loaded = pkg.load_package(target, review_root=REVIEWS)
            self.assertEqual(canonical_bytes(loaded), canonical_bytes(original))
            for name in RECORD_NAMES:
                self.assertEqual((target / name).read_bytes(), canonical_bytes(original[name]))
            self.assertEqual((target / "manifest.json").read_bytes(), canonical_bytes(manifest))
            relocated = Path(td) / "relocated"
            shutil.copytree(target, relocated)
            self.assertEqual(pkg.load_package(relocated, review_root=REVIEWS), original)
        self.assertEqual(self.records, original)

    def test_retained_package_matches_offline_rebuild_without_fresh_source_claim(self):
        loaded = pkg.load_package(PACKAGE, review_root=REVIEWS)
        self.assertEqual(canonical_bytes(loaded), canonical_bytes(self.records))
        self.assertFalse((PACKAGE / "projection.json").exists())

    def assertRejectedBeforeWrite(self, candidate):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "must-not-exist" / "package"
            with self.assertRaises(GameplayContractError):
                pkg.write_package(target, candidate, review_root=REVIEWS)
            self.assertFalse(target.parent.exists())

    def test_record_identity_changes_are_rejected_before_directory_creation(self):
        for name in RECORD_NAMES:
            candidate = copy.deepcopy(self.records)
            candidate[name]["review_id"] = "sha256:" + "0" * 64
            with self.subTest(record=name):
                self.assertRejectedBeforeWrite(candidate)

    def test_rehashed_authored_findings_cannot_acquire_authority(self):
        candidate = copy.deepcopy(self.records)
        record = candidate["local-scope.json"]
        record["findings"]["current_605.3_to_602.2"] = "DIRECT_REFERENCE_RESOLVED"
        candidate["local-scope.json"] = pkg.identify_record(record)
        self.assertRejectedBeforeWrite(candidate)
        with self.assertRaises(GameplayContractError):
            pkg.manifest(candidate)

    def test_plain_json_types_are_required_without_python_subclass_coercion(self):
        class DictSubclass(dict):
            pass

        class ListSubclass(list):
            pass

        class IntSubclass(int):
            pass

        class StrSubclass(str):
            pass

        for value in (DictSubclass(), {"value": ListSubclass()}, {"value": IntSubclass(1)},
                      {"value": StrSubclass("text")}, {"value": b"bytes"}, {"value": (1,)},
                      {"value": float("inf")}):
            with self.subTest(kind=type(value).__name__), self.assertRaises(GameplayContractError):
                pkg.identify_record(value)

    def test_returned_records_and_bindings_do_not_alias_immutable_inputs(self):
        first = pkg.rebuild_package(review_root=REVIEWS)
        first["local-scope.json"]["findings"]["candidate_references"].append("603")
        self.assertEqual(pkg.rebuild_package(review_root=REVIEWS), self.records)
        binding = pkg.retained_binding()
        binding["rule_bindings"].clear()
        self.assertTrue(pkg.retained_binding()["rule_bindings"])

    def test_json_distinct_numeric_substitutions_rejected_even_after_rehash(self):
        # Python equality accepts False == 0 == 0.0 and True == 1 == 1.0.
        # Exercise both envelope and nested authored/inspection values after
        # recomputing the identity, so an old identity cannot mask the defect.
        kinds = (
            (lambda v: type(v) is bool and v is False, (0, 0.0)),
            (lambda v: type(v) is bool and v is True, (1, 1.0)),
            (lambda v: type(v) is int and v == 1, (True, 1.0)),
            (lambda v: type(v) is int and v > 1, (None,)),
        )
        for predicate, replacements in kinds:
            matches = [(name, path) for name, record in self.records.items()
                       for path in paths_to(record, predicate)]
            self.assertTrue(matches)
            # One envelope and one nested representative per kind, if present.
            selected = [matches[0]]
            nested = next((item for item in matches if len(item[1]) > 1), None)
            if nested and nested not in selected:
                selected.append(nested)
            for name, path in selected:
                for replacement in replacements:
                    candidate = copy.deepcopy(self.records)
                    old = candidate[name]
                    for key in path:
                        old = old[key]
                    new = float(old) if replacement is None else replacement
                    replace_at(candidate[name], path, new)
                    candidate[name] = pkg.identify_record({k: v for k, v in candidate[name].items()
                                                           if k != "review_id"})
                    with self.subTest(record=name, path=path, substitute=type(new).__name__):
                        self.assertRejectedBeforeWrite(candidate)

    def test_malformed_containers_and_fields_rejected_without_coercion(self):
        candidates = [[], tuple(self.records.items()), {**self.records, "extra.json": {}}]
        for mutate in (lambda r: r.pop(next(iter(r))),
                       lambda r: r["readiness.json"].update({1: "nonstring-key"}),
                       lambda r: r["readiness.json"].update({"findings": ()}),
                       lambda r: r["readiness.json"].update({"schema_version": float("nan")})):
            value = copy.deepcopy(self.records)
            mutate(value)
            candidates.append(value)
        for candidate in candidates:
            with self.subTest(kind=type(candidate).__name__):
                self.assertRejectedBeforeWrite(candidate)

    def test_write_is_append_only_and_rejects_symlink_destinations(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "package"
            pkg.write_package(target, self.records, review_root=REVIEWS)
            before = {p.name: p.read_bytes() for p in target.iterdir()}
            with self.assertRaises(GameplayContractError):
                pkg.write_package(target, self.records, review_root=REVIEWS)
            self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
            link = Path(td) / "link"
            link.symlink_to(target, target_is_directory=True)
            with self.assertRaises(GameplayContractError):
                pkg.write_package(link / "nested", self.records, review_root=REVIEWS)
            self.assertFalse((target / "nested").exists())

    def test_load_rejects_noncanonical_bytes_extra_files_and_links(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for mode in ("whitespace", "duplicate", "extra", "symlink"):
                target = base / mode
                pkg.write_package(target, self.records, review_root=REVIEWS)
                name = "readiness.json"
                if mode == "whitespace":
                    (target / name).write_bytes(b" " + (target / name).read_bytes())
                elif mode == "duplicate":
                    raw = (target / name).read_bytes()
                    (target / name).write_bytes(b'{"schema_version":1,' + raw[1:])
                elif mode == "extra":
                    (target / "extra.json").write_bytes(b"{}\n")
                else:
                    (target / name).unlink()
                    (target / name).symlink_to(PACKAGE / name)
                with self.subTest(mode=mode), self.assertRaises(GameplayContractError):
                    pkg.load_package(target, review_root=REVIEWS)

    def test_manifest_numeric_substitutions_are_rejected_on_load(self):
        with tempfile.TemporaryDirectory() as td:
            for value in (True, 85.0):
                target = Path(td) / type(value).__name__
                pkg.write_package(target, self.records, review_root=REVIEWS)
                manifest_path = target / "manifest.json"
                modified = json.loads(manifest_path.read_bytes())
                modified["projected_rule_count_after"] = value
                manifest_path.write_bytes(canonical_bytes(modified))
                with self.subTest(kind=type(value).__name__), self.assertRaises(GameplayContractError):
                    pkg.load_package(target, review_root=REVIEWS)


class CanonicalPreservationTests(unittest.TestCase):
    def test_complete_canonical_source_and_evidence_inventory_is_unchanged(self):
        pkg.verify_preservation(ROOT)
        pins = json.loads((CODE / "pins.json").read_bytes())
        self.assertEqual(pins["canonical_base"], CANONICAL_MAIN)
        self.assertEqual(pins["inherited_source_count"], 333)
        protected = pins["protected_files"]
        inherited_source = {name for name in protected if name.startswith("src/")}
        self.assertEqual(len(inherited_source), 333)
        actual_source = {p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*")
                         if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}
        self.assertEqual(actual_source, inherited_source | NEW_SOURCE_PATHS)
        old_dirs = {Path(name).parts[1] for name in protected if name.startswith("reference-reviews/")}
        self.assertEqual(len(old_dirs), 17)
        for name in ("gameplay-rules-foundation", "gameplay-rules-source-versioning",
                     "gameplay-rules-release-discovery-closure", "gameplay-rules-artifact-verification"):
            self.assertIn(name, old_dirs)

    def test_only_exact_append_only_additions_are_excluded_from_historical_guards(self):
        self.assertEqual(len(NEW_SOURCE_PATHS), 6)
        self.assertEqual(len(NEW_REVIEW_PATHS), 8)
        for name in NEW_SOURCE_PATHS | NEW_REVIEW_PATHS:
            self.assertTrue(is_design_addition(ROOT / name))
        for name in ("src/gameplay_rules/engine.py",
                     "src/gameplay_rules/activated_ability_design/unreviewed.py",
                     "reference-reviews/gameplay-rules-activated-ability-procedure-design/projection.json"):
            self.assertFalse(is_design_addition(ROOT / name))

    def test_coverage_is_still_eighty_five_disjoint_units_in_nine_projections(self):
        projections = inherited_projections()
        self.assertEqual(len(projections), 9)
        self.assertEqual(len({p["projection_id"] for p in projections}), 9)
        rows = [r for p in projections for r in p["rules"]]
        self.assertEqual(len(rows), 85)
        refs = {r["rule_reference"] for r in rows}
        self.assertEqual(len(refs), 85)
        self.assertTrue(set(inspection.CANDIDATE_REFERENCES).isdisjoint(refs))
        self.assertTrue({"601.2a", "601.2c", "601.2d", "601.2e", "601.2i",
                         "733", "701.20a", "405.6", "603", "603.7d", "603.7e", "603.7f"}.isdisjoint(refs))
        by_ref = {r["rule_reference"]: r for r in rows}
        self.assertEqual(by_ref["605.3"]["direct_dependency_references"], ["602.2"])
        self.assertEqual(by_ref["605.3b"]["direct_dependency_references"], ["405.6c"])
        self.assertEqual(by_ref["605.4a"]["direct_dependency_references"], [])
        self.assertEqual(by_ref["601.2g"]["direct_dependency_references"], ["605"])
        self.assertEqual(by_ref["109.4a"]["direct_dependency_references"], ["605"])
        self.assertEqual(by_ref["109.4b"]["direct_dependency_references"], ["603", "603.7d", "603.7e", "603.7f"])
        stack = next(p for p in projections if any(r["rule_reference"] == "405.6c" for r in p["rules"]))
        self.assertEqual(stack["projection_id"], "sha256:7ff68d920bd2b846e3fb1616743c48d99e2935b007ccb6943057c47ce74cf87a")
        old = json.loads((REVIEWS / "gameplay-rules-bounded-mana-stack-exception-projection/manifest.json").read_bytes())
        self.assertEqual(old["package_id"], "sha256:da05752959743ca36c65489c75c50e7f648eee2f2bf6db3d94cecfa827072ff1")

    def test_design_namespace_has_no_runtime_or_network_dependency(self):
        forbidden = {"gameplay_rules.engine", "gameplay_rules.snapshots", "gameplay_rules.models",
                     "requests", "urllib", "socket", "subprocess"}
        for path in CODE.glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(alias.name not in forbidden for alias in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module, forbidden)
        for path in PACKAGE.iterdir():
            raw = path.read_bytes()
            for forbidden_text in (b"/tmp/", b"codex-remote-attachments", b"attachment_path", b"Example:"):
                self.assertNotIn(forbidden_text, raw)
        self.assertFalse(list(ROOT.rglob("*MagicCompRules*.txt")))


class ProcedureContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = pkg.rebuild_package(review_root=REVIEWS)

    def findings(self, name):
        return self.records[name + ".json"]["findings"]

    def test_review_authority_is_separate_from_historical_pm_authority(self):
        findings = self.findings("source-correspondence")
        classes = {row["class"]: row for row in findings["authority_classes"]}
        self.assertEqual(set(classes), {
            "PREVIOUSLY_RETAINED_PROJECTED_SOURCE_EVIDENCE", "HISTORICAL_PM_DESIGN_OBSERVATIONS",
            "NEW_EXACT_SOURCE_INSPECTION", "ARCHITECTURAL_DESIGN_JUDGMENT",
            "UNKNOWN_INCOMPLETE_UNSUPPORTED_UNRESOLVED",
        })
        historical = classes["HISTORICAL_PM_DESIGN_OBSERVATIONS"]
        self.assertEqual(historical["authority"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
        self.assertFalse(historical["original_authority_upgraded"])
        source = classes["NEW_EXACT_SOURCE_INSPECTION"]["inspection"]
        self.assertTrue(source["review_only"])
        self.assertFalse(source["projected"])
        self.assertFalse(source["source_body_retained"])
        self.assertEqual(len(source["review_spans"]), 3)
        self.assertFalse(findings["historical_evidence_mutated"])
        self.assertFalse(findings["source_inspection_resolves_projected_dependencies"])
        self.assertEqual(findings["new_projection_objects"], 0)
        self.assertEqual(findings["new_projected_rule_identities"], 0)
        self.assertEqual(findings["new_registered_projected_source_anchors"], 0)

    def test_scope_coherence_is_narrow_and_insufficient_scope_stops(self):
        scope = self.findings("local-scope")
        self.assertEqual(scope["candidate_references"], ["602.2", "602.2a", "602.2b"])
        self.assertEqual(scope["candidate_count"], 3)
        self.assertEqual(scope["current_projection_allowlist"], [])
        self.assertEqual(scope["candidate_coverage"], "UNPROJECTED")
        self.assertEqual([row["reference"] for row in scope["roles"]], scope["candidate_references"])
        policy = scope["insufficient_scope_policy"]
        self.assertTrue(policy["coherence_is_not_assumed_from_prior_design"])
        self.assertFalse(policy["complete_procedure_scope_sufficient"])
        self.assertFalse(policy["automatic_scope_expansion"])
        self.assertIn("STOP_FOR_OWNER_SCOPE_REVIEW", policy["if_future_source_or_context_differs"])
        self.assertIn("unprojected_imported_stages", policy["gaps"])
        self.assertEqual(scope["current_605.3_to_602.2"], "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY")

    def test_ten_procedure_responsibilities_have_separate_blocked_contracts(self):
        matrix = self.findings("procedure-responsibilities")
        self.assertEqual(matrix["contract_kind"], "REVIEW_REQUIREMENTS_ONLY")
        rows = matrix["rows"]
        self.assertEqual({row["responsibility"] for row in rows}, {
            "ability_kind_recognition", "activation_authority_and_controller", "announcement_and_ability_identity",
            "ability_stack_object_context", "activation_cost_determination", "casting_procedure_reuse",
            "mana_and_nonmana_payment", "activation_legality_and_timing", "illegal_action_handling_and_rollback",
            "resolution_downstream",
        })
        for row in rows:
            with self.subTest(responsibility=row["responsibility"]):
                self.assertTrue(row["purpose"])
                self.assertTrue(row["required_evidence_or_inputs"])
                self.assertTrue(row["missing_dependencies"])
                self.assertTrue(row["unknown_or_unsupported"])
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertFalse(row["implementation_available"])
        by_name = {row["responsibility"]: row for row in rows}
        self.assertEqual(by_name["ability_kind_recognition"]["inspected_candidate_support"], [])
        bindings = pkg.retained_binding()["rule_bindings"]
        self.assertEqual(by_name["ability_kind_recognition"]["existing_projected_evidence"],
                         [bindings[ref] for ref in ("605.1a", "605.1b", "115.6", "606.1", "606.2")])
        self.assertIn("do not define a general recognizer",
                      by_name["ability_kind_recognition"]["unknown_or_unsupported"])
        self.assertEqual(by_name["resolution_downstream"]["inspected_candidate_support"], [])

    def test_import_range_is_exact_partial_and_not_executable(self):
        findings = self.findings("casting-import")
        rows = findings["range_members"]
        self.assertEqual([row["reference"] for row in rows], list(inspection.IMPORTED_STAGES))
        coverage = {row["reference"]: row["coverage"] for row in rows}
        self.assertEqual(coverage, {"601.2" + s: "PROJECTED" if s in "bfgh" else "UNPROJECTED"
                                    for s in "bcdefghi"})
        for row in rows:
            with self.subTest(reference=row["reference"]):
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertTrue(row["unresolved_requirements"])
                if row["coverage"] == "PROJECTED":
                    self.assertIsNotNone(row["retained_evidence"])
                    self.assertEqual(row["body_authority"], "PREVIOUSLY_PROJECTED_SOURCE")
                else:
                    self.assertIsNone(row["retained_evidence"])
                    self.assertEqual(row["body_authority"], "UNKNOWN_NOT_INSPECTED")
        self.assertEqual(findings["excluded_stages"], ["601.2a"])
        for field in ("range_verification_projects_missing_members", "existing_casting_source_is_executable_procedure",
                      "partial_casting_satisfies_complete_activation", "casting_and_activation_interchangeable",
                      "imported_runtime_dispatch"):
            self.assertFalse(findings[field])
        mapping = findings["cost_mapping"]
        self.assertEqual(mapping["stage"], "601.2f")
        self.assertEqual(mapping["from_concept"], "SPELL_MANA_COST")
        self.assertEqual(mapping["to_concept"], "ABILITY_ACTIVATION_COST")
        for field in ("costs_calculated", "payments_performed", "cost_symbol_parser_supplied", "card_semantics_supplied"):
            self.assertFalse(mapping[field])

    def test_literal_references_range_import_and_structural_links_are_distinct(self):
        scope = self.findings("local-scope")
        refs = {(row["origin"], row["target"]): row for row in scope["outgoing_literal_references"]}
        self.assertEqual(set(refs), {("602.2", "733"), ("602.2a", "701.20a"), ("602.2b", "601.2f")})
        for edge in (("602.2", "733"), ("602.2a", "701.20a")):
            self.assertEqual(refs[edge]["coverage"], "UNPROJECTED")
            self.assertEqual(refs[edge]["status"], "UNRESOLVED")
        self.assertEqual(scope["range_import"]["members"], list(inspection.IMPORTED_STAGES))
        structural = scope["structural_relationships"]
        self.assertEqual(len(structural), 1)
        self.assertEqual(structural[0]["kind"], "STRUCTURAL_PARENT_CHILD_NOT_NUMBERED_CITATION")

    def test_general_activation_does_not_override_mana_exceptions(self):
        findings = self.findings("mana-relationships")
        general = findings["general_procedure"]
        self.assertEqual(general["coverage"], "UNPROJECTED")
        self.assertEqual(general["execution_readiness"], "BLOCKED")
        special = findings["qualifying_activated_mana_exception"]
        self.assertFalse(special["ordinary_stack_placement_unconditional"])
        self.assertFalse(special["exception_supplies_complete_activation"])
        edges = {(row["origin"], row["target"]): row for row in findings["preserved_relationships"]}
        self.assertEqual(edges[("605.3", "602.2")]["status"], "UNRESOLVED_PROJECTED_SOURCE_DEPENDENCY")
        self.assertEqual(edges[("605.3b", "405.6c")]["status"], "DIRECT_REFERENCE_RESOLVED")
        family = edges[("405.6c", "605")]
        self.assertEqual(family["status"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertEqual(len(family["concrete_members"]), 13)
        overlap = edges[("605.4a", "405.6c")]
        self.assertEqual(overlap["kind"], "SEMANTIC_OVERLAP_WITHOUT_DIRECT_CR_CITATION")
        self.assertFalse(overlap["direct_edge_created"])
        self.assertFalse(findings["additional_effect_context"]["finer_ordering_inferred"])
        self.assertEqual(findings["parent_405.6"], "UNPROJECTED_SCOPE_NOT_REOPENED")
        self.assertEqual(len(findings["independently_unresolved"]), 10)

    def test_priority_context_is_activated_only_and_conditional(self):
        priority = self.findings("mana-relationships")["priority_return"]
        self.assertEqual(priority["applicability"], "ACTIVATED_MANA_ABILITY_ONLY")
        self.assertEqual(priority["condition"], "PLAYER_HELD_PRIORITY_IMMEDIATELY_BEFORE_MANA_ABILITY_ACTIVATION")
        self.assertFalse(priority["every_mana_activation_grants_priority"])
        self.assertFalse(priority["triggered_priority_return_inferred"])
        self.assertFalse(priority["runtime_implemented"])
        self.assertEqual(priority["general_priority_semantics"], "OPEN")

    def test_consumers_keep_unresolved_indirect_and_controller_boundaries(self):
        findings = self.findings("consumer-bindings")
        rows = {row["consumer"]: row for row in findings["rows"]}
        self.assertEqual(set(rows), {"605.3", "605.3b", "601.2g", "bounded_casting", "madness", "109.4a"})
        self.assertEqual(rows["madness"]["route"], ["702.35b", "bounded_casting", "601.2g", "605"])
        self.assertEqual(rows["601.2g"]["source_correspondence"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertEqual(rows["109.4a"]["relationship_kind"], "SEPARATE_CONTROLLER_ATTRIBUTION_BOUNDARY")
        self.assertFalse(findings["controller_109.4a_requires_actual_stack_presence"])
        self.assertFalse(findings["unprojected_activation_inspection_closes_consumers"])
        for row in rows.values():
            with self.subTest(consumer=row["consumer"]):
                self.assertEqual(row["new_direct_edges"], [])
                self.assertFalse(row["historical_dependency_arrays_modified"])
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertTrue(row["missing_dependencies"])
        triggers = findings["shared_triggered_subsystem_outside_scope"]["preserved_frontiers"]
        self.assertEqual([(r["origin"], r["targets"]) for r in triggers], [
            ("605.4", ["603"]), ("109.4b", ["603", "603.7d", "603.7e", "603.7f"])])

    def test_exactly_one_future_recommendation_awaits_separate_owner_approval(self):
        findings = self.findings("readiness")
        self.assertEqual(findings["new_projected_real_source_units"], 0)
        self.assertEqual(findings["projected_real_source_units"], 85)
        self.assertEqual(findings["distinct_existing_projections"], 9)
        self.assertEqual(findings["current_projection_allowlist"], [])
        self.assertEqual(findings["execution_readiness"], "BLOCKED")
        self.assertEqual(findings["real_profile"], "DESIGN_ONLY / NOT EXECUTABLE")
        self.assertFalse(findings["projection_to_engine_path"])
        self.assertFalse(findings["real_snapshot_created"])
        self.assertEqual(len(findings["recommendations"]), 1)
        next_step = findings["recommendations"][0]
        self.assertEqual(next_step["milestone"], "Bounded Activated Ability Procedure Projection")
        self.assertEqual(next_step["proposed_future_allowlist"], ["602.2", "602.2a", "602.2b"])
        self.assertEqual(next_step["expected_new_unit_count"], 3)
        self.assertTrue(next_step["remaining_dependencies"])
        self.assertTrue(next_step["stop_conditions"])
        for key in ("future_milestone_authorized", "future_source_projection_authorized", "future_milestone_begun"):
            self.assertFalse(next_step[key])
        self.assertEqual(next_step["owner_approval"], "AWAITING_OWNER_APPROVAL")
        self.assertEqual(findings["permissions"], {
            "source_policy_clearance": "not_granted", "private_retention": "NOT_ESTABLISHED",
            "redistribution": "NOT_ESTABLISHED", "free_service": "NOT_ESTABLISHED",
            "commercial_service": "NOT_ESTABLISHED", "ai_export": "NOT_ESTABLISHED",
        })


if __name__ == "__main__":
    unittest.main()
