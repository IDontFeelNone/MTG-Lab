#!/usr/bin/env python3
"""Persist only the verified Phase 117 MB2 operator-authorization artifact."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

BATCH = "mb2-batch-000001-e32022126c07"
PATH = Path("data/reviews/phase-117") / BATCH / "operator-authorization.json"
BRANCH = f"operator-authorization/{BATCH}"


class PersistenceError(RuntimeError):
    pass


class Persistence:
    def __init__(self, args, *, run=subprocess.run):
        self.args, self.run = args, run
        self.report = {"status": "failed", "destination_branch": args.destination_branch,
            "base_branch": args.base_branch, "authorization_path": PATH.as_posix(),
            "authorization_digest": args.authorization_digest, "commit_sha": None,
            "pull_request_number": None, "pull_request_url": None, "failed_stage": None,
            "diagnostic": None, "canonical_write": False, "promotion_performed": False}

    def command(self, stage, *command, check=True):
        result = self.run(command, text=True, capture_output=True)
        if check and result.returncode:
            raise PersistenceError(f"{stage}: {(result.stderr or result.stdout).strip()}")
        return result

    def fail(self, stage, message):
        self.report.update(failed_stage=stage, diagnostic=str(message))
        raise PersistenceError(f"{stage}: {message}")

    def boundary(self, base, head):
        names = self.command("changed_file_boundary", "git", "diff", "--name-only", f"{base}...{head}").stdout.splitlines()
        if names != [PATH.as_posix()]:
            self.fail("changed_file_boundary", f"authorization-only change required, found: {names}")
        if any(name.startswith("data/canonical/") for name in names):
            self.fail("changed_file_boundary", "canonical files changed")

    def execute(self):
        if self.args.destination_branch != BRANCH or self.args.base_branch != "main":
            self.fail("branch_scope", "exact authorization destination branch and main base are required")
        if self.args.dry_run:
            self.report["status"] = "dry_run_verified"
            return self.report
        if not PATH.is_file():
            self.fail("artifact", "verified authorization artifact is absent")
        self.command("git_configuration", "git", "config", "user.name", "github-actions[bot]")
        self.command("git_configuration", "git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        remote = self.command("branch_lookup", "git", "ls-remote", "--exit-code", "--heads", "origin", BRANCH, check=False)
        if remote.returncode not in (0, 2): self.fail("branch_lookup", "cannot query authorization branch")
        if remote.returncode == 2:
            self.command("branch_creation", "git", "switch", "-c", BRANCH)
            self.command("staging", "git", "add", "--", str(PATH))
            staged = self.command("staging", "git", "diff", "--cached", "--name-only").stdout.splitlines()
            if staged != [PATH.as_posix()]: self.fail("staging", f"authorization-only staging required: {staged}")
            self.command("commit", "git", "commit", "-m", f"Record operator authorization for {BATCH}")
            sha = self.command("commit", "git", "rev-parse", "HEAD").stdout.strip()
            self.command("push", "git", "push", "origin", f"HEAD:refs/heads/{BRANCH}")
        else:
            self.command("branch_reuse", "git", "fetch", "--no-tags", "origin", f"refs/heads/{BRANCH}:refs/remotes/origin/{BRANCH}")
            sha = self.command("branch_reuse", "git", "rev-parse", f"refs/remotes/origin/{BRANCH}").stdout.strip()
            remote_text = self.command("branch_reuse", "git", "show", f"{sha}:{PATH.as_posix()}").stdout
            try:
                remote_artifact = json.loads(remote_text)
                actual = remote_artifact.pop("authorization_digest")
            except (json.JSONDecodeError, KeyError): self.fail("branch_reuse", "remote authorization is malformed")
            calculated = hashlib.sha256(json.dumps(remote_artifact, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False).encode()).hexdigest()
            if actual != calculated: self.fail("branch_reuse", "remote authorization digest is invalid")
            if actual != self.args.authorization_digest: self.fail("branch_reuse", "conflicting authorization branch")
        self.report["commit_sha"] = sha
        self.boundary(f"origin/{self.args.base_branch}", sha)
        owner = self.args.repository.split("/", 1)[0]
        query = f"repos/{self.args.repository}/pulls?state=open&head={owner}:{BRANCH}&base=main"
        prs = json.loads(self.command("pr", "gh", "api", query).stdout)
        if len(prs) > 1: self.fail("pr", "multiple matching pull requests")
        if not prs:
            self.command("pr", "gh", "pr", "create", "--repo", self.args.repository, "--base", "main",
                "--head", BRANCH, "--title", "Authorize first reviewed MB2 batch",
                "--body", "Authorization artifact only. No canonical write or promotion.")
            prs = json.loads(self.command("pr", "gh", "api", query).stdout)
        if len(prs) != 1: self.fail("pr", "one durable open pull request was not verified")
        pr = json.loads(self.command("pr_verification", "gh", "api", f"repos/{self.args.repository}/pulls/{prs[0]['number']}").stdout)
        if (pr.get("state") != "open" or pr.get("head", {}).get("sha") != sha or
                pr.get("head", {}).get("ref") != BRANCH or pr.get("base", {}).get("ref") != "main"):
            self.fail("pr_verification", "pull request state, base, or commit mismatch")
        self.report.update(status="persisted", pull_request_number=pr["number"], pull_request_url=pr.get("html_url"))
        if not self.report["pull_request_url"]: self.fail("pr_verification", "pull request URL absent")
        return self.report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--destination-branch", required=True); parser.add_argument("--base-branch", required=True)
    parser.add_argument("--repository", required=True); parser.add_argument("--authorization-digest", required=True)
    parser.add_argument("--dry-run", choices=("true", "false"), required=True); parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(); args.dry_run = args.dry_run == "true"; state = Persistence(args); status = 0
    try: state.execute()
    except (PersistenceError, OSError, json.JSONDecodeError) as error:
        status = 1
        if state.report["diagnostic"] is None: state.report.update(failed_stage="unexpected", diagnostic=str(error))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(state.report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(state.report, sort_keys=True)); return status


if __name__ == "__main__": sys.exit(main())
