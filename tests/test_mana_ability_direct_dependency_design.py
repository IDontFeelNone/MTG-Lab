"""Offline immutable scope-design proofs; no CR artifact or real abilities.

Preservation inventories are independent snapshots of canonical main
a9943fc8ca89ced4d3d288926f63fede12f4b57a (313 source and 185 review files).
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
PACKAGE = REVIEWS / "gameplay-rules-mana-direct-dependency-design"
CODE = ROOT / "src/gameplay_rules/mana_dependency_design"
CANONICAL = "a9943fc8ca89ced4d3d288926f63fede12f4b57a"
PM_INPUT = "PM_SUPPLIED_DESIGN_INPUT_NOT_SOURCE_VERIFIED"
HISTORICAL = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
FAMILY = ("605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a", "605.3b", "605.3c",
          "605.4", "605.4a", "605.5", "605.5a", "605.5b")
FRONTIER = ("115.6", "606", "602.2", "405.6c", "603")
VERIFIED_EDGES = (("605.1a", "115.6"), ("605.1a", "606"), ("605.1b", "115.6"),
                  ("605.3", "602.2"), ("605.3b", "405.6c"), ("605.4", "603"))
FILES = {"classification-dependencies.json", "activated-procedure-design.json", "triggered-procedure-design.json",
         "stack-context-design.json", "consumer-bindings.json", "dependency-groups.json", "readiness.json", "manifest.json"}
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
    "gameplay-rules-bounded-mana-ability-projection": "sha256:010ab048c504b4da4327dbda4a666a6754f2d41e93b73ea34bc595b39c929990",
}
RULE_IDS = {
    "601.2g": "sha256:7c01241cb591680e28dd16dd3c97b88b28ebcdaca80af8c153a5891e1363a662",
    "109.4a": "sha256:7793b14d8f2af5916dd02316ff0ea817d77b0bf656284c0f56d86b3f743fcea1",
    "109.4b": "sha256:d99dc32d944ad4ed333f0c8a7f64ec02aeaf4eedda8587fb48692564f4527a35",
    "605.1": "sha256:55feae19cf15baf6f9d2a5be09dd481f9198753dd9e5b9d85896fab985fb32ea",
    "605.1a": "sha256:636589285118095428a73c1245f5136efce8a129bba67e87f7abec7f142d8a06",
    "605.1b": "sha256:286cd92f7eaae924695a5841a90b4eade3eb66626a3419113bc44f6c0138d495",
    "605.2": "sha256:355f35759b1329e2a43513cee35f991649c7592d6c42a69db3af032eca5ee117",
    "605.3": "sha256:69a1bf6415c5506f9ad6596f3ef47864945b68376a0bf9ec7e1398854d8d63e1",
    "605.3a": "sha256:b996ad86f817a1d69ed179f5b299c6efe56591ff363d162dba64318c98f4c562",
    "605.3b": "sha256:64c8d9dffd2a31ad715d214fda4fb650c217f5bd803b72dcb65663cc03a73e04",
    "605.3c": "sha256:c00f9b451db7dcce795fcfb2b1c53a192610feb2c3112a0d73bf155f4709039c",
    "605.4": "sha256:1edd1b1e496b4b645efce70f9c60a5d09503f72efafdd901cfe522d52015da3d",
    "605.4a": "sha256:606df6d71f6a18f3648491c5b1134375988426f2598beef50b41d864c2572d5a",
    "605.5": "sha256:5c012081237767afe28ba1354e955a16e5cee439ac581535e444bb51169bcdb0",
    "605.5a": "sha256:0abcb8e6b2cf59ab74af50183c60f085cc9995521b1af6a4461d2d8e37da9a5e",
    "605.5b": "sha256:c00c026c3dba8e68cdc835fa8ddc92532f11c70a3926b22354e3f0fd96ebc0d9",
}


def regular_files(root):
    # This later append-only milestone is outside the historical inventory.
    return [p for p in _historical_regular_files(root)
            if not (p.parent == ROOT / "src/gameplay_rules/projection" and p.name.startswith("mana_classification_"))
            and "gameplay-rules-bounded-mana-classification-projection" not in p.parts]


def _historical_regular_files(root):
    return [p for p in root.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]


def inventory(paths):
    values = []
    for path in sorted(set(paths)):
        if path.is_symlink():
            raise AssertionError("Protected file must remain regular")
        raw = path.read_bytes()
        values.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return values


def prior_rules():
    rules = {}
    for package in PRIOR_PACKAGES:
        path = REVIEWS / package / "projection.json"
        if path.is_file():
            for rule in json.loads(path.read_bytes())["rules"]:
                if rule["rule_reference"] in rules:
                    raise AssertionError("Historical projections must remain disjoint")
                rules[rule["rule_reference"]] = rule
    return rules


def body(record):
    value = record.to_dict()
    return {key: value[key] for key in record.BODY_FIELDS}


class ManaDirectPreservationTests(unittest.TestCase):
    def test_all_313_source_files_preserve_engine_fictional_products_policy_writer_and_simulation(self):
        values = inventory(p for p in regular_files(ROOT / "src") if CODE not in p.parents)
        self.assertEqual(len(values), 313)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "4ce99b42367df7524fa3c5cb5f63ea472abca3a20647cb21aebee8324514d558")

    def test_all_185_prior_review_files_and_ten_package_identities_unchanged(self):
        values = inventory(p for p in regular_files(REVIEWS) if PACKAGE not in p.parents)
        self.assertEqual(len(values), 185)
        self.assertEqual(hashlib.sha256(deterministic_json(values).encode()).hexdigest(),
                         "909facca7e22f089a0cb9c422cdf931f5d2321167b00c23009f44c98e4f711d7")
        for package, identity in PRIOR_PACKAGES.items():
            with self.subTest(package=package):
                self.assertEqual(json.loads((REVIEWS / package / "manifest.json").read_bytes())["package_id"], identity)

    def test_eighty_one_real_units_remain_disjoint_and_all_new_frontiers_unprojected(self):
        rules = prior_rules()
        self.assertEqual(len(rules), 81)
        blocked = {*FRONTIER, "606.1", "606.2", "606.3", "606.4", "606.5", "606.6", "405.6",
                   "602.2a", "602.2b", "701.20a", "603.7", "603.7d", "603.7e", "603.7f", "114",
                   "901.6", "902.6", "904.7", "905.5", "613", "601.2a", "601.2c", "601.2d", "601.2e",
                   "601.2i", "601.3", "733", "700.2", "702.47", "118.8", "118.9", "107.3"}
        self.assertTrue(blocked.isdisjoint(rules))
        self.assertNotIn("605", rules)
        self.assertFalse((PACKAGE / "projection.json").exists())

    def test_existing_605_consumers_and_entire_family_identities_remain_exact(self):
        rules = prior_rules()
        for reference, identity in RULE_IDS.items():
            with self.subTest(reference=reference):
                self.assertEqual(rules[reference]["rule_id"], identity)
        projection = json.loads((REVIEWS / "gameplay-rules-bounded-mana-ability-projection/projection.json").read_bytes())
        self.assertEqual(projection["projection_id"], "sha256:c9432ee880d150d92b88096092cb999dc88fd423c1228bc04bbd284b2b2e1832")
        self.assertEqual([row["rule_reference"] for row in projection["rules"]], list(FAMILY))

    def test_verified_six_citation_edges_preserve_five_target_frontier_exactly(self):
        rules = prior_rules()
        edges = tuple((origin, target) for origin in FAMILY for target in rules[origin]["direct_dependency_references"]
                      if target not in FAMILY)
        self.assertEqual(edges, VERIFIED_EDGES)
        self.assertEqual(set(target for _, target in edges), set(FRONTIER))
        self.assertEqual(rules["109.4b"]["direct_dependency_references"], ["603", "603.7d", "603.7e", "603.7f"])
        for reference in ("109.4a", "601.2g"):
            self.assertEqual(rules[reference]["direct_dependency_references"], ["605"])

    def test_historical_anchors_unchanged_and_fictional_authority_still_separate(self):
        for reference, rule in prior_rules().items():
            policy = "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR" if reference.startswith("605.") or reference in {
                "601.2", "601.2b", "601.2f", "601.2g", "601.2h"} else "EXACT_RULE_LINE_EXCLUDING_LINE_TERMINATOR"
            self.assertEqual(rule["source_anchor"]["span_policy"], policy)
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        self.assertEqual({p.name for p in (ROOT / "src/simulation").iterdir() if p.name != "__pycache__"}, {".gitkeep"})

    def test_architecture_v13_decision_017_and_historical_replay_bytes_preserved(self):
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

    def test_namespace_has_no_runtime_network_ingestion_or_source_projection_path(self):
        imports = {"socket", "http", "urllib", "requests", "subprocess", "random", "simulation", "providers",
                   "external_ingestion", "market", "production_evidence"}
        runtime = {"GameplayRulesSnapshot", "GameplayRulesEngine", "CardGameplaySemantics", "GameState", "GameAction",
                   "LegalityResult", "GameTransition", "RawSnapshotStore"}
        functions = {"classify_mana_ability", "classify_loyalty_ability", "parse_targets", "select_targets", "activate_ability",
                     "detect_trigger", "execute_trigger", "resolve_ability", "produce_mana", "add_mana", "spend_mana",
                     "pay_cost", "assign_controller", "to_rules_snapshot", "to_execution_profile", "activate_profile",
                     "verify_source_artifact", "parse_comprehensive_rules", "locate_rule_anchors"}
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


class ManaDirectPackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_dependency_design.builder import build_design_package
        from gameplay_rules.mana_dependency_design.package import load_design_package, write_design_package, package_manifest
        cls.build = staticmethod(build_design_package)
        cls.load = staticmethod(load_design_package)
        cls.write = staticmethod(write_design_package)
        cls.manifest = staticmethod(package_manifest)
        cls.records = cls.load(PACKAGE, review_root=REVIEWS)

    def test_exact_canonical_seven_design_only_records_zero_new_projection_or_authority(self):
        self.assertEqual(set(self.records), FILES - {"manifest.json"})
        self.assertEqual({p.name for p in PACKAGE.iterdir()}, FILES)
        for record in self.records.values():
            value = record.to_dict()
            self.assertEqual(value["canonical_base"], CANONICAL)
            self.assertEqual(value["release_date"], "2026-09-25")
            self.assertEqual(value["status"], "DESIGN_ONLY")
            self.assertTrue(value["design_only"])
            self.assertTrue(value["non_executable"])
            self.assertEqual(value["new_source_units_projected"], 0)
            self.assertEqual(value["projected_real_source_units"], 81)
            for flag in ("source_artifact_required", "execution_authorized", "projection_authorized", "source_verification_claimed",
                         "source_body_retained", "real_rules_executable", "oracle_ingested", "real_snapshot_created", "real_profile_activated"):
                self.assertFalse(value[flag])

    def test_source_policy_and_all_permission_states_unchanged(self):
        for record in self.records.values():
            value = record.to_dict()
            self.assertEqual(value["source_policy_clearance"], "not_granted")
            self.assertEqual(value["owner_execution_approval"], "NOT_GRANTED")
            self.assertEqual(value["permissions"], {name: "NOT_ESTABLISHED" for name in
                ("private_retention", "redistribution", "free_service", "commercial_service", "ai_export")})

    def test_manifest_pins_design_identities_and_exact_81_zero_81_coverage(self):
        value = json.loads((PACKAGE / "manifest.json").read_bytes())
        self.assertEqual(value["canonical_base"], CANONICAL)
        self.assertEqual((value["projected_rule_count_before"], value["new_source_units_projected"],
                          value["projected_rule_count_after"]), (81, 0, 81))
        self.assertEqual(value["additional_rules_projected"], [])
        self.assertFalse(value["source_artifact_required"])
        self.assertFalse(value["source_anchors_created"])
        self.assertFalse(value["source_verification_claimed"])
        self.assertEqual(value["historical_acquisition_identity"], HISTORICAL)
        self.assertEqual(set(value["retained_evidence_binding"]["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(value["record_ids"], {record.ID_FIELD: record.identity for record in self.records.values()})
        raw = {name: (record.serialize() + "\n").encode() for name, record in self.records.items()}
        self.assertEqual(self.manifest(self.records, raw), value)

    def test_roundtrip_determinism_unique_identities_and_deep_immutability(self):
        self.assertEqual(len({record.identity for record in self.records.values()}), 7)
        for record in self.records.values():
            with self.subTest(record=type(record).__name__):
                self.assertEqual(type(record).from_json(record.serialize()), record)
                self.assertEqual(type(record).create(body(record)), record)
                self.assertEqual(record.serialize(), deterministic_json(record.to_dict()))
                self.assertEqual(record.verify(), record)
                self.assertRegex(record.identity, r"^sha256:[0-9a-f]{64}$")
                for key, value in (("_payload", {}), ("status", "EXECUTABLE"), ("unreviewed_attribute", True)):
                    with self.assertRaises((FrozenInstanceError, AttributeError, TypeError)):
                        setattr(record, key, value)
                with self.assertRaises(TypeError):
                    record._payload["status"] = "EXECUTABLE"
                with self.assertRaises(TypeError):
                    record._payload["permissions"]["ai_export"] = "GRANTED"
                detached = record.to_dict()
                detached["permissions"]["ai_export"] = "GRANTED"
                self.assertEqual(record.permissions["ai_export"], "NOT_ESTABLISHED")

    def test_false_source_authority_runtime_and_schema_promotions_rejected(self):
        for record in self.records.values():
            for field, value in ((record.ID_FIELD, "sha256:" + "f" * 64), ("schema_version", "changed"),
                                 ("source_verification_claimed", True), ("new_source_units_projected", 1),
                                 ("execution_authorized", True), ("projection_authorized", True),
                                 ("source_policy_clearance", "granted"), ("real_profile_activated", True)):
                changed = record.to_dict()
                changed[field] = value
                with self.subTest(record=type(record).__name__, field=field), self.assertRaises(GameplayContractError):
                    type(record).from_dict(changed)

    def test_duplicate_nonfinite_unknown_json_and_new_source_anchor_fields_rejected(self):
        record = self.records["classification-dependencies.json"]
        with self.assertRaises(GameplayContractError):
            type(record).from_json(record.serialize()[:-1] + ',"status":"DESIGN_ONLY"}')
        with self.assertRaises(GameplayContractError):
            type(record).from_json(record.serialize()[:-1] + ',"unknown":NaN}')
        for field in ("source_anchor", "source_text", "official_text", "source_excerpt", "oracle_text"):
            changed = body(record)
            changed[field] = {"rule_reference": "115.6"}
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                type(record).create(changed)

    def test_offline_rebuild_forbids_txt_network_raw_retention_and_external_source_verification(self):
        real_read_bytes = Path.read_bytes
        def source_free_read(path):
            if path.suffix.lower() == ".txt" or "codex-remote-attachments" in path.parts:
                raise AssertionError("No external source artifact may be accessed for this design")
            return real_read_bytes(path)
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ, {}, clear=True))
            stack.enter_context(patch.object(Path, "read_bytes", source_free_read))
            stack.enter_context(patch("socket.socket", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("urllib.request.urlopen", side_effect=AssertionError("network forbidden")))
            stack.enter_context(patch("acquisition.framework.RawSnapshotStore.store", side_effect=AssertionError("retention forbidden")))
            for module in ("source", "dependency_source", "object_control_source", "zone_change_source", "zone_change_dependency_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + "._verified_bytes",
                                          side_effect=AssertionError("source verification forbidden")))
            for module in ("bounded_casting_source", "bounded_mana_source"):
                stack.enter_context(patch("gameplay_rules.projection." + module + ".verify_" +
                                          ("bounded_casting_bytes" if module.startswith("bounded_casting") else "bounded_mana_bytes"),
                                          side_effect=AssertionError("source verification forbidden")))
            self.assertEqual(self.build(review_root=REVIEWS), self.records)
            self.assertEqual(self.load(PACKAGE, review_root=REVIEWS), self.records)

    def test_records_cannot_be_loaded_as_gameplay_snapshots_or_profiles(self):
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

    def test_retained_package_has_no_source_body_anchor_txt_or_attachment_path(self):
        forbidden = {"source_anchor", "source_anchors", "span_sha256", "byte_start", "byte_end", "line_number",
                     "source_text", "source_prose", "official_text", "official_examples", "oracle_text", "raw_source", "source_excerpt"}
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

    def test_each_meaningful_design_input_change_changes_identity(self):
        for record in self.records.values():
            changed_body = body(record)
            changed_body["design_notes"] = [*changed_body["design_notes"], "A different synthetic scope-review observation."]
            changed = type(record).create(changed_body)
            self.assertNotEqual(changed.identity, record.identity)
            self.assertEqual(changed, type(record).create(changed_body))

    def test_tampered_missing_extra_source_txt_and_directory_packages_rejected(self):
        for mutation in ("tamper", "missing", "txt", "source", "directory"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / "classification-dependencies.json"
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

    def test_symlink_hardlink_root_and_ancestor_symlink_packages_rejected(self):
        for link in ("symlink", "hardlink", "root-symlink", "ancestor-symlink"):
            with self.subTest(link=link), tempfile.TemporaryDirectory() as tmp:
                container = Path(tmp) / "container"
                container.mkdir()
                root = container / "package"
                shutil.copytree(PACKAGE, root)
                path = root / "classification-dependencies.json"
                load_root = root
                if link in {"symlink", "hardlink"}:
                    target = Path(tmp) / "outside.json"
                    path.rename(target)
                    if link == "symlink":
                        path.symlink_to(target)
                    else:
                        os.link(target, path)
                elif link == "root-symlink":
                    load_root = Path(tmp) / "package-alias"
                    load_root.symlink_to(root, target_is_directory=True)
                else:
                    alias = Path(tmp) / "ancestor-alias"
                    alias.symlink_to(container, target_is_directory=True)
                    load_root = alias / "package"
                with self.assertRaises(GameplayContractError):
                    self.load(load_root, review_root=REVIEWS)

    def test_noncanonical_json_rejected_for_every_retained_file(self):
        for name in FILES:
            with self.subTest(file=name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp) / "package"
                shutil.copytree(PACKAGE, root)
                path = root / name
                path.write_text(json.dumps(json.loads(path.read_bytes()), indent=2) + "\n")
                with self.assertRaises(GameplayContractError):
                    self.load(root, review_root=REVIEWS)

    def test_deterministic_offline_relocation_rebuild_and_append_only_write(self):
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

    def test_rehashed_modified_design_is_not_accepted_as_retained_reproduction(self):
        records = dict(self.records)
        record = records["readiness.json"]
        changed = body(record)
        changed["design_notes"] = [*changed["design_notes"], "A separately authored synthetic review statement."]
        records["readiness.json"] = type(record).create(changed)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "altered"
            self.write(root, records)
            with self.assertRaises(GameplayContractError):
                self.load(root, review_root=REVIEWS)

    def test_retained_evidence_tampering_rejected_without_external_source_access(self):
        with tempfile.TemporaryDirectory() as tmp:
            reviews = Path(tmp) / "reviews"
            shutil.copytree(REVIEWS, reviews)
            path = reviews / "gameplay-rules-bounded-mana-ability-projection/projection.json"
            path.write_bytes(path.read_bytes().replace(RULE_IDS["605.1a"].encode(), ("sha256:" + "f" * 64).encode()))
            with self.assertRaises(GameplayContractError):
                self.build(review_root=reviews)
            with self.assertRaises(GameplayContractError):
                self.load(PACKAGE, review_root=reviews)

    def test_package_rejects_mismatched_links_and_untyped_record_dictionaries(self):
        records = dict(self.records)
        record = records["classification-dependencies.json"]
        changed = body(record)
        changed["design_notes"] = [*changed["design_notes"], "A distinct synthetic classification grouping input."]
        records["classification-dependencies.json"] = type(record).create(changed)
        with self.assertRaises(GameplayContractError):
            self.manifest(records)
        records = dict(self.records)
        records["classification-dependencies.json"] = record.to_dict()
        with self.assertRaises(GameplayContractError):
            self.manifest(records)


class ManaDirectClassificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_dependency_design.classification import build_classification_design
        cls.record = build_classification_design()
        cls.value = cls.record.to_dict()

    def test_115_6_is_bounded_with_three_distinct_target_concepts(self):
        value = self.value["target_requirement_design"]
        self.assertEqual(value["dependency_reference"], "115.6")
        self.assertEqual(value["dependency_classification"], "BOUNDED_DIRECT_DEPENDENCY")
        self.assertEqual(value["consumer_references"], ["605.1a", "605.1b"])
        self.assertEqual(value["separate_concepts"], ["target_requirement_semantics", "current_targets_chosen", "target_legality"])
        self.assertFalse(value["target_requirement_equals_current_target_count"])
        self.assertFalse(value["target_requirement_equals_target_legality"])

    def test_zero_chosen_targets_do_not_erase_declared_requirement_or_infer_legality(self):
        rows = self.value["target_requirement_design"]["synthetic_declarations"]
        self.assertEqual(rows[0]["declared_requires_target"], True)
        self.assertEqual(rows[0]["declared_current_targets_chosen"], 0)
        self.assertEqual(rows[1]["declared_requires_target"], "UNKNOWN")
        for row in rows:
            self.assertEqual(row["fixture_kind"], "SYNTHETIC_ONLY")
            self.assertEqual(row["declared_target_legality"], "UNKNOWN")
            self.assertFalse(row["target_requirement_evaluated"])
            self.assertFalse(row["target_selection_performed"])
            self.assertFalse(row["target_legality_evaluated"])

    def test_115_6_standalone_scope_is_provisional_without_general_target_parser(self):
        value = self.value["target_requirement_design"]
        scope = value["standalone_scope_assessment"]
        self.assertEqual(scope["proposed_source_allowlist"], ["115.6"])
        self.assertFalse(scope["source_coherence_independently_verified"])
        self.assertTrue(scope["future_exact_source_verification_required"])
        for key in ("general_target_recognition_satisfied", "general_target_parser_available", "target_legality_satisfied"):
            self.assertFalse(scope[key])
        self.assertTrue({"activated_ability_target_grammar", "triggered_ability_target_grammar", "keyword_defined_targets",
                         "real_card_and_effect_semantics"}.issubset(value["unresolved_semantic_boundaries"]))
        self.assertEqual(value["additional_numbered_dependencies_claimed"], [])

    def test_loyalty_classification_and_execution_are_independent(self):
        value = self.value["loyalty_scope_comparison"]
        self.assertEqual(value["classification_capability"], "loyalty_ability_classification")
        self.assertEqual(value["execution_capability"], "loyalty_ability_execution")
        self.assertFalse(value["classification_implies_execution"])
        self.assertFalse(value["real_loyalty_classifier_available"])
        self.assertTrue({"timing", "stack_state", "main_phase_state", "prior_activation_history", "loyalty_counter_costs",
                         "cost_payment", "permanent_state", "controller_state"}.issubset(value["execution_requirements_remaining"]))

    def test_two_loyalty_scopes_compare_coherence_consumer_value_and_section_policy(self):
        value = self.value["loyalty_scope_comparison"]
        a, b = value["candidates"]
        self.assertEqual(a["source_allowlist"], ["606.1", "606.2"])
        self.assertEqual(b["source_allowlist"], ["606.1", "606.2", "606.3", "606.4", "606.5", "606.6"])
        self.assertEqual((a["source_unit_count"], b["source_unit_count"]), (2, 6))
        self.assertEqual(value["preferred_candidate"], "A_CLASSIFICATION_ONLY")
        self.assertTrue(value["preference_basis"])
        self.assertGreater(len(value["comparison_criteria"]), 3)
        self.assertFalse(a["broad_606_section_reference_resolved"])
        self.assertEqual(a["behavior_units_remaining_unprojected"], ["606.3", "606.4", "606.5", "606.6"])

    def test_classification_only_coverage_never_closes_broad_606_reference(self):
        policy = self.value["loyalty_scope_comparison"]["section_reference_policy"]
        self.assertFalse(policy["classification_only_coverage_closes_broad_606_reference"])
        self.assertFalse(policy["existing_605_1a_direct_dependency_rewritten"])
        self.assertEqual(policy["classification_relationship"], "NARROWER_THAN_FULL_SECTION_REFERENCE_RESOLUTION")
        self.assertEqual(policy["broad_section_dependency_state_after_classification_only"], "PARTIALLY_REPRESENTED_BEHAVIOR_SCOPE_OPEN")
        self.assertTrue(policy["future_reassessment_required"])

    def test_every_loyalty_candidate_remains_unverified_unprojected_pm_input(self):
        value = self.value["loyalty_scope_comparison"]
        for row in [unit for candidate in value["candidates"] for unit in candidate["units"]] + value["deferred_behavior_units"]:
            with self.subTest(reference=row["rule_reference"]):
                self.assertEqual(row["evidence_status"], PM_INPUT)
                self.assertEqual(row["coverage_state"], "UNPROJECTED")
                self.assertFalse(row["source_verified"])
                self.assertNotIn(row["rule_reference"], prior_rules())

    def test_narrow_classification_projection_is_exact_three_unit_unauthorized_candidate(self):
        value = self.value["proposed_classification_projection"]
        self.assertEqual(value["exact_provisional_source_allowlist"], ["115.6", "606.1", "606.2"])
        self.assertEqual(value["proposed_source_unit_count"], 3)
        self.assertEqual(value["target_consumers"], ["605.1a", "605.1b"])
        self.assertTrue(value["verified_txt_required_for_future_projection"])
        self.assertEqual(value["expected_anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
        self.assertEqual(value["expected_span_policy"], "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR")
        for key in ("source_verified", "broad_606_section_resolution_claimed", "historical_anchor_conversion", "authorized", "started"):
            self.assertFalse(value[key])

    def test_classification_knowledge_cannot_be_promoted_to_parser_execution_or_section_closure(self):
        record = self.record
        for field in ("source_coverage_implies_execution", "narrow_dependency_coverage_implies_full_section_resolution",
                      "target_requirement_semantics_implies_target_parser", "loyalty_classification_implies_loyalty_execution",
                      "real_ability_classification_available", "runtime_implemented"):
            changed = body(record)
            changed["classification_boundaries"][field] = True
            with self.subTest(promotion=field), self.assertRaises(GameplayContractError):
                type(record).create(changed)


class ManaDirectConsumerGroupingReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_dependency_design.builder import build_design_package
        from gameplay_rules.mana_dependency_design.evidence import load_retained_evidence
        cls.binding = load_retained_evidence(REVIEWS)
        cls.records = build_design_package(review_root=REVIEWS)
        cls.consumers = cls.records["consumer-bindings.json"]
        cls.grouping = cls.records["dependency-groups.json"]
        cls.readiness = cls.records["readiness.json"]

    def test_anchor_free_evidence_binds_ten_packages_81_units_seven_components_and_exact_verified_frontier(self):
        binding = self.binding
        self.assertEqual(binding["source_evidence_scope"], "VERIFIED_CITATION_EXISTENCE_ONLY_TARGET_BODIES_NOT_NEWLY_VERIFIED")
        self.assertEqual(binding["projected_real_source_units"], 81)
        self.assertEqual(set(binding["prior_package_ids"].values()), set(PRIOR_PACKAGES.values()))
        self.assertEqual(binding["frontier_references"], list(FRONTIER))
        edges = binding["frontier_edges"]
        self.assertEqual(tuple((row["from_reference"], row["target_reference"]) for row in edges), VERIFIED_EDGES)
        for row in edges:
            self.assertEqual(row["from_rule_id"], RULE_IDS[row["from_reference"]])
            self.assertEqual(row["evidence_basis"], "VERIFIED_SELECTED_SOURCE_BLOCK_CITATION")
            self.assertEqual(row["reference_state"], "UNRESOLVED")
            self.assertEqual(row["coverage_state"], "UNPROJECTED")
        components = binding["projection_components"]
        self.assertEqual(len(components), 7)
        self.assertEqual(len({row["projection_id"] for row in components.values()}), 7)
        self.assertEqual(sum(len(row["projected_references"]) for row in components.values()), 81)
        self.assertEqual(binding["historical_acquisition_identity"], HISTORICAL)

    def test_consumer_matrix_contains_seven_unchanged_actual_direct_citation_arrays(self):
        value = self.consumers.to_dict()
        self.assertEqual(value["retained_evidence_binding"], self.binding)
        rows = value["consumer_bindings"]
        self.assertEqual([row["consumer_reference"] for row in rows],
                         ["605.1a", "605.1b", "605.3", "605.3b", "605.4", "109.4b", "601.2g"])
        for row in rows:
            ref = row["consumer_reference"]
            self.assertEqual(row["consumer_evidence"]["rule_id"], RULE_IDS[ref])
            self.assertEqual(row["existing_direct_citations"], prior_rules()[ref]["direct_dependency_references"])
            self.assertEqual(row["citation_basis"], "UNCHANGED_RETAINED_PROJECTION_REFERENCES")
            self.assertEqual(row["capability_requirement_status"], PM_INPUT)
            self.assertFalse(row["capability_requirements_are_new_direct_citations"])
            self.assertFalse(row["retained_rule_mutated"])
            self.assertFalse(row["broad_605_reference_rewritten"])
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "BLOCKED")

    def test_classification_consumers_bind_target_requirement_loyalty_trigger_and_card_boundaries(self):
        rows = {row["consumer_reference"]: row for row in self.consumers.to_dict()["consumer_bindings"]}
        self.assertEqual(rows["605.1a"]["required_capabilities"],
                         ["target_requirement_semantics", "loyalty_ability_classification", "real_ability_and_card_semantics"])
        self.assertEqual(rows["605.1b"]["required_capabilities"],
                         ["target_requirement_semantics", "trigger_relationship_semantics", "real_ability_and_card_semantics"])
        self.assertIn("self_replacement_semantics", rows["605.1a"]["remaining_semantic_boundaries"])
        self.assertIn("trigger_event_detection", rows["605.1b"]["remaining_semantic_boundaries"])

    def test_behavior_controller_and_casting_consumers_reuse_separate_shared_requirements(self):
        rows = {row["consumer_reference"]: row for row in self.consumers.to_dict()["consumer_bindings"]}
        self.assertEqual(rows["605.3"]["required_capabilities"], ["general_activated_ability_procedure"])
        self.assertEqual(rows["605.3b"]["required_capabilities"], ["mana_ability_stack_exception_context"])
        self.assertEqual(rows["605.4"]["required_capabilities"], ["general_triggered_ability_subsystem"])
        self.assertEqual(rows["109.4b"]["required_capabilities"],
                         ["triggered_ability_controller_attribution", "delayed_trigger_controller_attribution"])
        self.assertIn("general_triggered_ability_subsystem", rows["109.4b"]["remaining_semantic_boundaries"])
        self.assertTrue({"mana_ability_classification", "activated_mana_ability_activation_window",
                         "activated_mana_ability_immediate_resolution", "mana_payment_opportunity"}.issubset(rows["601.2g"]["required_capabilities"]))
        self.assertEqual(rows["601.2g"]["section_reference_state"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertEqual(rows["601.2g"]["existing_direct_citations"], ["605"])

    def test_madness_and_hypothetical_controller_flows_do_not_invent_frontier_citations(self):
        value = self.consumers.to_dict()
        madness, controller = value["indirect_dependency_flows"]
        self.assertEqual(madness["relationship_kind"], "INDIRECT_DEPENDENCY_FLOW")
        self.assertEqual(madness["path"], ["702.35b", "bounded_casting_projection", "601.2g", "605", "mana_direct_dependency_groups"])
        self.assertFalse(madness["new_direct_madness_to_frontier_citation"])
        self.assertEqual(controller["consumer_reference"], "109.4a")
        self.assertEqual(controller["consumer_evidence"]["rule_id"], RULE_IDS["109.4a"])
        self.assertEqual(controller["existing_direct_citations"], ["605"])
        self.assertEqual(controller["required_future_primitive"], "hypothetical_stack_controller_attribution")
        self.assertFalse(controller["actual_stack_presence_required"])
        self.assertFalse(controller["new_direct_frontier_citation"])
        self.assertEqual(value["authority_boundary"]["new_direct_cr_citations_created"], [])
        self.assertFalse(value["authority_boundary"]["existing_direct_dependency_arrays_rewritten"])

    def test_one_shared_triggered_subsystem_does_not_close_distinct_consumers(self):
        policy = self.consumers.to_dict()["shared_subsystem_policy"]
        self.assertEqual(policy["triggered_subsystem_id"], "general_triggered_ability_subsystem")
        self.assertEqual(policy["shared_consumers"], ["605.4", "109.4b"])
        self.assertFalse(policy["separate_mana_and_controller_trigger_models_permitted"])
        self.assertTrue(policy["controller_attribution_distinct_from_casting_opportunity"])
        self.assertFalse(policy["one_consumer_readiness_closes_another"])

    def test_four_groups_partition_exactly_the_five_verified_frontier_targets(self):
        rows = self.grouping.to_dict()["dependency_groups"]
        self.assertEqual([row["group_id"] for row in rows], ["A", "B", "C", "D"])
        self.assertEqual([row["capability_group"] for row in rows], ["mana_classification_dependencies", "mana_stack_exception_context",
                         "general_activated_ability_procedure", "general_triggered_ability_subsystem"])
        members = [ref for row in rows for ref in row["verified_frontier_members"]]
        self.assertEqual(set(members), set(FRONTIER))
        self.assertEqual(len(members), 5)
        self.assertEqual(rows[0]["provisional_local_source_scope"], ["115.6", "606.1", "606.2"])
        self.assertEqual(rows[1]["provisional_local_source_scope"], ["405.6c"])
        self.assertEqual(rows[2]["classification"], "LARGE_CORE_SUBSYSTEM")
        self.assertEqual(rows[3]["classification"], "LARGE_SHARED_CORE_SUBSYSTEM")
        self.assertEqual(rows[3]["primary_consumers"], ["605.4", "109.4b"])
        for row in rows:
            self.assertEqual(row["body_observation_status"], PM_INPUT)
            self.assertFalse(row["candidate_source_units_verified"])
            self.assertEqual(row["execution_readiness"], "BLOCKED")

    def test_grouping_rejects_single_ability_engine_and_rule_count_only_selection(self):
        value = self.grouping.to_dict()
        policy = value["selection_policy"]
        self.assertFalse(policy["generic_single_ability_engine_group_created"])
        self.assertTrue(policy["activated_and_triggered_subsystems_independent"])
        self.assertFalse(policy["rule_count_alone_decides"])
        self.assertFalse(policy["largest_shared_dependency_automatically_wins"])
        self.assertEqual(policy["recommended_milestone_count"], 1)
        self.assertGreater(len(value["selection_criteria"]), 3)
        comparisons = value["candidate_comparison"]
        self.assertEqual(len(comparisons), 4)
        self.assertEqual([row["selection_state"] for row in comparisons].count("RECOMMENDED_NOT_AUTHORIZED"), 1)
        self.assertEqual(comparisons[1]["proposed_source_unit_count"], 1)
        self.assertTrue(all(row["decision_rationale"] for row in comparisons))

    def test_exactly_one_next_milestone_has_exact_three_unit_scope_and_unit_rationales(self):
        value = self.grouping.to_dict()["next_milestone"]
        self.assertEqual(value["candidate"], "Bounded Mana Classification Dependency Projection")
        self.assertEqual(value["exact_proposed_source_allowlist"], ["115.6", "606.1", "606.2"])
        self.assertEqual(value["proposed_source_unit_count"], 3)
        self.assertEqual([row["rule_reference"] for row in value["source_unit_rationales"]], ["115.6", "606.1", "606.2"])
        self.assertTrue(all(row["reason"] for row in value["source_unit_rationales"]))
        self.assertEqual(value["target_consumers"], ["605.1a", "605.1b"])
        self.assertEqual(value["indirect_beneficiaries"], ["601.2g", "109.4a", "madness"])
        self.assertEqual(value["body_observation_status"], PM_INPUT)
        self.assertTrue(value["exact_scope_requires_future_source_verification"])
        self.assertFalse(value["authorized"])
        self.assertFalse(value["started"])

    def test_next_projection_requires_txt_block_policy_fail_closed_scope_and_keeps_broad_606_open(self):
        value = self.grouping.to_dict()["next_milestone"]
        self.assertTrue(value["verified_txt_required"])
        self.assertEqual(value["expected_anchor_type"], "MULTI_LINE_RULE_BLOCK_ANCHOR")
        self.assertEqual(value["expected_span_policy"], "EXACT_RULE_BLOCK_RAW_BYTES_EXCLUDING_FINAL_LINE_TERMINATOR")
        self.assertEqual(value["internal_terminators"], "PRESERVE_RAW_BYTES")
        self.assertEqual(value["final_terminator"], "EXCLUDED")
        self.assertEqual(value["example_ownership_required"], "UNAMBIGUOUS_OR_STOP")
        self.assertTrue(value["one_line_blocks_permitted"])
        self.assertFalse(value["broad_606_section_resolved_by_classification_scope"])
        self.assertEqual(value["expected_606_relationship"], "CLASSIFICATION_CONTEXT_REPRESENTED_SECTION_REMAINS_OPEN")
        self.assertFalse(value["source_coverage_implies_execution"])
        self.assertTrue({"broad_606_section_reference", "606.3", "606.4", "606.5", "606.6", "602.2", "405.6c", "603",
                         "real_card_and_effect_semantics"}.issubset(value["deliberately_unresolved"]))
        self.assertEqual(value["scope_or_source_discrepancy_action"], "STOP_FOR_SEPARATE_REVIEW_NO_AUTOMATIC_EXPANSION")

    def test_fourteen_capabilities_each_have_independent_evidence_boundaries_primitives_and_blocked_readiness(self):
        rows = self.readiness.to_dict()["capabilities"]
        self.assertEqual(len(rows), 14)
        self.assertEqual(len({row["capability_id"] for row in rows}), 14)
        for row in rows:
            with self.subTest(capability=row["capability_id"]):
                for field in ("evidence_requirements", "semantic_dependencies", "required_future_primitives", "unsupported_boundaries"):
                    self.assertTrue(row[field])
                self.assertEqual(row["dependency_body_observation_status"], PM_INPUT)
                self.assertEqual(row["semantic_closure"], "OPEN")
                self.assertEqual(row["execution_readiness"], "BLOCKED")
                self.assertEqual(row["implementation_status"], "NOT_IMPLEMENTED")
                self.assertFalse(row["required_primitives_available"])
                self.assertFalse(row["execution_supported"])
                self.assertEqual(row["implied_ready_capabilities"], [])

    def test_605_section_resolution_remains_append_only_and_does_not_imply_semantic_or_runtime_closure(self):
        value = self.readiness.to_dict()["section_resolution"]
        self.assertEqual(value["601.2g"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertEqual(value["109.4a"], "SECTION_REFERENCE_RESOLVED_BY_COMPLETE_FAMILY")
        self.assertEqual(value["prior_605_family_closure_review_id"], self.binding["family_closure_review_id"])
        for key in ("section_resolution_implies_semantic_closure", "section_resolution_implies_execution",
                    "broad_606_section_resolved", "historical_direct_dependency_arrays_rewritten"):
            self.assertFalse(value[key])
        self.assertEqual(value["hypothetical_stack_controller_attribution"], "UNRESOLVED_FUTURE_PRIMITIVE")

    def test_all_seven_reassessments_keep_mana_behavior_control_casting_and_madness_blocked(self):
        value = self.readiness.to_dict()
        rows = value["readiness_reassessments"]
        self.assertEqual([row["capability_id"] for row in rows], ["mana_ability_classification", "activated_mana_ability_behavior",
                         "triggered_mana_ability_behavior", "object_control", "alternative_cost_casting_subprocedure",
                         "complete_spell_casting", "madness"])
        for row in rows:
            self.assertEqual(row["dependency_closure"], "OPEN")
            self.assertEqual(row["semantic_closure"], "OPEN")
            self.assertEqual(row["execution_readiness"], "EXECUTION_BLOCKED")
            self.assertFalse(row["required_primitives_available"])
            self.assertFalse(row["execution_supported"])
            self.assertEqual(row["blocker_interpretation_status"], PM_INPUT)
            self.assertTrue(row["blockers"])
            self.assertIn("OWNER_ACTIVATION_NOT_GRANTED", row["blockers"])
        self.assertEqual(value["overall_readiness"], "EXECUTION_BLOCKED")
        self.assertEqual(value["real_execution_profile_readiness"], "REAL_EXECUTION_PROFILE_NOT_READY")

    def test_production_pool_payment_and_fictional_authority_remain_separate_absent_and_unpromotable(self):
        value = self.readiness.to_dict()
        boundary = value["production_pool_payment_boundaries"]
        for key in ("mana_production_semantics", "mana_pool_semantics", "payment_integration"):
            self.assertEqual(boundary[key], "BLOCKED_ABSENT")
        for key in ("pool_representation_decided", "pool_clearing_rules_decided", "spending_restrictions_decided",
                    "mana_transformations_decided", "special_purpose_mana_decided"):
            self.assertFalse(boundary[key])
        authority = value["fictional_authority"]
        self.assertEqual(authority["finding"], "FICTIONAL_MANA_DOES_NOT_SATISFY_REAL_605")
        self.assertEqual(authority["accepted_real_execution_authority_proofs"], [])
        for key in ("fictional_mana_satisfies_real_605", "fictional_runtime_authority_inherited", "fictional_profile_changed"):
            self.assertFalse(authority[key])
            changed = body(self.readiness)
            changed["fictional_authority"][key] = True
            with self.subTest(promotion=key), self.assertRaises(GameplayContractError):
                type(self.readiness).create(changed)

    def test_readiness_capability_separation_cannot_be_promoted_by_reidentification(self):
        for key, value in self.readiness.to_dict()["capability_separation"].items():
            self.assertFalse(value)
            changed = body(self.readiness)
            changed["capability_separation"][key] = True
            with self.subTest(promotion=key), self.assertRaises(GameplayContractError):
                type(self.readiness).create(changed)
        changed = body(self.readiness)
        changed["capabilities"][0]["execution_readiness"] = "EXECUTION_READY"
        with self.assertRaises(GameplayContractError):
            type(self.readiness).create(changed)

    def test_count_and_unprojected_frontier_remain_exact_without_source_anchor_or_runtime_primitives(self):
        value = self.readiness.to_dict()
        self.assertEqual((value["projected_rule_count_before"], value["source_projections_added"], value["projected_rule_count_after"]), (81, 0, 81))
        self.assertEqual(value["remaining_unprojected_numbered_boundaries"], self.binding["existing_unprojected_references"])
        self.assertTrue(set(FRONTIER).issubset(value["remaining_unprojected_numbered_boundaries"]))
        self.assertEqual(value["new_body_scope_candidates"]["new_verified_direct_references"], [])
        self.assertEqual(value["new_body_scope_candidates"]["status"], PM_INPUT)
        self.assertFalse(value["new_body_scope_candidates"]["source_verified"])
        self.assertEqual(value["real_execution_primitives_available"], [])
        self.assertEqual(value["architecture"], {"fits_v13": True, "tier_zero_change": False, "runtime_changed": False})

    def test_builders_reject_duck_typed_or_mismatched_design_dependencies(self):
        from gameplay_rules.mana_dependency_design.consumers import build_consumer_matrix
        from gameplay_rules.mana_dependency_design.grouping import build_dependency_grouping
        from gameplay_rules.mana_dependency_design.readiness import build_readiness
        args = [self.records[name] for name in ("classification-dependencies.json", "activated-procedure-design.json",
                                              "triggered-procedure-design.json", "stack-context-design.json")]
        class IdentityShapedObject:
            identity = "sha256:" + "f" * 64
            def verify(self):
                return self
        for index in range(len(args)):
            changed = list(args)
            changed[index] = IdentityShapedObject()
            for build in (lambda: build_consumer_matrix(self.binding, *changed),
                          lambda: build_dependency_grouping(*changed, self.consumers),
                          lambda: build_readiness(self.binding, *changed, self.consumers, self.grouping)):
                with self.subTest(argument=index), self.assertRaises(GameplayContractError):
                    build()
        changed = list(args)
        changed_body = body(changed[0])
        changed_body["design_notes"] = [*changed_body["design_notes"], "Different synthetic classification review."]
        changed[0] = type(changed[0]).create(changed_body)
        with self.assertRaises(GameplayContractError):
            build_dependency_grouping(*changed, self.consumers)
        with self.assertRaises(GameplayContractError):
            build_readiness(self.binding, *changed, self.consumers, self.grouping)
        changed_binding = dict(self.binding)
        changed_binding["frontier_references"] = ["115.6"]
        with self.assertRaises(GameplayContractError):
            build_consumer_matrix(changed_binding, *args)


class ManaDirectProcedureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from gameplay_rules.mana_dependency_design.activated import build_activated_design
        from gameplay_rules.mana_dependency_design.triggered import build_triggered_design
        from gameplay_rules.mana_dependency_design.stack import build_stack_design
        cls.activated = build_activated_design()
        cls.triggered = build_triggered_design()
        cls.stack = build_stack_design()

    def test_general_activated_procedure_is_large_and_requires_separate_detailed_design(self):
        value = self.activated.to_dict()
        self.assertEqual(value["frontier_reference"], "602.2")
        self.assertEqual(value["subsystem"], "general_activated_ability_procedure")
        self.assertEqual(value["classification"], "LARGE_CORE_SUBSYSTEM")
        scope = value["scope_assessment"]
        self.assertTrue(scope["design_before_projection_required"])
        self.assertTrue(scope["dedicated_design_milestone_ready"])
        self.assertFalse(scope["detailed_subsystem_design_complete"])
        self.assertFalse(scope["projection_ready"])

    def test_activation_decomposes_ten_independently_blocked_capabilities(self):
        rows = self.activated.to_dict()["capabilities"]
        self.assertEqual([row["capability"] for row in rows], [
            "ability_kind_classification", "activation_authority_and_controller", "ability_announcement",
            "ability_stack_object_creation", "activation_cost", "casting_procedure_reuse", "ability_payment",
            "activation_legality", "illegal_activation_rollback", "ability_resolution"])
        self.assert_independent_capabilities(rows)

    def assert_independent_capabilities(self, rows):
        for row in rows:
            with self.subTest(capability=row["capability"]):
                self.assertTrue(row["evidence_requirements"])
                self.assertTrue(row["future_primitives"])
                self.assertTrue(row["semantic_dependencies"])
                self.assertTrue(row["independently_scoped"])
                self.assertEqual(row["implied_ready_capabilities"], [])
                self.assertEqual(row["readiness_status"], "BLOCKED")
                self.assertEqual(row["execution_readiness"], "NOT_IMPLEMENTED")
                self.assertFalse(row["implementation_available"])
                self.assertFalse(row["execution_supported"])
                self.assertFalse(row["source_verified"])
                self.assertEqual(row["evidence_status"], PM_INPUT)

    def test_602_2_parent_and_two_children_are_coherent_unverified_candidates_only(self):
        scope = self.activated.to_dict()["candidate_source_scope"]
        self.assertEqual(scope["exact_provisional_refs"], ["602.2", "602.2a", "602.2b"])
        self.assertEqual(scope["proposed_source_unit_count"], 3)
        self.assertEqual([row["rule_reference"] for row in scope["unit_roles"]], ["602.2", "602.2a", "602.2b"])
        self.assertTrue(scope["coherence_rationale"])
        self.assertTrue(scope["exact_source_shape_requires_verification"])
        self.assertTrue(scope["requires_dedicated_design_before_admission"])
        self.assertEqual(scope["coverage_state"], "UNPROJECTED")
        self.assertEqual(scope["evidence_status"], PM_INPUT)
        self.assertFalse(scope["source_verified"])
        self.assertFalse(scope["source_coverage_implies_execution"])
        self.assertFalse(scope["authorized"])

    def test_602_2b_casting_reuse_preserves_projected_and_missing_stages_without_runtime(self):
        value = self.activated.to_dict()["casting_reuse_design"]
        self.assertEqual(value["candidate_origin"], "602.2b")
        self.assertEqual(value["candidate_imported_range"], "601.2b-i")
        self.assertEqual(value["retained_projected_stage_references"], ["601.2b", "601.2f", "601.2g", "601.2h"])
        self.assertEqual(value["unprojected_stage_references"], ["601.2c", "601.2d", "601.2e", "601.2i"])
        self.assertEqual([row["rule_reference"] for row in value["range_members"]], ["601.2" + suffix for suffix in "bcdefghi"])
        for row in value["range_members"]:
            projected = row["rule_reference"] in prior_rules()
            self.assertEqual(row["coverage_state"], "PREVIOUSLY_PROJECTED" if projected else "UNPROJECTED_CASTING_STAGE")
            self.assertFalse(row["execution_supported"])
        self.assertEqual(value["evidence_status"], PM_INPUT)
        self.assertFalse(value["source_verified"])
        self.assertFalse(value["existing_casting_projection_satisfies_complete_reuse"])
        self.assertFalse(value["casting_runtime_imported"])

    def test_activation_new_outgoing_733_and_reveal_are_unverified_not_admitted(self):
        value = self.activated.to_dict()
        self.assertEqual([(row["originating_candidate_rule"], row["target_reference"]) for row in
                          value["candidate_outgoing_dependencies"]], [("602.2", "733"), ("602.2a", "701.20a")])
        for row in value["candidate_outgoing_dependencies"]:
            self.assertEqual(row["dependency_status"], "CANDIDATE_DIRECT_REFERENCE_REQUIRES_SOURCE_VERIFICATION")
            self.assertEqual(row["evidence_status"], PM_INPUT)
            self.assertEqual(row["coverage_state"], "UNPROJECTED")
            self.assertFalse(row["source_verified"])
        self.assertTrue({"733", "701.20a", "601.2c", "601.2d", "601.2e", "601.2i"}.issubset(value["deliberately_unresolved"]))

    def test_general_activation_and_mana_exception_are_conditional_and_separate(self):
        value = self.activated.to_dict()["general_special_relationship"]
        self.assertEqual(value["general_procedure"]["reference"], "602.2")
        self.assertEqual(value["general_procedure"]["role"], "GENERAL_PROCEDURE")
        self.assertEqual(value["mana_exception"]["retained_reference"], "605.3b")
        self.assertEqual(value["mana_exception"]["role"], "MANA_ABILITY_EXCEPTION")
        self.assertEqual(value["mana_exception"]["supporting_unprojected_context"], "405.6c")
        for key in ("general_stack_statement_is_unconditional", "mana_exception_overwrites_general_rule",
                    "mana_exception_satisfies_general_activation", "new_direct_citation_created", "runtime_dispatch_created"):
            self.assertFalse(value[key])

    def test_general_triggered_subsystem_is_large_shared_and_not_ready_for_whole_projection(self):
        value = self.triggered.to_dict()
        self.assertEqual(value["frontier_reference"], "603")
        self.assertEqual(value["subsystem"], "general_triggered_ability_subsystem")
        self.assertEqual(value["classification"], "LARGE_SHARED_CORE_SUBSYSTEM")
        scope = value["scope_assessment"]
        self.assertEqual(scope["shared_retained_consumers"], ["605.4", "109.4b"])
        self.assertTrue(scope["design_before_projection_required"])
        self.assertTrue(scope["dedicated_design_milestone_ready"])
        for field in ("whole_section_projection_recommended", "detailed_subsystem_design_complete", "projection_ready", "source_verified"):
            self.assertFalse(scope[field])

    def test_triggered_subsystem_decomposes_ten_independent_capabilities(self):
        rows = self.triggered.to_dict()["capabilities"]
        self.assertEqual([row["capability"] for row in rows], ["triggered_ability_classification", "trigger_event_detection",
            "trigger_registration", "triggered_ability_controller_attribution", "trigger_stack_placement", "trigger_ordering",
            "delayed_trigger_semantics", "delayed_trigger_controller_attribution", "zone_change_trigger_semantics", "reflexive_trigger_semantics"])
        self.assert_independent_capabilities(rows)

    def test_109_4b_uses_one_shared_triggered_subsystem_and_unchanged_delayed_frontier(self):
        value = self.triggered.to_dict()["shared_controller_consumer"]
        self.assertEqual(value["retained_rule_reference"], "109.4b")
        self.assertEqual(value["retained_dependency_references"], prior_rules()["109.4b"]["direct_dependency_references"])
        self.assertEqual(value["required_shared_subsystem"], "general_triggered_ability_subsystem")
        self.assertEqual(value["controller_capabilities"], ["triggered_ability_controller_attribution", "delayed_trigger_controller_attribution"])
        for key in ("separate_mana_trigger_model_created", "separate_controller_trigger_model_created",
                    "target_rule_bodies_source_verified_in_this_milestone", "existing_rule_or_dependencies_modified"):
            self.assertFalse(value[key])

    def test_delayed_controller_cluster_compares_isolated_with_parent_context_preference(self):
        value = self.triggered.to_dict()["delayed_trigger_controller_scope_comparison"]
        self.assertEqual(value["capability"], "delayed_trigger_controller_attribution")
        self.assertEqual(value["verified_retained_outgoing_frontier"], ["603.7d", "603.7e", "603.7f"])
        isolated, parent = value["options"]
        self.assertEqual(isolated["exact_provisional_refs"], ["603.7d", "603.7e", "603.7f"])
        self.assertEqual(isolated["proposed_source_unit_count"], 3)
        self.assertFalse(isolated["selected_for_future_scope_design"])
        self.assertEqual(parent["minimum_context_to_evaluate"], "603.7")
        self.assertTrue(parent["selected_for_future_scope_design"])
        self.assertFalse(parent["exact_final_allowlist_known"])
        self.assertEqual(value["preferred_approach"], "PARENT_CONTEXT_BEFORE_CONTROLLER_CLUSTER")
        self.assertEqual(value["decision_state"], "PROVISIONAL_DESIGN_JUDGMENT")
        self.assertFalse(value["automatic_scope_expansion"])
        self.assertFalse(value["projection_authorized"])

    def test_four_trigger_projection_stages_leave_specialized_families_deferred(self):
        rows = self.triggered.to_dict()["staged_source_coverage_strategy"]
        self.assertEqual([row["sequence"] for row in rows], [1, 2, 3, 4])
        self.assertEqual([row["stage"] for row in rows], ["TRIGGER_FOUNDATION", "STACK_AND_CONTROLLER_FOUNDATION",
                         "DELAYED_TRIGGER_CONTROLLER_CLUSTER", "SPECIALIZED_TRIGGER_FAMILIES_DEFERRED"])
        for row in rows:
            self.assertTrue(row["concepts"])
            self.assertEqual(row["evidence_status"], PM_INPUT)
            self.assertFalse(row["source_verified"])
            self.assertFalse(row["execution_supported"])
        self.assertEqual(rows[-1]["exact_future_source_allowlist"], "DEFERRED")

    def test_general_triggers_and_immediate_mana_exception_do_not_overwrite_or_satisfy_each_other(self):
        value = self.triggered.to_dict()["general_special_relationship"]
        self.assertEqual(value["general_procedure"]["reference"], "603")
        self.assertEqual(value["general_procedure"]["role"], "GENERAL_TRIGGERED_PROCEDURE")
        self.assertEqual(value["mana_exception"]["retained_reference"], "605.4a")
        self.assertEqual(value["mana_exception"]["role"], "TRIGGERED_MANA_EXCEPTION")
        for key in ("mana_exception_satisfies_general_trigger_semantics", "general_stack_statement_is_unconditional",
                    "mana_exception_overwrites_general_rule", "new_direct_citation_created", "runtime_dispatch_created"):
            self.assertFalse(value[key])

    def test_stack_context_is_bounded_with_605_3b_direct_and_605_4a_semantic_overlap(self):
        value = self.stack.to_dict()
        self.assertEqual(value["frontier_reference"], "405.6c")
        self.assertEqual(value["capability"], "mana_ability_stack_exception_context")
        self.assertEqual(value["classification"], "BOUNDED_STACK_CONTEXT")
        self.assertEqual(value["scope_assessment"]["direct_retained_consumer"], "605.3b")
        self.assertEqual(value["scope_assessment"]["semantic_overlap_without_new_citation"], ["605.4a"])
        self.assertFalse(value["scope_assessment"]["general_stack_semantics_supplied"])

    def test_stack_child_only_and_parent_options_are_compared_without_hierarchy_auto_admission(self):
        value = self.stack.to_dict()
        child, parent = value["scope_options"]
        self.assertEqual(child["exact_provisional_refs"], ["405.6c"])
        self.assertEqual(parent["exact_provisional_refs"], ["405.6", "405.6c"])
        self.assertEqual((child["proposed_source_unit_count"], parent["proposed_source_unit_count"]), (1, 2))
        decision = value["scope_decision"]
        self.assertEqual(decision["preferred_option"], "CHILD_ONLY")
        self.assertEqual(decision["parent_405.6_needed"], "NOT_ESTABLISHED_BY_AVAILABLE_DESIGN_INPUT")
        self.assertEqual(decision["if_child_requires_parent_context"], "STOP_FOR_SEPARATE_SCOPE_REVIEW")
        self.assertFalse(decision["independently_verified_minimum_scope"])
        self.assertFalse(decision["automatic_scope_expansion"])
        self.assertFalse(decision["authorized"])

    def test_stack_exception_never_supplies_general_stack_priority_or_response_runtime(self):
        boundary = self.stack.to_dict()["capability_boundary"]
        self.assertTrue({"general_stack_objects", "resolution_queue", "priority", "response_windows", "countering",
                         "effect_execution"}.issubset(boundary["unsupported_boundaries"]))
        self.assertEqual(boundary["readiness_status"], "BLOCKED")
        self.assertEqual(boundary["execution_readiness"], "NOT_IMPLEMENTED")
        for key in ("execution_supported", "source_coverage_implies_execution", "stack_runtime_created", "resolution_queue_created",
                    "priority_evaluated", "response_windows_created"):
            self.assertFalse(boundary[key])

    def test_stack_exception_relationships_do_not_create_new_direct_cr_citations(self):
        rows = self.stack.to_dict()["exception_relationships"]
        self.assertEqual([(row["general_reference"], row["retained_exception_reference"]) for row in rows],
                         [("602.2", "605.3b"), ("603", "605.4a")])
        for row in rows:
            self.assertEqual(row["supporting_candidate_context"], "405.6c")
            self.assertFalse(row["new_direct_citation_created"])
            self.assertFalse(row["general_statement_unconditionally_applied_to_mana_abilities"])
            self.assertEqual(row["evidence_status"], PM_INPUT)
            self.assertFalse(row["source_verified"])

    def test_every_unprojected_procedure_body_is_pm_input_without_source_verification(self):
        for record in (self.activated, self.triggered, self.stack):
            self.assertEqual(record.evidence_status, PM_INPUT)
            self.assertFalse(record.source_verification_claimed)
            self.assertEqual(record.new_source_units_projected, 0)
            self.assertTrue(record.non_executable)


if __name__ == "__main__":
    unittest.main()
