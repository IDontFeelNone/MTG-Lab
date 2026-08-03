import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from production_evidence.pilot_printings import FILES, PILOT
from scripts.verify_pilot_printing_evidence_boundary import verify


ROOT = Path(__file__).parents[1]
WORKFLOW = ROOT / ".github/workflows/pilot-printing-acquisition.yml"


class Phase135AWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text()

    def test_manual_only_minimum_permissions_and_dependencies(self):
        self.assertIn("workflow_dispatch:", self.text)
        self.assertNotIn("schedule:", self.text); self.assertNotIn("push:\n", self.text)
        self.assertIn("permissions:\n  contents: read", self.text)
        self.assertIn("contents: write\n      pull-requests: write", self.text)
        self.assertNotIn("actions: write", self.text)
        self.assertIn("pip install --upgrade pip", self.text)
        self.assertIn("pip install -r requirements.txt", self.text)

    def test_single_acquisition_deterministic_identity_and_transient_boundary(self):
        command = "python scripts/retain_pilot_printings.py"
        self.assertEqual(self.text.count(command), 1)
        self.assertIn('RUN_ID="mtgjson-pilot-${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"', self.text)
        self.assertIn('ref: ${{ github.sha }}', self.text)
        self.assertIn('> "$RUNNER_TEMP/acquisition.log"', self.text)
        self.assertNotIn("AllPrintings.json.gz\n", self.text)

    def test_generated_valid_timestamp_is_passed_and_diagnosed(self):
        self.assertIn("ACQUIRED_AT=\"$(date -u +'%Y-%m-%dT%H:%M:%SZ')\"", self.text)
        self.assertIn('printf \'%s\\n\' "$ACQUIRED_AT" > "$RUNNER_TEMP/acquired-at.txt"', self.text)
        self.assertIn('--acquired-at "$ACQUIRED_AT"', self.text)
        self.assertIn('--diagnostics "$RUNNER_TEMP/transport-diagnostic.json"', self.text)
        self.assertNotIn("github.run_started_at", self.text)

    def test_exact_files_branch_replay_pr_and_diagnostics(self):
        for name in FILES: self.assertIn(f'$EVIDENCE/{name}', self.text)
        self.assertIn('pilot-printing-acquisition/$RUN_ID', self.text)
        self.assertIn("cmp --silent", self.text); self.assertIn("git fetch origin", self.text)
        self.assertNotIn("--force", self.text); self.assertNotIn("gh pr merge", self.text)
        self.assertIn("gh pr create --head", self.text); self.assertIn("gh pr list --state all", self.text)
        for field in ("baseRefName", "headRefName", "headRefOid", "title", "state"): self.assertIn(field, self.text)
        self.assertIn("if: always()", self.text); self.assertIn("retention-days: 14", self.text)
        self.assertNotIn("data/canonical", self.text.split("git add --", 1)[1].splitlines()[0])
        self.assertNotIn("promotion", self.text.split("scripts/retain_pilot_printings.py", 1)[0])


class BoundaryVerifierTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.root, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.root, check=True)
        (self.root / "seed").write_text("seed\n"); subprocess.run(["git", "add", "seed"], cwd=self.root, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=self.root, check=True)
        self.run_id = "mtgjson-pilot-123-1"; self.directory = self.root / "data/evidence/phase-135" / self.run_id
        self.directory.mkdir(parents=True)
        rows=[]
        for index, name in enumerate(PILOT, 1):
            rows.append({"card_name": name, "set_code": "TST", "provider_printing_id": f"00000000-0000-4000-8000-{index:012d}"})
        manifest={"acquisition_run_id": self.run_id, "pilot_scope": list(PILOT), "printing_counts_by_pilot_card": {x:1 for x in PILOT},
            "unmatched_pilot_cards": [], "ambiguous_records": 0, "malformed_records": 0, "unsupported_records": 0,
            "canonical_write": False, "promotion_performed": False, "facts_created": False, "retained_printing_count": 10}
        payloads={"manifest.json":manifest, "source-pilot-printings.json":{"pilot_printings":rows}, "acquisition-report.json":{}}
        for name, value in payloads.items(): (self.directory/name).write_text(json.dumps(value)+"\n")

    def tearDown(self): self.temp.cleanup()

    def test_precommit_and_commit_exact_boundary(self):
        self.assertTrue(verify(self.root, self.run_id, "pre-commit")["valid"])
        subprocess.run(["git", "add", "--", str(self.directory.relative_to(self.root))], cwd=self.root, check=True)
        self.assertTrue(verify(self.root, self.run_id, "commit")["valid"])

    def test_rejects_unrelated_protected_symlink_and_bad_census(self):
        (self.root / "unrelated").write_text("x")
        self.assertIn("changed_file_boundary_mismatch", verify(self.root, self.run_id, "pre-commit")["failure_reason_codes"])
        (self.root / "unrelated").unlink(); manifest=json.loads((self.directory/"manifest.json").read_text())
        manifest["facts_created"]=True; (self.directory/"manifest.json").write_text(json.dumps(manifest))
        self.assertIn("census_or_safety_gate_failed", verify(self.root, self.run_id, "pre-commit")["failure_reason_codes"])


if __name__ == "__main__": unittest.main()
