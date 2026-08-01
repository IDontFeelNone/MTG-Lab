"""Phase 117A GitHub-native authorization workflow tests (unittest only)."""
import json
from pathlib import Path
import re
from types import SimpleNamespace
import unittest

from production_evidence.operator_authorization import BATCH_ID, canonical_state_digest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/mb2-operator-authorization.yml"


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text()
        section = cls.text.split("    inputs:\n", 1)[1].split("\n# Repository Settings", 1)[0]
        cls.inputs = {}
        matches = list(re.finditer(r"(?m)^      ([a-z_]+):\n", section))
        for index, match in enumerate(matches):
            name = match.group(1)
            body = section[match.end():matches[index + 1].start() if index + 1 < len(matches) else len(section)]
            values = {}
            for line in body.splitlines():
                stripped = line.strip()
                if stripped.startswith("default: "):
                    raw = stripped.split(": ", 1)[1]
                    values["default"] = raw == "true" if raw in ("true", "false") else raw
            cls.inputs[name] = values

    def test_dispatch_input_contract_and_human_defaults_absent(self):
        expected = {"operator_identity", "operator_role", "review_reference", "reviewed_at",
            "authorization_decision", "operator_notes", "signature_request_digest",
            "authorized_batch_id", "authorized_candidate_digest", "destination_branch",
            "base_branch", "dry_run"}
        self.assertEqual(set(self.inputs), expected)
        for name in ("operator_identity", "operator_role", "review_reference", "reviewed_at",
                     "authorization_decision", "operator_notes"):
            self.assertNotIn("default", self.inputs[name])

    def test_immutable_defaults(self):
        expected = {
            "signature_request_digest": "4b281b3eb45b6a7e3e82a2309c271bffe1cb6c8cb939d46c5b8be059e0b6000d",
            "authorized_batch_id": BATCH_ID,
            "authorized_candidate_digest": "e32022126c07036337f810d06dc29b5eead5afd850f7f3af0a26ad5b0d46e66e",
            "destination_branch": f"operator-authorization/{BATCH_ID}", "base_branch": "main", "dry_run": True}
        self.assertEqual({key: self.inputs[key]["default"] for key in expected}, expected)

    def test_dry_run_and_safety_contract_are_explicit(self):
        for phrase in ("cp -a data", "build_signature_request", "canonical pre-state drift",
                       "operator-authorization.json", "git diff --quiet -- data/canonical",
                       "canonical_write: `false`", "promotion_performed: `false`",
                       "actions/upload-artifact@v4"):
            self.assertIn(phrase, self.text)
        self.assertIn("permissions:\n  contents: write\n  pull-requests: write", self.text)

    def test_scope_is_one_mb2_batch_and_excludes_msh(self):
        self.assertIn('target_isolation_status"] != "MB2_only"', self.text)
        self.assertIn('approved_candidate_count"] != 1000', self.text)
        self.assertNotIn("mb2-batch-000002", self.text)
        self.assertNotIn("data/reviews/phase-117/MSH", self.text)

    def test_base_checkout_and_persistence_are_durable(self):
        self.assertIn("ref: ${{ inputs.base_branch }}", self.text)
        for phrase in ('"git", "switch"', '"git", "commit"', '"git", "push"', '"gh", "pr", "create"',
                       "pull request state, base, or commit mismatch"):
            source = self.text + (ROOT / "scripts/mb2_authorization_persistence.py").read_text()
            self.assertIn(phrase, source)


class PersistenceBoundaryTests(unittest.TestCase):
    def test_dry_run_does_not_invoke_git_or_github(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("persistence", ROOT / "scripts/mb2_authorization_persistence.py")
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        args = SimpleNamespace(destination_branch=f"operator-authorization/{BATCH_ID}", base_branch="main",
            repository="owner/repo", authorization_digest="a" * 64, dry_run=True)
        calls = []
        report = module.Persistence(args, run=lambda *a, **k: calls.append(a)).execute()
        self.assertEqual(report["status"], "dry_run_verified"); self.assertEqual(calls, [])
        self.assertFalse(report["canonical_write"]); self.assertFalse(report["promotion_performed"])

    def test_retained_baseline_has_no_authorization_and_canonical_digest_is_exact(self):
        path = ROOT / "data/reviews/phase-117" / BATCH_ID / "operator-authorization.json"
        self.assertFalse(path.exists())
        self.assertEqual(canonical_state_digest(ROOT / "data"),
            "0e5ead0d4693f1dc75c2f7b5e401f22e4fa302f93bb8eab59f0ddeefd0f680ba")


if __name__ == "__main__": unittest.main()
