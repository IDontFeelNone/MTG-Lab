"""Static safety contract for the GitHub-native production evidence intake."""
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "production-evidence-intake.yml"


class ProductionEvidenceIntakeWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_dispatch_defaults_select_first_successful_reviewable_run(self):
        self.assertIn('default: "30663562841"', self.workflow)
        self.assertIn("default: mtgjson-ingestion-30663562841", self.workflow)
        self.assertIn("archive_sha256:", self.workflow)

    def test_artifact_is_authenticated_and_phase_111_intake_is_reverified(self):
        self.assertIn("sha256sum --check --strict", self.workflow)
        self.assertIn("normalize-workflow-artifact", self.workflow)
        self.assertLess(self.workflow.index("sha256sum --check --strict"),
                        self.workflow.index("normalize-workflow-artifact"))
        self.assertIn("evidence intake", self.workflow)
        self.assertGreaterEqual(self.workflow.count("evidence verify"), 2)
        self.assertIn("status\") != \"completed\"", self.workflow)
        self.assertIn("conclusion\") != \"success\"", self.workflow)

    def test_write_scope_is_noncanonical_and_pr_based(self):
        self.assertIn("grep -Ev '^data/production_runs/'", self.workflow)
        self.assertIn('branch="$DESTINATION_BRANCH"', self.workflow)
        self.assertIn('test "$branch" = "production-evidence/run-$RUN_ID"', self.workflow)
        self.assertIn("git diff --cached --quiet", self.workflow)
        self.assertIn("gh pr create", self.workflow)
        self.assertNotIn("reviewed-promotion", self.workflow)

    def test_dry_run_uploads_adapter_contract_without_git_side_effects(self):
        self.assertIn("dry_run:", self.workflow)
        self.assertIn("if: ${{ !inputs.dry_run }}", self.workflow)
        self.assertIn("normalized/adapter-report.json", self.workflow)
        self.assertIn("normalized/manifest.json", self.workflow)
        self.assertIn("normalized/normalized-inventory.json", self.workflow)
        self.assertIn("verification-result.json", self.workflow)


if __name__ == "__main__":
    unittest.main()
