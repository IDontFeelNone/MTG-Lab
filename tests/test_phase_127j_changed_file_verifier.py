"""Phase 127J machine-readable market evidence boundary tests."""

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from scripts.verify_market_evidence_boundary import TRANSIENT_PATHS, verify


RUN_ID = "scryfall-mb2-12345-1"


class Phase127JChangedFileVerifierTests(unittest.TestCase):
    def make_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=root, check=True)
        (root / "baseline.txt").write_text("baseline\n")
        subprocess.run(["git", "add", "baseline.txt"], cwd=root, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=root, check=True)
        return temporary, root

    def write_boundary(self, root, run_id=RUN_ID, manifest_run_id=None):
        evidence = root / "data/market/acquisitions" / run_id
        evidence.mkdir(parents=True)
        (evidence / "dry-run-report.json").write_text("{}\n")
        (evidence / "manifest.json").write_text(json.dumps({
            "acquisition_run_id": manifest_run_id or run_id,
        }) + "\n")
        (evidence / "source-mb2.json").write_text("[]\n")
        for name in TRANSIENT_PATHS:
            (root / name).write_text("diagnostic\n")
        return evidence

    def test_valid_pre_commit_report_has_exact_seven_untracked_paths(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_boundary(root)
            report = verify(root, RUN_ID, "pre-commit")
            self.assertTrue(report["valid"])
            self.assertEqual(len(report["expected_durable_paths"]), 3)
            self.assertEqual(len(report["permitted_transient_paths"]), 4)
            self.assertEqual(len(report["actual_changed_paths"]), 7)
            self.assertEqual({item["status"] for item in report["path_statuses"]}, {"??"})
            self.assertEqual(report["failure_reason_codes"], [])
            # Reproduce Phase 127I: the real seven-path status cannot equal its
            # former three-durable-path-only shell expectation.
            self.assertNotEqual(report["actual_changed_paths"],
                                report["expected_durable_paths"])

    def test_valid_commit_boundary_is_exactly_three_staged_durable_paths(self):
        temporary, root = self.make_repository()
        with temporary:
            evidence = self.write_boundary(root)
            subprocess.run(["git", "add", "--", str(evidence.relative_to(root))], cwd=root, check=True)
            report = verify(root, RUN_ID, "commit")
            self.assertTrue(report["valid"])
            self.assertEqual(report["staged_paths"], report["expected_durable_paths"])
            statuses = {item["path"]: item["status"] for item in report["path_statuses"]}
            self.assertTrue(all(statuses[path] == "A " for path in report["expected_durable_paths"]))
            self.assertTrue(all(statuses[path] == "??" for path in report["permitted_transient_paths"]))

    def test_missing_evidence_and_transient_files_fail(self):
        temporary, root = self.make_repository()
        with temporary:
            evidence = self.write_boundary(root)
            (evidence / "source-mb2.json").unlink()
            (root / TRANSIENT_PATHS[0]).unlink()
            report = verify(root, RUN_ID, "pre-commit")
            self.assertFalse(report["valid"])
            self.assertIn("missing_durable_path", report["failure_reason_codes"])
            self.assertIn("missing_evidence_file", report["failure_reason_codes"])
            self.assertIn("missing_transient_path", report["failure_reason_codes"])

    def test_unexpected_untracked_file_and_space_are_structured(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_boundary(root)
            (root / "unauthorized file.txt").write_text("no\n")
            report = verify(root, RUN_ID, "pre-commit")
            self.assertIn("unauthorized file.txt", report["unexpected_paths"])
            self.assertIn("unauthorized file.txt", report["unsafe_paths"])
            self.assertIn("unexpected_path", report["failure_reason_codes"])
            self.assertIn("unsafe_path", report["failure_reason_codes"])

    def test_unexpected_tracked_staged_and_unstaged_changes_fail(self):
        for staged, expected in ((False, "unexpected_path"), (True, "unauthorized_staged_path")):
            with self.subTest(staged=staged):
                temporary, root = self.make_repository()
                with temporary:
                    self.write_boundary(root)
                    (root / "baseline.txt").write_text("modified\n")
                    if staged:
                        subprocess.run(["git", "add", "baseline.txt"], cwd=root, check=True)
                    report = verify(root, RUN_ID, "pre-commit")
                    self.assertFalse(report["valid"])
                    self.assertIn(expected, report["failure_reason_codes"])
                    status = next(x["status"] for x in report["path_statuses"]
                                  if x["path"] == "baseline.txt")
                    self.assertEqual(status, "M " if staged else " M")

    def test_deletion_and_rename_fail_with_exact_reasons(self):
        temporary, root = self.make_repository()
        with temporary:
            evidence = self.write_boundary(root)
            subprocess.run(["git", "add", "--", str(evidence.relative_to(root))], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "evidence"], cwd=root, check=True)
            (evidence / "source-mb2.json").unlink()
            report = verify(root, RUN_ID, "pre-commit")
            self.assertIn("deletion_not_permitted", report["failure_reason_codes"])
        temporary, root = self.make_repository()
        with temporary:
            evidence = self.write_boundary(root)
            subprocess.run(["git", "add", "--", str(evidence.relative_to(root))], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "evidence"], cwd=root, check=True)
            subprocess.run(["git", "mv", str((evidence / "source-mb2.json").relative_to(root)),
                            str((evidence / "renamed.json").relative_to(root))], cwd=root, check=True)
            report = verify(root, RUN_ID, "commit")
            self.assertIn("rename_not_permitted", report["failure_reason_codes"])
            self.assertIn(str((evidence / "renamed.json").relative_to(root)), report["unexpected_paths"])

    def test_symlink_unsafe_run_id_and_manifest_mismatch_fail(self):
        temporary, root = self.make_repository()
        with temporary:
            evidence = self.write_boundary(root)
            (evidence / "source-mb2.json").unlink()
            (evidence / "source-mb2.json").symlink_to(root / "baseline.txt")
            self.assertIn("evidence_symlink", verify(root, RUN_ID, "pre-commit")["failure_reason_codes"])
        temporary, root = self.make_repository()
        with temporary:
            self.write_boundary(root, manifest_run_id="scryfall-mb2-999-1")
            self.assertIn("manifest_run_id_mismatch",
                          verify(root, RUN_ID, "pre-commit")["failure_reason_codes"])
            self.assertIn("unsafe_run_id",
                          verify(root, "../unsafe", "pre-commit")["failure_reason_codes"])

    def test_canonical_and_market_observation_changes_are_explicit(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_boundary(root)
            canonical = root / "data/canonical/changed.json"
            observation = root / "data/market/observations/changed.json"
            canonical.parent.mkdir(parents=True); observation.parent.mkdir(parents=True)
            canonical.write_text("{}\n"); observation.write_text("{}\n")
            report = verify(root, RUN_ID, "pre-commit")
            self.assertEqual(report["canonical_paths"], ["data/canonical/changed.json"])
            self.assertEqual(report["market_observation_paths"],
                             ["data/market/observations/changed.json"])
            self.assertIn("canonical_change", report["failure_reason_codes"])
            self.assertIn("market_observation_change", report["failure_reason_codes"])

    def test_cli_writes_structured_diagnostics_before_failure(self):
        temporary, root = self.make_repository()
        with temporary:
            self.write_boundary(root)
            (root / "unexpected.txt").write_text("no\n")
            output = root / "report.json"
            script = Path(__file__).parents[1] / "scripts/verify_market_evidence_boundary.py"
            completed = subprocess.run(
                ["python", str(script), "--repository", str(root), "--run-id", RUN_ID,
                 "--output", str(output)], text=True, capture_output=True,
            )
            self.assertEqual(completed.returncode, 1)
            self.assertTrue(output.is_file())
            self.assertEqual(json.loads(completed.stdout), json.loads(output.read_text()))
            self.assertFalse(json.loads(completed.stdout)["valid"])

    def test_workflow_prints_status_and_reports_and_always_preserves_them(self):
        workflow = (Path(__file__).parents[1] /
                    ".github/workflows/market-acquisition.yml").read_text()
        self.assertGreaterEqual(workflow.count("git status --short --untracked-files=all"), 2)
        for name in ("market-acquisition-pre-commit-boundary.json",
                     "market-acquisition-commit-boundary.json"):
            self.assertIn("cat \"$RUNNER_TEMP/" + name + "\"", workflow)
        retention = workflow[workflow.index("- name: Retain diagnostics"):]
        self.assertIn("if: always()", retention)
        self.assertIn("${{ runner.temp }}/market-acquisition-*-boundary.json", retention)


if __name__ == "__main__":
    unittest.main()
