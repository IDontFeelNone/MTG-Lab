"""The ordinary CLI plans by default and supplies no admission authority."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/automatic_canonical_update.py"
FIXTURE = ROOT / "tests/fixtures/phase_121_synthetic"


class AutomaticUpdateCliPlanningTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        shutil.copytree(FIXTURE / "data", self.root / "data")
        self.config = self.root / "config.json"
        shutil.copyfile(FIXTURE / "config.json", self.config)

    def inventory(self):
        return {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.rglob("*") if p.is_file()}

    def invoke(self, command=None, *, config=None, environment=None):
        args = [sys.executable, str(SCRIPT)]
        if command is not None:
            args.append(command)
        args.extend(["--config", str(config or self.config),
                     "--repository-root", str(self.root)])
        env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")
        env.update(environment or {})
        return subprocess.run(args, cwd=self.root, env=env,
                              capture_output=True, text=True, timeout=10)

    def assert_blocked(self, result):
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        document = json.loads(result.stdout)
        self.assertEqual(document["status"], "blocked")
        return document

    def pending_payload(self):
        path = self.root / "data/evidence/candidates.json"
        payload = json.loads(path.read_bytes())
        for row in payload["candidate_payloads"]:
            row.pop("final_classification", None)
            row["review_status"] = "pending"
        path.write_text(json.dumps(payload))
        config = json.loads(self.config.read_bytes())
        config["integrity"]["candidate_payload_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.config.write_text(json.dumps(config))
        return path

    def test_omitted_command_matches_explicit_plan_without_any_file_changes(self):
        before = self.inventory()
        default = self.invoke()
        explicit = self.invoke("plan")
        self.assertEqual(default.returncode, 0, default.stderr)
        self.assertEqual(explicit.returncode, 0, explicit.stderr)
        self.assertEqual(default.stderr, "")
        self.assertEqual(json.loads(default.stdout), json.loads(explicit.stdout))
        self.assertFalse(json.loads(default.stdout)["canonical_write"])
        self.assertEqual(self.inventory(), before)

    def test_missing_config_returns_blocked_json_without_file_changes(self):
        before = self.inventory()
        document = self.assert_blocked(self.invoke(config=self.root / "absent.json"))
        self.assertTrue(document["error"].startswith("FileNotFoundError:"))
        self.assertEqual(self.inventory(), before)

    def test_invalid_configuration_returns_blocked_json_without_file_changes(self):
        original = json.loads(self.config.read_bytes())
        for change in ({"schema_version": "unsupported"}, {"data_root": "../outside"}):
            with self.subTest(change=change):
                self.config.write_text(json.dumps({**original, **change}))
                before = self.inventory()
                document = self.assert_blocked(self.invoke())
                self.assertTrue(document["error"].startswith("EvidenceError:"))
                self.assertEqual(self.inventory(), before)

    def test_explicit_execute_cannot_admit_pending_rows_without_a_boundary(self):
        payload = self.pending_payload()
        original = (self.root / "data/canonical/state.json").read_bytes()
        pending = payload.read_bytes()
        document = self.assert_blocked(self.invoke("execute"))
        self.assertIn("authenticated trusted host review boundary", document["error"])
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), original)
        self.assertEqual(payload.read_bytes(), pending)
        self.assertFalse((self.root / "data/audit/syn-batch-000001-4f2c.json").exists())

    def test_json_approval_and_actor_environment_do_not_install_a_boundary(self):
        self.pending_payload()
        config = json.loads(self.config.read_bytes())
        config["approved"] = True
        config["review_boundary"] = {"approved": True, "actor": "fictional-owner"}
        self.config.write_text(json.dumps(config))
        original = (self.root / "data/canonical/state.json").read_bytes()
        document = self.assert_blocked(self.invoke("execute", environment={
            "GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "fictional-owner",
            "GITHUB_TRIGGERING_ACTOR": "fictional-owner"}))
        self.assertIn("authenticated trusted host review boundary", document["error"])
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), original)
        self.assertFalse((self.root / "data/audit/syn-batch-000001-4f2c.json").exists())


if __name__ == "__main__":
    unittest.main()
