"""Reusable, fail-closed orchestration for trusted canonical updates.

The engine deliberately knows nothing about Magic set codes.  Product-specific facts live
in a versioned descriptor and stage implementations communicate only through JSON values.
"""
from __future__ import annotations

from dataclasses import dataclass
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable, Mapping, Protocol

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


ADMISSION_OPERATION = "canonical-admission"


@dataclass(frozen=True)
class AdmissionDecision:
    """A decision returned by the authenticated host review boundary, not input JSON.

    The host owns authentication and operation authorization.  A digest, reviewer
    string, or this value alone cannot authenticate anyone.  The standalone CLI has
    no such host integration and cannot authorize a new admission.
    """
    decision: str
    reviewer: str
    decided_at: str
    operation: str
    bindings: Mapping
    review_reference: str
    scope: str = "production"

    def as_dict(self) -> dict:
        return {name: deepcopy(getattr(self, name)) for name in self.__dataclass_fields__}


class AdmissionReviewBoundary(Protocol):
    """Capability injected by trusted host code after authentication/access control.

    Untrusted callers must never choose this object or install it through a config,
    actor field, or request body.  Code/OS operators able to replace the host are
    necessarily inside the trusted computing boundary.  No authentication service
    is implemented here.
    """
    authenticated_reviewer: str

    def authorize(self, bindings: Mapping) -> AdmissionDecision: ...


class IsolatedAdmissionTestBoundary:
    """Nonserialized simulated authority scoped to one live TemporaryDirectory.

    A retained decision from this boundary cannot be loaded as real authorization.
    The temporary-directory capability, exact root, and lifetime are checked on
    every use.  It cannot target the implementation checkout or another directory.
    """
    def __init__(self, temporary_directory: tempfile.TemporaryDirectory, *,
                 reviewer: str = "SIMULATED_TEST_REVIEWER",
                 decided_at: str = "2026-10-13T00:00:00+00:00"):
        if not isinstance(temporary_directory, tempfile.TemporaryDirectory):
            raise EvidenceError("isolated authorization requires a live TemporaryDirectory capability")
        self._temporary = temporary_directory
        self.root = Path(temporary_directory.name).resolve()
        self.authenticated_reviewer = reviewer
        self.decided_at = decided_at
        self._pinned_decision: AdmissionDecision | None = None
        self._verify_root(self.root)

    def _verify_root(self, root: Path) -> None:
        lifetime = self._temporary._finalizer.peek()
        if (not lifetime or Path(lifetime[2][0]).resolve() != self.root or root.resolve() != self.root
                or not self.root.is_dir()
                or Path(__file__).resolve().is_relative_to(self.root)):
            raise EvidenceError("simulated authorization is limited to its live disposable root")

    def authorize(self, bindings: Mapping) -> AdmissionDecision:
        self._verify_root(Path(bindings["repository_root"]))
        if self._pinned_decision is None:
            self._pinned_decision = AdmissionDecision("approved", self.authenticated_reviewer, self.decided_at,
                ADMISSION_OPERATION, deepcopy(bindings), "SIMULATED_TEST_AUTHORIZATION_ONLY", "isolated-test")
        return self._pinned_decision


def _retained_path(data_root: Path, relative: str) -> Path:
    path = Path(relative)
    resolved = (data_root / path).resolve()
    if path.is_absolute() or ".." in path.parts or not resolved.is_relative_to(data_root.resolve()):
        raise EvidenceError("retained evidence path escapes the data root")
    if not resolved.is_file(): raise EvidenceError(f"retained evidence is missing: {relative}")
    return resolved


def validate_admission_audit(data_root: Path | str, audit: Mapping) -> dict:
    """Check a retained admission's content bindings; this grants no authority.

    Simulated receipts are usable only as historical test evidence, never as a
    production execution capability.  Authentication is performed at the live
    host boundary on every new/resumed write, not inferred from these bytes.
    """
    root = Path(data_root)
    body = {key: item for key, item in audit.items() if key != "audit_digest"}
    if audit.get("audit_digest") != digest(body): raise EvidenceError("immutable audit digest mismatch")
    bindings = audit.get("input_bindings", {})
    decision = audit.get("admission_decision", {})
    if (audit.get("result") != "succeeded" or decision.get("decision") != "approved"
            or decision.get("operation") != ADMISSION_OPERATION
            or decision.get("bindings") != bindings
            or audit.get("admission_decision_digest") != digest(decision)
            or decision.get("scope") not in {"production", "isolated-test"}
            or decision.get("scope") != audit.get("authorization_scope")
            or not decision.get("review_reference") or not decision.get("reviewer")):
        raise EvidenceError("admission audit decision binding mismatch")
    try:
        timestamp = datetime.fromisoformat(decision["decided_at"].replace("Z", "+00:00"))
        if timestamp.utcoffset() is None: raise ValueError
    except (KeyError, TypeError, ValueError): raise EvidenceError("admission decision time is invalid") from None
    for item in bindings.get("evidence_files", []):
        raw = _retained_path(root, item["path"]).read_bytes()
        if len(raw) != item["byte_length"] or digest(raw) != item["sha256"]:
            raise EvidenceError("admission retained evidence integrity mismatch")
    raw = _retained_path(root, bindings["candidate_payload_path"]).read_bytes()
    payload = json.loads(raw)
    if (digest(raw) != bindings.get("candidate_payload_sha256")
            or payload.get("candidate_ids") != bindings.get("candidate_ids")
            or digest(payload["candidate_payloads"]) != bindings.get("candidate_rows_digest")
            or digest(bindings.get("candidate_ids")) != audit.get("candidate_id_digest")):
        raise EvidenceError("admission retained payload integrity mismatch")
    state = json.loads((root / "canonical/state.json").read_bytes())
    records = audit.get("admitted_records", [])
    if not records or len(records) != len(bindings["candidate_ids"]):
        raise EvidenceError("admission record membership is incomplete")
    if [r["candidate_identifier"] for r in records] != bindings["candidate_ids"]:
        raise EvidenceError("admission record order mismatch")
    for item in records:
        record = state.get(item["entity_type"], {}).get(item["canonical_identity"])
        if record is None or digest(record) != item["record_sha256"]:
            raise EvidenceError("admitted canonical record integrity mismatch")
        if audit.get("canonical_record_digests", {}).get(item["entity_type"], {}).get(
                item["canonical_identity"]) != item["record_sha256"]:
            raise EvidenceError("admission record digest inventory mismatch")
    expected_inventory = {}
    for item in records:
        group = expected_inventory.setdefault(item["entity_type"], {})
        if item["canonical_identity"] in group:
            raise EvidenceError("admission contains a duplicate canonical identity")
        group[item["canonical_identity"]] = item["record_sha256"]
    if audit.get("canonical_record_digests") != expected_inventory:
        raise EvidenceError("admission digest inventory contains an unadmitted record")
    if (audit.get("canonical_pre_state_digest") != bindings.get("canonical_pre_state_digest")
            or audit.get("batch_id") != bindings.get("target", {}).get("batch_identifier")
            or audit.get("promotion_id") != audit.get("batch_id")
            or audit.get("promoted_entities") != bindings["candidate_ids"]):
        raise EvidenceError("admission audit scope mismatch")
    return {"valid": True, "admitted_record_count": len(records),
            "authorization_scope": decision["scope"]}


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
                 *, handlers: Mapping[str, Callable[[dict], dict]] | None = None,
                 review_boundary: AdmissionReviewBoundary | None = None):
        self.root = Path(repository_root)
        self._repository_scope = self.root.resolve()
        self.descriptor, self.config = TargetDescriptor.load(config)
        data_relative = Path(self.config.get("data_root", "data"))
        self.data = self.root / data_relative
        if (data_relative.is_absolute() or ".." in data_relative.parts
                or not self.data.resolve().is_relative_to(self.root.resolve())):
            raise EvidenceError("canonical data root escapes the repository root")
        self.run_root = self.data / "automatic_updates" / self.descriptor.batch_identifier
        if (Path(self.descriptor.batch_identifier).name != self.descriptor.batch_identifier
                or ".." in Path(self.descriptor.batch_identifier).parts
                or not self.run_root.resolve().is_relative_to(self.data.resolve())):
            raise EvidenceError("batch identifier escapes its run root")
        audit_relative = Path(self.config["artifacts"]["promotion_audit"])
        if (audit_relative.is_absolute() or ".." in audit_relative.parts
                or not (self.data / audit_relative).resolve().is_relative_to(self.data.resolve())):
            raise EvidenceError("promotion audit path escapes the data root")
        self.handlers = dict(handlers or {})
        self.review_boundary = review_boundary

    def _assert_storage_scope(self, *, check_tree: bool = False) -> None:
        """Repeat isolation checks; paths can change after engine construction."""
        if self.root.resolve() != self._repository_scope or not self.data.resolve().is_relative_to(self._repository_scope):
            raise EvidenceError("admission data root no longer belongs to its repository scope")
        for path in (self.data / "canonical", self.data / "canonical/state.json",
                     self.run_root, self.data / "audit",
                     self.run_root / "canonical-pre-state.bytes",
                     self.run_root / "blocked-report.json", self.run_root / "stages",
                     self.data / self.config["artifacts"]["promotion_audit"]):
            if not path.resolve().is_relative_to(self.data.resolve()):
                raise EvidenceError("admission canonical, run, or audit path escapes its data scope")
        if check_tree:
            for path in self.data.rglob("*"):
                if path.is_symlink() and not path.resolve().is_relative_to(self.data.resolve()):
                    raise EvidenceError("admission storage contains a symlink escaping its data scope")

    def admission_bindings(self) -> dict:
        """The complete live input the trusted host must explicitly authorize."""
        _, payload, raw = self._payload()
        ids = payload["candidate_ids"]
        if ids != [row["candidate_identifier"] for row in payload["candidate_payloads"]]:
            raise EvidenceError("candidate inventory/order mismatch")
        if not ids or len(set(ids)) != len(ids) or digest(ids) != self.descriptor.candidate_digest:
            raise EvidenceError("candidate digest mismatch")
        artifacts = self.config["artifacts"]
        items = [{"path": artifacts["source_artifact"], "role": "source"}]
        for item in artifacts.get("receipts", []):
            items.append({"path": item, "role": "receipt"} if isinstance(item, str)
                         else {**item, "role": item.get("role", "receipt")})
        evidence = []
        for item in items:
            content = _retained_path(self.data, item["path"]).read_bytes()
            actual = digest(content)
            if item.get("sha256", actual) != actual:
                raise EvidenceError("retained receipt hash mismatch")
            evidence.append({"path": item["path"], "role": item["role"],
                             "sha256": actual, "byte_length": len(content)})
        return {"operation": ADMISSION_OPERATION, "repository_root": str(self.root.resolve()),
                "candidate_ids": ids, "candidate_id_digest": digest(ids),
                "candidate_payload_path": artifacts["candidate_payload"],
                "candidate_payload_sha256": digest(raw),
                "candidate_rows_digest": digest(payload["candidate_payloads"]),
                "evidence_files": evidence,
                "canonical_pre_state_digest": self.config["integrity"]["canonical_pre_state_digest"],
                "target": deepcopy(self.descriptor.__dict__),
                "policy_digest": digest(self.config["policy"]),
                "construction_policy_digest": digest(self.config.get("canonical_identity_fields", {}))}

    def _authorization(self) -> AdmissionDecision:
        if self.review_boundary is None:
            raise EvidenceError("new admission requires an authenticated trusted host review boundary")
        bindings = self.admission_bindings()
        # Unconditionally repeat integrity gates. Completed stage files cannot
        # grant permission to use a different retained source or payload.
        self._stage_source_acquisition_verification({})
        self._stage_evidence_normalization({})
        self._stage_target_partitioning({})
        previous = self._checkpoint("candidate_review")
        if previous.exists():
            checkpoint = json.loads(previous.read_bytes())
            self._verify_result(checkpoint, "candidate_review")
            if checkpoint["details"].get("input_bindings_digest") != digest(bindings):
                raise EvidenceError("resumed admission input differs from reviewed checkpoint")
        decision = self.review_boundary.authorize(deepcopy(bindings))
        if not isinstance(decision, AdmissionDecision):
            raise EvidenceError("trusted review boundary did not return an AdmissionDecision")
        if (decision.decision != "approved" or decision.operation != ADMISSION_OPERATION
                or decision.bindings != bindings or not decision.review_reference
                or not decision.reviewer.strip()
                or decision.reviewer != self.review_boundary.authenticated_reviewer):
            raise EvidenceError("admission decision is absent, rejected, mismatched, or out of scope")
        try:
            timestamp = datetime.fromisoformat(decision.decided_at.replace("Z", "+00:00"))
            if timestamp.utcoffset() is None: raise ValueError
        except (TypeError, ValueError): raise EvidenceError("admission decision time is invalid") from None
        if isinstance(self.review_boundary, IsolatedAdmissionTestBoundary) and decision.scope != "isolated-test":
            raise EvidenceError("simulated test boundary cannot authorize production admission")
        if decision.scope == "isolated-test":
            if not isinstance(self.review_boundary, IsolatedAdmissionTestBoundary):
                raise EvidenceError("simulated authorization requires the live isolated test capability")
            self.review_boundary._verify_root(self.root)
        elif decision.scope != "production":
            raise EvidenceError("unsupported admission authorization scope")
        elif decision.review_reference.startswith("SIMULATED"):
            raise EvidenceError("simulated authorization cannot be reused for production admission")
        # The host callback is not allowed to leave a stale content observation.
        # Reread after returning from authentication, including the last write gate.
        if self.admission_bindings() != bindings:
            raise EvidenceError("admission evidence or payload changed during authorization")
        self._stage_source_acquisition_verification({})
        self._stage_evidence_normalization({})
        # Valid checkpoints are observations, never cached authorization/integrity.
        actual = canonical_state_digest(self.data)
        audit_path = self.data / self.config["artifacts"]["promotion_audit"]
        if audit_path.exists():
            audit = json.loads(audit_path.read_bytes())
            validate_admission_audit(self.data, audit)
            if (audit.get("input_bindings") != bindings
                    or audit.get("canonical_post_state_digest") != actual):
                raise EvidenceError("conflicting replay of promoted batch")
        elif actual != bindings["canonical_pre_state_digest"]:
            raise EvidenceError("canonical pre-state drift")
        return decision

    def _checkpoint(self, stage: str) -> Path:
        self._assert_storage_scope()
        path = self.run_root / "stages" / f"{STAGES.index(stage) + 1:02d}-{stage}.json"
        if not path.resolve().is_relative_to(self.data.resolve()):
            raise EvidenceError("admission checkpoint escapes its data scope")
        return path

    def _result(self, stage: str, details: dict) -> dict:
        body = {"schema_version": SCHEMA, "stage": stage, "status": "succeeded",
                "batch_identifier": self.descriptor.batch_identifier, "details": details}
        return {**body, "result_digest": digest(body)}

    def _verify_result(self, result: dict, stage: str) -> None:
        if not isinstance(result, dict) or not isinstance(result.get("details"), dict):
            raise EvidenceError(f"invalid completed-stage checkpoint: {stage}")
        supplied = result.get("result_digest")
        body = {k: v for k, v in result.items() if k != "result_digest"}
        if (result.get("schema_version") != SCHEMA
                or result.get("batch_identifier") != self.descriptor.batch_identifier
                or result.get("stage") != stage or result.get("status") != "succeeded"
                or supplied != digest(body)):
            raise EvidenceError(f"invalid completed-stage checkpoint: {stage}")

    def _has_contiguous_acceptance(self) -> bool:
        """Recognize previous completion without trusting a lone cached success.

        These protected local artifacts establish content/progress consistency,
        not reviewer authentication. Every new write still requires the live host
        boundary, and resumed consumers are executed again below. A valid previous
        completion must not be undone merely because its source is later damaged.
        """
        completed = {}
        try:
            for stage in STAGES[:STAGES.index("query_and_analytics_smoke_tests") + 1]:
                path = self._checkpoint(stage)
                if not path.is_file(): return False
                checkpoint = json.loads(path.read_bytes())
                self._verify_result(checkpoint, stage)
                completed[stage] = checkpoint["details"]
            audit = json.loads((self.data / self.config["artifacts"]["promotion_audit"]).read_bytes())
            body = {key: item for key, item in audit.items() if key != "audit_digest"}
            post = audit["canonical_post_state_digest"]
            if (audit.get("audit_digest") != digest(body)
                    or audit.get("batch_id") != self.descriptor.batch_identifier
                    or audit.get("candidate_id_digest") != self.descriptor.candidate_digest
                    or completed["bounded_canonical_promotion"].get("canonical_post_state_digest") != post
                    or completed["canonical_post_state_verification"].get("canonical_post_state_digest") != post
                    or canonical_state_digest(self.data) != post):
                return False
            state = json.loads((self.data / "canonical/state.json").read_bytes())
            consumer = completed["bounded_canonical_promotion"].get("consumer_validation", {})
            admitted = audit["admitted_records"]
            if (consumer.get("valid") is not True or consumer.get("projection_valid") is not True
                    or consumer.get("printing_relationships_checked") != sum(row["entity_type"] == "printing" for row in admitted)
                    or consumer.get("identifier_resolution_checked") != sum(row["entity_type"] == "identifier" for row in admitted)):
                return False
            expected = {"entity_counts": {kind: len(rows) for kind, rows in sorted(state.items())},
                        "consumer_validation": consumer, "passed": True}
            return completed["query_and_analytics_smoke_tests"] == expected
        except (OSError, ValueError, KeyError, TypeError, EvidenceError):
            return False

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
        self._assert_storage_scope(check_tree=True)
        status = self.status()
        audit = self.data / self.config["artifacts"]["promotion_audit"]
        if audit.exists():
            value = json.loads(audit.read_text()); expected = value.get("audit_digest")
            body = {k: v for k, v in value.items() if k != "audit_digest"}
            if expected and expected != digest(body): raise EvidenceError("immutable audit digest mismatch")
        return {**status, "verified": True, "audit_present": audit.exists(),
                "canonical_state_digest": canonical_state_digest(self.data)}

    def execute(self, *, stop_after: str | None = None) -> dict:
        self._assert_storage_scope(check_tree=True)
        self._restored_write_pre_digest = None
        if stop_after is not None and stop_after not in STAGES:
            raise EvidenceError("unknown stop-after stage")
        audit_path = self.data / self.config["artifacts"]["promotion_audit"]
        # A completed retained receipt permits inspection/replay, never a new write.
        if self.review_boundary is None and audit_path.exists():
            audit = json.loads(audit_path.read_bytes())
            if "input_bindings" not in audit:
                return self._verify_historical_read_only(audit)
            validate_admission_audit(self.data, audit)
            if (audit.get("input_bindings") != self.admission_bindings()
                    or canonical_state_digest(self.data) != audit.get("canonical_post_state_digest")):
                raise EvidenceError("conflicting read-only admission replay")
            return {**self.status(), "idempotent": True, "read_only": True}
        context = {"engine": self, "config": self.config, "target": self.descriptor.__dict__}
        backup_path = self.run_root / "canonical-pre-state.bytes"
        incomplete = not self._has_contiguous_acceptance()
        acceptance_completed = not incomplete
        original = backup_path.read_bytes() if incomplete and backup_path.exists() else None
        for stage in STAGES:
            path = self._checkpoint(stage)
            try:
                if STAGES.index("candidate_review") <= STAGES.index(stage) <= STAGES.index("bounded_canonical_promotion"):
                    self._authorization()
                    # Check current source/payload pins even when earlier stages resume.
                    self._stage_source_acquisition_verification(context)
                    self._stage_evidence_normalization(context)
                    self._stage_target_partitioning(context)
                if stage == "bounded_canonical_promotion" and not path.exists() and not audit_path.exists():
                    original = (self.data / "canonical/state.json").read_bytes()
                    if not backup_path.exists():
                        self._atomic_write(backup_path, original.decode(), exclusive=True)
                if path.exists():
                    value = json.loads(path.read_text()); self._verify_result(value, stage)
                    if stage == "query_and_analytics_smoke_tests":
                        fresh = self._stage_query_and_analytics_smoke_tests(context)
                        if fresh != value["details"]:
                            raise EvidenceError("cached consumer acceptance differs from live validation")
                        context[stage] = fresh
                    else:
                        context[stage] = value["details"]
                else:
                    details = (self.handlers.get(stage) or getattr(self, f"_stage_{stage}"))(context)
                    result = self._result(stage, details)
                    path.parent.mkdir(parents=True, exist_ok=True)
                    self._atomic_write(path, json.dumps(result, indent=2, sort_keys=True) + "\n", exclusive=True)
                    context[stage] = details
                if stage == "query_and_analytics_smoke_tests":
                    original = None
                    acceptance_completed = True
            except BaseException as error:
                # Never attempt compensation/diagnostic writes through a moved
                # data/canonical/audit symlink. The raised error is the diagnostic.
                self._assert_storage_scope()
                restored = False
                recovery_reason = "no canonical write owned by this incomplete run"
                if original is not None:
                    restored, recovery_reason = self._restore_owned_incomplete_state(original)
                invalidated = []
                if not acceptance_completed:
                    # A recovery conflict must preserve current bytes and immutable
                    # receipts, but cannot leave a successful acceptance/write
                    # checkpoint for an operation that remains incomplete.
                    for failed_stage in STAGES[STAGES.index("bounded_canonical_promotion"):]:
                        checkpoint = self._checkpoint(failed_stage)
                        if checkpoint.exists():
                            checkpoint.unlink()
                            invalidated.append(failed_stage)
                self.run_root.mkdir(parents=True, exist_ok=True)
                report = {"schema_version": SCHEMA, "status": "blocked", "failed_stage": stage,
                          "error": f"{type(error).__name__}: {error}",
                          "canonical_original_bytes_restored": restored,
                          "failure_recovery": recovery_reason,
                          "invalidated_write_acceptance_checkpoints": invalidated,
                          "audit_file_retained": audit_path.exists()}
                self._atomic_write(self.run_root / "blocked-report.json", json.dumps(report, indent=2, sort_keys=True) + "\n")
                raise
            if stop_after == stage: break
        return self.status()

    def _restore_owned_incomplete_state(self, original: bytes) -> tuple[bool, str]:
        """Compensate our partial write, never overwrite drift or an unbound backup."""
        canonical = self.data / "canonical"
        self._assert_storage_scope(check_tree=True)
        inventory = [{"path": path.relative_to(canonical).as_posix(),
                      "sha256": digest(original if path == canonical / "state.json" else path.read_bytes())}
                     for path in sorted(canonical.rglob("*")) if path.is_file()]
        expected_pre = self.config["integrity"]["canonical_pre_state_digest"]
        if digest(inventory) != expected_pre:
            return False, "retained pre-state bytes do not match the authorized canonical pre-state"
        if (getattr(self, "_restored_write_pre_digest", None) == expected_pre
                and canonical_state_digest(self.data) == expected_pre):
            return True, "this attempt already restored its authenticated original write bytes"
        expected_post = getattr(self, "_owned_post_state_digest", None)
        audit_path = self.data / self.config["artifacts"]["promotion_audit"]
        if expected_post is None and audit_path.exists():
            try:
                audit = json.loads(audit_path.read_bytes())
                body = {key: item for key, item in audit.items() if key != "audit_digest"}
                if (audit.get("audit_digest") != digest(body)
                        or audit.get("batch_id") != self.descriptor.batch_identifier
                        or audit.get("candidate_id_digest") != self.descriptor.candidate_digest
                        or audit.get("canonical_pre_state_digest") != expected_pre):
                    return False, "incomplete admission ownership receipt is invalid"
                # A self-hashed audit/post-state claim does not establish ownership.
                # Reconstruct our exact deterministic delta from the bound input
                # and authenticated pre-state; arbitrary extra records cannot be
                # compensated even if an attacker rehashes receipt/checkpoint JSON.
                bindings = audit["input_bindings"]
                _, payload, payload_raw = self._payload()
                if (digest(payload_raw) != bindings["candidate_payload_sha256"]
                        or payload["candidate_ids"] != bindings["candidate_ids"]
                        or digest(payload["candidate_payloads"]) != bindings["candidate_rows_digest"]
                        or bindings["target"] != self.descriptor.__dict__
                        or bindings["construction_policy_digest"] != digest(self.config.get("canonical_identity_fields", {}))):
                    return False, "incomplete admission payload is no longer the bound input"
                reconstructed = json.loads(original)
                for candidate in payload["candidate_payloads"]:
                    kind, identifier, record = self._canonical_record(candidate,
                        payload.get("candidate_contexts", {}).get(candidate["candidate_identifier"]))
                    existing = reconstructed.setdefault(kind, {}).get(identifier)
                    if existing and existing != record:
                        return False, "incomplete admission reconstruction conflicts with its pre-state"
                    reconstructed[kind][identifier] = record
                reconstructed_bytes = (json.dumps(reconstructed, indent=2, sort_keys=True) + "\n").encode()
                owned_inventory = [{"path": item["path"], "sha256":
                    digest(reconstructed_bytes) if item["path"] == "state.json" else item["sha256"]}
                    for item in inventory]
                expected_post = digest(owned_inventory)
                if expected_post != audit.get("canonical_post_state_digest"):
                    return False, "incomplete admission post-state claim differs from its exact reconstructed delta"
            except (OSError, ValueError, TypeError, KeyError, EvidenceError):
                return False, "incomplete admission ownership receipt is unreadable"
        if not expected_post or canonical_state_digest(self.data) != expected_post:
            return False, "current canonical bytes differ from this run's owned partial post-state"
        owns_audit = False
        if audit_path.exists():
            raw = audit_path.read_bytes()
            owns_audit = getattr(self, "_owned_audit_sha256", None) == digest(raw)
            if not owns_audit:
                try:
                    receipt = json.loads(raw)
                    validate_admission_audit(self.data, receipt)
                    owns_audit = (receipt.get("batch_id") == self.descriptor.batch_identifier
                        and receipt.get("candidate_id_digest") == self.descriptor.candidate_digest
                        and receipt.get("canonical_pre_state_digest") == expected_pre
                        and receipt.get("canonical_post_state_digest") == expected_post
                        and receipt.get("input_bindings", {}).get("target") == self.descriptor.__dict__)
                except (OSError, ValueError, KeyError, TypeError, AttributeError, EvidenceError):
                    owns_audit = False
        self._atomic_write(canonical / "state.json", original.decode())
        if owns_audit:
            audit_path.unlink(missing_ok=True)
        for failed_stage in STAGES[STAGES.index("bounded_canonical_promotion"):]:
            self._checkpoint(failed_stage).unlink(missing_ok=True)
        self._owned_post_state_digest = None
        self._restored_write_pre_digest = expected_pre
        return True, "restored authenticated original bytes from this run's owned partial write"

    def _verify_historical_read_only(self, audit: Mapping) -> dict:
        """Inspect original bounded admissions through their real retained evidence.

        Legacy review labels are never upgraded into new authenticated authority.
        This path is read-only and cannot produce a canonical delta/checkpoint.
        """
        from projection.engine import TypedCanonicalProjectionEngine, _historical_admission_records
        admitted = _historical_admission_records(self.data, audit)
        state = json.loads((self.data / "canonical/state.json").read_bytes())
        if (audit.get("batch_id") != self.descriptor.batch_identifier
                or audit.get("candidate_id_digest") != self.descriptor.candidate_digest
                or audit.get("canonical_pre_state_digest") != self.config["integrity"]["canonical_pre_state_digest"]):
            raise EvidenceError("historical admission scope mismatch")
        for kind, records in admitted.items():
            if any(state.get(kind, {}).get(key) != record for key, record in records.items()):
                raise EvidenceError("historical admitted record conflicts with retained evidence")
        self._stage_source_acquisition_verification({})
        self._stage_evidence_normalization({})
        projection = TypedCanonicalProjectionEngine(self.data / "canonical", self.data / "canonical/games",
                                                   self.data / "audit/projection", game=self.descriptor.game).validate()
        if not projection["valid"]:
            raise EvidenceError("current state does not match its historical admissions")
        return {**self.status(), "idempotent": True, "read_only": True,
                "historical_admission_verified": True}

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
        self._assert_storage_scope(check_tree=True)
        path = _retained_path(self.data, self.config["artifacts"]["candidate_payload"])
        raw = path.read_bytes(); return path, json.loads(raw), raw

    def _stage_source_acquisition_verification(self, c):
        p = _retained_path(self.data, self.config["artifacts"]["source_artifact"])
        if not p.is_file(): raise EvidenceError("source artifact is not retained")
        expected = self.config["integrity"].get("source_sha256")
        actual = digest(p.read_bytes())
        if expected and actual != expected: raise EvidenceError("source artifact hash mismatch")
        checkpoint = self._checkpoint("source_acquisition_verification")
        if checkpoint.exists():
            previous = json.loads(checkpoint.read_bytes()); self._verify_result(previous, "source_acquisition_verification")
            if previous["details"].get("sha256") != actual:
                raise EvidenceError("resumed source differs from verified checkpoint")
        if self.descriptor.trusted_provider not in self.config["policy"]["trusted_providers"]:
            raise EvidenceError("provider is not explicitly trusted")
        return {"path": str(p.relative_to(self.root)), "sha256": actual}

    def _stage_evidence_normalization(self, c):
        path, payload, raw = self._payload(); candidates = payload["candidate_payloads"]
        ids = payload.get("candidate_ids", [x["candidate_identifier"] for x in candidates])
        expected_payload = self.config["integrity"].get("candidate_payload_sha256")
        if expected_payload and digest(raw) != expected_payload:
            raise EvidenceError("candidate payload checksum mismatch")
        checkpoint = self._checkpoint("evidence_normalization")
        if checkpoint.exists():
            previous = json.loads(checkpoint.read_bytes()); self._verify_result(previous, "evidence_normalization")
            if previous["details"].get("payload_sha256") != digest(raw):
                raise EvidenceError("resumed payload differs from verified checkpoint")
        if not ids or any(not isinstance(value, str) or not value for value in ids):
            raise EvidenceError("candidate inventory contains a missing candidate")
        if len(ids) != len(set(ids)):
            raise EvidenceError("candidate inventory contains a duplicate candidate")
        if ids != [x["candidate_identifier"] for x in candidates]: raise EvidenceError("candidate inventory/order mismatch")
        if digest(ids) != self.descriptor.candidate_digest: raise EvidenceError("candidate digest mismatch")
        if len(ids) != self.config["integrity"].get("expected_candidate_count"):
            raise EvidenceError("candidate count mismatch")
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
        decision = self._authorization()
        for row in payload["candidate_payloads"]:
            if not row.get("provenance"):
                raise EvidenceError("candidate is missing explicit provenance")
            if row["provenance"].get("provider") != self.descriptor.trusted_provider:
                raise EvidenceError("candidate provenance provider is not explicitly trusted")
            if row.get("validation_state") != "validated":
                raise EvidenceError("candidate is not validated")
            # A human/host decision authorizes the exact pending data. Validation
            # itself never constructs an approved candidate classification.
            state = row.get("final_classification", row.get("review_status", "pending"))
            blocked = {"unresolved", "rejected", "quarantined", "fatal", "held", "simulated"}
            normalized = str(state).casefold()
            if str(row.get("review_status", "")).casefold() in blocked or normalized in blocked:
                raise EvidenceError("candidate review contains a blocking classification")
            allowed = {"pending", "approved"} | {str(value).casefold() for value in
                self.config["policy"]["permitted_final_classifications"]}
            if not isinstance(state, str) or normalized not in allowed:
                raise EvidenceError("candidate review contains an unsupported classification")
            if "SIMULATED" in str(state) and decision.scope != "isolated-test":
                raise EvidenceError("simulated candidate review cannot authorize production admission")
            counts[state] = counts.get(state, 0) + 1
        if set(counts).intersection({"unresolved", "rejected", "quarantined", "fatal", "held", "simulated"}):
            raise EvidenceError("candidate review contains a blocking classification")
        return {"classifications": counts, "admission_decision_digest": digest(decision.as_dict()),
                "input_bindings_digest": digest(decision.bindings),
                "authorization_scope": decision.scope,
                "complete": sum(counts.values()) == c["evidence_normalization"]["candidate_count"]}

    def _stage_identifier_and_conflict_policy_resolution(self, c):
        _, payload, _ = self._payload()
        if any(row.get("conflict_state") not in (None, "none", "deterministically_resolved") for row in payload["candidate_payloads"]):
            raise EvidenceError("unresolved or unapproved identity conflict")
        return {"policy": self.descriptor.promotion_policy, "unresolved_conflicts": 0}

    def _stage_dependency_closure_verification(self, c):
        _, payload, _ = self._payload()
        from query.engine import CanonicalQueryEngine
        query = CanonicalQueryEngine(self.descriptor.game,
            games_root=self.data / "canonical/games", data_root=self.data)
        inventory = {}
        for entity in query.snapshot().entities:
            inventory.setdefault(entity.entity_type, set()).add(entity.canonical_identity)
        proposed = []
        for row in payload["candidate_payloads"]:
            kind, identifier, record = self._canonical_record(row,
                payload.get("candidate_contexts", {}).get(row["candidate_identifier"]))
            inventory.setdefault(kind, set()).add(identifier)
            proposed.append((kind, identifier, record))
        for kind, identifier, record in proposed:
            fields = record["values"]
            if kind == "printing":
                if fields.get("card_id") not in inventory.get("card", set()):
                    raise EvidenceError("dependency closure contains orphaned Printing Card")
                if not fields.get("set_id"):
                    raise EvidenceError("Printing is missing its set namespace")
                # Set is a virtual namespace in the existing query/projection contract.
                if any(finish not in inventory.get("finish", set()) for finish in fields.get("finish_ids", [])):
                    raise EvidenceError("dependency closure contains missing Finish")
            if kind == "identifier" and fields.get("printing_uuid") not in inventory.get("printing", set()):
                raise EvidenceError("dependency closure contains orphaned identifier")
        return {"valid": True, "orphaned_printings": 0, "checked_delta": len(proposed),
                "existing_and_delta_dependencies": True}

    def _stage_promotion_readiness_planning(self, c):
        self._authorization()
        return {"ready": True, "candidate_digest": self.descriptor.candidate_digest, "plan_digest": digest({"target": self.descriptor.__dict__, "count": c["evidence_normalization"]["candidate_count"]})}

    def _stage_deterministic_promotion_preflight(self, c):
        self._authorization()
        actual = canonical_state_digest(self.data); expected = self.config["integrity"]["canonical_pre_state_digest"]
        audit = self.data / self.config["artifacts"]["promotion_audit"]
        if actual != expected and not audit.exists(): raise EvidenceError("canonical pre-state drift")
        return {"canonical_pre_state_digest": expected, "observed_state_digest": actual, "existing_audit": audit.exists()}

    def _canonical_record(self, candidate: Mapping, context: Mapping | None = None) -> tuple[str, str, dict]:
        """Adapt source fields to the existing state representation without losing them."""
        kind = candidate["entity_type"]
        if kind not in {"card", "printing", "identifier", "finish"}:
            raise EvidenceError(f"unsupported canonical candidate kind: {kind}")
        source = deepcopy(candidate["mapped_fields"])
        fields = deepcopy(source)
        identity_key = self.config.get("canonical_identity_fields", {}).get(
            kind, {"card": "card_reference", "printing": "uuid", "finish": "value"}.get(kind))
        identity = fields.get(identity_key) if identity_key else candidate["candidate_identifier"].rsplit(":", 1)[-1]
        if not isinstance(identity, str) or not identity.strip():
            raise EvidenceError("candidate has no canonical identity")
        identifier = identity.casefold()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", identifier):
            raise EvidenceError("candidate canonical identity is not a stable supported identifier")
        if kind == "card" and not isinstance(fields.get("name"), str):
            raise EvidenceError("Card candidate is missing its name")
        if kind == "printing":
            card = fields.get("card_id", fields.get("card_reference"))
            set_id = fields.get("set_id", fields.get("set_code"))
            if not isinstance(card, str) or not isinstance(set_id, str):
                raise EvidenceError("Printing candidate is missing Card or set relationship")
            if fields.get("card_reference") and fields["card_reference"].casefold() != card.casefold():
                raise EvidenceError("Printing Card relationships contradict")
            if fields.get("set_code") and fields["set_code"].casefold() != set_id.casefold():
                raise EvidenceError("Printing set relationships contradict")
            fields["card_id"], fields["set_id"] = card.casefold(), set_id.casefold()
            finishes = fields.get("finish_ids", fields.get("finishes"))
            if finishes is None and fields.get("finish"): finishes = [fields["finish"]]
            if not isinstance(finishes, list) or not finishes or any(not isinstance(x, str) or not x for x in finishes):
                raise EvidenceError("Printing candidate has no evidenced Finish relationship")
            fields["finish_ids"] = [value.casefold() for value in finishes]
            if fields.get("finishes") and [x.casefold() for x in fields["finishes"]] != fields["finish_ids"]:
                raise EvidenceError("Printing Finish relationships contradict")
            language = fields.get("language")
            equivalents = {"english": "en", "en": "en", "japanese": "ja", "ja": "ja"}
            if not isinstance(language, str) or not language:
                raise EvidenceError("Printing candidate has no evidenced language")
            normalized = equivalents.get(language.casefold(), language)
            if fields.get("language_code") and equivalents.get(str(fields["language_code"]).casefold(), fields["language_code"]) != normalized:
                raise EvidenceError("Printing language evidence contradicts")
            fields["language"] = normalized
            if not isinstance(fields.get("collector_number"), str) or not fields["collector_number"]:
                raise EvidenceError("Printing candidate has no collector number")
        if kind == "identifier":
            fields["namespace"] = fields.get("namespace", fields.get("scheme"))
            if not fields.get("namespace") or not fields.get("value") or not fields.get("printing_uuid"):
                raise EvidenceError("identifier candidate is missing namespace, value, or Printing")
            fields["printing_uuid"] = str(fields["printing_uuid"]).casefold()
        metadata = deepcopy(candidate.get("acquisition_metadata", {}))
        lineage = deepcopy(candidate.get("acquisition_lineage", [metadata] if metadata else []))
        if isinstance(lineage, Mapping): lineage = [lineage]
        record = {"entity_type": kind, "values": fields, "source_values": source,
                  "evidence_references": [candidate["candidate_identifier"]],
                  "dataset_identity": [self.descriptor.source_dataset_identity],
                  "promotion_id": self.descriptor.batch_identifier,
                  "provenance": deepcopy(candidate.get("provenance", {})),
                  "acquisition_metadata": metadata,
                  "acquisition_lineage": lineage,
                  "confidence": candidate.get("confidence"),
                  "unknown_fields": deepcopy(candidate.get("unknown_fields", {})),
                  "unknown_values": deepcopy(candidate.get("unknown_fields", {})),
                  "uncertainty_state": candidate.get("uncertainty_state", "unknown")}
        if context:
            record["candidate_context"] = deepcopy(context)
            record["field_provenance"] = deepcopy(context.get("field_provenance", []))
            record["parsed_record_references"] = {key: deepcopy(context[key]) for key in
                ("parsed_artifact_id", "parsed_record_id", "parsed_record_ids", "source_id", "raw_evidence_hash")
                if key in context}
            for key in ("parsed_artifact_id", "parsed_record_id", "source_id", "raw_evidence_hash"):
                values = sorted({str(item[key]) for item in context.get("field_provenance", []) if item.get(key)})
                if values and key not in record["parsed_record_references"]:
                    record["parsed_record_references"][key + "s"] = values
        return kind, identifier, record

    def _stage_bounded_canonical_promotion(self, c):
        decision = self._authorization()
        # These gates cannot be replaced by optional stage handlers/checkpoints.
        self._stage_candidate_review({"evidence_normalization": self._stage_evidence_normalization({})})
        self._stage_identifier_and_conflict_policy_resolution({})
        self._stage_dependency_closure_verification({})
        audit_path = self.data / self.config["artifacts"]["promotion_audit"]
        if audit_path.exists():
            audit = json.loads(audit_path.read_text())
            if audit.get("batch_id") != self.descriptor.batch_identifier or audit.get("candidate_id_digest") != self.descriptor.candidate_digest:
                raise EvidenceError("conflicting replay of promoted batch")
            if canonical_state_digest(self.data) != audit["canonical_post_state_digest"]: raise EvidenceError("canonical state conflicts with audit")
            return {"idempotent": True, "canonical_post_state_digest": audit["canonical_post_state_digest"]}
        state_path = self.data / "canonical/state.json"; original = state_path.read_bytes()
        state = json.loads(original); _, payload, _ = self._payload(); promoted = []
        admitted_records = []; record_digests = {}
        for candidate in payload["candidate_payloads"]:
            kind, identifier, record = self._canonical_record(candidate,
                payload.get("candidate_contexts", {}).get(candidate["candidate_identifier"]))
            existing = state.setdefault(kind, {}).get(identifier)
            if existing and existing != record: raise EvidenceError(f"conflicting canonical {kind} identity")
            state[kind][identifier] = record; promoted.append(candidate["candidate_identifier"])
            record_digests.setdefault(kind, {})[identifier] = digest(record)
            admitted_records.append({"entity_type": kind, "canonical_identity": identifier,
                "candidate_identifier": candidate["candidate_identifier"], "record_sha256": digest(record)})
        body = {"schema_version": SCHEMA, "promotion_id": self.descriptor.batch_identifier,
                "batch_id": self.descriptor.batch_identifier, "candidate_id_digest": self.descriptor.candidate_digest,
                "canonical_pre_state_digest": c["deterministic_promotion_preflight"]["canonical_pre_state_digest"],
                "promoted_entities": promoted, "result": "succeeded",
                "admitted_records": admitted_records, "canonical_record_digests": record_digests,
                "input_bindings": deepcopy(decision.bindings),
                "admission_decision": decision.as_dict(),
                "admission_decision_digest": digest(decision.as_dict()),
                "authorization_scope": decision.scope}
        state_text = json.dumps(state, indent=2, sort_keys=True) + "\n"
        # Validate the proposed state and receipt with real readers in isolated
        # storage. No actual canonical byte is changed before consumers succeed.
        with tempfile.TemporaryDirectory(prefix="catalog-admission-consumers-") as temporary:
            staged = Path(temporary) / "data"
            # Preserve links rather than following any unreviewed target while
            # copying; bound readers still reject escapes in the staged copy.
            shutil.copytree(self.data, staged, symlinks=True)
            self._atomic_write(staged / "canonical/state.json", state_text)
            body["canonical_post_state_digest"] = canonical_state_digest(staged)
            audit = {**body, "audit_digest": digest(body)}
            self._atomic_write(staged / self.config["artifacts"]["promotion_audit"],
                               json.dumps(audit, indent=2, sort_keys=True) + "\n", exclusive=True)
            consumer_validation = self._validate_consumers(staged, admitted_records)
        # Reauthenticate and reread every bound input immediately before writing.
        final_decision = self._authorization()
        if final_decision.as_dict() != decision.as_dict():
            raise EvidenceError("admission decision changed before canonical write")
        try:
            self._owned_post_state_digest = body["canonical_post_state_digest"]
            self._assert_storage_scope()
            self._atomic_write(state_path, state_text)
            self._assert_storage_scope(check_tree=True)
            if body["canonical_post_state_digest"] != canonical_state_digest(self.data):
                raise EvidenceError("canonical post-state verification failed")
            configured = self.config["integrity"].get("canonical_post_state_digest")
            if configured and configured != body["canonical_post_state_digest"]: raise EvidenceError("canonical post-state differs from plan")
            audit = {**body, "audit_digest": digest(body)}
            audit_text = json.dumps(audit, indent=2, sort_keys=True) + "\n"
            self._atomic_write(audit_path, audit_text, exclusive=True)
            self._owned_audit_sha256 = digest(audit_text.encode())
        except BaseException:
            self._assert_storage_scope()
            self._restore_owned_incomplete_state(original)
            raise
        return {"idempotent": False, "canonical_post_state_digest": body["canonical_post_state_digest"],
                "consumer_validation": consumer_validation}

    def _validate_consumers(self, data_root: Path, admitted_records: list[dict]) -> dict:
        from query.engine import CanonicalQueryEngine
        from collection.intelligence import CanonicalCollectionResolver
        from projection.engine import TypedCanonicalProjectionEngine
        query = CanonicalQueryEngine(self.descriptor.game,
            games_root=data_root / "canonical/games", data_root=data_root)
        resolver = CanonicalCollectionResolver(self.descriptor.game, data_root)
        printing_count = alias_count = 0
        for item in admitted_records:
            kind, identity = item["entity_type"], item["canonical_identity"]
            result = query.entity(identity, entity_type=kind)
            if kind == "printing":
                fields = result.canonical_values
                if query.related(identity, "printing_card")[0].canonical_identity != fields["card_id"]:
                    raise EvidenceError("canonical Printing-to-Card query failed")
                if identity not in {x.canonical_identity for x in query.related(fields["card_id"], "card_printings")}:
                    raise EvidenceError("canonical Card-to-Printing query failed")
                if query.related(identity, "printing_set")[0]["canonical_identity"] != fields["set_id"]:
                    raise EvidenceError("canonical Printing-to-set query failed")
                resolved = resolver.resolve({"entries": [{"printing_id": identity, "quantity": 1,
                    "language": fields["language"]}]})["results"][0]
                if resolved["status"] != "resolved" or resolved.get("card_id") != fields["card_id"]:
                    raise EvidenceError("canonical collection resolution failed")
                printing_count += 1
            elif kind == "identifier":
                values = result.canonical_values
                resolved = resolver.resolve({"entries": [{"external_identifiers": {
                    values["namespace"]: values["value"]}, "quantity": 1}]})["results"][0]
                if resolved.get("printing_id") != values["printing_uuid"] or resolved["status"] != "resolved":
                    raise EvidenceError("canonical alias collection resolution failed")
                alias_count += 1
        projection = TypedCanonicalProjectionEngine(data_root / "canonical", data_root / "canonical/games",
                                                   data_root / "audit/projection", game=self.descriptor.game).validate()
        if not projection["valid"]:
            failed = [check for check in projection["checks"] if not check["valid"]]
            raise EvidenceError(f"canonical projection compatibility failed: {failed[:5]}")
        return {"valid": True, "printing_relationships_checked": printing_count,
                "identifier_resolution_checked": alias_count,
                "projection_valid": True,
                "typed_materialization_ready": projection.get("typed_materialization_ready", True),
                "historical_finish_gaps": projection.get("historical_unresolved_finish_references", [])}

    def _stage_immutable_promotion_audit(self, c):
        path = self.data / self.config["artifacts"]["promotion_audit"]
        if not path.is_file(): raise EvidenceError("immutable promotion audit missing")
        value = json.loads(path.read_text()); supplied = value.get("audit_digest")
        body = {key: item for key, item in value.items() if key != "audit_digest"}
        if not supplied or supplied != digest(body): raise EvidenceError("immutable audit digest mismatch")
        return {"path": str(path.relative_to(self.root)), "sha256": digest(path.read_bytes()), "immutable": True}

    def _stage_canonical_post_state_verification(self, c):
        actual = canonical_state_digest(self.data); expected = c["bounded_canonical_promotion"]["canonical_post_state_digest"]
        if actual != expected: raise EvidenceError("canonical post-state verification failed")
        return {"canonical_post_state_digest": actual, "verified": True}

    def _stage_query_and_analytics_smoke_tests(self, c):
        state = json.loads((self.data / "canonical/state.json").read_text())
        if not all(isinstance(value, dict) for value in state.values()): raise EvidenceError("canonical query smoke test failed")
        audit = json.loads((self.data / self.config["artifacts"]["promotion_audit"]).read_bytes())
        validate_admission_audit(self.data, audit)
        consumers = self._validate_consumers(self.data, audit["admitted_records"])
        return {"entity_counts": {key: len(value) for key, value in sorted(state.items())},
                "consumer_validation": consumers, "passed": True}

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

    def enable_auto_merge(self, pr: str, branch: str, base: str, head_oid: str) -> dict:
        """Verify the protected PR boundary and required checks before requesting auto-merge."""
        command = ["gh", "pr", "view", pr, "--json", "headRefName,baseRefName,headRefOid,statusCheckRollup"]
        result = self.run(command, check=True, text=True, capture_output=True)
        value = json.loads(result.stdout)
        if (value.get("headRefName"), value.get("baseRefName"), value.get("headRefOid")) != (branch, base, head_oid):
            raise EvidenceError("pull request merge boundary mismatch")
        checks = value.get("statusCheckRollup") or []
        if not checks or any(check.get("conclusion") != "SUCCESS" for check in checks):
            raise EvidenceError("required checks are not green")
        merge = ["gh", "pr", "merge", pr, "--auto", "--squash", "--delete-branch=false"]
        completed = self.run(merge, check=False, text=True, capture_output=True)
        if completed.returncode: raise EvidenceError("auto-merge request failed")
        return {"auto_merge_requested": True, "eligible": True, "branch_protection_bypass": False}
