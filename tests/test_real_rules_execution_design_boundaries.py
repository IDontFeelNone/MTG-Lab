"""Release-pinned preservation and integration proofs for the inactive design.

The preservation digests were computed from canonical main
90ce520be8b0319111ca74fdb385b01de522523a. They cover controlled source and
retained evidence, never the mutable catalog census. The publication rehearsal
can therefore validate these same boundaries after its isolated catalog write.
No official rules document or external source path is a test input.
"""
import ast
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from validation_performance_preservation import is_validation_performance_addition

from shared_casting_stage_preservation import is_shared_casting_design_addition

from gameplay_rules.capabilities import ENGINE_CONTRACT_VERSION, EXECUTION_PROFILE
from gameplay_rules.engine import GameplayRulesEngine
from gameplay_rules.errors import GameplayContractError
from gameplay_rules.models import GameplayRulesSnapshot
from gameplay_rules.projection import FoundationalProjection
from gameplay_rules_fixture import action, fixture_documents, snapshot_body


ROOT = Path(__file__).resolve().parents[1]
PROJECTION = ROOT / "reference-reviews/gameplay-rules-foundational-projection"
DESIGN = ROOT / "reference-reviews/gameplay-rules-execution-profile-design"
DESIGN_CODE = ROOT / "src/gameplay_rules/execution_design"
PACKAGE_ID = "sha256:22740145cf0ec457e0b297eba5ebed3d58054b6d16179bdd738a4f5ccc5463ea"
PROJECTION_ID = "sha256:98bfd574c774a48aaaab4753eb8eb864dc7242effa011568f2ebf59c6a9ce6f7"
HISTORICAL_ID = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
TARGET_PROFILE = "magic-comprehensive-rules-20260925-v1"

# Each digest binds sorted path, byte length, and SHA-256 entries. Runtime
# __pycache__ files are excluded; retained inventories and file bytes are not.
PROTECTED_GROUPS = {
    "fictional_runtime": (
        ("src/gameplay_rules/__init__.py", "src/gameplay_rules/capabilities.py",
         "src/gameplay_rules/costs.py", "src/gameplay_rules/engine.py",
         "src/gameplay_rules/errors.py", "src/gameplay_rules/models.py",
         "src/gameplay_rules/snapshots.py", "tests/gameplay_rules_fixture.py",
         "tests/fixtures/gameplay_rules"),
        15, "bd8c79afcd39ff0256cc6dd536b3b6785cd9e1f25a2953a42c52391477f006af"),
    # Pin the original module inventory explicitly: the separately authorized
    # dependency milestone adds projection modules and generalizes only the
    # source locator's fixed-allowlist parameter. Retained packages stay pinned
    # independently below; newly added modules have their own boundary tests.
    "projection_and_source_evidence_code": (
        ("src/gameplay_rules/projection/__init__.py",
         "src/gameplay_rules/projection/__main__.py",
         "src/gameplay_rules/projection/contracts.py",
         "src/gameplay_rules/projection/package.py",
         "src/gameplay_rules/projection/scope.py",
         "src/gameplay_rules/projection/source.py", "src/gameplay_rules/source_evidence",
         "tests/gameplay_rules_source_fixture.py"),
        17, "462ab6a5cb1be58ec3e3cc4af73dfa6008f8893c62a2f0af7d9f4e32541e99e1"),
    "product_rules": (
        ("src/repository/rules.py", "src/decisions/rules.py"),
        2, "d1b0447582e4c97d3ec2ae1f74881a755d7d725b7298a7545ff650da0bbc94f6"),
    "card_intelligence_roles_and_context": (
        ("src/card_intelligence", "src/reasoning", "src/semantic"),
        23, "65669149389b53e3818a5ca5b031136ff07d6f28d41429cdbb93bc9595eec867"),
    "writer_admission_evidence_and_transport": (
        ("src/production_evidence", "src/promotion", "src/repository",
         "src/ingestion", "scripts", "config", ".github"),
        82, "210a951e39781044205cb25b6551809a2c4c3450086cc4c74be37c83da8320d5"),
    "historical_card_acquisition_replay": (
        ("tests/fixtures/historical_replay/card-acquisition-pilot",),
        2, "d8049babb50f55323b18afbb415b2fb4f5cbd778fe1601b7288880b48edb0868"),
    "gameplay-rules-foundation": (
        ("reference-reviews/gameplay-rules-foundation",),
        2, "bef81389a9321e192c3953670f920a053d6daeb0085ab7c6b01165206e04f659"),
    "gameplay-rules-source-versioning": (
        ("reference-reviews/gameplay-rules-source-versioning",),
        8, "b96a22e946f24313f00868100e5438411a702f3655af81c7dccfdd26ce609a33"),
    "gameplay-rules-release-discovery-closure": (
        ("reference-reviews/gameplay-rules-release-discovery-closure",),
        7, "0d0981ddeb0cb76b348affd32cc68c7bd72fa6b44d23113a0d714e5d5eeb0fff"),
    "gameplay-rules-artifact-verification": (
        ("reference-reviews/gameplay-rules-artifact-verification",),
        5, "02274c2bfd851d51511d07f51c5009204c3394c02aa98289269d4ca2af240ef3"),
    "gameplay-rules-foundational-projection": (
        ("reference-reviews/gameplay-rules-foundational-projection",),
        2, "0e88e8baac7171f2a390f8a46913952a4a7a57fe7605ece47572c6a9a5fff5f2"),
    "mb2-reference-coverage": (
        ("reference-reviews/mb2-reference-coverage",),
        47, "9960b4c5b6b7e575a30f34fe9f3724f6f728e4c4a672de99fbab63e2846d57e9"),
    "mb2-810-source-policy": (
        ("reference-reviews/mb2-810-source-policy",),
        34, "132f98d1f3ed71632ac91ed477f3f5d4ac48fe9404fecafb4c01665ebcb52b64"),
    "mb2-810-production-readiness": (
        ("reference-reviews/mb2-810-production-readiness",),
        5, "61a864676251b139da461368fcec00622e45192316fe58e1eb284b8175630434"),
    "v13-stage2-legacy-public-profile": (
        ("reference-reviews/v13-stage2-legacy-public-profile",),
        8, "d3a0da36da8d47b8cd60ebc19e68f3cd78eba8db71f2798654126b503a9444a0"),
    "v13-legacy-profile-permission-closure": (
        ("reference-reviews/v13-legacy-profile-permission-closure",),
        11, "6f22e516c746c35a4eb71545f88900d8ca3329e59a34c05922d1a902d1316fa6"),
}


def controlled_inventory(roots):
    files = set()
    for relative in roots:
        path = ROOT / relative
        if path.is_file():
            files.add(path)
        else:
            files.update(p for p in path.rglob("*") if p.is_file()
                         and "__pycache__" not in p.parts and p.suffix != ".pyc")
    result = []
    for path in sorted(files):
        # Preserve the original writer/admission inventory and its exact digest.
        # The exact added review/profiling tools have separate current pins.
        if is_shared_casting_design_addition(path) or is_validation_performance_addition(path):
            continue
        if path.is_symlink():
            raise AssertionError("Controlled artifact must not be a symlink")
        raw = path.read_bytes()
        result.append({"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
                       "sha256": hashlib.sha256(raw).hexdigest()})
    return result


class RealRulesExecutionDesignBoundaryTests(unittest.TestCase):
    def test_preexisting_kernel_evidence_product_and_admission_bytes_are_preserved(self):
        for name, (roots, expected_count, expected_hash) in PROTECTED_GROUPS.items():
            with self.subTest(group=name):
                inventory = controlled_inventory(roots)
                self.assertEqual(len(inventory), expected_count)
                raw = json.dumps(inventory, sort_keys=True, separators=(",", ":")).encode()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected_hash)

    def test_original_foundational_package_identity_and_both_file_bytes_are_exact(self):
        bindings = {
            "manifest.json": (625, "d817cc48b3c5cb6489167e297a731ce0c732abdfc4a5a6013eab1ef7fdf63e95"),
            "projection.json": (25250, "6d4062e69f497d84f514b17d6ce26610c2ffa57b0eec5752044764e0602d9005"),
        }
        self.assertEqual({p.name for p in PROJECTION.iterdir()}, set(bindings))
        for name, (length, digest) in bindings.items():
            with self.subTest(file=name):
                raw = (PROJECTION / name).read_bytes()
                self.assertEqual(len(raw), length)
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
        manifest = json.loads((PROJECTION / "manifest.json").read_bytes())
        self.assertEqual(manifest["package_id"], PACKAGE_ID)
        self.assertEqual(manifest["projection_id"], PROJECTION_ID)
        projection = FoundationalProjection.from_json((PROJECTION / "projection.json").read_bytes())
        self.assertEqual(projection.identity, PROJECTION_ID)
        self.assertEqual(projection.to_dict()["selected_rule_count"], 20)
        self.assertEqual(projection.to_dict()["status"], "IMPLEMENTED_PENDING_REVIEW")
        self.assertFalse(projection.to_dict()["boundary_flags"]["real_rules_executable"])

    def test_fictional_profile_constants_and_source_class_gate_remain_enforced(self):
        self.assertEqual(ENGINE_CONTRACT_VERSION, "gameplay-kernel-v1")
        self.assertEqual(EXECUTION_PROFILE, "fictional-two-player-v1")
        for field, value in (("execution_profile", TARGET_PROFILE),
                             ("engine_contract_version", "gameplay-real-rules-kernel-v1")):
            body = snapshot_body()
            body[field] = value
            with self.subTest(field=field), self.assertRaises(GameplayContractError):
                GameplayRulesSnapshot.create(body)
        body = snapshot_body()
        body["sources"][0]["source_class"] = "official_comprehensive_rules"
        with self.assertRaises(GameplayContractError):
            GameplayRulesSnapshot.create(body)

    def test_fictional_evaluation_and_transition_keep_canonical_proof_identities(self):
        snapshot, semantics, state = fixture_documents()
        before = state.to_dict()
        engine = GameplayRulesEngine(snapshot, semantics)
        self.assertEqual(snapshot.identity,
                         "sha256:21c4d3a5a061882ff7454e34bd2ab1fc1c878a3a3c0db6b10c5bde2e4308e358")
        self.assertEqual(state.identity,
                         "sha256:627ff0a373eb8e11ea8def1da1da7a8c45216f18000b15565c04d4b623b9c71d")
        requested = action(state, "play_land", object_id="moss-plot")
        result = engine.evaluate_action(state, requested)
        self.assertEqual(result.status, "LEGAL")
        self.assertEqual(result.identity,
                         "sha256:f02a8544861589f28d582f2917facf212516de40863fe51f2b3e04409ed5b680")
        transition = engine.apply_action(state, requested)
        self.assertEqual(transition.identity,
                         "sha256:0365c6a3821be9f46157c0fad1e0c047dd2cff5f3011977c404b6ba25f97c5e7")
        self.assertEqual(transition.to_dict()["after_state_id"],
                         "sha256:f29abedc87b0632df17b6fbf2db69afd5b80fe50a773f42f6e7464d47dfe4173")
        self.assertEqual(state.to_dict(), before)

    def test_no_projection_to_engine_or_snapshot_execution_path_exists(self):
        self.assertFalse(hasattr(GameplayRulesEngine, "from_projection"))
        self.assertFalse(hasattr(FoundationalProjection, "to_rules_snapshot"))
        self.assertFalse(hasattr(FoundationalProjection, "to_execution_profile"))
        projection = FoundationalProjection.from_json((PROJECTION / "projection.json").read_bytes())
        with self.assertRaises(GameplayContractError):
            GameplayRulesEngine(projection, ())

    def test_design_layer_has_no_network_oracle_simulation_or_runtime_constructors(self):
        forbidden_roots = {"socket", "http", "urllib", "requests", "subprocess",
                           "simulation", "providers", "external_ingestion", "market",
                           "production_evidence", "repository", "random", "secrets"}
        forbidden_runtime_contracts = {"GameplayRulesSnapshot", "CardGameplaySemantics",
                                       "GameState", "GameAction", "LegalityResult",
                                       "GameTransition", "GameplayRulesEngine"}
        paths = list(DESIGN_CODE.glob("*.py"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(file=path.name):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    imports = []
                    if isinstance(node, ast.Import):
                        imports = [name.name for name in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        imports = [node.module or ""]
                    self.assertFalse({name.split(".")[0] for name in imports} & forbidden_roots)
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.assertNotEqual(node.name, "to_rules_snapshot")
                    if isinstance(node, ast.Call):
                        root = node.func
                        while isinstance(root, ast.Attribute):
                            root = root.value
                        if isinstance(root, ast.Name):
                            self.assertNotIn(root.id, forbidden_runtime_contracts | {"exec", "eval", "compile"})

    def test_retained_design_package_has_only_review_metadata_and_no_source_document(self):
        expected = {"projection-review.json", "capability-matrix.json",
                    "execution-profile-design.json", "activation-gates.json",
                    "readiness.json", "manifest.json"}
        self.assertEqual({p.relative_to(DESIGN).as_posix() for p in DESIGN.rglob("*") if p.is_file()},
                         expected)
        forbidden_fields = {"source_text", "rule_text", "official_text", "oracle_text",
                            "raw_source", "source_body", "document_text"}

        def inspect(value):
            if isinstance(value, dict):
                self.assertFalse(set(value) & forbidden_fields)
                for item in value.values():
                    inspect(item)
            elif isinstance(value, list):
                for item in value:
                    inspect(item)

        for name in expected:
            with self.subTest(file=name):
                self.assertFalse((DESIGN / name).is_symlink())
                raw = (DESIGN / name).read_bytes()
                self.assertNotIn(b"/tmp/codex-remote-attachments/", raw)
                inspect(json.loads(raw))

    def test_design_records_remain_metadata_and_cannot_be_given_to_the_engine(self):
        from gameplay_rules.execution_design.contracts import (
            FoundationalProjectionReview, RealRulesActivationGateDesign,
            RealRulesCapabilityMatrix, RealRulesExecutionProfileDesign,
            RealRulesExecutionReadiness,
        )
        from gameplay_rules.models import (
            CardGameplaySemantics, GameAction, GameState, GameTransition, LegalityResult,
        )
        records = {
            "projection-review.json": FoundationalProjectionReview,
            "capability-matrix.json": RealRulesCapabilityMatrix,
            "execution-profile-design.json": RealRulesExecutionProfileDesign,
            "activation-gates.json": RealRulesActivationGateDesign,
            "readiness.json": RealRulesExecutionReadiness,
        }
        runtime_types = (GameplayRulesSnapshot, CardGameplaySemantics, GameAction,
                         GameState, GameTransition, LegalityResult)
        for name, contract in records.items():
            with self.subTest(record=name):
                value = contract.from_json((DESIGN / name).read_bytes())
                self.assertNotIsInstance(value, runtime_types)
                self.assertFalse(hasattr(value, "to_rules_snapshot"))
                self.assertFalse(value.to_dict()["real_rules_executable"])
                with self.assertRaises(GameplayContractError):
                    GameplayRulesEngine(value, ())

    def test_full_package_rebuild_and_load_need_no_source_network_or_runtime_objects(self):
        from gameplay_rules.execution_design import build_design_package, load_design_package
        from gameplay_rules.models import (
            CardGameplaySemantics, GameAction, GameState, GameTransition, LegalityResult,
        )
        roots = {
            "projection_root": PROJECTION,
            "artifact_review_root": ROOT / "reference-reviews/gameplay-rules-artifact-verification",
            "source_root": ROOT / "reference-reviews/gameplay-rules-source-versioning",
            "discovery_root": ROOT / "reference-reviews/gameplay-rules-release-discovery-closure",
        }
        runtime_contracts = (GameplayRulesSnapshot, CardGameplaySemantics, GameAction,
                             GameState, GameTransition, LegalityResult)
        with ExitStack() as stack:
            for target in ("socket.socket",
                           "gameplay_rules.source_evidence.artifacts.verify_local_artifact",
                           "gameplay_rules.projection.source.build_projection",
                           "pathlib.Path.write_bytes", "pathlib.Path.write_text"):
                stack.enter_context(patch(target, side_effect=AssertionError(
                    "Design reproduction must use only retained metadata without writes")))
            stack.enter_context(patch.object(GameplayRulesEngine, "__init__",
                                             side_effect=AssertionError("No runtime engine construction")))
            for cls in runtime_contracts:
                for method in ("__init__", "create", "from_dict"):
                    stack.enter_context(patch.object(cls, method, side_effect=AssertionError(
                        "No gameplay runtime contract construction")))
            built = build_design_package(**roots)
            loaded = load_design_package(DESIGN, **roots)
            self.assertEqual({name: value.to_dict() for name, value in built.items()},
                             {name: value.to_dict() for name, value in loaded.items()})
            self.assertEqual(len(loaded), 5)
            self.assertEqual(loaded["execution-profile-design.json"].status, "DESIGN_ONLY")
            self.assertTrue(all(not record.real_rules_executable for record in loaded.values()))

    def test_historical_card_acquisition_fixture_keeps_protected_identity_and_every_file(self):
        root = ROOT / "tests/fixtures/historical_replay/card-acquisition-pilot"
        manifest = json.loads((root / "manifest.json").read_bytes())
        self.assertEqual(manifest["protected_inventory_identity"], HISTORICAL_ID)
        for relative, binding in manifest["files"].items():
            with self.subTest(file=relative):
                raw = (root / relative).read_bytes()
                self.assertEqual(len(raw), binding["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), binding["sha256"])

    def test_source_policy_approval_list_and_simulation_remain_unchanged(self):
        tree = ast.parse((ROOT / "scripts/automatic_canonical_update.py").read_text())
        definitions = [node for node in tree.body if isinstance(node, ast.AnnAssign)
                       and isinstance(node.target, ast.Name)
                       and node.target.id == "SOURCE_POLICY_CLEARED_PLANS"]
        self.assertEqual(len(definitions), 1)
        value = definitions[0].value
        self.assertIsInstance(value, ast.Call)
        self.assertIsInstance(value.func, ast.Name)
        self.assertEqual(value.func.id, "frozenset")
        self.assertEqual(value.args, [])
        self.assertEqual(value.keywords, [])
        self.assertEqual({p.name for p in (ROOT / "src/simulation").iterdir()
                          if p.name != "__pycache__"}, {".gitkeep"})


if __name__ == "__main__":
    unittest.main()
