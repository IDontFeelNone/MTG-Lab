"""Controlled, audited promotion of validated product candidates."""
from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from ingestion.hashing import hash_bytes
from validation import SchemaValidationError, validate_document

from .products import product_record_path

_IDENTIFIER = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


class PromotionError(RuntimeError):
    """Base class for controlled-promotion failures."""


class PromotionValidationError(PromotionError):
    """Raised when a candidate is not eligible for promotion."""


class PromotionConflict(PromotionError):
    """Raised when promotion or rollback would overwrite canonical state."""


class AuditStorageError(PromotionError):
    """Raised when immutable audit history cannot be read or written safely."""


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ProductReview:
    """An explicit application-workflow decision made by an identified actor."""

    decision: ReviewDecision
    actor: str
    decided_at: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError("actor must not be empty")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("reason must not be empty when supplied")


class ProductPromotionService:
    """Promotes one reviewed product candidate without silently merging data."""

    def __init__(self, *, games_root: Path | None = None, audit_root: Path | None = None) -> None:
        self._games_root = Path(games_root) if games_root else _PROJECT_ROOT / "data/canonical/games"
        self._audit_root = Path(audit_root) if audit_root else _PROJECT_ROOT / "data/audit/promotions"
        if self._audit_root.resolve().is_relative_to(self._games_root.resolve()):
            raise ValueError("audit history must be stored outside canonical product data")

    def review(
        self,
        candidate_artifact: Mapping[str, Any],
        parsed_artifact: Mapping[str, Any],
        candidate_id: str,
        review: ProductReview,
    ) -> Mapping[str, Any]:
        """Reject or promote an eligible candidate and return its immutable audit event."""
        candidate = self._eligible_candidate(candidate_artifact, parsed_artifact, candidate_id)
        product_id = self._product_id(candidate)
        action = "promotion" if review.decision is ReviewDecision.APPROVED else "rejection"
        audit_id = self._audit_id(action, candidate_artifact["id"], candidate_id, review)
        existing_audit = self._load_audit_if_present(audit_id)
        if existing_audit is not None:
            return existing_audit

        canonical_path = product_record_path("magic", product_id, games_root=self._games_root)
        canonical_before = self._load_canonical_if_present(canonical_path)
        if review.decision is ReviewDecision.REJECTED:
            event = self._event(
                audit_id=audit_id,
                action="rejection",
                candidate_artifact=candidate_artifact,
                candidate=candidate,
                review=review,
                outcome="rejected",
                canonical_before=canonical_before,
                canonical_after=canonical_before,
            )
            return self._store_audit(event)

        payload = deepcopy(candidate["payload"])
        created_canonical = canonical_before is None
        if created_canonical:
            self._validate_new_product(payload, product_id)
            self._create_canonical(canonical_path, payload)
            canonical_after = payload
            outcome = "promoted"
        else:
            conflicts = {
                key: {"canonical": canonical_before.get(key), "candidate": value}
                for key, value in payload.items()
                if canonical_before.get(key) != value
            }
            if conflicts:
                fields = ", ".join(sorted(conflicts))
                raise PromotionConflict(f"Candidate conflicts with canonical product fields: {fields}")
            canonical_after = canonical_before
            outcome = "confirmed"

        event = self._event(
            audit_id=audit_id,
            action="promotion",
            candidate_artifact=candidate_artifact,
            candidate=candidate,
            review=review,
            outcome=outcome,
            canonical_before=canonical_before,
            canonical_after=canonical_after,
        )
        try:
            return self._store_audit(event)
        except (AuditStorageError, SchemaValidationError):
            # A canonical write without its audit record is not a valid promotion.
            if created_canonical and self._load_canonical_if_present(canonical_path) == payload:
                canonical_path.unlink()
            raise

    def rollback(self, promotion_audit_id: str, review: ProductReview) -> Mapping[str, Any]:
        """Restore state recorded before a promotion and append a rollback event."""
        if review.decision is not ReviewDecision.APPROVED:
            raise PromotionValidationError("Rollback requires explicit approval")
        promotion = self._load_audit(promotion_audit_id)
        if promotion["action"] != "promotion":
            raise PromotionValidationError("Only promotion audit events can be rolled back")
        rollback_id = self._audit_id("rollback", promotion_audit_id, promotion["candidate_id"], review)
        existing = self._load_audit_if_present(rollback_id)
        if existing is not None:
            return existing

        canonical_path = product_record_path("magic", promotion["entity_id"], games_root=self._games_root)
        current = self._load_canonical_if_present(canonical_path)
        if current != promotion["canonical_after"]:
            raise PromotionConflict("Canonical product changed after promotion; rollback refused")
        before = promotion["canonical_before"]
        event = {
            "schema_version": "v1",
            "id": rollback_id,
            "action": "rollback",
            "entity_type": "product",
            "entity_id": promotion["entity_id"],
            "candidate_artifact_id": promotion["candidate_artifact_id"],
            "candidate_id": promotion["candidate_id"],
            "actor": review.actor,
            "decided_at": review.decided_at,
            "decision": review.decision.value,
            "outcome": "rolled_back",
            "candidate_snapshot": deepcopy(promotion["candidate_snapshot"]),
            "canonical_before": deepcopy(current),
            "canonical_after": deepcopy(before),
            "related_audit_id": promotion_audit_id,
        }
        if review.reason is not None:
            event["reason"] = review.reason
        validate_document(event, "promotion-audit")
        if before is None:
            if canonical_path.exists():
                canonical_path.unlink()
        elif current != before:
            self._replace_canonical(canonical_path, before)
        try:
            return self._store_audit(event)
        except (AuditStorageError, SchemaValidationError):
            # Restore the promoted state if rollback history cannot be persisted.
            if promotion["canonical_after"] is not None:
                self._replace_canonical(canonical_path, promotion["canonical_after"])
            raise

    @staticmethod
    def _eligible_candidate(
        artifact: Mapping[str, Any], parsed: Mapping[str, Any], candidate_id: str
    ) -> Mapping[str, Any]:
        validation = validate_candidate_artifact(artifact, parsed)
        if validation.state is not CandidateValidationState.VALID:
            raise PromotionValidationError("Candidate artifact failed cross-artifact validation")
        matches = [candidate for candidate in artifact["candidates"] if candidate["id"] == candidate_id]
        if len(matches) != 1:
            raise PromotionValidationError("Candidate identifier is missing or ambiguous")
        candidate = matches[0]
        if candidate["validation_state"] != CandidateValidationState.VALID.value:
            raise PromotionValidationError("Candidate must have validation_state 'valid'")
        if candidate["entity_type"] != "product" or artifact["candidate_type"] != "product":
            raise PromotionValidationError("Only product candidates can be promoted")
        payload_fields = set(candidate["payload"])
        provenance_fields = {item["field_path"] for item in candidate["field_provenance"]}
        if not payload_fields.issubset(provenance_fields):
            raise PromotionValidationError("Every promoted product field requires field provenance")
        allowed_fields = {
            "schema_version",
            "id",
            "game",
            "name",
            "product_type",
            "lifecycle_status",
            "slot_ids",
            "provenance",
        }
        if not payload_fields.issubset(allowed_fields):
            raise PromotionValidationError("Product candidate contains unknown canonical fields")
        if payload_fields == {"id"}:
            raise PromotionValidationError("Product candidate must propose at least one product field")
        return candidate

    @staticmethod
    def _product_id(candidate: Mapping[str, Any]) -> str:
        product_id = candidate["payload"].get("id")
        if not isinstance(product_id, str) or not _IDENTIFIER.fullmatch(product_id):
            raise PromotionValidationError("Product candidate requires a stable payload id")
        return product_id

    @staticmethod
    def _validate_new_product(payload: Mapping[str, Any], product_id: str) -> None:
        try:
            validate_document(payload, "product")
        except SchemaValidationError as error:
            raise PromotionValidationError(
                "A new canonical product requires a complete schema-valid payload"
            ) from error
        if payload["id"] != product_id or payload["game"] != "magic":
            raise PromotionValidationError("Product payload identifiers do not match its canonical path")

    def _event(
        self,
        *,
        audit_id: str,
        action: str,
        candidate_artifact: Mapping[str, Any],
        candidate: Mapping[str, Any],
        review: ProductReview,
        outcome: str,
        canonical_before: Mapping[str, Any] | None,
        canonical_after: Mapping[str, Any] | None,
    ) -> dict[str, Any]:
        event = {
            "schema_version": "v1",
            "id": audit_id,
            "action": action,
            "entity_type": "product",
            "entity_id": self._product_id(candidate),
            "candidate_artifact_id": candidate_artifact["id"],
            "candidate_id": candidate["id"],
            "actor": review.actor,
            "decided_at": review.decided_at,
            "decision": review.decision.value,
            "outcome": outcome,
            "candidate_snapshot": deepcopy(candidate),
            "canonical_before": deepcopy(canonical_before),
            "canonical_after": deepcopy(canonical_after),
        }
        if review.reason is not None:
            event["reason"] = review.reason
        return event

    @staticmethod
    def _audit_id(action: str, source_id: str, candidate_id: str, review: ProductReview) -> str:
        identity = json.dumps(
            {
                "action": action,
                "source_id": source_id,
                "candidate_id": candidate_id,
                "actor": review.actor,
                "decided_at": review.decided_at,
                "decision": review.decision.value,
                "reason": review.reason,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return f"product-{action}-{hash_bytes(identity)[:24]}"

    def _audit_path(self, audit_id: str) -> Path:
        if not _IDENTIFIER.fullmatch(audit_id):
            raise AuditStorageError("Invalid audit identifier")
        root = self._audit_root.resolve()
        path = root / f"{audit_id}.json"
        if not path.resolve().is_relative_to(root):
            raise AuditStorageError("Audit path escapes storage root")
        return path

    def _store_audit(self, event: Mapping[str, Any]) -> Mapping[str, Any]:
        validate_document(event, "promotion-audit")
        path = self._audit_path(event["id"])
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (json.dumps(event, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            existing = self._load_audit(event["id"])
            if existing != event:
                raise AuditStorageError("Audit identifier already stores different content")
            return existing
        except OSError as error:
            raise AuditStorageError("Unable to create permanent audit event") from error
        try:
            with os.fdopen(descriptor, "wb") as audit_file:
                audit_file.write(content)
        except OSError as error:
            path.unlink(missing_ok=True)
            raise AuditStorageError("Unable to write permanent audit event") from error
        return deepcopy(event)

    def _load_audit_if_present(self, audit_id: str) -> Mapping[str, Any] | None:
        if not self._audit_path(audit_id).exists():
            return None
        return self._load_audit(audit_id)

    def _load_audit(self, audit_id: str) -> Mapping[str, Any]:
        path = self._audit_path(audit_id)
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validate_document(document, "promotion-audit")
        except (OSError, json.JSONDecodeError, SchemaValidationError) as error:
            raise AuditStorageError(f"Cannot load valid audit event: {audit_id}") from error
        return document

    @staticmethod
    def _load_canonical_if_present(path: Path) -> Mapping[str, Any] | None:
        if not path.exists():
            return None
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validate_document(document, "product")
        except (OSError, json.JSONDecodeError, SchemaValidationError) as error:
            raise PromotionConflict("Existing canonical product is unreadable or invalid") from error
        return document

    @staticmethod
    def _create_canonical(path: Path, document: Mapping[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode()
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise PromotionConflict("Canonical product appeared during promotion") from error
        except OSError as error:
            raise PromotionError("Unable to create canonical product") from error
        try:
            with os.fdopen(descriptor, "wb") as product_file:
                product_file.write(content)
        except OSError as error:
            path.unlink(missing_ok=True)
            raise PromotionError("Unable to write canonical product") from error

    @staticmethod
    def _replace_canonical(path: Path, document: Mapping[str, Any]) -> None:
        validate_document(document, "product")
        descriptor, temporary = tempfile.mkstemp(prefix=".rollback-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as product_file:
                json.dump(document, product_file, sort_keys=True, indent=2, ensure_ascii=False)
                product_file.write("\n")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


__all__ = [
    "AuditStorageError",
    "ProductPromotionService",
    "ProductReview",
    "PromotionConflict",
    "PromotionError",
    "PromotionValidationError",
    "ReviewDecision",
]
