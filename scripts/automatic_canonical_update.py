#!/usr/bin/env python3
"""JSON CLI for automatic canonical updates; default to read-only planning."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from production_evidence.automatic_updates import (
    ADMISSION_OPERATION, AdmissionDecision, AutomaticCanonicalUpdate, GitHubPersistence, canonical_json,
)
from production_evidence.repository import EvidenceError


# Trusted reviewed host policy, never dispatch/configuration inputs. This personal
# repository currently permits only its authenticated owner, not all collaborators.
OWNER_REPOSITORY = "IDontFeelNone/MTG-Lab"
# Independently read repository metadata; immutable IDs prevent namespace reuse.
OWNER_REPOSITORY_ID = "1314720822"
OWNER_ACCOUNT_ID = "310046194"
OWNER_REF = "refs/heads/main"
OWNER_WORKFLOW = ".github/workflows/automatic-canonical-update.yml"
OIDC_ISSUER = "https://token.actions.githubusercontent.com"
OIDC_AUDIENCE = "mtg-lab:canonical-admission"
OIDC_JWKS = OIDC_ISSUER + "/.well-known/jwks"
# Operation-specific source permissions require a separate reviewed decision.
# No real plan has that clearance; caller-provided labels cannot add one.
SOURCE_POLICY_CLEARED_PLANS: frozenset[str] = frozenset()


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *arguments],
                            capture_output=True, text=True, timeout=10)
    if result.returncode:
        raise EvidenceError(f"reviewed checkout verification failed (git {arguments[0]}, exit {result.returncode})")
    return result.stdout.strip()


def _workflow_configuration(root: Path, name: str) -> Path:
    """A dispatch can select a reviewed file, never a path outside this boundary."""
    if not re.fullmatch(r"config/automatic_updates/[A-Za-z0-9][A-Za-z0-9_.-]*\.json", name):
        raise EvidenceError("workflow configuration must be a permitted repository-relative file")
    path = root / name
    if (not path.is_file() or any(p.is_symlink() for p in (path, *path.parents))
            or not path.resolve().is_relative_to(root.resolve())):
        raise EvidenceError("workflow configuration is missing or escapes its reviewed directory")
    # Byte comparison (not text normalization) with the reviewed Git blob.
    result = subprocess.run(["git", "-C", str(root), "show", "HEAD:" + name],
                            capture_output=True, timeout=10)
    if result.returncode or result.stdout != path.read_bytes():
        raise EvidenceError("workflow configuration differs from reviewed code")
    return path


def _signed_github_claims() -> dict:
    """Only GitHub's signature authenticates the context; environment is transport."""
    token = os.environ.get("MTG_LAB_ADMISSION_OIDC", "")
    if os.environ.get("GITHUB_ACTIONS") != "true" or not token:
        raise EvidenceError("GitHub admission requires a signed platform identity token")
    try:
        import jwt
        key = jwt.PyJWKClient(OIDC_JWKS, timeout=10).get_signing_key_from_jwt(token).key
        return jwt.decode(token, key, algorithms=["RS256"], issuer=OIDC_ISSUER,
                          audience=OIDC_AUDIENCE, options={"strict_aud": True, "require": [
                              "iss", "aud", "sub", "exp", "iat", "nbf", "jti",
                              "actor", "actor_id", "repository", "repository_id",
                              "repository_owner", "repository_owner_id", "ref", "sha",
                              "workflow_ref", "workflow_sha", "run_id", "run_attempt",
                              "event_name", "runner_environment"]})
    except Exception as error:
        # Neither token, key material, endpoint headers nor raw transport errors
        # belong in reports. No caller-selected key/issuer or unsigned fallback.
        raise EvidenceError(f"GitHub OIDC verification failed ({type(error).__name__})") from None


def _checked_github_context(root: Path, revision: str) -> dict:
    claims = _signed_github_claims()
    owner, repository = OWNER_REPOSITORY.split("/")
    if (claims.get("repository") != OWNER_REPOSITORY
            or str(claims.get("repository_id")) != OWNER_REPOSITORY_ID
            or claims.get("repository_owner") != owner
            or str(claims.get("repository_owner_id")) != OWNER_ACCOUNT_ID
            or claims.get("ref") != OWNER_REF
            or claims.get("workflow_ref") != f"{OWNER_REPOSITORY}/{OWNER_WORKFLOW}@{OWNER_REF}"
            or claims.get("event_name") != "workflow_dispatch"
            or claims.get("runner_environment") != "github-hosted"):
        raise EvidenceError("GitHub repository/ref/workflow context is outside owner admission policy")
    if (claims.get("actor") != owner or claims.get("actor_id") != claims.get("repository_owner_id")
            or not all(re.fullmatch(r"[1-9][0-9]*", str(claims.get(k, "")))
                       for k in ("actor_id", "repository_owner_id", "repository_id", "run_id"))):
        raise EvidenceError("GitHub actor is not the authorized repository owner")
    if str(claims.get("run_attempt")) != "1":
        raise EvidenceError("GitHub admission reruns are unsupported; a new reviewed dispatch is required")
    subjects = {f"repo:{OWNER_REPOSITORY}:ref:{OWNER_REF}",
                f"repo:{owner}@{claims['repository_owner_id']}/{repository}@{claims['repository_id']}:ref:{OWNER_REF}"}
    if claims.get("sub") not in subjects:
        raise EvidenceError("GitHub subject is outside owner admission policy")
    if (not re.fullmatch(r"[0-9a-f]{40}", revision or "")
            or claims.get("sha") != revision or claims.get("workflow_sha") != revision
            or _git(root, "rev-parse", "HEAD") != revision):
        raise EvidenceError("GitHub execution does not match the explicitly reviewed code revision")
    if Path(os.environ.get("GITHUB_WORKSPACE", "")).resolve() != root.resolve():
        raise EvidenceError("GitHub checkout root does not match the trusted runner workspace")
    _git(root, "diff", "--exit-code", "HEAD", "--")
    # The reviewed workflow passes these inputs as argv, without shell evaluation.
    # GitHub supplies the event file; its contents alone do not authenticate it.
    event = json.loads(Path(os.environ.get("GITHUB_EVENT_PATH", "")).read_bytes())
    if (event.get("repository", {}).get("full_name") != OWNER_REPOSITORY
            or str(event.get("repository", {}).get("id")) != str(claims["repository_id"])
            or str(event.get("sender", {}).get("id")) != str(claims["actor_id"])
            or os.environ.get("GITHUB_RUN_ID") != str(claims["run_id"])
            or os.environ.get("GITHUB_RUN_ATTEMPT") != "1"
            or os.environ.get("GITHUB_TRIGGERING_ACTOR") != claims["actor"]):
        raise EvidenceError("GitHub runner/event context differs from signed execution identity")
    return {"repository": OWNER_REPOSITORY, "repository_id": str(claims["repository_id"]),
            "actor": claims["actor"], "actor_id": str(claims["actor_id"]),
            "workflow_ref": claims["workflow_ref"], "code_revision": revision,
            "run_id": str(claims["run_id"]), "run_attempt": "1", "oidc_token_id": claims["jti"],
            "operation": ADMISSION_OPERATION, "dispatch_inputs": event.get("inputs", {})}


class GitHubOwnerReviewBoundary:
    """Authenticated owner dispatch, pinned plan, and live checks before every write.

    Trusted: GitHub issuer/host, reviewed main code/actions/dependencies and runner
    isolation. Not trusted: request JSON, arbitrary actor strings or saved receipts.
    """
    def __init__(self, engine: AutomaticCanonicalUpdate, plan_id: str, revision: str):
        self.engine, self.plan_id, self.revision = engine, plan_id, revision
        self.context = _checked_github_context(engine.root, revision)
        self.authenticated_reviewer = self.context["actor"]
        self.decided_at = datetime.now(timezone.utc).isoformat()
        self._check_dispatch()

    def _check_dispatch(self) -> None:
        inputs = self.context["dispatch_inputs"]
        name = self.engine._configuration_path.relative_to(self.engine.root).as_posix()
        if (inputs.get("operation") != "admit" or inputs.get("expected_plan_id") != self.plan_id
                or inputs.get("reviewed_revision") != self.revision or inputs.get("config") != name):
            raise EvidenceError("explicit owner admission action and reviewed plan inputs are required")

    def authorize(self, bindings) -> AdmissionDecision:
        if _checked_github_context(self.engine.root, self.revision) != self.context:
            raise EvidenceError("GitHub admission execution identity changed")
        self._check_dispatch()
        _workflow_configuration(self.engine.root, self.context["dispatch_inputs"]["config"])
        plan = self.engine.plan(expected_plan_id=self.plan_id)
        if (not plan["integrity_verified"] or not plan["pre_state_matches_expected"]
                or plan["decision_inputs"]["scope"] != "new_admission_preview"
                or plan["decision_inputs"]["bindings"] != bindings):
            raise EvidenceError("owner authorization requires the exact integrity-verified new admission plan")
        if self.plan_id not in SOURCE_POLICY_CLEARED_PLANS:
            raise EvidenceError("operation-specific source-policy clearance is unresolved for this plan")
        return self._decision(bindings)

    def _decision(self, bindings) -> AdmissionDecision:
        reference = "github-actions:" + canonical_json({**self.context, "plan_id": self.plan_id}).decode()
        return AdmissionDecision("approved", self.authenticated_reviewer, self.decided_at,
                                 ADMISSION_OPERATION, deepcopy(bindings), reference)


def workflow_entry(engine: AutomaticCanonicalUpdate, command: str, *,
                   expected_plan_id: str | None = None, reviewed_revision: str | None = None,
                   publish: bool = False) -> dict:
    """Use the existing planner/writer and exact-delta publication boundary."""
    name = engine._configuration_path.relative_to(engine.root).as_posix()
    _workflow_configuration(engine.root, name)
    if command == "plan":
        if publish: raise EvidenceError("planning cannot execute or publish an admission")
        _git(engine.root, "diff", "--exit-code", "HEAD", "--")
        result = engine.plan(expected_plan_id=expected_plan_id)
        return {**result, "reviewed_code_revision": _git(engine.root, "rev-parse", "HEAD"),
                "publication": "disabled"}
    if command != "admit" or not expected_plan_id or not reviewed_revision:
        raise EvidenceError("admission requires an explicit operation, expected plan and reviewed revision")
    # Recompute only to validate the previously supplied identity, never to select
    # or approve a fresh identity on the operator's behalf.
    plan = engine.plan(expected_plan_id=expected_plan_id)
    boundary = GitHubOwnerReviewBoundary(engine, expected_plan_id, reviewed_revision)
    decision = boundary.authorize(engine.admission_bindings())  # fail closed before checkpoints
    engine.review_boundary = boundary
    result = engine.execute(stop_after="query_and_analytics_smoke_tests")
    if publish:
        return GitHubPersistence().publish_admission(engine, plan, reviewed_revision, decision,
                                                    repository=boundary.context["repository"])
    return {"status": "validated-local-only", "plan_id": expected_plan_id,
            "execution": result, "publication": "disabled", "automatic_merge": False}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", nargs="?", default="plan",
                        choices=("plan", "admit", "verify", "execute", "status", "replay", "rollback-plan"),
                        help="operation to perform (default: read-only plan)")
    parser.add_argument("--config", required=True)
    parser.add_argument("--repository-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--expected-plan-id", help="recheck a previous read-only plan identity")
    parser.add_argument("--reviewed-revision", help="exact reviewed GitHub workflow/code SHA for admission")
    parser.add_argument("--github-owner-entry", action="store_true",
                        help="use the reviewed workflow entry; admission requires verified GitHub OIDC")
    parser.add_argument("--publish-admission-pr", action="store_true",
                        help="after authenticated admission and required validation, publish its exact delta as a draft PR")
    args = parser.parse_args(argv)
    try:
        root = Path(args.repository_root).resolve()
        config = _workflow_configuration(root, args.config) if args.github_owner_entry else args.config
        pending = json.loads(Path(config).read_bytes())
        if pending.get("launch_state") == "pending":
            raise EvidenceError("pending first-use configuration; unavailable execution inputs: " +
                                ", ".join(pending.get("missing_execution_inputs", [])))
        engine = AutomaticCanonicalUpdate(root, config)
        if args.github_owner_entry:
            result = workflow_entry(engine, args.command, expected_plan_id=args.expected_plan_id,
                                    reviewed_revision=args.reviewed_revision, publish=args.publish_admission_pr)
            print(json.dumps(result, indent=2, sort_keys=True))
            return 1 if result.get("status") == "blocked" else 0
        if args.command == "admit" or args.reviewed_revision is not None or args.publish_admission_pr:
            raise EvidenceError("ordinary CLI calls cannot install owner admission authority")
        method = getattr(engine, args.command.replace("-", "_"))
        if args.expected_plan_id is not None and args.command != "plan":
            raise ValueError("--expected-plan-id is only valid for read-only planning")
        result = method(expected_plan_id=args.expected_plan_id) if args.command == "plan" else method()
    except BaseException as error:
        print(json.dumps({"status": "blocked", "error": f"{type(error).__name__}: {error}"}, sort_keys=True))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True)); return 0


if __name__ == "__main__": sys.exit(main())
