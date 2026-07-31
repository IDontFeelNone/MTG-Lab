"""Phase 112B fail-closed persistence tests (unittest only)."""
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-evidence-intake.yml"
SPEC = importlib.util.spec_from_file_location("persistence", ROOT / "scripts" / "production_evidence_persistence.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def result(code=0, stdout="", stderr=""):
    return subprocess.CompletedProcess((), code, stdout, stderr)


class Harness(module.Persistence):
    def __init__(self, args, responses):
        super().__init__(args)
        self.responses, self.calls = responses, []

    def command(self, stage, *command, check=True):
        self.calls.append((stage, command))
        response = self.responses.get(stage, result())
        if isinstance(response, list):
            response = response.pop(0)
        if check and response.returncode:
            raise module.PersistenceError(f"{stage}: command failed ({response.returncode})")
        return response


class ProductionEvidencePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.old = Path.cwd()
        import os
        os.chdir(self.temp.name)
        path = Path("data/production_runs/30663562841")
        path.mkdir(parents=True)
        (path / "manifest.json").write_text("{}\n")
        (path.parent / "index.json").write_text("{}\n")
        self.args = SimpleNamespace(run_id="30663562841", artifact_name="mtgjson-ingestion-30663562841",
            archive_sha256="a" * 64, destination_branch="production-evidence/run-30663562841",
            base_branch="main", repository="owner/repo", dry_run=False)

    def tearDown(self):
        import os
        os.chdir(self.old)
        self.temp.cleanup()

    def test_non_dry_run_creates_evidence_commit_branch_and_verified_pr(self):
        prs = json.dumps([{"number": 7}])
        pr = json.dumps({"number": 7, "state": "open", "html_url": "https://example/pr/7",
            "head": {"ref": self.args.destination_branch, "sha": "abc"}, "base": {"ref": "main"}})
        h = Harness(self.args, {"evidence_staging": [result(1), result(), result(stdout="data/production_runs/30663562841/manifest.json\n")],
            "branch_creation": [result(2), result()], "commit_creation": [result(), result(stdout="abc\n")],
            "branch_push": result(), "pr_creation": result(stdout=prs),
            "pr_verification": [result(stdout=pr), result(stdout=json.dumps([{"filename": "data/production_runs/30663562841/manifest.json"}]))]})
        report = h.execute()
        self.assertEqual("persisted", report["intake_status"])
        self.assertEqual(7, report["pull_request_number"])
        self.assertIn("branch_push", [stage for stage, _ in h.calls])

    def test_ignored_file_staging_failure(self):
        with self.assertRaisesRegex(module.PersistenceError, "ignored"):
            Harness(self.args, {"evidence_staging": result(0)}).execute()

    def test_empty_commit_failure(self):
        h = Harness(self.args, {"evidence_staging": [result(1), result(), result(stdout="")],
            "branch_creation": [result(2), result()]})
        with self.assertRaisesRegex(module.PersistenceError, "no bounded evidence"):
            h.execute()

    def test_branch_push_failure(self):
        h = Harness(self.args, {"evidence_staging": [result(1), result(), result(stdout="data/production_runs/30663562841/manifest.json\n")],
            "branch_creation": [result(2), result()], "commit_creation": [result(), result(stdout="abc\n")],
            "branch_push": result(1, stderr="denied")})
        with self.assertRaises(module.PersistenceError):
            h.execute()

    def test_missing_permissions_and_pr_creation_failure(self):
        for stage in ("branch_push", "pr_creation"):
            h = Harness(self.args, {"evidence_staging": [result(1), result(), result(stdout="data/production_runs/30663562841/manifest.json\n")],
                "branch_creation": [result(2), result()], "commit_creation": [result(), result(stdout="abc\n")],
                "branch_push": result(1) if stage == "branch_push" else result(),
                "pr_creation": result(1)})
            with self.assertRaises(module.PersistenceError):
                h.execute()

    def test_pr_verification_failure_and_success_requires_real_pr(self):
        h = Harness(self.args, {"pr_verification": result(stdout=json.dumps({"state": "open", "head": {}, "base": {}}))})
        with self.assertRaisesRegex(module.PersistenceError, "does not match"):
            h.verify_pr(7, "abc")

    def test_byte_identical_existing_branch_and_pr_reuse(self):
        count, digest = module.tree_digest(Path("data/production_runs/30663562841"))
        prs = json.dumps([{"number": 7}])
        pr = json.dumps({"state": "open", "html_url": "u", "head": {"ref": self.args.destination_branch, "sha": "abc"}, "base": {"ref": "main"}})
        h = Harness(self.args, {"evidence_staging": result(1), "branch_creation": [result(0), result()],
            "existing_evidence_verification": result(stdout="abc\n"), "pr_creation": result(stdout=prs),
            "pr_verification": [result(stdout=pr), result(stdout=json.dumps([{"filename": "data/production_runs/30663562841/manifest.json"}]))]})
        h.git_tree_digest = lambda ref: (count, digest)
        self.assertEqual("persisted", h.execute()["intake_status"])
        self.assertNotIn("branch_push", [stage for stage, _ in h.calls])

    def test_conflicting_existing_evidence_fails(self):
        h = Harness(self.args, {"evidence_staging": result(1), "branch_creation": [result(0), result()]})
        h.git_tree_digest = lambda ref: (99, "wrong")
        with self.assertRaisesRegex(module.PersistenceError, "not byte-identical"):
            h.execute()

    def test_changed_file_boundary_no_canonical_write_or_promotion(self):
        pr = json.dumps({"state": "open", "head": {"ref": self.args.destination_branch, "sha": "abc"}, "base": {"ref": "main"}})
        h = Harness(self.args, {"pr_verification": [result(stdout=pr), result(stdout=json.dumps([{"filename": "data/canonical/games/magic.json"}]))]})
        with self.assertRaisesRegex(module.PersistenceError, "out-of-bound"):
            h.verify_pr(7, "abc")
        self.assertFalse(h.report["canonical_write"])
        self.assertFalse(h.report["promotion_performed"])

    def test_workflow_always_runs_persistence_and_uploads_failure_report(self):
        workflow = WORKFLOW.read_text()
        self.assertNotIn("if: ${{ !inputs.dry_run }}", workflow)
        self.assertIn("scripts/production_evidence_persistence.py", workflow)
        self.assertIn("persistence-report.json", workflow)
        self.assertIn("if: ${{ always() }}", workflow)


if __name__ == "__main__":
    unittest.main()
