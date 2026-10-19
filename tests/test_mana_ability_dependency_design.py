"""Offline design proofs for the shared, still-unprojected 605 dependency.

Synthetic declarations carry no real-rule classification or runtime authority.
Preservation digests were captured independently from canonical main
3d403a62c66b8cb678eda9c07038da3ac59ae659: all 297 source and 169 review files.
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
PACKAGE = REVIEWS / "gameplay-rules-mana-ability-design"
CODE = ROOT / "src/gameplay_rules/mana_ability_design"
CANONICAL = "3d403a62c66b8cb678eda9c07038da3ac59ae659"
HISTORICAL = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
FAMILY = ("605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b", "605.3c",
          "605.4", "605.4a", "605.5", "605.5a", "605.5b")
OUTGOING = ("115.6", "606", "602.2", "405.6c", "603")
CAPABILITIES = ("mana_ability_classification", "activated_mana_ability_activation_window",
                "activated_mana_ability_immediate_resolution", "triggered_mana_ability_immediate_resolution",
                "mana_ability_controller_attribution", "mana_payment_opportunity",
                "mana_production_semantics", "mana_pool_semantics")
FILES = {"classification-design.json", "behavior-design.json", "controller-design.json",
         "consumer-bindings.json", "projection-frontier.json", "readiness.json", "manifest.json"}
PRIOR_PACKAGES = {
    "gameplay-rules-foundational-projection": "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea",
    "gameplay-rules-execution-profile-design": "sha256:f20d51ee190b4b23789208d0ae4bfa092d72aa23086fb01251d67b324ddb0687",
    "gameplay-rules-foundational-dependencies": "sha256:684727e763c228c5eebaacbbde9e19de631f168252f8f592a600ee0a60640a3a",
    "gameplay-rules-object-control-exceptions": "sha256:f8cf8053b8bf9e7cc9471520eb02cc3e1e29a716f99a2ac623ec36b40343acab",
    "gameplay-rules-zone-change-exceptions": "sha256:4836f6ea330cc40365540f85541160ef2251ff6ed88f7959f9d9e594031f7875",
    "gameplay-rules-zone-change-direct-dependencies": "sha256:d51fab1425f6aa9b82e4621ac8c88d4b83d736c6906a4f4c589c41ff1aeadba4",
    "gameplay-rules-madness-casting-design": "sha256:06cd012d08d204f10337d834f312bcf19b060a3569ef3cf879c46714d30944c8",
    "gameplay-rules-bounded-casting-projection": "sha256:d2b1832f170d1bbd6ef21efe3d3452923880cc47c57dad523f7aefff4bc427d7",
}
RULE_IDS = {
    "601.2g": "sha256:7c01241cb591680e28dd16dd3c97b88b28ebcdaca80af8c153a5891e1363a662",
    "109.4a": "sha256:7793b14d8f2af5916dd02316ff0ea817d77b0bf656284c0f56d86b3f743fcea1",
    "702.35a": "sha256:48da52c60c006aaae9a752b23155581474244b4a7b3a050b588fb2f51c1b6534",
    "702.35b": "sha256:884e5ecb63b242196785a1d38f8a3014896342a6d4b738e6005430c1ac22d5ae",
    "702.35c": "sha256:79b507ab353539b0d1166876f25c279a2171f860f69ab40b53cc2d942f198fb4",
    "400.7k": "sha256:5fd728b81834e50cc3555e61fd9cf9f9cb6e3cce172618d23cfcd0649efe21c5",
}


def regular_files(root):
    # This later append-only milestone is outside the historical inventory.
    return [p for p in _historical_regular_files(root)
            if not (p.parent == ROOT / "src/gameplay_rules/projection" and p.name.startswith("mana_classification_"))
            and "gameplay-rules-bounded-mana-classification-projection" not in p.parts]


def _historical_regular_files(root):
    return [path for path in root.rglob("*") if path.is_file()
            and "__pycache__" not in path.parts and path.suffix != ".pyc"]


def inventory(paths):
    result = []
    for path in sorted(set(paths)):
        if path.is_symlink():
            raise AssertionError("Protected files must remain regular files")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


def prior_rules():
    result = {}
    for name in PRIOR_PACKAGES:
        path = REVIEWS / name / "projection.json"
        if path.is_file():
            for rule in json.loads(path.read_bytes())["rules"]:
                reference = rule["rule_reference"]
                if reference in result:
                    raise AssertionError("Distinct retained projections must not duplicate a real rule")
                result[reference] = rule
    return result


def design_body(record):
    return {key: record.to_dict()[key] for key in record.BODY_FIELDS}


class ManaAbilityPreservationTests(unittest.TestCase):
    def test_all_297_prior_source_files_byte_identical(self):
        values = inventory(path for path in regular_files(ROOT / "src") if CODE not in path.parents
                           and "mana_dependency_design" not in path.parts
                           and not (path.parent == ROOT / "src/gameplay_rules/projection"
                                    and path.name.startswith("bounded_mana_")))
        self.assertEqual(len(values), 297)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "4a43a0935d7a401e2da4c96d4b2d27a269466ad266534fab24879d2d900a1b96")

    def test_all_169_prior_review_files_byte_identical(self):
        values = inventory(path for path in regular_files(REVIEWS) if PACKAGE not in path.parents
                           and "gameplay-rules-bounded-mana-ability-projection" not in path.parts
                           and "gameplay-rules-mana-direct-dependency-design" not in path.parts)
        self.assertEqual(len(values), 169)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "578b6f24130bc8363fecb86fe8115c31f7f558b78ab974d74a142758fb9b740e")

    def test_eight_prior_package_identities_remain_exact(self):
        for name, identity in PRIOR_PACKAGES.items():
            with self.subTest(package=name):
                self.assertEqual(json.loads((REVIEWS / name / "manifest.json").read_bytes())["package_id"], identity)

    def test_sixty_eight_real_units_remain_disjoint_and_no_605_or_candidates_projected(self):
        rules = prior_rules()
        self.assertEqual(len(rules), 68)
        self.assertFalse(any(ref == "605" or ref.startswith("605.") for ref in rules))
        blocked = {*FAMILY, *OUTGOING, "613", "603.7d", "603.7e", "603.7f", "114", "901.6",
                   "902.6", "904.7", "905.5", "601.2a", "601.2c", "601.2d", "601.2e", "601.2i",
                   "601.3", "733", "700.2", "702.47", "118.8", "118.9", "107.3"}
        self.assertTrue(blocked.isdisjoint(rules))

    def test_consumer_madness_and_lookup_rule_identities_unchanged(self):
        rules = prior_rules()
        for reference, identity in RULE_IDS.items():
            with self.subTest(reference=reference):
                self.assertEqual(rules[reference]["rule_id"], identity)
        for reference in ("601.2g", "109.4a"):
            self.assertIn("605", rules[reference]["direct_dependency_references"])

    def test_historical_replay_identity_and_fixture_bytes_preserved(self):
        root = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((root / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL)
        for name, binding in manifest["files"].items():
            raw = (root / name).read_bytes()
            self.assertEqual({"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}, binding)

    def test_architecture_v13_and_decision_017_unchanged(self):
        values = inventory(ROOT / "docs" / name for name in (
            "ARCHITECTURE.md", "DECISIONS.md", "DECISION_ENGINE.md", "DECISION_INTELLIGENCE.md",
            "DECISION_INTELLIGENCE_ASSESSMENT_2026_08_12.md"))
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "92054f7315fabe2ac30c6dda0429ebb47bf5cc92f08998de579c5fc1140e98a2")

    def test_fictional_profile_and_simulation_unchanged(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({path.name for path in (ROOT / "src/simulation").iterdir()
                          if path.name != "__pycache__"}, {".gitkeep"})

    def test_namespace_has_no_runtime_network_or_card_ingestion_implementation(self):
        imports = {"socket", "http", "urllib", "requests", "subprocess", "random", "simulation",
                   "providers", "external_ingestion", "market", "production_evidence", "repository"}
        runtime = {"GameplayRulesSnapshot", "GameplayRulesEngine", "CardGameplaySemantics", "GameState",
                   "GameAction", "LegalityResult", "GameTransition", "RawSnapshotStore"}
        functions = {"classify_mana_ability", "detect_mana_ability", "activate_mana_ability", "activate_ability",
                     "detect_trigger", "execute_trigger", "resolve_ability", "produce_mana", "add_mana",
                     "spend_mana", "pay_cost", "pay_mana", "assign_controller", "to_rules_snapshot",
                     "to_execution_profile", "activate_profile", "execute_payment"}
        paths = list(CODE.glob("*.py"))
        self.assertGreater(len(paths), 1)
        for path in paths:
            for node in ast.walk(ast.parse(path.read_text(), filename=str(path))):
                if isinstance(node, ast.Import):
                    self.assertTrue(imports.isdisjoint(alias.name.split(".")[0] for alias in node.names))
                elif isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or "").split(".")[0], imports)
                    self.assertTrue(runtime.isdisjoint(alias.name for alias in node.names))
                elif isinstance(node, ast.Name):
                    self.assertNotIn(node.id, runtime)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.assertNotIn(node.name, functions)


class ManaAbilityPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_ability_design.builder import build_design_package
        from gameplay_rules.mana_ability_design.package import load_design_package, write_design_package, package_manifest
        cls.build = staticmethod(build_design_package)
        cls.load = staticmethod(load_design_package)
        cls.write = staticmethod(write_design_package)
        cls.manifest = staticmethod(package_manifest)
        cls.records = cls.load(PACKAGE, review_root=REVIEWS)

    def test_exact_canonical_and_six_design_only_records_without_new_source_authority(self):
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
            for flag in ("execution_authorized", "projection_authorized", "source_verification_claimed", "source_body_retained",
                         "real_rules_executable", "oracle_ingested", "real_snapshot_created", "real_profile_activated"):
                self.assertFalse(value[flag])

    def test_policy_owner_activation_and_five_permission_states_remain_unchanged(self):
        for record in self.records.values():
            value = record.to_dict()
            self.assertEqual(value["source_policy_clearance"], "not_granted")
            self.assertEqual(value["owner_execution_approval"], "NOT_GRANTED")
            self.assertEqual(value["permissions"], {name: "NOT_ESTABLISHED" for name in
                ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})

    def test_identity_roundtrip_determinism_and_deep_immutability(self):
        self.assertEqual(len({record.identity for record in self.records.values()}), 6)
        for record in self.records.values():
            with self.subTest(record=type(record).__name__):
                self.assertEqual(type(record).from_json(record.serialize()), record)
                self.assertEqual(type(record).create(design_body(record)), record)
                self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
                self.assertEqual(record.verify(), record)
                self.assertRegex(record.identity, r"^sha256:[0-9a-f]{64}$")
                for attr, value in (("_payload", {}), ("execution_authorized", True),
                                    ("status", "EXECUTABLE"), ("unreviewed_attribute", True)):
                    with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                        setattr(record, attr, value)
                with self.assertRaises(TypeError):
                    record._payload["execution_authorized"] = True
                with self.assertRaises(TypeError):
                    record._payload["permissions"]["ai_export"] = "GRANTED"
                detached = record.to_dict()
                detached["permissions"]["ai_export"] = "GRANTED"
                self.assertEqual(record.permissions["ai_export"], "NOT_ESTABLISHED")

    def test_false_authority_flags_tampered_identity_schema_and_duplicate_json_rejected(self):
        record = self.records["classification-design.json"]
        for field, value in ((record.ID_FIELD, "sha256:" + "f" * 64), ("schema_version", "different"),
                             ("execution_authorized", True), ("source_verification_claimed", True),
                             ("new_source_units_projected", 1), ("real_profile_activated", True),
                             ("source_policy_clearance", "granted")):
            changed = record.to_dict()
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                type(record).from_dict(changed)
        with self.assertRaises(GameplayContractError):
            type(record).from_json(record.serialize()[:-1] + ',"status":"DESIGN_ONLY"}')
        with self.assertRaises(GameplayContractError):
            type(record).from_json(record.serialize()[:-1] + ',"unknown":NaN}')
        for key in ("source_anchor", "official_text", "oracle_text", "source_excerpt"):
            changed = design_body(record)
            changed[key] = {"rule_reference": "605.1a"}
            with self.subTest(key=key), self.assertRaises(GameplayContractError):
                type(record).create(changed)

    def test_offline_rebuild_requires_no_source_artifact_network_or_retention(self):
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")))
            for module in ("source", "dependency_source", "object_control_source", "zone_change_source", "zone_change_dependency_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + "._verified_bytes",
                                          side_effect=AssertionError("external source access forbidden")))
            stack.enter_context(patch("gameplay_rules.projection.bounded_casting_source.verify_bounded_casting_bytes",
                                      side_effect=AssertionError("external source access forbidden")))
            self.assertEqual(self.build(review_root=REVIEWS), self.records)
            self.assertEqual(self.load(PACKAGE, review_root=REVIEWS), self.records)

    def test_design_records_cannot_be_loaded_as_real_snapshots_or_profiles(self):
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

    def test_package_has_no_source_prose_new_anchor_txt_or_external_paths(self):
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
                for prefix in ("/workspace/", "/tmp/", "file://", "sediment://"):
                    self.assertNotIn(prefix, value)
        for path in PACKAGE.iterdir():
            self.assertEqual(path.suffix, ".json")
            check(json.loads(path.read_bytes()))
        self.assertFalse((PACKAGE / "projection.json").exists())

    def test_manifest_preserves_eight_packages_and_sixty_eight_coverage(self):
        value = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(value["canonical_base"], CANONICAL)
        self.assertEqual((value["projected_rule_count_before"], value["new_source_units_projected"],
                          value["projected_rule_count_after"]), (68, 0, 68))
        self.assertEqual(value["additional_rules_projected"], [])
        self.assertFalse(value["source_artifact_required"])
        self.assertFalse(value["source_anchors_created"])
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL)
        self.assertEqual(set(value["retained_evidence_binding"]["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(value["record_ids"], {record.ID_FIELD: record.identity for record in self.records.values()})
        raw = {name: (record.serialize() + "\n").encode() for name, record in self.records.items()}
        self.assertEqual(self.manifest(self.records, raw), value)

    def test_modified_missing_or_extra_txt_source_and_directory_rejected(self):
        for mutation in ("tamper", "missing", "txt", "source", "directory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / "classification-design.json"
                if mutation == "tamper":
                    path.write_bytes(path.read_bytes().replace(b'DESIGN_ONLY', b'UNREVIEWED!', 1))
                elif mutation == "missing":
                    path.unlink()
                elif mutation == "directory":
                    (root / "unexpected").mkdir()
                else:
                    (root / ("source.txt" if mutation == "txt" else "source.json")).write_text("synthetic extra")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_symlink_hardlink_root_and_ancestor_symlink_rejected(self):
        for link in ("symlink", "hardlink", "root-symlink", "ancestor-symlink"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as tmp:
                container = Path(tmp) / "container"
                container.mkdir()
                root = container / "package"
                shutil.copytree(PACKAGE, root)
                if link in {"root-symlink", "ancestor-symlink"}:
                    alias = Path(tmp) / "alias"
                    alias.symlink_to(root if link == "root-symlink" else container, target_is_directory=True)
                    root = alias if link == "root-symlink" else alias / "package"
                else:
                    path = root / "classification-design.json"
                    held = Path(tmp) / "held.json"
                    path.rename(held)
                    if link == "symlink":
                        path.symlink_to(held)
                    else:
                        os.link(held, path)
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_noncanonical_record_and_manifest_bytes_rejected(self):
        for name in ("classification-design.json", "manifest.json"):
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / name
                path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2) + "\n")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_relocation_offline_rebuild_and_append_only_writer(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "reviews"
            shutil.copytree(REVIEWS, reviews)
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


    def test_each_meaningful_design_note_change_changes_its_identity(self):
        for name, record in self.records.items():
            with self.subTest(record=name):
                body = design_body(record)
                body["design_notes"] = [*body["design_notes"], "A different synthetic design-review input."]
                changed = type(record).create(body)
                self.assertNotEqual(changed.identity, record.identity)
                self.assertEqual(changed, type(record).create(body))

    def test_loader_rejects_retained_evidence_tampering_without_any_source_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "reviews"
            shutil.copytree(REVIEWS, reviews)
            path = reviews / "gameplay-rules-bounded-casting-projection" / "projection.json"
            path.write_bytes(path.read_bytes().replace(RULE_IDS["601.2g"].encode(), ("sha256:" + "f" * 64).encode()))
            with self.assertRaises(GameplayContractError):
                self.build(review_root=reviews)
            with self.assertRaises(GameplayContractError):
                self.load(PACKAGE, review_root=reviews)


    def test_reidentified_rehashed_findings_cannot_replace_retained_reproduction(self):
        records = dict(self.records)
        frontier = records["projection-frontier.json"]
        body = design_body(frontier)
        body["design_notes"] = [*body["design_notes"], "A separately reviewed synthetic source-scope conclusion."]
        frontier = type(frontier).create(body)
        records["projection-frontier.json"] = frontier
        readiness = records["readiness.json"]
        body = design_body(readiness)
        body["projection_frontier_id"] = frontier.identity
        records["readiness.json"] = type(readiness).create(body)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "altered"
            self.write(root, records)
            with self.assertRaises(GameplayContractError):
                self.load(root, review_root=REVIEWS)

    def test_package_rejects_mismatched_design_links_and_untyped_record_objects(self):
        records = dict(self.records)
        classification = records["classification-design.json"]
        body = design_body(classification)
        body["design_notes"] = [*body["design_notes"], "A different synthetic classification scope input."]
        records["classification-design.json"] = type(classification).create(body)
        with self.assertRaises(GameplayContractError):
            self.manifest(records)
        records = dict(self.records)
        records["classification-design.json"] = classification.to_dict()
        with self.assertRaises(GameplayContractError):
            self.manifest(records)


class ManaAbilityClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_ability_design.classification import (
            build_classification_design, build_activated_classification_input,
            build_triggered_classification_input, build_classification_persistence,
        )
        cls.design = build_classification_design()
        cls.activated = staticmethod(build_activated_classification_input)
        cls.triggered = staticmethod(build_triggered_classification_input)
        cls.persistence = staticmethod(build_classification_persistence)

    def activated_fields(self):
        return {"has_target": False, "could_add_mana_on_resolution": True,
                "loyalty_ability_status": "NO", "library_movement_in_cost": False,
                "library_movement_in_effect": False, "self_replacement_knowledge": "KNOWN_SYNTHETIC_ONLY",
                "other_replacement_effect_knowledge": "KNOWN_SYNTHETIC_ONLY",
                "card_effect_semantics_availability": "KNOWN_SYNTHETIC_ONLY"}

    def triggered_fields(self):
        return {"has_target": False, "could_add_mana_on_resolution": True,
                "trigger_source_category": "MANA_ADDED",
                "triggered_by_activated_mana_ability_activation": False,
                "triggered_by_activated_mana_ability_resolution": False,
                "triggered_by_mana_added": True,
                "source_semantics_knowledge": "KNOWN_SYNTHETIC_ONLY",
                "dependency_semantics_knowledge": "KNOWN_SYNTHETIC_ONLY"}

    def test_four_classification_results_are_separate_from_three_execution_states(self):
        value = self.design.to_dict()
        self.assertEqual(value["classification_states"], ["MANA_ABILITY", "NOT_MANA_ABILITY", "INDETERMINATE", "UNSUPPORTED"])
        self.assertEqual(value["execution_states"], ["NOT_IMPLEMENTED", "BLOCKED", "UNSUPPORTED"])
        self.assertTrue(value["classification_and_execution_independent"])
        for key in ("classification_implies_execution", "classification_implies_mana_production",
                    "classification_implies_mana_pool_semantics", "classification_implies_current_activation",
                    "real_classifier_available"):
            self.assertFalse(value[key])
        self.assertEqual(value["evidence_status"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
        self.assertEqual(value["source_605_status"], "UNPROJECTED_NOT_SOURCE_VERIFIED")

    def test_activated_and_triggered_input_contracts_are_distinct_and_unevaluated(self):
        activated, triggered = self.activated(), self.triggered()
        self.assertIsNot(type(activated), type(triggered))
        self.assertEqual(activated.ability_kind, "ACTIVATED")
        self.assertEqual(triggered.ability_kind, "TRIGGERED")
        for value in (activated, triggered):
            self.assertEqual(value.classification, "INDETERMINATE")
            self.assertTrue(value.unknown_fields)
            self.assertFalse(value.classification_evaluated)
            self.assertEqual(value.classification_source, "CALLER_SUPPLIED_HYPOTHETICAL_DECLARATION")
            self.assertTrue(value.hypothetical_only)
            self.assertFalse(value.execution_implied)
            self.assertEqual(value.execution_readiness, "NOT_IMPLEMENTED")

    def test_complete_synthetic_fields_do_not_automatically_infer_positive_classification(self):
        for build, fields in ((self.activated, self.activated_fields()), (self.triggered, self.triggered_fields())):
            default = build(**fields)
            declared = build(**fields, classification="MANA_ABILITY")
            self.assertEqual(default.classification, "INDETERMINATE")
            self.assertEqual(declared.classification, "MANA_ABILITY")
            self.assertFalse(default.classification_evaluated)
            self.assertFalse(declared.classification_evaluated)
            self.assertNotEqual(default.identity, declared.identity)
            self.assertFalse(declared.execution_authorized)

    def test_every_unknown_required_input_prevents_asserted_known_classification(self):
        for build, known in ((self.activated, self.activated_fields()), (self.triggered, self.triggered_fields())):
            for field, value in known.items():
                unknown = dict(known)
                unknown[field] = None if type(value) is bool else "UNKNOWN"
                # A selected trigger category requires its matching relation; use an unknown category
                # while testing absent relation declarations, rather than asserting contradictory metadata.
                if field.startswith("triggered_by_"):
                    unknown["trigger_source_category"] = "UNKNOWN"
                with self.subTest(builder=build.__name__, field=field):
                    self.assertEqual(build(**unknown).classification, "INDETERMINATE")
                    self.assertEqual(build(**unknown, classification="UNSUPPORTED").classification, "UNSUPPORTED")
                    for result in ("MANA_ABILITY", "NOT_MANA_ABILITY"):
                        with self.assertRaises(GameplayContractError):
                            build(**unknown, classification=result)

    def test_targeted_activated_exclusion_is_an_explicit_synthetic_declaration(self):
        fields = self.activated_fields()
        fields["has_target"] = True
        declared = self.activated(**fields, classification="NOT_MANA_ABILITY", exclusion_metadata=["TARGETED_ABILITY"])
        self.assertEqual(declared.classification, "NOT_MANA_ABILITY")
        self.assertEqual(declared.exclusion_metadata, ("TARGETED_ABILITY",))
        self.assertFalse(declared.classification_evaluated)
        with self.assertRaises(GameplayContractError):
            self.activated(**fields, classification="MANA_ABILITY")
        with self.assertRaises(GameplayContractError):
            self.activated(**self.activated_fields(), classification="NOT_MANA_ABILITY", exclusion_metadata=["TARGETED_ABILITY"])

    def test_loyalty_library_and_replacement_effect_information_are_distinct_inputs(self):
        required = self.design.to_dict()["activated_input_design"]["required_concepts"]
        self.assertTrue({"loyalty_ability_status", "library_movement_in_cost", "library_movement_in_effect",
                         "applicable_self_replacement_information", "other_replacement_effect_knowledge"}.issubset(required))
        for field, setting, exclusion in (("loyalty_ability_status", "YES", "LOYALTY_ABILITY"),
                ("library_movement_in_cost", True, "LIBRARY_MOVEMENT_IN_COST"),
                ("library_movement_in_effect", True, "LIBRARY_MOVEMENT_IN_EFFECT")):
            fields = self.activated_fields()
            fields[field] = setting
            value = self.activated(**fields, classification="NOT_MANA_ABILITY", exclusion_metadata=[exclusion])
            self.assertEqual(value.classification, "NOT_MANA_ABILITY")
            self.assertFalse(value.classification_evaluated)
        replacement = self.design.to_dict()["activated_input_design"]["replacement_effect_distinction"]
        self.assertTrue(replacement["source_verification_required"])
        self.assertNotEqual(replacement["self_replacement"], replacement["other_replacement_effects"])

    def test_three_trigger_source_categories_are_distinct_declared_relationships(self):
        categories = (("ACTIVATED_MANA_ABILITY_ACTIVATION", "triggered_by_activated_mana_ability_activation"),
                      ("ACTIVATED_MANA_ABILITY_RESOLUTION", "triggered_by_activated_mana_ability_resolution"),
                      ("MANA_ADDED", "triggered_by_mana_added"))
        values = []
        for category, field in categories:
            fields = self.triggered_fields()
            for _, flag in categories:
                fields[flag] = flag == field
            fields["trigger_source_category"] = category
            value = self.triggered(**fields, classification="MANA_ABILITY")
            self.assertEqual(value.trigger_source_category, category)
            self.assertTrue(value.to_dict()[field])
            self.assertFalse(value.classification_evaluated)
            values.append(value.identity)
        self.assertEqual(len(set(values)), 3)

    def test_wrong_trigger_or_nonproductive_ability_exclusion_is_descriptive_only(self):
        for exclusion in ("WRONG_TRIGGER_RELATIONSHIP", "CANNOT_ADD_MANA_ON_RESOLUTION"):
            fields = self.triggered_fields()
            if exclusion == "WRONG_TRIGGER_RELATIONSHIP":
                fields["trigger_source_category"] = "OTHER"
                fields["triggered_by_mana_added"] = False
            else:
                fields["could_add_mana_on_resolution"] = False
            value = self.triggered(**fields, classification="NOT_MANA_ABILITY", exclusion_metadata=[exclusion])
            self.assertEqual(value.classification, "NOT_MANA_ABILITY")
            self.assertFalse(value.classification_evaluated)
        boundary = self.design.to_dict()["spells_boundary"]
        self.assertEqual(boundary["spells_that_add_mana"], "DESIGN_EXCLUDED_FROM_ABILITY_CLASSIFICATION")
        self.assertEqual(boundary["card_text_keyword_matching"], "INSUFFICIENT_AUTHORITY")

    def test_classification_persists_with_zero_output_or_ineligible_activation(self):
        declared = self.activated(**self.activated_fields(), classification="MANA_ABILITY")
        active = self.persistence(declared, current_activation_eligibility="ELIGIBLE",
                                  current_mana_output_known=True, current_mana_output_amount=2)
        inactive = self.persistence(declared, current_activation_eligibility="INELIGIBLE",
                                    current_mana_output_known=True, current_mana_output_amount=0,
                                    current_game_state_constraints=["synthetic-state-constraint-alpha"])
        unknown = self.persistence(declared)
        for value in (active, inactive, unknown):
            self.assertEqual(value.classification, "MANA_ABILITY")
            self.assertEqual(value.classification_input_id, declared.identity)
            self.assertFalse(value.classification_recomputed_from_current_state)
            self.assertFalse(value.activation_evaluated)
            self.assertFalse(value.mana_output_calculated)
            self.assertFalse(value.execution_implied)
        self.assertNotEqual(active.identity, inactive.identity)
        self.assertEqual(inactive.current_mana_output_amount, 0)
        self.assertIsNone(unknown.current_mana_output_amount)

    def test_synthetic_inputs_cannot_smuggle_real_references_unknown_fields_or_output(self):
        for build in (self.activated, self.triggered):
            with self.assertRaises(GameplayContractError):
                build(synthetic_ability_reference="unverified-ability-reference")
            value = build()
            body = design_body(value)
            body["unknown_fields"] = []
            with self.assertRaises(GameplayContractError):
                type(value).create(body)
        with self.assertRaises(GameplayContractError):
            self.persistence(self.activated(), current_mana_output_known=False, current_mana_output_amount=1)
        with self.assertRaises(GameplayContractError):
            self.persistence(self.activated(), current_mana_output_known=True, current_mana_output_amount=-1)
        with self.assertRaises(GameplayContractError):
            self.persistence(self.design)


    def test_synthetic_declarations_and_nested_persistence_are_immutable(self):
        declaration = self.activated(**self.activated_fields(), classification="MANA_ABILITY")
        records = (declaration, self.triggered(), self.persistence(declaration))
        for record in records:
            self.assertEqual(type(record).from_json(record.serialize()), record)
            self.assertEqual(record.verify(), record)
            with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                record.execution_authorized = True
            with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                record.unreviewed_attribute = True
            with self.assertRaises(TypeError):
                record._payload["classification"] = "UNSUPPORTED"
        persistent = records[-1]
        with self.assertRaises(TypeError):
            persistent._payload["classification_input"]["classification"] = "UNSUPPORTED"
        changed = design_body(persistent)
        changed["classification_input_id"] = "sha256:" + "f" * 64
        with self.assertRaises(GameplayContractError):
            type(persistent).create(changed)


class ManaAbilityBehaviorControllerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_ability_design.behavior import build_behavior_design
        from gameplay_rules.mana_ability_design.controller import build_controller_design
        from gameplay_rules.mana_ability_design.evidence import load_retained_evidence
        cls.binding = load_retained_evidence(REVIEWS)
        cls.behavior = build_behavior_design()
        cls.controller = build_controller_design(cls.binding)

    def test_five_activation_opportunities_are_deterministic_descriptive_categories(self):
        value = self.behavior.to_dict()["activation_windows"]
        self.assertEqual([row["sequence"] for row in value], [1, 2, 3, 4, 5])
        self.assertEqual([row["opportunity_id"] for row in value], ["ORDINARY_PRIORITY_WINDOW",
            "DURING_SPELL_CASTING_REQUIRING_MANA_PAYMENT", "DURING_ABILITY_ACTIVATION_REQUIRING_MANA_PAYMENT",
            "RULE_REQUESTS_MANA_PAYMENT", "EFFECT_REQUESTS_MANA_PAYMENT"])
        for row in value:
            self.assertTrue(row["eligibility_category_only"])
            self.assertFalse(row["actual_activation_eligibility_evaluated"])
            self.assertFalse(row["execution_supported"])
            self.assertEqual(row["evidence_status"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")

    def test_activated_no_stack_and_immediate_resolution_are_not_runtime(self):
        value = self.behavior.to_dict()["activated_mana_behavior"]
        self.assertEqual(value["stack_presence_concept"], "DOES_NOT_ENTER_STACK")
        self.assertEqual(value["resolution_sequence_concept"], "IMMEDIATELY_AFTER_ACTIVATION")
        self.assertEqual(value["same_ability_reactivation_concept"], "PROHIBITED_UNTIL_ITS_ACTIVATION_FINISHES_RESOLVING")
        for field in ("activation_performed", "resolution_performed", "response_window_created", "stack_object_created", "countering_implemented"):
            self.assertFalse(value[field])
        self.assertEqual(value["stack_object_targeting_concept"], "NO_NORMAL_STACK_OBJECT_TARGET")
        self.assertEqual(value["stack_object_countering_concept"], "NO_NORMAL_STACK_OBJECT_COUNTERING")
        self.assertEqual(value["stack_object_response_concept"], "NO_NORMAL_STACK_OBJECT_RESPONSE")

    def test_triggered_no_stack_immediate_sequence_and_no_priority_wait_are_distinct(self):
        value = self.behavior.to_dict()["triggered_mana_behavior"]
        self.assertEqual(value["qualifying_trigger_relationship_categories"], ["ACTIVATION_OF_ACTIVATED_MANA_ABILITY",
                         "RESOLUTION_OF_ACTIVATED_MANA_ABILITY", "MANA_ADDED"])
        self.assertEqual(value["stack_presence_concept"], "DOES_NOT_ENTER_STACK")
        self.assertEqual(value["resolution_sequence_concept"], "IMMEDIATELY_AFTER_THE_MANA_ABILITY_THAT_CAUSED_IT")
        self.assertEqual(value["priority_wait_concept"], "DOES_NOT_WAIT_FOR_PRIORITY")
        for field in ("trigger_detection_performed", "resolution_performed", "priority_evaluated", "stack_object_created"):
            self.assertFalse(value[field])

    def test_no_general_activation_trigger_priority_or_stack_runtime_is_inherited(self):
        value = self.behavior.to_dict()["ordinary_ability_boundary"]
        for key in ("stack_runtime", "priority_runtime", "trigger_runtime", "general_activation_runtime"):
            self.assertEqual(value[key], "ABSENT")
        self.assertFalse(value["mana_exception_satisfies_general_ability_semantics"])
        separate = self.behavior.to_dict()["capability_separation"]
        for key in ("classification_implies_activation", "activation_window_implies_resolution",
                    "no_stack_concept_implies_stack_runtime", "immediate_resolution_implies_mana_production",
                    "mana_payment_opportunity_implies_payment", "source_coverage_implies_execution"):
            self.assertFalse(separate[key])
        for key in ("mana_production_semantics", "mana_pool_semantics", "payment_integration"):
            self.assertEqual(separate[key], "BLOCKED_ABSENT")

    def test_controller_binds_existing_109_4a_with_hypothetical_not_actual_stack(self):
        value = self.controller.to_dict()
        self.assertEqual(value["consumer_binding"]["rule_reference"], "109.4a")
        self.assertEqual(value["consumer_binding"]["rule_id"], RULE_IDS["109.4a"])
        self.assertEqual(value["consumer_binding"]["direct_dependency_references"], ["605"])
        model = value["attribution_model"]
        self.assertEqual(model["primitive_concept"], "hypothetical_stack_controller_attribution")
        self.assertEqual(model["retained_consumer_relationship"], "DETERMINE_CONTROLLER_AS_THOUGH_ABILITY_WERE_ON_STACK")
        self.assertFalse(model["actual_stack_presence_required"])
        self.assertFalse(model["stack_object_created_for_attribution"])
        self.assertFalse(model["controller_assigned"])
        self.assertFalse(model["fictional_controller_authority_inherited"])

    def test_controller_subtypes_general_and_delayed_semantics_remain_separate_open_boundaries(self):
        value = self.controller.to_dict()
        self.assertEqual([row["ability_subtype"] for row in value["subtype_attribution"]],
                         ["ACTIVATED", "TRIGGERED", "GENERAL_OR_UNKNOWN", "DELAYED_TRIGGER"])
        for row in value["subtype_attribution"]:
            self.assertTrue(row["source_review_required"])
            self.assertFalse(row["execution_supported"])
        self.assertEqual(value["candidate_numbered_dependencies"], [])
        self.assertEqual(value["boundaries"]["runtime_controller_assignment"], "ABSENT")
        self.assertFalse(value["boundaries"]["casting_source_coverage_implies_controller"])
        self.assertFalse(value["boundaries"]["future_605_projection_closes_general_control"])

    def test_controller_rejects_missing_or_changed_consumer_evidence(self):
        from gameplay_rules.mana_ability_design.controller import build_controller_design
        for mutation in ("missing", "identity", "dependency"):
            binding = json.loads(json.dumps(self.binding))
            if mutation == "missing":
                binding["consumers"].pop("109.4a")
            elif mutation == "identity":
                binding["consumers"]["109.4a"]["rule_id"] = "sha256:" + "f" * 64
            else:
                binding["consumers"]["109.4a"]["direct_dependency_references"] = []
            with self.subTest(mutation=mutation), self.assertRaises(GameplayContractError):
                build_controller_design(binding)


class ManaAbilityConsumerFrontierTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_ability_design.classification import build_classification_design
        from gameplay_rules.mana_ability_design.behavior import build_behavior_design
        from gameplay_rules.mana_ability_design.controller import build_controller_design
        from gameplay_rules.mana_ability_design.evidence import load_retained_evidence
        from gameplay_rules.mana_ability_design.consumers import build_consumer_matrix
        from gameplay_rules.mana_ability_design.frontier import build_projection_frontier
        cls.binding = load_retained_evidence(REVIEWS)
        cls.arguments = [build_classification_design(), build_behavior_design(), build_controller_design(cls.binding)]
        cls.consumers = build_consumer_matrix(cls.binding, *cls.arguments)
        cls.frontier = build_projection_frontier(*cls.arguments)

    def test_consumers_bind_existing_identities_with_distinct_required_capabilities(self):
        value = self.consumers.to_dict()
        self.assertEqual(value["retained_evidence_binding"], self.binding)
        rows = {row["consumer_reference"]: row for row in value["consumer_bindings"]}
        self.assertEqual(set(rows), {"601.2g", "109.4a"})
        for reference, row in rows.items():
            self.assertEqual(row["consumer_evidence"]["rule_id"], RULE_IDS[reference])
            self.assertEqual(row["relationship_kind"], "EXISTING_DIRECT_CR_DEPENDENCY")
            self.assertEqual(row["unresolved_target"], "605")
            self.assertEqual(row["execution_readiness"], "BLOCKED")
            self.assertFalse(row["required_primitives_available"])
        self.assertTrue({"mana_ability_classification", "activated_mana_ability_activation_window",
                         "mana_payment_opportunity"}.issubset(rows["601.2g"]["required_capabilities"]))
        self.assertTrue({"mana_production_semantics", "mana_pool_semantics", "payment_integration"}.issubset(
                        rows["601.2g"]["later_capabilities"]))
        self.assertEqual(rows["109.4a"]["required_capabilities"],
                         ["mana_ability_classification", "mana_ability_controller_attribution"])
        self.assertNotEqual(rows["109.4a"]["required_capabilities"], rows["601.2g"]["required_capabilities"])

    def test_madness_path_is_indirect_and_does_not_invent_direct_605_citation(self):
        rows = self.consumers.to_dict()["indirect_dependency_flows"]
        self.assertEqual(len(rows), 1)
        flow = rows[0]
        self.assertEqual(flow["relationship_kind"], "INDIRECT_DEPENDENCY_FLOW")
        self.assertEqual(flow["retained_madness_rule"]["rule_id"], RULE_IDS["702.35b"])
        self.assertEqual(flow["path"], ["702.35b", "bounded_casting_projection", "601.2g", "605"])
        self.assertFalse(flow["new_direct_madness_to_605_citation"])
        self.assertEqual(flow["execution_readiness"], "BLOCKED")
        self.assertNotIn("605", prior_rules()["702.35b"]["direct_dependency_references"])

    def test_fictional_mana_cannot_close_either_consumer_or_classification(self):
        authority = self.consumers.to_dict()["authority_boundary"]
        self.assertEqual(authority["finding"], "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605")
        for key in ("fictional_runtime_authority_inherited", "fictional_mana_satisfies_real_605",
                    "classification_implies_execution", "one_consumer_satisfies_other_consumer"):
            self.assertFalse(authority[key])
            body = design_body(self.consumers)
            body["authority_boundary"][key] = True
            with self.subTest(promotion=key), self.assertRaises(GameplayContractError):
                type(self.consumers).create(body)
        self.assertTrue(authority["controller_attribution_distinct_from_casting_opportunity"])

    def test_thirteen_candidate_family_units_preserve_parent_and_subrule_structure(self):
        value = self.frontier.to_dict()
        rows = value["candidate_family"]
        self.assertEqual([row["rule_reference"] for row in rows], list(FAMILY))
        self.assertEqual(value["candidate_source_unit_count"], 13)
        for row in rows:
            reference = row["rule_reference"]
            with self.subTest(reference=reference):
                self.assertEqual(row["candidate_parent"], reference[:-1] if reference[-1].isalpha() else None)
                if row["candidate_parent"]:
                    self.assertIn(row["candidate_parent"], FAMILY)
                self.assertTrue(row["scope_rationale"])
                self.assertEqual(row["coverage_state"], "UNPROJECTED")
                self.assertEqual(row["evidence_status"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
                self.assertFalse(row["source_verified"])
                self.assertEqual(row["exact_source_body_and_role"], "REQUIRES_FUTURE_SOURCE_VERIFICATION")

    def test_family_minimality_is_provisional_scope_judgment_not_verified_source_claim(self):
        value = self.frontier.to_dict()["coherence_review"]
        self.assertEqual(value["finding"], "PROVISIONALLY_SMALLEST_COHERENT_PM_CANDIDATE_FAMILY")
        self.assertFalse(value["independently_verified_minimal_source_scope"])
        self.assertTrue(value["minimum_scope_requires_future_source_verification"])
        self.assertFalse(value["madness_specific_cherry_picking"])
        self.assertFalse(value["automatically_expand_scope"])
        self.assertEqual(value["source_shape_or_scope_discrepancy_action"], "STOP_FOR_SEPARATE_REVIEW")
        self.assertEqual({row["conceptual_group"] for row in self.frontier.to_dict()["candidate_family"]},
                         {"classification", "classification_persistence", "activated_behavior", "triggered_behavior", "non_mana_exclusions"})

    def test_five_candidate_outgoing_references_remain_unverified_unprojected(self):
        rows = self.frontier.to_dict()["candidate_direct_references"]
        self.assertEqual([row["rule_reference"] for row in rows], list(OUTGOING))
        for row in rows:
            with self.subTest(reference=row["rule_reference"]):
                self.assertEqual(row["relationship_status"], "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION")
                self.assertEqual(row["evidence_status"], "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED")
                self.assertEqual(row["coverage_state"], "UNPROJECTED")
                self.assertFalse(row["source_verified"])
                self.assertFalse(row["recursive_design_authorized"])
                self.assertNotIn(row["rule_reference"], prior_rules())

    def test_large_activated_and_triggered_subsystems_are_deferred_separately(self):
        value = self.frontier.to_dict()
        rows = {row["rule_reference"]: row for row in value["candidate_direct_references"]}
        self.assertEqual(rows["602.2"]["subsystem_size"], "LARGE_CORE_SUBSYSTEM")
        self.assertEqual(rows["603"]["subsystem_size"], "LARGE_CORE_SUBSYSTEM")
        self.assertEqual(rows["115.6"]["subsystem_size"], "POTENTIALLY_BOUNDED")
        self.assertEqual(rows["606"]["subsystem_size"], "POTENTIALLY_BOUNDED")
        self.assertEqual(rows["405.6c"]["subsystem_size"], "POTENTIALLY_BOUNDED_WITH_STACK_INTERACTIONS")
        self.assertTrue({"general_activated_abilities", "general_triggered_abilities", "general_controller_semantics",
                         "stack", "priority", "mana_production", "mana_pool", "payment_integration",
                         "real_card_and_effect_semantics"}.issubset(value["deferred_semantic_boundaries"]))

    def test_exactly_one_future_projection_recommendation_is_not_authorized_or_started(self):
        value = self.frontier.to_dict()["next_milestone"]
        self.assertIsInstance(value, dict)
        self.assertEqual(value["candidate"], "Bounded Mana Ability Rules Projection")
        self.assertEqual(value["exact_proposed_source_allowlist"], list(FAMILY))
        self.assertEqual(value["proposed_source_unit_count"], 13)
        self.assertEqual(value["candidate_outgoing_dependencies"], list(OUTGOING))
        self.assertEqual(value["deliberately_deferred_numbered_dependencies"], list(OUTGOING))
        self.assertTrue(value["verified_txt_required"])
        self.assertEqual(value["expected_anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
        self.assertEqual(value["expected_span_policy"], "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR")
        self.assertEqual(value["example_ownership_required"], "UNAMBIGUOUS_OR_STOP")
        self.assertTrue(value["one_line_blocks_permitted"])
        self.assertFalse(value["source_coverage_implies_execution"])
        self.assertFalse(value["authorized"])
        self.assertFalse(value["started"])

    def test_consumer_and_frontier_builders_require_concrete_design_inputs(self):
        from gameplay_rules.mana_ability_design.consumers import build_consumer_matrix
        from gameplay_rules.mana_ability_design.frontier import build_projection_frontier
        class IdentityShapedObject:
            identity = "sha256:" + "f" * 64
            def verify(self):
                return self
        for index in range(len(self.arguments)):
            arguments = list(self.arguments)
            arguments[index] = IdentityShapedObject()
            for builder in (lambda: build_consumer_matrix(self.binding, *arguments),
                            lambda: build_projection_frontier(*arguments)):
                with self.subTest(argument=index), self.assertRaises(GameplayContractError):
                    builder()


class ManaAbilityReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_ability_design.builder import build_design_package
        cls.records = build_design_package(review_root=REVIEWS)
        cls.readiness = cls.records["readiness.json"]
        cls.value = cls.readiness.to_dict()

    def test_eight_capabilities_each_retain_their_own_evidence_dependencies_and_primitives(self):
        rows = self.value["capabilities"]
        self.assertEqual([row["capability_id"] for row in rows], list(CAPABILITIES))
        for row in rows:
            with self.subTest(capability=row["capability_id"]):
                for key in ("evidence_requirements", "semantic_dependencies", "required_future_primitives", "unsupported_boundaries"):
                    self.assertTrue(row[key])
                self.assertEqual(row["source_coverage"], "DESIGN_SCOPED_605_UNPROJECTED")
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertEqual(row["implementation_status"], "NOT_IMPLEMENTED")
                self.assertEqual(row["implied_ready_capabilities"], [])
                self.assertFalse(row["required_primitives_available"])
                self.assertFalse(row["source_verified"])
                self.assertFalse(row["execution_supported"])
        self.assertNotIn("mana_abilities_supported", self.readiness.serialize())

    def test_capability_readiness_does_not_imply_another_capability(self):
        separation = self.value["capability_separation"]
        for key in ("classification_implies_execution", "classification_implies_activation",
                    "classification_implies_controller_attribution", "classification_implies_mana_production",
                    "classification_implies_mana_pool", "activation_window_implies_immediate_resolution",
                    "immediate_resolution_implies_mana_production", "mana_payment_opportunity_implies_payment",
                    "one_capability_readiness_implies_another"):
            self.assertFalse(separation[key])
            body = design_body(self.readiness)
            body["capability_separation"][key] = True
            with self.subTest(promotion=key), self.assertRaises(GameplayContractError):
                type(self.readiness).create(body)

    def test_source_coverage_is_independent_of_execution_and_605_remains_unprojected(self):
        value = self.value["source_coverage_vs_execution"]
        self.assertEqual(value["mana_ability_source_coverage"], "DESIGN_SCOPED")
        self.assertEqual(value["605_coverage_state"], "UNPROJECTED")
        self.assertEqual(value["mana_ability_execution"], "EXECUTION_BLOCKED")
        self.assertTrue(value["future_projection_may_improve_source_coverage"])
        self.assertTrue(value["execution_requires_independent_semantic_and_runtime_closure"])
        self.assertFalse(value["source_coverage_implies_execution"])
        self.assertFalse(value["future_605_projection_supplies_general_abilities"])
        body = design_body(self.readiness)
        body["source_coverage_vs_execution"]["source_coverage_implies_execution"] = True
        with self.assertRaises(GameplayContractError):
            type(self.readiness).create(body)

    def test_production_pool_and_payment_remain_absent_without_pool_design_decisions(self):
        value = self.value["production_pool_payment_boundaries"]
        for key in ("mana_production_semantics", "mana_pool_semantics", "payment_integration"):
            self.assertEqual(value[key], "BLOCKED_ABSENT")
        for key in ("pool_representation_decided", "pool_clearing_rules_decided", "spending_restrictions_decided",
                    "mana_transformations_decided", "special_purpose_mana_decided", "mana_history_decided"):
            self.assertFalse(value[key])
        rows = {row["capability_id"]: row for row in self.value["capabilities"]}
        self.assertNotEqual(rows["mana_ability_classification"]["required_future_primitives"],
                            rows["mana_production_semantics"]["required_future_primitives"])
        self.assertNotEqual(rows["mana_production_semantics"]["required_future_primitives"],
                            rows["mana_pool_semantics"]["required_future_primitives"])
        self.assertIn("payment_integration", rows["mana_pool_semantics"]["semantic_dependencies"])

    def test_fictional_authority_is_structurally_forbidden_for_every_real_capability(self):
        authority = self.value["fictional_authority"]
        self.assertEqual(authority["finding"], "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605")
        self.assertEqual(authority["accepted_real_605_execution_authority_proofs"], [])
        for key in ("fictional_mana_satisfies_real_605", "fictional_runtime_authority_inherited",
                    "fictional_kernel_accepted_as_real_evidence", "fictional_mana_output_accepted_as_real_evidence",
                    "fictional_controller_behavior_accepted_as_real_evidence", "architectural_reuse_grants_rules_authority"):
            self.assertFalse(authority[key])
            body = design_body(self.readiness)
            body["fictional_authority"][key] = True
            with self.subTest(promotion=key), self.assertRaises(GameplayContractError):
                type(self.readiness).create(body)
        for index, row in enumerate(self.value["capabilities"]):
            self.assertFalse(row["fictional_mana_satisfies_real_605"])
            self.assertFalse(row["fictional_runtime_authority_inherited"])
            for field in ("execution_readiness", "source_verified", "fictional_mana_satisfies_real_605"):
                body = design_body(self.readiness)
                body["capabilities"][index][field] = "EXECUTION_READY" if field == "execution_readiness" else True
                with self.subTest(capability=row["capability_id"], promotion=field), self.assertRaises(GameplayContractError):
                    type(self.readiness).create(body)

    def test_five_append_only_reassessments_remain_blocked_for_distinct_reasons(self):
        rows = self.value["readiness_reassessments"]
        self.assertEqual([row["capability_id"] for row in rows], ["mana_abilities", "alternative_cost_casting_subprocedure",
                         "complete_spell_casting", "object_control", "madness"])
        for row in rows:
            with self.subTest(capability=row["capability_id"]):
                self.assertEqual(row["dependency_closure"], "OPEN")
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
                self.assertFalse(row["required_primitives_available"])
                self.assertFalse(row["execution_supported"])
                self.assertTrue(row["blockers"])
                self.assertIn("605_UNPROJECTED_AND_UNIMPLEMENTED", row["blockers"])
                self.assertEqual(row["previous_casting_readiness_id"],
                                 "sha256:ea27a6f08ae9dc4696871fdbe5560587dd76f4a7e459ba458d70cb991340b38f")
        by_name = {row["capability_id"]: row for row in rows}
        self.assertEqual(by_name["mana_abilities"]["source_coverage"], "DESIGN_SCOPED")
        self.assertIn("HYPOTHETICAL_STACK_CONTROLLER_ATTRIBUTION_ABSENT", by_name["object_control"]["blockers"])
        self.assertIn("INDIRECT_CASTING_DEPENDENCY_OPEN", by_name["madness"]["blockers"])
        self.assertNotEqual(by_name["object_control"]["blockers"], by_name["alternative_cost_casting_subprocedure"]["blockers"])

    def test_existing_madness_evidence_and_consumer_bindings_are_reused_without_reprojection(self):
        retained = self.value["retained_evidence"]
        self.assertEqual(retained["projected_real_source_units"], 68)
        self.assertEqual(set(retained["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        for reference, row in retained["consumers"].items():
            self.assertEqual(row["rule_id"], RULE_IDS[reference])
            self.assertEqual(row["dependency_state"], "UNRESOLVED")
            self.assertEqual(row["dependency_coverage_state"], "UNPROJECTED")
        for row in retained["madness_rules"]:
            self.assertEqual(row["rule_id"], RULE_IDS[row["rule_reference"]])
        self.assertEqual(retained["zone_change_lookup"]["rule_id"], RULE_IDS["400.7k"])
        self.assertEqual(self.value["binding_policy"], "IMMUTABLE_RETAINED_RULE_IDENTITIES_NO_REPROJECTION")
        self.assertFalse(self.value["consumer_flow"]["madness_direct_605_citation_created"])

    def test_count_and_existing_rule_frontiers_remain_unchanged_and_profile_not_ready(self):
        self.assertEqual((self.value["projected_rule_count_before"], self.value["source_projections_added"],
                          self.value["projected_rule_count_after"]), (68, 0, 68))
        remaining = set(self.value["remaining_unprojected_numbered_boundaries"])
        self.assertTrue({*OUTGOING, "605", "613", "603.7d", "603.7e", "603.7f", "114",
                         "901.6", "902.6", "904.7", "905.5", "601.2a", "601.2c", "601.2d",
                         "601.2e", "601.2i", "601.3", "733", "700.2", "702.47", "118.8", "118.9", "107.3"}.issubset(remaining))
        self.assertTrue(self.value["required_future_primitives"])
        self.assertEqual(self.value["real_execution_primitives_available"], [])
        self.assertEqual(self.value["overall_readiness"], "EXECUTION_BLOCKED")
        self.assertEqual(self.value["real_execution_profile_readiness"], "REAL_EXECUTION_PROFILE_NOT_READY")

    def test_readiness_builder_rejects_duck_typed_or_mismatched_designs(self):
        from gameplay_rules.mana_ability_design.readiness import build_readiness
        names = ("classification-design.json", "behavior-design.json", "controller-design.json",
                 "consumer-bindings.json", "projection-frontier.json")
        arguments = [self.records[name] for name in names]
        class IdentityShapedObject:
            identity = "sha256:" + "f" * 64
            def verify(self):
                return self
        for index in range(len(arguments)):
            changed = list(arguments)
            changed[index] = IdentityShapedObject()
            with self.subTest(argument=index), self.assertRaises(GameplayContractError):
                build_readiness(self.value["retained_evidence"], *changed)
        changed = list(arguments)
        body = design_body(changed[0])
        body["design_notes"] = [*body["design_notes"], "A separately scoped synthetic classification review."]
        changed[0] = type(changed[0]).create(body)
        with self.assertRaises(GameplayContractError):
            build_readiness(self.value["retained_evidence"], *changed)


if __name__ == "__main__":
    unittest.main()
