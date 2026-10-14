"""Slow integration: actual publication gate runs the complete project suite.

Run explicitly after discovery (also in CI), so the suite executed by the gate
does not recursively launch another whole-suite publication. No test is skipped,
validation is not mocked, and platform doubles grant no live GitHub authority.
"""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from catalog_admission_helpers import prepare_reference_rehearsal, RECOMMENDED_DIGEST
from production_evidence.automatic_updates import (
    AutomaticCanonicalUpdate, GitHubPersistence, IsolatedAdmissionTestBoundary, digest,
)
from test_automatic_update_publication import FictionalGitHubTransport

ROOT = Path(__file__).resolve().parents[1]


class ExpandedPublicationValidationRegression(unittest.TestCase):
    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.PIPE)

    def engine(self):
        return AutomaticCanonicalUpdate(self.root, self.config)

    def test_real_writer_expansion_passes_real_publication_suite_and_readback(self):
        # Keep the actual TemporaryDirectory capability alive throughout writing
        # and publication; no simulated receipt can substitute for this object.
        temporary = tempfile.TemporaryDirectory(prefix="mtglab-expanded-publication-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.config, selected = prepare_reference_rehearsal(self.root)
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
        extra = ["tests/historical_catalog.py", "tests/test_current_catalog_validation.py",
                 "tests/publication_validation_regression.py", "tests/fixtures/historical_catalog/manifest.json",
                 "tests/fixtures/historical_catalog/canonical-3bf4cc27.zip"]
        for relative in sorted({p.decode() for p in paths if p} | set(extra)):
            if relative.startswith("data/"):
                continue
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "SIMULATED_PUBLICATION_TEST_ONLY")
        self.git("config", "user.email", "fictional@example.invalid")
        # This baseline is disposable, public-test inputs only; never sent to GitHub.
        self.git("add", ".")
        # The project intentionally ignores locally generated state.json. Its
        # real historical counterpart is already tracked in the real checkout;
        # seed that same exact file explicitly in this fresh disposable repository.
        self.git("add", "--force", "data/canonical/state.json")
        self.git("commit", "--quiet", "-m", "Disposable original catalog and pending test inputs")
        self.base = self.git("rev-parse", "HEAD").strip()
        origin = self.root / ".git/fictional-origin.git"
        self.git("init", "--bare", "--quiet", str(origin))
        self.git("remote", "add", "origin", str(origin))
        self.git("push", "--quiet", "origin", "HEAD:refs/heads/main")
        original = (self.root / "data/canonical/state.json").read_bytes()
        engine = self.engine()
        plan = engine.plan()
        boundary = IsolatedAdmissionTestBoundary(temporary)
        engine.review_boundary = boundary
        decision = boundary.authorize(engine.admission_bindings())
        engine.execute(stop_after="query_and_analytics_smoke_tests")
        state = json.loads((self.root / "data/canonical/state.json").read_bytes())
        self.assertEqual(len(state["card"]), 654)
        self.assertEqual(len(selected), 810)
        self.assertEqual(digest(plan["decision_inputs"]["bindings"]["candidate_ids"]), RECOMMENDED_DIGEST)
        self.assertNotEqual(original, (self.root / "data/canonical/state.json").read_bytes())
        transport = FictionalGitHubTransport(self)
        # No validation replacement: this calls the publication helper, real
        # writer-output integrity checks and its complete unittest subprocess.
        result = GitHubPersistence(transport).publish_admission(
            engine, plan, self.base, decision, repository="IDontFeelNone/MTG-Lab")
        if result["status"] != "published":
            log = self.root / ".git/catalog-admission-validation.log"
            if log.exists():
                print(log.read_text(), flush=True)
        self.assertEqual(result["status"], "published", result)
        self.assertEqual(result["validation"]["exit_status"], 0)
        self.assertGreaterEqual(result["validation"]["tests"], 938)
        self.assertIn("data/canonical/state.json", result["inventory"]["changed_paths"])
        self.assertEqual(result["head"], self.git("rev-parse", "HEAD").strip())
        self.assertTrue(result["draft"])
        self.assertEqual(self.git("ls-remote", "origin", "refs/heads/" + engine.descriptor.destination_branch).split()[0],
                         result["head"])
        self.assertFalse(any("merge" in c or "--force" in c for c in transport.calls))
        print(json.dumps({"simulated_platform_only": True, "actual_writer_card_count": 654,
            "validation": result["validation"], "published_to": "disposable_local_bare_remote"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
