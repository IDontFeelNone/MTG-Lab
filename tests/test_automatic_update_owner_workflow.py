"""Offline host doubles; real entry point and repaired writer, disposable only.

No test authenticates a live GitHub operator or creates production authorization.
"""
from contextlib import redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from production_evidence.automatic_updates import (
    ADMISSION_OPERATION, AdmissionDecision, AutomaticCanonicalUpdate,
    IsolatedAdmissionTestBoundary, canonical_json, digest,
)
from production_evidence.repository import EvidenceError
import test_phase_120_automatic_updates as fixtures


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("owner_update_entry", ROOT / "scripts/automatic_canonical_update.py")
ENTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENTRY)
REAL_BOUNDARY = ENTRY.GitHubOwnerReviewBoundary


class SimulatedPlatformBoundary(REAL_BOUNDARY, IsolatedAdmissionTestBoundary):
    """TEST DOUBLE: platform checks plus non-reusable isolated authorization."""
    def __init__(self, engine, plan_id, revision, temporary):
        IsolatedAdmissionTestBoundary.__init__(self, temporary)
        REAL_BOUNDARY.__init__(self, engine, plan_id, revision)
        self.authenticated_reviewer = "SIMULATED_PLATFORM_OWNER_ONLY"

    def _decision(self, bindings):
        self._verify_root(self.engine.root)
        reference = "SIMULATED_GITHUB_PLATFORM_TEST_ONLY:" + canonical_json(
            {**self.context, "plan_id": self.plan_id}).decode()
        return AdmissionDecision("approved", self.authenticated_reviewer, self.decided_at,
                                 ADMISSION_OPERATION, deepcopy(bindings), reference, "isolated-test")


class OwnerWorkflowEntryTests(unittest.TestCase):
    def setUp(self):
        # Reviewed policy IDs are explicitly replaced only by this in-process
        # fictional platform double; no CLI flag/config can perform that change.
        for name, value in (("OWNER_REPOSITORY_ID", "200"), ("OWNER_ACCOUNT_ID", "100")):
            policy_double = patch.object(ENTRY, name, value)
            policy_double.start()
            self.addCleanup(policy_double.stop)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root, old_config = fixtures.AutomaticUpdateTests().synthetic(self.temporary.name)
        self.config_name = "config/automatic_updates/fictional.json"
        self.config = self.root / self.config_name
        self.config.parent.mkdir(parents=True)
        self.payload = self.root / "data/evidence/payload.json"
        self.source = self.root / "data/evidence/source.json"
        self.receipt = self.root / "data/evidence/fictional-policy.txt"
        self.receipt.write_text("Fictional test notice; simulated processing permission only.\n")
        config = json.loads(old_config.read_bytes())
        config["integrity"]["candidate_payload_sha256"] = digest(self.payload.read_bytes())
        config["artifacts"]["receipts"] = [{"path": "evidence/fictional-policy.txt",
            "role": "source-policy", "sha256": digest(self.receipt.read_bytes())}]
        self.config.write_text(json.dumps(config))
        old_config.unlink()
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Fictional fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "Fictional isolated fixture, not approval")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.plan_id = self.engine().plan()["plan_id"]
        self.inputs = {"operation": "admit", "config": self.config_name,
                       "expected_plan_id": self.plan_id, "reviewed_revision": self.revision}
        self.claims = {"repository": ENTRY.OWNER_REPOSITORY, "repository_id": "200",
            "repository_owner": "IDontFeelNone", "repository_owner_id": "100",
            "actor": "IDontFeelNone", "actor_id": "100", "run_id": "300", "run_attempt": "1",
            "jti": "SIMULATED_PLATFORM_CONTEXT_ONLY",
            "workflow_ref": f"{ENTRY.OWNER_REPOSITORY}/{ENTRY.OWNER_WORKFLOW}@{ENTRY.OWNER_REF}",
            "workflow_sha": self.revision, "sha": self.revision, "ref": ENTRY.OWNER_REF,
            "event_name": "workflow_dispatch", "runner_environment": "github-hosted",
            "sub": f"repo:{ENTRY.OWNER_REPOSITORY}:ref:{ENTRY.OWNER_REF}"}
        self.event = self.root / "fake-platform-event.json"
        self.environment = {"GITHUB_ACTIONS": "true", "GITHUB_WORKSPACE": str(self.root),
            "GITHUB_EVENT_PATH": str(self.event), "GITHUB_RUN_ID": "300", "GITHUB_RUN_ATTEMPT": "1",
            "GITHUB_TRIGGERING_ACTOR": "IDontFeelNone", "MTG_LAB_ADMISSION_OIDC": "SIMULATED_TRANSPORT_ONLY"}
        self.write_event()

    def git(self, *arguments):
        result = subprocess.run(["git", "-C", str(self.root), *arguments],
                                capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def write_event(self):
        self.event.write_text(json.dumps({"inputs": self.inputs,
            "repository": {"full_name": ENTRY.OWNER_REPOSITORY, "id": 200}, "sender": {"id": 100}}))

    def engine(self):
        return AutomaticCanonicalUpdate(self.root, self.config)

    def inventory(self):
        return {p.relative_to(self.root).as_posix(): digest(p.read_bytes())
                for p in self.root.rglob("*") if p.is_file() and not p.is_relative_to(self.root / ".git")}

    def invoke(self, command="plan", *, plan=None, revision=None, config=None, simulate=True):
        args = [command, "--github-owner-entry", "--repository-root", str(self.root),
                "--config", config or self.config_name]
        if plan is not None:
            args += ["--expected-plan-id", plan]
        if revision is not None:
            args += ["--reviewed-revision", revision]
        output = io.StringIO()
        factory = lambda engine, plan_id, sha: SimulatedPlatformBoundary(engine, plan_id, sha, self.temporary)
        with patch.dict(os.environ, self.environment), redirect_stdout(output), \
             patch.object(ENTRY, "_signed_github_claims", side_effect=lambda: deepcopy(self.claims)), \
             patch.object(ENTRY, "SOURCE_POLICY_CLEARED_PLANS", frozenset({self.plan_id})), \
             patch.object(ENTRY, "GitHubOwnerReviewBoundary", factory if simulate else REAL_BOUNDARY):
            code = ENTRY.main(args)
        return code, json.loads(output.getvalue())

    def assert_blocked_unchanged(self, reason, **options):
        before = self.inventory()
        code, report = self.invoke("admit", plan=self.plan_id, revision=self.revision, **options)
        self.assertEqual(code, 1, report)
        self.assertEqual(report["status"], "blocked")
        self.assertIn(reason, report["error"])
        self.assertEqual(self.inventory(), before)

    def test_default_workflow_planning_never_authorizes_executes_or_publishes(self):
        before = self.inventory()
        with patch.object(AutomaticCanonicalUpdate, "execute", side_effect=AssertionError("execute called")), \
             patch.object(REAL_BOUNDARY, "__init__", side_effect=AssertionError("decision boundary installed")):
            code, report = self.invoke()
        self.assertEqual(code, 0, report)
        self.assertFalse(report["canonical_write"])
        self.assertFalse(report["execution_authorized"])
        self.assertEqual(report["plan_id"], self.plan_id)
        self.assertEqual(report["reviewed_code_revision"], self.revision)
        self.assertEqual(report["publication"], "disabled")
        self.assertEqual(self.inventory(), before)

    def test_missing_expected_plan_or_reviewed_revision_never_installs_boundary(self):
        for plan, revision in ((None, self.revision), (self.plan_id, None), ("", self.revision)):
            with self.subTest(plan=plan, revision=revision):
                before = self.inventory()
                code, report = self.invoke("admit", plan=plan, revision=revision)
                self.assertEqual(code, 1)
                self.assertIn("explicit operation, expected plan", report["error"])
                self.assertEqual(self.inventory(), before)

    def test_missing_explicit_action_and_approved_json_cannot_supply_authority(self):
        self.inputs["operation"] = "plan"
        self.inputs["approved"] = True
        self.write_event()
        self.assert_blocked_unchanged("explicit owner admission action")

    def test_unauthorized_actor_repository_ref_workflow_and_runner_are_rejected(self):
        for field, value, reason in (("actor", "collaborator", "authorized repository owner"),
                ("actor_id", "999", "authorized repository owner"),
                ("repository", "other/repository", "repository/ref/workflow"),
                ("repository_id", "201", "repository/ref/workflow"),
                ("repository_owner_id", "101", "repository/ref/workflow"),
                ("ref", "refs/heads/unreviewed", "repository/ref/workflow"),
                ("workflow_ref", "other/workflow@refs/heads/main", "repository/ref/workflow"),
                ("event_name", "push", "repository/ref/workflow"),
                ("runner_environment", "self-hosted", "repository/ref/workflow"),
                ("sub", "repo:other/repo:ref:refs/heads/main", "subject")):
            with self.subTest(field=field):
                original = self.claims[field]
                self.claims[field] = value
                self.assert_blocked_unchanged(reason)
                self.claims[field] = original

    def test_reruns_and_different_triggering_actor_never_inherit_authority(self):
        self.claims["run_attempt"] = "2"
        self.assert_blocked_unchanged("reruns are unsupported")
        self.claims["run_attempt"] = "1"
        self.environment["GITHUB_TRIGGERING_ACTOR"] = "other-operator"
        self.assert_blocked_unchanged("runner/event context")

    def test_wrong_code_revision_run_identity_or_workspace_is_rejected(self):
        self.claims["workflow_sha"] = "a" * 40
        self.assert_blocked_unchanged("reviewed code revision")
        self.claims["workflow_sha"] = self.revision
        self.environment["GITHUB_RUN_ID"] = "400"
        self.assert_blocked_unchanged("runner/event context")
        self.environment["GITHUB_RUN_ID"] = "300"
        self.environment["GITHUB_WORKSPACE"] = str(self.root / "other")
        self.assert_blocked_unchanged("runner workspace")

    def test_immutable_subject_and_exact_simulated_action_reach_actual_writer(self):
        self.claims["sub"] = "repo:IDontFeelNone@100/MTG-Lab@200:ref:refs/heads/main"
        before_payload = self.payload.read_bytes()
        before_source = self.source.read_bytes()
        # These forbidden downstream methods must not even be reached.
        with patch.object(AutomaticCanonicalUpdate, "_stage_branch_and_pull_request_persistence",
                          side_effect=AssertionError("publication called")), \
             patch.object(AutomaticCanonicalUpdate, "_stage_automatic_merge_eligibility_verification",
                          side_effect=AssertionError("merge called")):
            code, report = self.invoke("admit", plan=self.plan_id, revision=self.revision)
        self.assertEqual(code, 0, report)
        self.assertEqual(report["status"], "validated-local-only")
        self.assertEqual(report["publication"], "disabled")
        self.assertFalse(report["automatic_merge"])
        engine = self.engine()
        audit = json.loads((self.root / "data/audit/promotion.json").read_bytes())
        decision = audit["admission_decision"]
        self.assertEqual(decision["scope"], "isolated-test")
        self.assertTrue(decision["review_reference"].startswith("SIMULATED_GITHUB_PLATFORM_TEST_ONLY:"))
        context = json.loads(decision["review_reference"].split(":", 1)[1])
        self.assertEqual(context["plan_id"], self.plan_id)
        self.assertEqual(context["code_revision"], self.revision)
        self.assertEqual(context["run_id"], "300")
        self.assertEqual(context["operation"], ADMISSION_OPERATION)
        self.assertEqual(decision["bindings"], engine.admission_bindings())
        self.assertEqual(engine.verify()["canonical_state_digest"], audit["canonical_post_state_digest"])
        state = json.loads((self.root / "data/canonical/state.json").read_bytes())
        self.assertEqual({kind: len(records) for kind, records in state.items()},
                         {"card": 1, "printing": 1, "finish": 1, "identifier": 0})
        self.assertEqual(state["printing"]["p1"]["values"]["card_id"], "c1")
        self.assertEqual(self.payload.read_bytes(), before_payload)
        self.assertEqual(self.source.read_bytes(), before_source)
        acceptance = json.loads(engine._checkpoint("query_and_analytics_smoke_tests").read_bytes())
        self.assertTrue(acceptance["details"]["consumer_validation"]["valid"])
        self.assertTrue(acceptance["details"]["consumer_validation"]["projection_valid"])
        self.assertEqual(acceptance["details"]["consumer_validation"]["printing_relationships_checked"], 1)
        self.assertFalse(engine._checkpoint("branch_and_pull_request_persistence").exists())
        self.assertFalse(engine._checkpoint("automatic_merge_eligibility_verification").exists())
        # A saved plan/decision never grants a later dispatch authority.
        self.assert_blocked_unchanged("plan identity does not match")

    def test_changed_plan_and_decision_relevant_inputs_do_not_reuse_authority(self):
        before = self.inventory()
        code, report = self.invoke("admit", plan="sha256:" + "0" * 64, revision=self.revision)
        self.assertEqual(code, 1)
        self.assertIn("plan identity", report["error"])
        self.assertEqual(self.inventory(), before)
        for path, reason in ((self.payload, "candidate payload checksum"),
                             (self.source, "source artifact hash"), (self.receipt, "retained receipt hash")):
            with self.subTest(path=path.name):
                original = path.read_bytes()
                path.write_bytes(original + b"\n")
                self.assert_blocked_unchanged(reason)
                path.write_bytes(original)
        drift = self.root / "data/canonical/drift.json"
        drift.write_text('{}\n')
        self.assert_blocked_unchanged("canonical pre-state drift")

    def test_changed_policy_configuration_is_not_silently_rebound(self):
        config = json.loads(self.config.read_bytes())
        config["policy"]["approved"] = True
        self.config.write_text(json.dumps(config))
        self.assert_blocked_unchanged("configuration differs from reviewed code")

    def test_distinct_reviewed_policy_change_still_cannot_reuse_old_plan(self):
        config = json.loads(self.config.read_bytes())
        config["policy"]["review_note"] = "Explicitly different fictional proposal"
        self.config.write_text(json.dumps(config))
        self.git("add", self.config_name)
        self.git("-c", "user.name=Fictional fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--quiet", "-m", "Distinct proposal, no approval")
        self.revision = self.git("rev-parse", "HEAD").strip()
        self.inputs["reviewed_revision"] = self.revision
        self.claims["sha"] = self.claims["workflow_sha"] = self.revision
        self.write_event()
        self.assert_blocked_unchanged("plan identity does not match")

    def test_real_entry_rejects_forged_local_platform_claims_without_any_write(self):
        before = self.inventory()
        arguments = ["admit", "--github-owner-entry", "--config", self.config_name,
            "--repository-root", str(self.root), "--expected-plan-id", self.plan_id,
            "--reviewed-revision", self.revision]
        for token, reason in (("", "signed platform identity"), ("FORGED_LOCAL_TOKEN", "OIDC verification failed")):
            with self.subTest(token=token):
                output = io.StringIO()
                with patch.dict(os.environ, {**self.environment, "MTG_LAB_ADMISSION_OIDC": token}), \
                     redirect_stdout(output):
                    code = ENTRY.main(arguments)
                self.assertEqual(code, 1)
                report = json.loads(output.getvalue())
                self.assertIn(reason, report["error"])
                self.assertEqual(self.inventory(), before)

    def test_ordinary_cli_admission_has_no_platform_boundary(self):
        before = self.inventory()
        output = io.StringIO()
        with redirect_stdout(output):
            code = ENTRY.main(["admit", "--repository-root", str(self.root), "--config", str(self.config),
                               "--expected-plan-id", self.plan_id])
        self.assertEqual(code, 1)
        self.assertIn("ordinary CLI calls", json.loads(output.getvalue())["error"])
        self.assertEqual(self.inventory(), before)

    def test_missing_policy_clearance_is_blocked_before_any_checkpoint(self):
        before = self.inventory()
        with patch.dict(os.environ, self.environment), \
             patch.object(ENTRY, "_signed_github_claims", return_value=self.claims):
            boundary = REAL_BOUNDARY(self.engine(), self.plan_id, self.revision)
            with self.assertRaisesRegex(EvidenceError, "source-policy clearance is unresolved"):
                boundary.authorize(self.engine().admission_bindings())
        self.assertEqual(self.inventory(), before)
        self.assertFalse(self.engine().run_root.exists())

    def test_source_change_at_final_write_gate_blocks_actual_entry_and_writer(self):
        original_state = (self.root / "data/canonical/state.json").read_bytes()
        original_preflight = AutomaticCanonicalUpdate._stage_deterministic_promotion_preflight

        def change_after_preflight(engine, context):
            result = original_preflight(engine, context)
            self.receipt.write_text("Changed after authorization and preflight")
            return result

        with patch.object(AutomaticCanonicalUpdate, "_stage_deterministic_promotion_preflight", change_after_preflight):
            code, report = self.invoke("admit", plan=self.plan_id, revision=self.revision)
        self.assertEqual(code, 1, report)
        self.assertEqual(report["status"], "blocked")
        self.assertEqual((self.root / "data/canonical/state.json").read_bytes(), original_state)
        self.assertEqual(self.receipt.read_text(), "Changed after authorization and preflight")
        self.assertFalse((self.root / "data/audit/promotion.json").exists())
        self.assertFalse(self.engine()._checkpoint("bounded_canonical_promotion").exists())
        self.assertTrue((self.engine().run_root / "blocked-report.json").exists())

    def test_config_shell_metacharacters_escape_absolute_and_symlink_are_rejected(self):
        symlink = self.config.parent / "link.json"
        symlink.symlink_to(self.config)
        for name in ("../config.json", str(self.config), "config/automatic_updates/../fictional.json",
                     "config/automatic_updates/$(touch injected).json", "config/automatic_updates/link.json",
                     'config/automatic_updates/x.json\"; touch injected; #'):
            with self.subTest(name=name):
                before = self.inventory()
                code, report = self.invoke(config=name)
                self.assertEqual(code, 1)
                self.assertEqual(report["status"], "blocked")
                self.assertEqual(self.inventory(), before)
                self.assertFalse((self.root / "injected").exists())

    def test_workflow_job_separation_and_no_automatic_merge_or_approval(self):
        workflow = (ROOT / ENTRY.OWNER_WORKFLOW).read_text()
        planning = workflow.split("  plan:\n", 1)[1].split("  admit:\n", 1)[0]
        self.assertIn("default: plan", workflow)
        self.assertIn("if: inputs.operation == 'plan'", planning)
        for forbidden in (".py admit ", ".py execute ", "getIDToken", "id-token: write", "git push", "gh pr"):
            self.assertNotIn(forbidden, planning)
        for forbidden in ("gh pr merge", "gh pr review", "--auto", "git push", "git reset", "contents: write",
                          "pull-requests: write", '"${{ inputs.', "approved=true"):
            self.assertNotIn(forbidden, workflow)
        self.assertIn("shell: false", workflow)
        self.assertIn("Publication is DISABLED", workflow)

    def test_workflow_spawn_passes_malicious_inputs_only_as_arguments(self):
        workflow = (ROOT / ENTRY.OWNER_WORKFLOW).read_text()
        block = workflow.split("          script: |\n", 1)[1].split("      - name:", 1)[0]
        script = "\n".join(line[12:] for line in block.splitlines())
        malicious = 'config/automatic_updates/$(touch SHOULD_NOT_EXIST).json; echo hacked'
        harness = r'''
        const requireReal = require;
        const fakeFs = {writeFileSync: () => {}};
        const fakeSpawn = (command, args, options) => {
          console.log(JSON.stringify({command, args, shell: options.shell, token: options.env.MTG_LAB_ADMISSION_OIDC}));
          return {status: 1, stdout: '{"status":"blocked"}'};
        };
        const fakeRequire = name => name === 'fs' ? fakeFs : name === 'child_process' ? {spawnSync: fakeSpawn} : requireReal(name);
        const core = {getIDToken: async () => 'SIMULATED_PLATFORM_TOKEN', setSecret: () => {}, info: () => {}, setFailed: () => {}};
        const AsyncFunction = Object.getPrototypeOf(async function(){}).constructor;
        new AsyncFunction('require', 'core', process.env.WORKFLOW_TEST_SCRIPT)(fakeRequire, core).catch(() => process.exit(1));
        '''
        result = subprocess.run(["node", "-e", harness], cwd=self.root, capture_output=True, text=True, timeout=10,
            env={**os.environ, "WORKFLOW_TEST_SCRIPT": script, "UPDATE_CONFIG": malicious,
                 "EXPECTED_PLAN_ID": "$(another-command)", "REVIEWED_REVISION": "; arbitrary"})
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        self.assertEqual(observed["command"], "python")
        self.assertIn("--config=" + malicious, observed["args"])
        self.assertIn("--expected-plan-id=$(another-command)", observed["args"])
        self.assertFalse(observed["shell"])
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())

    def test_option_like_config_is_a_value_not_a_help_or_operator_override(self):
        before = self.inventory()
        output = io.StringIO()
        with redirect_stdout(output):
            code = ENTRY.main(["plan", "--github-owner-entry", "--config=--help",
                               "--repository-root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(output.getvalue())["status"], "blocked")
        self.assertEqual(self.inventory(), before)


class GitHubSignatureVerificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def claims(self):
        now = int(time.time())
        return {"iss": ENTRY.OIDC_ISSUER, "aud": ENTRY.OIDC_AUDIENCE,
            "exp": now + 60, "nbf": now - 5, "iat": now - 5, "jti": "FICTIONAL_TEST_TOKEN",
            **{name: "TEST_DOUBLE" for name in ("sub", "actor", "actor_id", "repository", "repository_id",
               "repository_owner", "repository_owner_id", "ref", "sha", "workflow_ref", "workflow_sha",
               "run_id", "run_attempt", "event_name", "runner_environment")}}

    def test_valid_test_signature_verifies_with_fixed_issuer_audience_and_key_endpoint(self):
        claims = self.claims()
        token = jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "test"})
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "MTG_LAB_ADMISSION_OIDC": token}), \
             patch("jwt.PyJWKClient") as client:
            client.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
            self.assertEqual(ENTRY._signed_github_claims(), claims)
            client.assert_called_once_with(ENTRY.OIDC_JWKS, timeout=10)

    def test_unsigned_forged_expired_wrong_issuer_audience_and_missing_claims_fail_closed(self):
        for change in ({"iss": "https://attacker.invalid"}, {"aud": "unrelated-operation"},
                       {"exp": int(time.time()) - 10}, {"nbf": int(time.time()) + 120}, {"actor_id": None}):
            with self.subTest(change=change):
                claims = {**self.claims(), **change}
                if claims["actor_id"] is None:
                    del claims["actor_id"]
                token = jwt.encode(claims, self.key, algorithm="RS256", headers={"kid": "test"})
                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "MTG_LAB_ADMISSION_OIDC": token}), \
                     patch("jwt.PyJWKClient") as client:
                    client.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
                    with self.assertRaisesRegex(EvidenceError, "OIDC verification failed") as error:
                        ENTRY._signed_github_claims()
                    self.assertNotIn(token, str(error.exception))
        for algorithm, key in (("none", ""), ("HS256", "FICTIONAL_ATTACK_KEY_WITH_32_BYTES_MINIMUM"),
                               ("RS256", rsa.generate_private_key(public_exponent=65537, key_size=2048))):
            with self.subTest(algorithm=algorithm):
                token = jwt.encode(self.claims(), key, algorithm=algorithm)
                with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "MTG_LAB_ADMISSION_OIDC": token}), \
                     patch("jwt.PyJWKClient") as client:
                    client.return_value.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.key.public_key())
                    with self.assertRaisesRegex(EvidenceError, "OIDC verification failed"):
                        ENTRY._signed_github_claims()

    def test_local_forged_environment_is_not_a_production_boundary(self):
        with patch.dict(os.environ, {"GITHUB_ACTIONS": "true", "GITHUB_ACTOR": "IDontFeelNone",
                                    "MTG_LAB_ADMISSION_OIDC": "", "approved": "true"}), \
             patch("jwt.PyJWKClient", side_effect=AssertionError("network authentication attempted")):
            with self.assertRaisesRegex(EvidenceError, "signed platform identity"):
                ENTRY._signed_github_claims()


if __name__ == "__main__":
    unittest.main()
