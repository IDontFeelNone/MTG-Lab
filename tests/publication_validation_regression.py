"""Slow integration: actual publication gate runs the complete project suite.

Run explicitly after discovery (also in CI), so the suite executed by the gate
does not recursively launch another whole-suite publication. No test is skipped,
validation is not mocked, and platform doubles grant no live GitHub authority.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time
import unittest

from catalog_admission_helpers import prepare_reference_rehearsal, RECOMMENDED_DIGEST
from production_evidence.automatic_updates import (
    AutomaticCanonicalUpdate, GitHubPersistence, IsolatedAdmissionTestBoundary, digest,
)
from test_automatic_update_publication import FictionalGitHubTransport

ROOT = Path(__file__).resolve().parents[1]


def nested_validation_diagnostics(raw, validation):
    """Describe the actual retained subprocess log without changing its authority.

    Production already decided whether publication may proceed. These independent
    consistency checks make the integration test's observations auditable; they
    neither replace validation nor become canonical evidence.
    """
    if type(raw) is not bytes or type(validation) is not dict:
        raise ValueError("validation diagnostics require log bytes and the real result")
    log_sha256 = hashlib.sha256(raw).hexdigest()
    if validation.get("log_sha256") != log_sha256:
        raise ValueError("retained validation log hash differs from the real result")
    if type(validation.get("exit_status")) is not int or validation["exit_status"] != 0:
        raise ValueError("validation diagnostics require a successful real result")
    text = raw.decode("utf-8")
    summaries = re.findall(r"^Ran (\d+) tests? in (\d+(?:\.\d+)?)s\r?$", text, re.MULTILINE)
    final = re.search(
        r"^Ran (\d+) tests? in (\d+(?:\.\d+)?)s\r?\n\r?\n"
        r"OK(?: \(skipped=(\d+)\))?\r?\n?\Z", text, re.MULTILINE)
    if len(summaries) != 1 or final is None:
        raise ValueError("one complete successful nested discovery summary is required")
    count = int(final[1])
    if (type(validation.get("tests")) is not int or count <= 0
            or count != validation["tests"]):
        raise ValueError("nested discovery test count differs from the real result")
    elapsed = float(final[2])
    if not math.isfinite(elapsed):
        raise ValueError("observed nested discovery duration must be finite")
    skipped = int(final[3]) if final[3] is not None else 0
    observed_skips = len(re.findall(r"^.* \.\.\. skipped [^\r\n]+\r?$", text, re.MULTILINE))
    if skipped > count or observed_skips != skipped:
        raise ValueError("verbose skip entries differ from the nested discovery summary")
    return {"tests": count, "elapsed_seconds": elapsed, "skipped": skipped,
            "log_sha256": log_sha256}


class ExpandedPublicationValidationRegression(unittest.TestCase):
    def git(self, *args):
        return subprocess.check_output(["git", *args], cwd=self.root, text=True, stderr=subprocess.PIPE)

    def engine(self):
        return AutomaticCanonicalUpdate(self.root, self.config)

    def prepare_writer_expansion(self):
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
        original_paths = {p.decode() for p in paths if p}
        code_paths = original_paths | set(extra)
        for relative in sorted(code_paths):
            if relative.startswith("data/"):
                continue
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
        self.git("init", "--quiet", "--initial-branch=main")
        self.git("config", "user.name", "SIMULATED_PUBLICATION_TEST_ONLY")
        self.git("config", "user.email", "fictional@example.invalid")
        # Seed only the explicit copied tracked-file inventory and the already
        # bound rehearsal inputs. Historical files that match ignore rules must
        # remain tracked in this baseline, not become unrelated ignored extras.
        # This repository is disposable; nothing here is sent to GitHub.
        config = json.loads(self.config.read_bytes())
        artifacts = config["artifacts"]
        seed = {name for name in code_paths if (self.root / name).is_file()}
        seed.add(self.config.relative_to(self.root).as_posix())
        seed.update("data/" + artifacts[key] for key in ("source_artifact", "candidate_payload"))
        seed.update("data/" + ref["path"] for ref in artifacts["receipts"])
        ignored_history = {"data/canonical/state.json",
            "data/validation/production-runs/30649546787/phase109_run_evidence_summary.json"}
        self.assertTrue(ignored_history <= original_paths & seed)
        self.git("add", "--", *sorted(seed - ignored_history))
        self.git("add", "--force", "--", *sorted(ignored_history))
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
        return engine, plan, decision

    def test_real_writer_expansion_passes_real_publication_suite_and_readback(self):
        started = time.monotonic()
        engine, plan, decision = self.prepare_writer_expansion()
        prepared = time.monotonic()
        transport = FictionalGitHubTransport(self)
        # No validation replacement: this calls the publication helper, real
        # writer-output integrity checks and its complete unittest subprocess.
        result = GitHubPersistence(transport).publish_admission(
            engine, plan, self.base, decision, repository="IDontFeelNone/MTG-Lab")
        publication_finished = time.monotonic()
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
        readback_head = self.git("ls-remote", "origin", "refs/heads/" + engine.descriptor.destination_branch).split()[0]
        self.assertEqual(readback_head, result["head"])
        self.assertFalse(any("merge" in c or "--force" in c for c in transport.calls))
        nested = nested_validation_diagnostics(
            (self.root / ".git/catalog-admission-validation.log").read_bytes(), result["validation"])
        completed = time.monotonic()
        print(json.dumps({"simulated_platform_only": True, "actual_writer_card_count": 654,
            "validation": result["validation"], "nested_discovery": nested,
            "timings_seconds": {"preparation": prepared - started,
                "publication_integration": publication_finished - prepared,
                "total_integration": completed - started},
            "published_head": result["head"], "readback_head": readback_head,
            "published_to": "disposable_local_bare_remote"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
