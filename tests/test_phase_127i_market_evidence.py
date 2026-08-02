"""Phase 127I durable bounded market-acquisition evidence tests."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.market_acquisition_evidence import branch_name, retain, verify

ROOT = Path(__file__).parents[1]


class Phase127IEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.canonical = (ROOT / "data/canonical/state.json").read_bytes()
        self.canonical_id = "sha256:" + hashlib.sha256(self.canonical).hexdigest()
        self.run_id = "scryfall-mb2-12345-1"
        self.source = [{"id": "one", "set": "mb2", "prices": {"usd": "1.00"}}]
        self.report = {
            "schema_version": "market-acquisition-run-v1", "run_id": self.run_id,
            "provider": "scryfall", "source_dataset": "default_cards",
            "source_url": "scryfall:default_cards", "retrieved_at": "2026-08-02T01:02:03Z",
            "source_observed_at": "2026-08-02T00:00:00Z", "currency": "USD",
            "target": {"set": "MB2", "promoted_only": True},
            "source_sha256": "1" * 64, "normalized_sha256": "2" * 64,
            "canonical_snapshot_identity": self.canonical_id,
            "mapping_counts": {"matched": 1, "unmatched": 0, "ambiguous": 0, "rejected": 0},
            "source_record_count": 99999, "mb2_record_count": 1,
            "known_price_observation_count": 1, "missing_price_observation_count": 0,
            "observation_count": 1, "canonical_write": False,
            "promotion_performed": False, "persisted": False,
        }

    def make(self, temp, report=None, source=None):
        root = Path(temp); (root / "canonical").mkdir(parents=True)
        (root / "canonical/state.json").write_bytes(self.canonical)
        rp, sp = root / "report.json", root / "source.json"
        rp.write_text(json.dumps(report or self.report)); sp.write_text(json.dumps(source or self.source))
        return root, rp, sp

    def test_successful_retention_deterministic_layout_manifest_and_digests(self):
        with tempfile.TemporaryDirectory() as temp:
            root, rp, sp = self.make(temp); manifest = retain(rp, sp, root)
            directory = root / "market/acquisitions" / self.run_id
            self.assertEqual(sorted(x.name for x in directory.iterdir()),
                             ["dry-run-report.json", "manifest.json", "source-mb2.json"])
            self.assertEqual(manifest, verify(directory, root / "canonical/state.json"))
            for name, identity in manifest["files"].items():
                payload = (directory / name).read_bytes()
                self.assertEqual(hashlib.sha256(payload).hexdigest(), identity["sha256"])
            self.assertEqual(manifest["canonical_snapshot_identity"], self.canonical_id)
            self.assertEqual(manifest["mapping_counts"], self.report["mapping_counts"])
            self.assertEqual(manifest["price_census"], {"known": 1, "missing": 0, "observations": 1})
            self.assertFalse(manifest["canonical_write"])
            self.assertFalse(manifest["promotion_performed"])
            self.assertFalse(manifest["observations_persisted"])

    def test_idempotent_replay_and_conflicting_replay_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            root, rp, sp = self.make(temp); first = retain(rp, sp, root)
            before = {x.name: x.read_bytes() for x in (root/"market/acquisitions"/self.run_id).iterdir()}
            self.assertEqual(first, retain(rp, sp, root))
            self.assertEqual(before, {x.name: x.read_bytes() for x in (root/"market/acquisitions"/self.run_id).iterdir()})
            changed = copy.deepcopy(self.report); changed["normalized_sha256"] = "3" * 64
            rp.write_text(json.dumps(changed))
            with self.assertRaisesRegex(ValueError, "conflicting"):
                retain(rp, sp, root)

    def test_digest_tampering_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root, rp, sp = self.make(temp); retain(rp, sp, root)
            directory = root / "market/acquisitions" / self.run_id
            (directory / "source-mb2.json").write_text("[]\n")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                verify(directory, root / "canonical/state.json")

    def test_mb2_boundary_and_full_provider_exclusion(self):
        with tempfile.TemporaryDirectory() as temp:
            bad = self.source + [{"id": "other", "set": "neo"}]
            report = dict(self.report, mb2_record_count=2)
            root, rp, sp = self.make(temp, report, bad)
            with self.assertRaisesRegex(ValueError, "non-MB2"):
                retain(rp, sp, root)
        with tempfile.TemporaryDirectory() as temp:
            full = [{"id": str(x), "set": "mb2"} for x in range(1001)]
            root, rp, sp = self.make(temp, dict(self.report, mb2_record_count=1001), full)
            with self.assertRaisesRegex(ValueError, "bounded"):
                retain(rp, sp, root)

    def test_canonical_and_observation_isolation(self):
        with tempfile.TemporaryDirectory() as temp:
            root, rp, sp = self.make(temp); before = (root/"canonical/state.json").read_bytes()
            retain(rp, sp, root)
            self.assertEqual(before, (root/"canonical/state.json").read_bytes())
            self.assertFalse((root/"market/observations").exists())
            changed = root/"canonical/changed.json"; changed.write_text("{}")
            with self.assertRaisesRegex(ValueError, "canonical snapshot"):
                verify(root/"market/acquisitions"/self.run_id, changed)

    def test_write_flags_are_mandatory(self):
        for field in ("canonical_write", "promotion_performed", "persisted"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as temp:
                report = dict(self.report); report[field] = True
                root, rp, sp = self.make(temp, report)
                with self.assertRaisesRegex(ValueError, "isolation"):
                    retain(rp, sp, root)

    def test_deterministic_branch_and_workflow_safety_contract(self):
        self.assertEqual(branch_name(self.run_id), "market-acquisition/" + self.run_id)
        workflow = (ROOT / ".github/workflows/market-acquisition.yml").read_text()
        for required in ("branch collision or conflicting evidence identity", "git diff --name-only",
                         "gh pr list --state all", "baseRefName", "headRefName", "headRefOid",
                         "gh pr checks", "--required --watch",
                         "gh workflow run python-validation.yml --ref \"$BRANCH\"",
                         "required checks were not registered",
                         "length > 0 and all(.[]; .state == \"SUCCESS\")",
                         "gh pr merge \"$PR\" --auto"):
            self.assertIn(required, workflow)
        self.assertNotIn("branches/$BASE/protection", workflow)
        self.assertNotIn("branch-protection.json", workflow)
        self.assertNotIn("--force", workflow)
        self.assertNotIn("--admin", workflow)

    def test_required_checks_are_explicitly_registered_before_the_gate(self):
        workflow = (ROOT / ".github/workflows/market-acquisition.yml").read_text()
        register = workflow.index("Register required pull-request checks")
        gate = workflow.index("Require checks and request auto-merge")
        self.assertLess(register, gate)
        section = workflow[register:gate]
        self.assertIn("actions: write", workflow)
        self.assertIn("gh workflow run python-validation.yml --ref \"$BRANCH\"", section)
        self.assertIn("gh pr checks \"$PR\" --required --json name", section)
        self.assertIn("if test \"${CHECK_COUNT:-0}\" -gt 0", section)
        self.assertIn("headRefOid", section)

    def test_failure_diagnostics_remain_always_uploaded(self):
        workflow = (ROOT / ".github/workflows/market-acquisition.yml").read_text()
        upload = workflow.index("Upload acquisition diagnostics")
        self.assertLess(upload, workflow.index("Verify dry run hard stop"))
        self.assertIn("if: always()", workflow[upload:upload + 500])
        self.assertIn("retention-days: 14", workflow[upload:upload + 500])

    def test_changed_file_boundary_accounts_for_workflow_diagnostics(self):
        workflow = (ROOT / ".github/workflows/market-acquisition.yml").read_text()
        validation = workflow[workflow.index("Validate repository and changed-file boundary"):
                              workflow.index("Create or safely reuse evidence branch")]
        self.assertIn("scripts/verify_market_evidence_boundary.py", validation)
        self.assertIn("--boundary pre-commit", validation)
        self.assertIn("git status --short --untracked-files=all", validation)
        verifier = (ROOT / "scripts/verify_market_evidence_boundary.py").read_text()
        for transient in ("market-acquisition-dry-run.json",
                          "market-acquisition-run-id.txt",
                          "market-acquisition-source-mb2.json",
                          "market-acquisition-stamp.txt"):
            self.assertIn(transient, verifier)


if __name__ == "__main__":
    unittest.main()
