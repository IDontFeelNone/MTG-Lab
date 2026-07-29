"""Entity-agnostic, controlled promotion of reviewed canonical candidates."""
from __future__ import annotations

import json
import os
import re
import tempfile
from copy import deepcopy
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable, Mapping

from ingestion.candidate_validation import validate_candidate_artifact
from ingestion.candidates import CandidateValidationState
from ingestion.hashing import hash_bytes
from validation import SchemaValidationError, validate_document

from .cards import card_record_path, load_card, load_card_repository, load_printing, printing_record_path
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
    """Raised when immutable audit history cannot be stored safely."""


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class CandidateReview:
    """An explicit application-workflow decision by an identified actor."""

    decision: ReviewDecision
    actor: str
    decided_at: str
    reason: str | None = None

    def __post_init__(self) -> None:
        if not self.actor.strip():
            raise ValueError("actor must not be empty")
        if self.reason is not None and not self.reason.strip():
            raise ValueError("reason must not be empty when supplied")


# Compatibility name for the already published product workflow.
ProductReview = CandidateReview


@dataclass(frozen=True, slots=True)
class EntityPromotionDefinition:
    """Repository boundary required to promote one canonical entity type."""

    entity_type: str
    schema_name: str
    canonical_path: Callable[[str, str, Path], Path]
    validate_canonical: Callable[[str, str, Path], None]
    validate_repository: Callable[[str, Path], None] = lambda game, root: None


def _card_definition() -> EntityPromotionDefinition:
    return EntityPromotionDefinition(
        "card", "card",
        lambda game, entity_id, root: card_record_path(game, entity_id, games_root=root),
        lambda game, entity_id, root: load_card(game, entity_id, games_root=root),
        lambda game, root: load_card_repository(game, games_root=root),
    )


def _printing_definition() -> EntityPromotionDefinition:
    return EntityPromotionDefinition(
        "printing", "printing",
        lambda game, entity_id, root: printing_record_path(game, entity_id, games_root=root),
        lambda game, entity_id, root: load_printing(game, entity_id, games_root=root),
        lambda game, root: load_card_repository(game, games_root=root),
    )


class CandidatePromotionService:
    """Review candidates through registered entity-specific repository boundaries."""

    def __init__(
        self, *, game: str = "magic", games_root: Path | None = None,
        audit_root: Path | None = None,
        definitions: tuple[EntityPromotionDefinition, ...] | None = None,
    ) -> None:
        self._game = game
        self._games_root = Path(games_root) if games_root else _PROJECT_ROOT / "data/canonical/games"
        self._audit_root = Path(audit_root) if audit_root else _PROJECT_ROOT / "data/audit/promotions"
        enabled = definitions if definitions is not None else (_card_definition(), _printing_definition())
        self._definitions = {definition.entity_type: definition for definition in enabled}
        if len(self._definitions) != len(enabled):
            raise ValueError("entity promotion definitions must be unique")
        if self._audit_root.resolve().is_relative_to(self._games_root.resolve()):
            raise ValueError("audit history must be stored outside canonical data")

    def review(self, artifact: Mapping[str, Any], parsed: Mapping[str, Any], candidate_id: str,
               review: CandidateReview) -> Mapping[str, Any]:
        candidate, definition = self._eligible_candidate(artifact, parsed, candidate_id)
        entity_id = self._entity_id(candidate, definition.entity_type)
        action = "promotion" if review.decision is ReviewDecision.APPROVED else "rejection"
        audit_id = self._audit_id(definition.entity_type, action, artifact["id"], candidate_id, review)
        existing = self._load_audit_if_present(audit_id)
        if existing is not None:
            if existing["candidate_snapshot"] != candidate:
                raise PromotionConflict("Audit identity was reused for different candidate content")
            return existing
        path = definition.canonical_path(self._game, entity_id, self._games_root)
        before = self._load_canonical_if_present(path, definition)
        if review.decision is ReviewDecision.REJECTED:
            return self._store_audit(self._event(audit_id, action, artifact, candidate, definition,
                                                 review, "rejected", before, before))

        payload = deepcopy(candidate["payload"])
        created = before is None
        if created:
            self._validate_new(payload, entity_id, definition)
            self._create_canonical(path, payload, definition)
            try:
                definition.validate_canonical(self._game, entity_id, self._games_root)
                if definition.entity_type == "printing":
                    load_card(self._game, payload["card_id"], games_root=self._games_root)
            except Exception as error:
                path.unlink(missing_ok=True)
                raise PromotionValidationError(
                    f"New canonical {definition.entity_type} failed repository validation: {error}"
                ) from error
            after, outcome = payload, "promoted"
        else:
            conflicts = {key for key, value in payload.items() if before.get(key) != value}
            if conflicts:
                raise PromotionConflict(
                    f"Candidate conflicts with canonical {definition.entity_type} fields: "
                    f"{', '.join(sorted(conflicts))}"
                )
            after, outcome = before, "confirmed"
        event = self._event(audit_id, action, artifact, candidate, definition, review, outcome, before, after)
        try:
            return self._store_audit(event)
        except (AuditStorageError, SchemaValidationError):
            if created and self._load_canonical_if_present(path, definition) == payload:
                path.unlink()
            raise

    def rollback(self, promotion_audit_id: str, review: CandidateReview) -> Mapping[str, Any]:
        if review.decision is not ReviewDecision.APPROVED:
            raise PromotionValidationError("Rollback requires explicit approval")
        promotion = self._load_audit(promotion_audit_id)
        if promotion["action"] != "promotion":
            raise PromotionValidationError("Only promotion audit events can be rolled back")
        definition = self._definition(promotion["entity_type"])
        rollback_id = self._audit_id(definition.entity_type, "rollback", promotion_audit_id,
                                     promotion["candidate_id"], review)
        existing = self._load_audit_if_present(rollback_id)
        if existing is not None:
            return existing
        path = definition.canonical_path(self._game, promotion["entity_id"], self._games_root)
        current = self._load_canonical_if_present(path, definition)
        if current != promotion["canonical_after"]:
            raise PromotionConflict(f"Canonical {definition.entity_type} changed after promotion; rollback refused")
        before = promotion["canonical_before"]
        event = self._event(rollback_id, "rollback", {"id": promotion["candidate_artifact_id"]},
                            promotion["candidate_snapshot"], definition, review, "rolled_back", current, before)
        event["related_audit_id"] = promotion_audit_id
        if before is None:
            path.unlink(missing_ok=True)
        else:
            self._replace_canonical(path, before, definition)
        try:
            definition.validate_repository(self._game, self._games_root)
            return self._store_audit(event)
        except Exception as error:
            if promotion["canonical_after"] is not None:
                self._replace_canonical(path, promotion["canonical_after"], definition)
            if isinstance(error, (AuditStorageError, SchemaValidationError)):
                raise
            raise PromotionConflict(
                f"Rollback would invalidate the canonical {definition.entity_type} repository"
            ) from error

    def _eligible_candidate(self, artifact: Mapping[str, Any], parsed: Mapping[str, Any],
                            candidate_id: str) -> tuple[Mapping[str, Any], EntityPromotionDefinition]:
        if validate_candidate_artifact(artifact, parsed).state is not CandidateValidationState.VALID:
            raise PromotionValidationError("Candidate artifact failed cross-artifact validation")
        matches = [item for item in artifact["candidates"] if item["id"] == candidate_id]
        if len(matches) != 1:
            raise PromotionValidationError("Candidate identifier is missing or ambiguous")
        candidate = matches[0]
        if candidate["validation_state"] != CandidateValidationState.VALID.value:
            raise PromotionValidationError("Candidate must have validation_state 'valid'")
        entity_type = candidate["entity_type"]
        if artifact["candidate_type"] != entity_type:
            raise PromotionValidationError("Artifact and candidate entity types must match")
        definition = self._definition(entity_type)
        payload_fields = set(candidate["payload"])
        provenance_fields = {item["field_path"] for item in candidate["field_provenance"]}
        if not payload_fields.issubset(provenance_fields):
            raise PromotionValidationError(f"Every promoted {entity_type} field requires field provenance")
        if payload_fields == {"id"}:
            raise PromotionValidationError(f"{entity_type.title()} candidate must propose more than an id")
        return candidate, definition

    def _definition(self, entity_type: str) -> EntityPromotionDefinition:
        try:
            return self._definitions[entity_type]
        except KeyError as error:
            raise PromotionValidationError(f"Entity type is not enabled for promotion: {entity_type}") from error

    @staticmethod
    def _entity_id(candidate: Mapping[str, Any], entity_type: str) -> str:
        entity_id = candidate["payload"].get("id")
        if not isinstance(entity_id, str) or not _IDENTIFIER.fullmatch(entity_id):
            raise PromotionValidationError(f"{entity_type.title()} candidate requires a stable payload id")
        return entity_id

    def _validate_new(self, payload: Mapping[str, Any], entity_id: str,
                      definition: EntityPromotionDefinition) -> None:
        try:
            validate_document(payload, definition.schema_name)
        except SchemaValidationError as error:
            raise PromotionValidationError(
                f"A new canonical {definition.entity_type} requires a complete schema-valid payload"
            ) from error
        if payload["id"] != entity_id or payload.get("game", self._game) != self._game:
            raise PromotionValidationError("Payload identifiers do not match its canonical path")

    def _event(self, audit_id: str, action: str, artifact: Mapping[str, Any],
               candidate: Mapping[str, Any], definition: EntityPromotionDefinition,
               review: CandidateReview, outcome: str, before: Mapping[str, Any] | None,
               after: Mapping[str, Any] | None) -> dict[str, Any]:
        event = {"schema_version": "v1", "id": audit_id, "action": action,
                 "entity_type": definition.entity_type,
                 "entity_id": self._entity_id(candidate, definition.entity_type),
                 "candidate_artifact_id": artifact["id"], "candidate_id": candidate["id"],
                 "actor": review.actor, "decided_at": review.decided_at,
                 "decision": review.decision.value, "outcome": outcome,
                 "candidate_snapshot": deepcopy(candidate), "canonical_before": deepcopy(before),
                 "canonical_after": deepcopy(after)}
        if review.reason is not None:
            event["reason"] = review.reason
        return event

    @staticmethod
    def _audit_id(entity_type: str, action: str, source_id: str, candidate_id: str,
                  review: CandidateReview) -> str:
        identity = json.dumps({"entity_type": entity_type, "action": action, "source_id": source_id,
                               "candidate_id": candidate_id, "actor": review.actor,
                               "decided_at": review.decided_at, "decision": review.decision.value,
                               "reason": review.reason}, sort_keys=True, separators=(",", ":")).encode()
        return f"{entity_type}-{action}-{hash_bytes(identity)[:24]}"

    def _audit_path(self, audit_id: str) -> Path:
        if not _IDENTIFIER.fullmatch(audit_id):
            raise AuditStorageError("Invalid audit identifier")
        return self._audit_root.resolve() / f"{audit_id}.json"

    def _store_audit(self, event: Mapping[str, Any]) -> Mapping[str, Any]:
        validate_document(event, "promotion-audit")
        path = self._audit_path(event["id"]); path.parent.mkdir(parents=True, exist_ok=True)
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
            with os.fdopen(descriptor, "wb") as output: output.write(content)
        except OSError as error:
            path.unlink(missing_ok=True); raise AuditStorageError("Unable to write permanent audit event") from error
        return deepcopy(event)

    def _load_audit_if_present(self, audit_id: str) -> Mapping[str, Any] | None:
        return self._load_audit(audit_id) if self._audit_path(audit_id).exists() else None

    def _load_audit(self, audit_id: str) -> Mapping[str, Any]:
        try:
            document = json.loads(self._audit_path(audit_id).read_text())
            validate_document(document, "promotion-audit")
            return document
        except (OSError, json.JSONDecodeError, SchemaValidationError) as error:
            raise AuditStorageError(f"Cannot load valid audit event: {audit_id}") from error

    @staticmethod
    def _load_canonical_if_present(path: Path, definition: EntityPromotionDefinition) -> Mapping[str, Any] | None:
        if not path.exists(): return None
        try:
            document = json.loads(path.read_text()); validate_document(document, definition.schema_name); return document
        except (OSError, json.JSONDecodeError, SchemaValidationError) as error:
            raise PromotionConflict(f"Existing canonical {definition.entity_type} is unreadable or invalid") from error

    @staticmethod
    def _create_canonical(path: Path, document: Mapping[str, Any], definition: EntityPromotionDefinition) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try: descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error: raise PromotionConflict(f"Canonical {definition.entity_type} appeared during promotion") from error
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(document, output, sort_keys=True, indent=2, ensure_ascii=False); output.write("\n")
        except OSError as error:
            path.unlink(missing_ok=True); raise PromotionError(f"Unable to write canonical {definition.entity_type}") from error

    @staticmethod
    def _replace_canonical(path: Path, document: Mapping[str, Any], definition: EntityPromotionDefinition) -> None:
        validate_document(document, definition.schema_name)
        descriptor, temporary = tempfile.mkstemp(prefix=".rollback-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as output:
                json.dump(document, output, sort_keys=True, indent=2, ensure_ascii=False); output.write("\n")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary): os.unlink(temporary)


class ProductPromotionService(CandidatePromotionService):
    """Compatibility facade retaining the existing controlled Product workflow."""

    def __init__(self, *, games_root: Path | None = None, audit_root: Path | None = None) -> None:
        definition = EntityPromotionDefinition(
            "product", "product",
            lambda game, entity_id, root: product_record_path(game, entity_id, games_root=root),
            lambda game, entity_id, root: None,
        )
        super().__init__(games_root=games_root, audit_root=audit_root, definitions=(definition,))


__all__ = ["AuditStorageError", "CandidatePromotionService", "CandidateReview",
           "EntityPromotionDefinition", "ProductPromotionService", "ProductReview",
           "PromotionConflict", "PromotionError", "PromotionValidationError", "ReviewDecision"]
