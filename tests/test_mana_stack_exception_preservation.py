"""Canonical byte-preservation checks, never Comprehensive Rules authority.

The new fixture was generated from ``git ls-tree`` and ``git show`` at the
owner-selected canonical base. It extends, without replacing, the preceding
guard. It is deliberately independent of source extraction and of local Git
history so the same checks run in shallow CI and disposable publication trees.
"""
import hashlib
import json
from pathlib import Path
import unittest


from activated_ability_preservation import is_design_addition


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_MAIN = "c9f46a2768cdee5e32f72e27d0255c6d4efbe175"
FIXTURE = ROOT / "tests/fixtures/mana-stack-exception-protected-state.json"
FIXTURE_SHA256 = "26ffe31092f4fcbe7207afab58bf85ddf4907e432a16c0fad13cf4cd126aed8e"
OLD_GUARD_SHA256 = "e21f4a50990577e46ddc36ffb21bf16852fa9efa4f2800ecd30b54ef17e3d784"
NEW_SOURCE_PATHS = frozenset(
    "src/gameplay_rules/projection/mana_stack_exception_" + part + ".py"
    for part in ("package", "pins", "reports", "source")
)
PRIOR_PACKAGE_IDS = {
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
    "gameplay-rules-mana-direct-dependency-design": "sha256:af42a280e70618102a71381f43122fb98c5e60367f63bd33750677a9a7d9646c",
    "gameplay-rules-bounded-mana-classification-projection": "sha256:57c9a21ec6a253ad9bfc3a650ec2edc8a389a456eb555a213c3a3f5c673eea73",
}
MANA_FAMILY = frozenset(("605.1", "605.1a", "605.1b", "605.2", "605.3", "605.3a",
    "605.3b", "605.3c", "605.4", "605.4a", "605.5", "605.5a", "605.5b"))


def fixture():
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != FIXTURE_SHA256:
        raise AssertionError("Canonical preservation fixture bytes changed")
    return json.loads(raw)


def source_paths():
    return {p.relative_to(ROOT).as_posix() for p in (ROOT / "src").rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        and not is_design_addition(p)}


class CanonicalPreservationTests(unittest.TestCase):
    def assertInventoryPreserved(self, rows):
        self.assertEqual(len(rows), len({row["path"] for row in rows}))
        for row in rows:
            with self.subTest(path=row["path"]):
                path = ROOT / row["path"]
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                raw = path.read_bytes()
                self.assertEqual(len(raw), row["bytes"])
                self.assertEqual(hashlib.sha256(raw).hexdigest(), row["sha256"])

    def test_guard_is_preservation_only_subordinate_to_exact_canonical_git(self):
        guard = fixture()
        self.assertEqual(guard["canonical_base"], CANONICAL_MAIN)
        self.assertEqual(guard["purpose"], "BYTE_PRESERVATION_GUARD_ONLY")
        self.assertEqual(guard["authority"], "CANONICAL_GIT_STATE")
        self.assertFalse(guard["gameplay_authority"])
        self.assertFalse(guard["comprehensive_rules_authority"])
        self.assertFalse(guard["supersedes_prior_digests"])
        self.assertEqual(set(guard["allowed_new_source_paths"]), NEW_SOURCE_PATHS)
        self.assertEqual(len(NEW_SOURCE_PATHS), 4)

    def test_old_guard_digest_and_every_historical_entry_are_preserved(self):
        guard = fixture()
        prior = guard["prior_guard"]
        self.assertEqual(prior["path"], "tests/fixtures/mana-classification-protected-source.json")
        self.assertEqual(prior["sha256"], OLD_GUARD_SHA256)
        raw = (ROOT / prior["path"]).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), OLD_GUARD_SHA256)
        old = {row["path"]: row["sha256"] for row in json.loads(raw)}
        current = {row["path"]: row["sha256"] for row in guard["canonical_source_files"]}
        self.assertEqual({name: current[name] for name in old}, old)
        self.assertEqual(set(current) - set(old), {
            "src/gameplay_rules/projection/mana_classification_" + part + ".py"
            for part in ("package", "pins", "reports", "source")})

    def test_all_329_canonical_source_files_and_exact_four_file_extension(self):
        rows = fixture()["canonical_source_files"]
        self.assertEqual(len(rows), 329)
        canonical = {row["path"] for row in rows}
        self.assertFalse(canonical & NEW_SOURCE_PATHS)
        self.assertEqual(source_paths(), canonical | NEW_SOURCE_PATHS)
        self.assertInventoryPreserved(rows)

    def test_engine_fictional_runtime_products_policy_writer_and_simulation_preserved(self):
        rows = fixture()["canonical_source_files"]
        names = {row["path"] for row in rows}
        # The complete source inventory above protects every implementation;
        # these assertions make the important boundaries explicit.
        for name in ("src/gameplay_rules/engine.py", "src/gameplay_rules/models.py",
                "src/gameplay_rules/capabilities.py", "src/gameplay_rules/costs.py",
                "src/card_intelligence/__init__.py", "src/product_intelligence/__init__.py",
                "src/production_evidence/automatic_updates.py", "src/repository/canonical.py",
                "src/simulation/.gitkeep"):
            self.assertIn(name, names)
        self.assertEqual({p.name for p in (ROOT / "src/simulation").iterdir()
            if p.name != "__pycache__"}, {".gitkeep"})
        self.assertInventoryPreserved(fixture()["protected_support_files"])

    def test_all_twelve_prior_packages_exact_file_bytes_and_historical_anchors(self):
        pins = fixture()["prior_packages"]
        self.assertEqual(set(pins), set(PRIOR_PACKAGE_IDS))
        self.assertEqual(len(pins), 12)
        self.assertEqual(sum(len(pin["files"]) for pin in pins.values()), 75)
        for name, pin in pins.items():
            with self.subTest(package=name):
                self.assertEqual(pin["package_id"], PRIOR_PACKAGE_IDS[name])
                root = ROOT / "reference-reviews" / name
                self.assertEqual({p.name for p in root.iterdir()},
                    {Path(row["path"]).name for row in pin["files"]})
                self.assertInventoryPreserved(pin["files"])
                self.assertEqual(json.loads((root / "manifest.json").read_bytes())["package_id"],
                    pin["package_id"])

    def test_historical_rule_identities_and_dependency_arrays_unchanged(self):
        from test_mana_ability_direct_dependency_design import prior_rules, RULE_IDS
        rules = prior_rules()
        self.assertEqual(len(rules), 81)
        for ref, identity in RULE_IDS.items():
            self.assertEqual(rules[ref]["rule_id"], identity)
        self.assertEqual({ref for ref in rules if ref.startswith("605.")}, MANA_FAMILY)
        self.assertEqual(rules["605.3b"]["direct_dependency_references"], ["405.6c"])
        self.assertEqual(rules["605.4a"]["direct_dependency_references"], [])
        self.assertEqual(rules["601.2g"]["direct_dependency_references"], ["605"])
        self.assertEqual(rules["109.4a"]["direct_dependency_references"], ["605"])
        for ref in ("605.4a", "601.2g", "109.4a", "702.35b"):
            self.assertNotIn("405.6c", rules[ref]["direct_dependency_references"])

    def test_historical_acquisition_identity_remains_exact(self):
        from gameplay_rules.projection.bounded_mana_package import HISTORICAL_ACQUISITION_ID
        identity = "sha256:669d7db9ebcaf97853058fd62f408ce3c6596d5dae0ee72ff39d2ba9df56bb53"
        self.assertEqual(HISTORICAL_ACQUISITION_ID, identity)
        manifest = ROOT / "reference-reviews/gameplay-rules-bounded-mana-classification-projection/manifest.json"
        self.assertEqual(json.loads(manifest.read_bytes())["historical_acquisition_identity"], identity)


if __name__ == "__main__":
    unittest.main()
