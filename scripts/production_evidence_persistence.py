#!/usr/bin/env python3
"""Fail-closed GitHub persistence for a verified production-evidence run."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


class PersistenceError(RuntimeError):
    """A durable Git or GitHub persistence stage failed."""


def tree_digest(root: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix()
        digest.update(relative.encode() + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return len(files), digest.hexdigest()


class Persistence:
    def __init__(self, args, *, run=subprocess.run):
        self.args, self.run = args, run
        self.path = Path("data/production_runs") / args.run_id
        self.report = {
            "schema_version": "1.0.0", "intake_status": "failed",
            "run_id": args.run_id, "evidence_path": self.path.as_posix(),
            "destination_branch": args.destination_branch,
            "evidence_commit_sha": None, "pull_request_number": None,
            "pull_request_url": None, "retained_file_count": 0,
            "retained_tree_digest": None, "canonical_write": False,
            "promotion_performed": False, "failed_stage": None, "diagnostic": None,
        }

    def command(self, stage, *command, check=True):
        completed = self.run(command, text=True, capture_output=True)
        if check and completed.returncode:
            detail = (completed.stderr or completed.stdout).strip()
            raise PersistenceError(f"{stage}: command failed ({completed.returncode}): {detail}")
        return completed

    def fail(self, stage, message):
        self.report.update(failed_stage=stage, diagnostic=str(message))
        raise PersistenceError(f"{stage}: {message}")

    def changed_files(self, base, head):
        output = self.command("changed_file_boundary", "git", "diff", "--name-only", f"{base}...{head}").stdout
        return [line for line in output.splitlines() if line]

    def git_tree_digest(self, ref):
        listing = self.command("existing_evidence_verification", "git", "ls-tree", "-r", "--name-only",
                               ref, "--", str(self.path)).stdout.splitlines()
        digest = hashlib.sha256()
        prefix = self.path.as_posix() + "/"
        for name in sorted(listing):
            if not name.startswith(prefix):
                self.fail("existing_evidence_verification", f"unexpected remote path: {name}")
            content = self.command("existing_evidence_verification", "git", "show", f"{ref}:{name}").stdout.encode()
            digest.update(name[len(prefix):].encode() + b"\0" + hashlib.sha256(content).digest())
        return len(listing), digest.hexdigest()

    def verify_pr(self, number, expected_sha):
        raw = self.command("pr_verification", "gh", "api",
            f"repos/{self.args.repository}/pulls/{number}").stdout
        try:
            pr = json.loads(raw)
        except json.JSONDecodeError as error:
            self.fail("pr_verification", f"invalid GitHub API response: {error}")
        if (pr.get("head", {}).get("ref") != self.args.destination_branch or
                pr.get("base", {}).get("ref") != self.args.base_branch or
                pr.get("head", {}).get("sha") != expected_sha or
                pr.get("state") != "open"):
            self.fail("pr_verification", "PR head, base, commit, or open state does not match")
        files = []
        page = 1
        while True:
            payload = self.command("pr_verification", "gh", "api",
                f"repos/{self.args.repository}/pulls/{number}/files?per_page=100&page={page}").stdout
            try:
                batch = json.loads(payload)
            except json.JSONDecodeError as error:
                self.fail("pr_verification", f"invalid PR-files response: {error}")
            files.extend(item.get("filename", "") for item in batch)
            if len(batch) < 100:
                break
            page += 1
        prefix = self.path.as_posix() + "/"
        if not files or any(not (name.startswith(prefix) or name == "data/production_runs/index.json") for name in files):
            self.fail("changed_file_boundary", f"PR contains missing or out-of-bound files: {files}")
        if not any(name.startswith(prefix) for name in files):
            self.fail("changed_file_boundary", "PR does not contain the retained run path")
        if any(name.startswith("data/canonical/") for name in files):
            self.fail("changed_file_boundary", "canonical files changed")
        return pr

    def execute(self):
        if not self.path.is_dir():
            self.fail("write_boundary", f"verified evidence path is absent: {self.path}")
        count, digest = tree_digest(self.path)
        self.report.update(retained_file_count=count, retained_tree_digest=digest)
        if not count:
            self.fail("write_boundary", "evidence path is empty")
        if self.args.dry_run:
            self.report["intake_status"] = "dry_run_verified"
            return self.report

        expected = f"production-evidence/run-{self.args.run_id}"
        if self.args.destination_branch != expected:
            self.fail("branch_creation", f"destination branch must be {expected}")
        ignored = self.command("evidence_staging", "git", "check-ignore", "-q", str(self.path), check=False)
        if ignored.returncode == 0:
            self.fail("evidence_staging", "evidence path is ignored by Git")
        self.command("git_configuration", "git", "config", "user.name", "github-actions[bot]")
        self.command("git_configuration", "git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        remote = self.command("branch_creation", "git", "ls-remote", "--exit-code", "--heads", "origin",
                              self.args.destination_branch, check=False)
        existing = remote.returncode == 0
        if remote.returncode not in (0, 2):
            self.fail("branch_creation", (remote.stderr or remote.stdout).strip() or "cannot query destination branch")
        if existing:
            self.command("branch_creation", "git", "fetch", "--no-tags", "origin",
                         f"refs/heads/{self.args.destination_branch}:refs/remotes/origin/{self.args.destination_branch}")
            head = f"refs/remotes/origin/{self.args.destination_branch}"
            remote_count, remote_digest = self.git_tree_digest(head)
            if (remote_count, remote_digest) != (count, digest):
                self.fail("existing_evidence_verification", "existing branch evidence is not byte-identical")
            sha = self.command("existing_evidence_verification", "git", "rev-parse", head).stdout.strip()
        else:
            self.command("branch_creation", "git", "switch", "-c", self.args.destination_branch)
            self.command("evidence_staging", "git", "add", "--", str(self.path), "data/production_runs/index.json")
            staged = self.command("evidence_staging", "git", "diff", "--cached", "--name-only").stdout.splitlines()
            prefix = self.path.as_posix() + "/"
            if not staged:
                self.fail("commit_creation", "no bounded evidence was staged")
            if any(not (name.startswith(prefix) or name == "data/production_runs/index.json") for name in staged):
                self.fail("changed_file_boundary", f"staged path outside evidence boundary: {staged}")
            self.command("commit_creation", "git", "commit", "-m", f"Retain production evidence for run {self.args.run_id}",
                         "-m", f"Artifact: {self.args.artifact_name}", "-m", f"Artifact-SHA256: {self.args.archive_sha256}")
            sha = self.command("commit_creation", "git", "rev-parse", "HEAD").stdout.strip()
            self.command("branch_push", "git", "push", "origin", f"HEAD:refs/heads/{self.args.destination_branch}")
        self.report["evidence_commit_sha"] = sha

        existing_prs = json.loads(self.command("pr_creation", "gh", "api",
            f"repos/{self.args.repository}/pulls?state=open&head={self.args.repository.split('/')[0]}:{self.args.destination_branch}&base={self.args.base_branch}").stdout)
        if len(existing_prs) > 1:
            self.fail("pr_creation", "multiple open pull requests exist for destination branch")
        if existing_prs:
            number = existing_prs[0]["number"]
        else:
            created = self.command("pr_creation", "gh", "pr", "create", "--repo", self.args.repository,
                "--base", self.args.base_branch, "--head", self.args.destination_branch,
                "--title", f"Retain production evidence for run {self.args.run_id}",
                "--body", "Verified non-canonical production evidence intake only; no review, promotion, or canonical write.")
            if not created.stdout.strip():
                self.fail("pr_creation", "gh pr create returned no pull request")
            prs = json.loads(self.command("pr_creation", "gh", "api",
                f"repos/{self.args.repository}/pulls?state=open&head={self.args.repository.split('/')[0]}:{self.args.destination_branch}&base={self.args.base_branch}").stdout)
            if len(prs) != 1:
                self.fail("pr_creation", "created pull request could not be uniquely resolved")
            number = prs[0]["number"]
        pr = self.verify_pr(number, sha)
        self.report.update(intake_status="persisted", pull_request_number=number,
                           pull_request_url=pr.get("html_url"), failed_stage=None, diagnostic=None)
        if not self.report["pull_request_url"]:
            self.fail("pr_verification", "verified PR has no URL")
        return self.report


def parser():
    value = argparse.ArgumentParser()
    for name in ("run-id", "artifact-name", "archive-sha256", "destination-branch", "base-branch", "repository"):
        value.add_argument(f"--{name}", required=True)
    value.add_argument("--dry-run", choices=("true", "false"), required=True)
    value.add_argument("--report", type=Path, required=True)
    return value


def main():
    args = parser().parse_args()
    args.dry_run = args.dry_run == "true"
    persistence = Persistence(args)
    status = 0
    try:
        persistence.execute()
    except (PersistenceError, json.JSONDecodeError, OSError) as error:
        status = 1
        if persistence.report["diagnostic"] is None:
            persistence.report.update(failed_stage="unexpected", diagnostic=str(error))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(persistence.report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(persistence.report, sort_keys=True))
    return status


if __name__ == "__main__":
    sys.exit(main())
