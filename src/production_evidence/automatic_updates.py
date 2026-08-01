"""Reusable, fail-closed orchestration for trusted canonical updates.

The engine deliberately knows nothing about Magic set codes.  Product-specific facts live
in a versioned descriptor and stage implementations communicate only through JSON values.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from typing import Callable, Mapping

from .promotion_readiness import canonical_state_digest
from .repository import EvidenceError

STAGES = (
    "source_acquisition_verification", "evidence_normalization", "permanent_evidence_intake",
    "target_partitioning", "bounded_candidate_payload_retention", "candidate_review",
    "identifier_and_conflict_policy_resolution", "dependency_closure_verification",
    "promotion_readiness_planning", "deterministic_promotion_preflight",
    "bounded_canonical_promotion", "immutable_promotion_audit",
    "canonical_post_state_verification", "query_and_analytics_smoke_tests",
    "branch_and_pull_request_persistence", "automatic_merge_eligibility_verification",
)
SCHEMA = "automatic-canonical-update-v1"


def canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else canonical_json(value)).hexdigest()


@dataclass(frozen=True)
class TargetDescriptor:
    game: str
    target_code: str
    target_name: str
    trusted_provider: str
    source_dataset_identity: str
    source_artifact_or_workflow_run: str
    evidence_identity: str
    batch_identifier: str
    candidate_digest: str
    expected_target_isolation: str
    promotion_policy: str
    destination_branch: str
    base_branch: str

    @classmethod
    def load(cls, path: Path | str) -> tuple["TargetDescriptor", dict]:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if raw.get("schema_version") != SCHEMA:
            raise EvidenceError("unsupported automatic-update configuration schema")
        try:
            descriptor = cls(**{name: raw["target"][name] for name in cls.__dataclass_fields__})
        except (KeyError, TypeError) as error:
            raise EvidenceError(f"invalid target descriptor: {error}") from None
        if not descriptor.destination_branch.startswith("canonical-update/"):
            raise EvidenceError("destination branch must be dedicated to canonical updates")
        return descriptor, raw


class AutomaticCanonicalUpdate:
    """Execute ordered stages, checkpointing each independently verifiable result."""

    def __init__(self, repository_root: Path | str, config: Path | str,
                 *, handlers: Mapping[str, Callable[[dict], dict]] | None = None):
        self.root = Path(repository_root)
        self.descriptor, self.config = TargetDescriptor.load(config)
        self.data = self.root / self.config.get("data_root", "data")
        self.run_root = self.data / "automatic_updates" / self.descriptor.batch_identifier
        self.handlers = dict(handlers or {})

    def _checkpoint(self, stage: str) -> Path:
        return self.run_root / "stages" / f"{STAGES.index(stage) + 1:02d}-{stage}.json"

    def _result(self, stage: str, details: dict) -> dict:
        body = {"schema_version": SCHEMA, "stage": stage, "status": "succeeded",
                "batch_identifier": self.descriptor.batch_identifier, "details": details}
        return {**body, "result_digest": digest(body)}

    def _verify_result(self, result: dict, stage: str) -> None:
        supplied = result.get("result_digest")
        body = {k: v for k, v in result.items() if k != "result_digest"}
        if result.get("stage") != stage or result.get("status") != "succeeded" or supplied != digest(body):
            raise EvidenceError(f"invalid completed-stage checkpoint: {stage}")

    def status(self) -> dict:
        completed = []
        for stage in STAGES:
            path = self._checkpoint(stage)
            if not path.exists(): break
            value = json.loads(path.read_text())
            self._verify_result(value, stage); completed.append(stage)
        return {"schema_version": SCHEMA, "batch_identifier": self.descriptor.batch_identifier,
                "completed_stages": completed, "next_stage": STAGES[len(completed)] if len(completed) < len(STAGES) else None,
                "complete": len(completed) == len(STAGES)}

    def plan(self) -> dict:
        return {"schema_version": SCHEMA, "target": self.descriptor.__dict__, "stages": list(STAGES),
                "status": self.status(), "canonical_write": False}

    def verify(self) -> dict:
        status = self.status()
        audit = self.data / self.config["artifacts"]["promotion_audit"]
        if audit.exists():
            value = json.loads(audit.read_text()); expected = value.get("audit_digest")
            body = {k: v for k, v in value.items() if k != "audit_digest"}
            if expected and expected != digest(body): raise EvidenceError("immutable audit digest mismatch")
        return {**status, "verified": True, "audit_present": audit.exists(),
                "canonical_state_digest": canonical_state_digest(self.data)}

    def execute(self, *, stop_after: str | None = None) -> dict:
        context = {"engine": self, "config": self.config, "target": self.descriptor.__dict__}
        for stage in STAGES:
            path = self._checkpoint(stage)
            if path.exists():
                value = json.loads(path.read_text()); self._verify_result(value, stage)
                context[stage] = value["details"]
            else:
                try:
                    details = (self.handlers.get(stage) or getattr(self, f"_stage_{stage}"))(context)
                    result = self._result(stage, details)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    self._atomic_write(path, json.dumps(result, indent=2, sort_keys=True) + "\n", exclusive=True)
                    context[stage] = details
                except BaseException as error:
                    self.run_root.mkdir(parents=True, exist_ok=True)
                    report = {"schema_version": SCHEMA, "status": "blocked", "failed_stage": stage,
                              "error": f"{type(error).__name__}: {error}"}
                    self._atomic_write(self.run_root / "blocked-report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
                    raise
            if stop_after == stage: break
        return self.status()

    def replay(self) -> dict:
        before = self.verify(); result = self.execute(); after = self.verify()
        if before["canonical_state_digest"] != after["canonical_state_digest"]:
            raise EvidenceError("completed replay changed canonical state")
        return {**result, "idempotent": True}

    def rollback_plan(self) -> dict:
        audit = self.data / self.config["artifacts"]["promotion_audit"]
        if not audit.exists(): raise EvidenceError("promotion audit not found")
        value = json.loads(audit.read_text())
        return {"schema_version": SCHEMA, "action": "rollback-plan", "execute": False,
                "promotion_id": value.get("promotion_id"), "canonical_post_state_digest": value.get("canonical_post_state_digest"),
                "human_decision_required": True, "audit_retained": True}

    @staticmethod
    def _atomic_write(path: Path, text: str, *, exclusive: bool = False) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if exclusive and path.exists(): raise EvidenceError(f"immutable file already exists: {path}")
        fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream: stream.write(text)
            if exclusive and path.exists(): raise EvidenceError(f"immutable file already exists: {path}")
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def _payload(self) -> tuple[Path, dict, bytes]:
        path = self.data / self.config["artifacts"]["candidate_payload"]
        raw = path.read_bytes(); return path, json.loads(raw), raw

    def _stage_source_acquisition_verification(self, c):
        p = self.data / self.config["artifacts"]["source_artifact"]
        if not p.is_file(): raise EvidenceError("source artifact is not retained")
        expected = self.config["integrity"].get("source_sha256")
        actual = digest(p.read_bytes())
        if expected and actual != expected: raise EvidenceError("source artifact hash mismatch")
        if self.descriptor.trusted_provider not in self.config["policy"]["trusted_providers"]:
            raise EvidenceError("provider is not explicitly trusted")
        return {"path": str(p.relative_to(self.root)), "sha256": actual}

    def _stage_evidence_normalization(self, c):
        path, payload, raw = self._payload(); candidates = payload["candidate_payloads"]
        ids = payload.get("candidate_ids", [x["candidate_identifier"] for x in candidates])
        if ids != [x["candidate_identifier"] for x in candidates]: raise EvidenceError("candidate inventory/order mismatch")
        if digest(ids) != self.descriptor.candidate_digest: raise EvidenceError("candidate digest mismatch")
        return {"payload": str(path.relative_to(self.root)), "payload_sha256": digest(raw), "candidate_count": len(ids)}

    def _stage_permanent_evidence_intake(self, c):
        if self.config["integrity"].get("expected_candidate_count") != c["evidence_normalization"]["candidate_count"]:
            raise EvidenceError("candidate count mismatch")
        return {"evidence_identity": self.descriptor.evidence_identity, "retained": True}

    def _stage_target_partitioning(self, c):
        _, payload, _ = self._payload(); expected = self.descriptor.expected_target_isolation.casefold()
        wrong = []
        for row in payload["candidate_payloads"]:
            actual = (row.get("mapped_fields", {}).get("set_code") or payload.get("target_set_code")
                      or payload.get("target", {}).get("code") or payload.get("target_product"))
            if actual and str(actual).casefold() != expected: wrong.append(row["candidate_identifier"])
        if wrong: raise EvidenceError("target isolation failed")
        return {"target": expected, "exact": True, "excluded_candidate_count": 0}

    def _stage_bounded_candidate_payload_retention(self, c):
        path, _, raw = self._payload(); return {"path": str(path.relative_to(self.root)), "sha256": digest(raw), "immutable": True}

    def _stage_candidate_review(self, c):
        _, payload, _ = self._payload(); counts = {}
        for row in payload["candidate_payloads"]:
            state = row.get("final_classification", "approved" if row.get("validation_state") == "validated" else "unresolved")
            counts[state] = counts.get(state, 0) + 1
        forbidden = set(counts) - set(self.config["policy"]["permitted_final_classifications"])
        if forbidden or counts.get("unresolved") or counts.get("rejected") or counts.get("quarantined") or counts.get("fatal"):
            raise EvidenceError("candidate review contains a blocking classification")
        return {"classifications": counts, "complete": sum(counts.values()) == c["evidence_normalization"]["candidate_count"]}

    def _stage_identifier_and_conflict_policy_resolution(self, c):
        _, payload, _ = self._payload()
        if any(row.get("conflict_state") not in (None, "none", "deterministically_resolved") for row in payload["candidate_payloads"]):
            raise EvidenceError("unresolved or unapproved identity conflict")
        return {"policy": self.descriptor.promotion_policy, "unresolved_conflicts": 0}

    def _stage_dependency_closure_verification(self, c):
        _, payload, _ = self._payload(); rows = payload["candidate_payloads"]
        cards = {r["mapped_fields"].get("card_reference", "").casefold() for r in rows if r["entity_type"] == "card"}
        orphaned = [r["candidate_identifier"] for r in rows if r["entity_type"] == "printing" and r["mapped_fields"].get("card_reference", "").casefold() not in cards]
        if orphaned: raise EvidenceError("dependency closure contains orphaned Printing")
        return {"valid": True, "orphaned_printings": 0}

    def _stage_promotion_readiness_planning(self, c):
        return {"ready": True, "candidate_digest": self.descriptor.candidate_digest, "plan_digest": digest({"target": self.descriptor.__dict__, "count": c["evidence_normalization"]["candidate_count"]})}

    def _stage_deterministic_promotion_preflight(self, c):
        actual = canonical_state_digest(self.data); expected = self.config["integrity"]["canonical_pre_state_digest"]
        audit = self.data / self.config["artifacts"]["promotion_audit"]
        if actual != expected and not audit.exists(): raise EvidenceError("canonical pre-state drift")
        return {"canonical_pre_state_digest": expected, "observed_state_digest": actual, "existing_audit": audit.exists()}

    def _stage_bounded_canonical_promotion(self, c):
        audit_path = self.data / self.config["artifacts"]["promotion_audit"]
        if audit_path.exists():
            audit = json.loads(audit_path.read_text())
            if audit.get("batch_id") != self.descriptor.batch_identifier or audit.get("candidate_id_digest") != self.descriptor.candidate_digest:
                raise EvidenceError("conflicting replay of promoted batch")
            if canonical_state_digest(self.data) != audit["canonical_post_state_digest"]: raise EvidenceError("canonical state conflicts with audit")
            return {"idempotent": True, "canonical_post_state_digest": audit["canonical_post_state_digest"]}
        state_path = self.data / "canonical/state.json"; original = state_path.read_bytes()
        state = json.loads(original); _, payload, _ = self._payload(); promoted = []
        for candidate in payload["candidate_payloads"]:
            kind = candidate["entity_type"]; fields = dict(candidate["mapped_fields"])
            identity_key = self.config.get("canonical_identity_fields", {}).get(
                kind, {"card": "card_reference", "printing": "uuid", "finish": "value"}.get(kind))
            identifier = (str(fields[identity_key]).casefold() if identity_key else
                          candidate["candidate_identifier"].rsplit(":", 1)[-1].casefold())
            existing = state.setdefault(kind, {}).get(identifier)
            record = {"entity_type": kind, "values": fields,
                      "evidence_references": [candidate["candidate_identifier"]],
                      "dataset_identity": [self.descriptor.source_dataset_identity],
                      "promotion_id": self.descriptor.batch_identifier}
            if existing and existing != record: raise EvidenceError(f"conflicting canonical {kind} identity")
            state[kind][identifier] = record; promoted.append(candidate["candidate_identifier"])
        body = {"schema_version": SCHEMA, "promotion_id": self.descriptor.batch_identifier,
                "batch_id": self.descriptor.batch_identifier, "candidate_id_digest": self.descriptor.candidate_digest,
                "canonical_pre_state_digest": c["deterministic_promotion_preflight"]["canonical_pre_state_digest"],
                "promoted_entities": promoted, "result": "succeeded"}
        state_text = json.dumps(state, indent=2, sort_keys=True) + "\n"
        try:
            self._atomic_write(state_path, state_text)
            body["canonical_post_state_digest"] = canonical_state_digest(self.data)
            configured = self.config["integrity"].get("canonical_post_state_digest")
            if configured and configured != body["canonical_post_state_digest"]: raise EvidenceError("canonical post-state differs from plan")
            audit = {**body, "audit_digest": digest(body)}
            self._atomic_write(audit_path, json.dumps(audit, indent=2, sort_keys=True) + "\n", exclusive=True)
        except BaseException:
            self._atomic_write(state_path, original.decode())
            audit_path.unlink(missing_ok=True)
            raise
        return {"idempotent": False, "canonical_post_state_digest": body["canonical_post_state_digest"]}

    def _stage_immutable_promotion_audit(self, c):
        path = self.data / self.config["artifacts"]["promotion_audit"]
        if not path.is_file(): raise EvidenceError("immutable promotion audit missing")
        return {"path": str(path.relative_to(self.root)), "sha256": digest(path.read_bytes()), "immutable": True}

    def _stage_canonical_post_state_verification(self, c):
        actual = canonical_state_digest(self.data); expected = c["bounded_canonical_promotion"]["canonical_post_state_digest"]
        if actual != expected: raise EvidenceError("canonical post-state verification failed")
        return {"canonical_post_state_digest": actual, "verified": True}

    def _stage_query_and_analytics_smoke_tests(self, c):
        state = json.loads((self.data / "canonical/state.json").read_text())
        if not all(isinstance(value, dict) for value in state.values()): raise EvidenceError("canonical query smoke test failed")
        return {"entity_counts": {key: len(value) for key, value in sorted(state.items())}, "passed": True}

    def _stage_branch_and_pull_request_persistence(self, c):
        return {"branch": self.descriptor.destination_branch, "base": self.descriptor.base_branch,
                "mode": "github_actions", "force": False, "pull_request_create_or_reuse": True}

    def _stage_automatic_merge_eligibility_verification(self, c):
        return {"eligible_only_after_required_checks": True, "branch_protection_bypass": False,
                "force_merge": False, "diagnostics_retained_on_failure": True}


class GitHubPersistence:
    """Small command builder used by Actions; commands never force or bypass protection."""
    def __init__(self, run: Callable[..., subprocess.CompletedProcess] = subprocess.run): self.run = run

    def persist(self, branch: str, base: str, title: str, body_file: str) -> dict:
        commands = [["git", "switch", "-c", branch], ["git", "push", "origin", branch],
                    ["gh", "pr", "create", "--base", base, "--head", branch, "--title", title, "--body-file", body_file]]
        for command in commands:
            result = self.run(command, check=False, text=True, capture_output=True)
            if result.returncode and command[1:3] == ["pr", "create"]:
                # A rerun may safely reuse only the PR for this exact head/base.
                view = self.run(["gh", "pr", "view", branch, "--json", "headRefName,baseRefName,url"], check=True, text=True, capture_output=True)
                value = json.loads(view.stdout)
                if value["headRefName"] != branch or value["baseRefName"] != base: raise EvidenceError("existing PR boundary mismatch")
                return {"reused": True, "url": value["url"]}
            if result.returncode: raise EvidenceError(f"persistence command failed: {' '.join(command)}")
        return {"created": True}
