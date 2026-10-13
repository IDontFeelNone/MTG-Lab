"""Source-bound personal Card review history owned by the Collection layer.

Records describe a user's review state. They neither admit knowledge facts nor
change ownership, approve functional roles, or execute a reassessment.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping

from card_intelligence.models import Evidence
from reasoning.models import freeze, thaw
from .intelligence import CanonicalCollectionResolver, _normalize_row, canonical_json, digest, read_import


ASSESSMENT_VERSION = "collection-assessment-v1"
STATUSES = frozenset({"reviewed", "pending", "unresolved", "reassessment_needed"})
_HASH = re.compile(r"^[0-9a-f]{64}$")
_IDENTITY = re.compile(r"^sha256:[0-9a-f]{64}$")
_FIELDS = frozenset({"schema_version", "assessment_id", "collection_id", "card_id", "purpose",
    "status", "outcome", "reason", "assessed_at", "recorded_at", "assessment_version",
    "prior_assessment_id", "supersedes", "manual_reassessment_trigger", "human_review",
    "snapshot_binding", "evidence_references", "source"})


class CollectionAssessmentError(ValueError):
    """An assessment lacks a valid source, subject, or history binding."""


def assessment_inventory_compatible(record: Mapping[str, Any], *, source: Mapping[str, Any]) -> bool:
    """A mock claim is operative only for an explicitly fictional inventory.

    This applies independently of caller trust: trust can establish a retained
    human approval, but cannot make synthetic evidence an actual personal review.
    """
    if record["human_review"]["kind"] != "synthetic_mock":
        return True
    if not isinstance(source, Mapping):
        return False
    if any(source.get(name) is not None and not isinstance(source[name], str)
           for name in ("type", "mode", "notice")):
        return False
    synthetic = source.get("synthetic")
    real = source.get("real_user_inventory")
    if any(value is not None and type(value) is not bool for value in (synthetic, real)):
        return False
    declared_synthetic = source.get("mode") == "synthetic_demonstration" or \
        source.get("type") in ("synthetic", "synthetic_fixture")
    return real is not True and (synthetic is True or synthetic is None and declared_synthetic)


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CollectionAssessmentError(f"{label} must be nonempty text")
    return value


def _time(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z", value):
        raise CollectionAssessmentError(f"{label} must be a UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise CollectionAssessmentError(f"invalid {label}") from error
    return parsed


def _identity(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _IDENTITY.fullmatch(value):
        raise CollectionAssessmentError(f"invalid {label}")
    return value


def _bound_path(root: Path, relative: Any) -> Path:
    _text(relative, "source relative_path")
    fragment = Path(relative)
    if fragment.is_absolute() or ".." in fragment.parts:
        raise CollectionAssessmentError("source path must stay below source_root")
    path = (Path(root) / fragment).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise CollectionAssessmentError("source path escapes source_root")
    return path


def _pointer(document: Any, pointer: Any) -> Any:
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise CollectionAssessmentError("source requires an exact JSON pointer")
    value = document
    try:
        for segment in pointer[1:].split("/"):
            if re.search(r"~(?![01])", segment):
                raise CollectionAssessmentError("invalid JSON pointer escape")
            key = segment.replace("~1", "/").replace("~0", "~")
            if isinstance(value, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    raise CollectionAssessmentError("invalid JSON pointer array index")
                value = value[int(key)]
            else:
                value = value[key]
    except (KeyError, IndexError, TypeError) as error:
        raise CollectionAssessmentError("source JSON pointer does not resolve") from error
    return value


@dataclass(frozen=True, init=False)
class CollectionAssessment:
    payload: Mapping[str, Any]
    source_root: Path
    snapshot: Mapping[str, Any]
    trusted_human_review: bool

    def __init__(self, payload: Mapping[str, Any], source_root: Path, *,
                 snapshot: Mapping[str, Any], trusted_human_review: bool = False):
        if not isinstance(payload, Mapping) or set(payload) != _FIELDS:
            raise CollectionAssessmentError("assessment has missing or unexpected fields")
        try:
            body = thaw(freeze(payload))
        except TypeError as error:
            raise CollectionAssessmentError("assessment values must be serializable immutable data") from error
        if body["schema_version"] != ASSESSMENT_VERSION:
            raise CollectionAssessmentError("unsupported assessment schema")
        identity = _identity(body["assessment_id"], "assessment_id")
        unsigned = {k: v for k, v in body.items() if k != "assessment_id"}
        if identity != "sha256:" + digest(unsigned):
            raise CollectionAssessmentError("assessment content identity mismatch")
        for field in ("collection_id", "card_id", "purpose", "reason", "assessment_version"):
            _text(body[field], field)
        if body["assessment_version"].strip().casefold() in {"unknown", "null"}:
            raise CollectionAssessmentError("assessment_version must identify the reviewed method")
        if not isinstance(body["status"], str) or body["status"] not in STATUSES:
            raise CollectionAssessmentError("unsupported assessment status")
        if body["outcome"] is not None:
            _text(body["outcome"], "outcome")
        assessed = _time(body["assessed_at"], "assessed_at")
        recorded = _time(body["recorded_at"], "recorded_at")
        if assessed > recorded:
            raise CollectionAssessmentError("assessment cannot follow recorded time")
        prior = body["prior_assessment_id"]
        if prior is not None:
            _identity(prior, "prior_assessment_id")
        if not isinstance(body["supersedes"], list) or body["supersedes"] != ([] if prior is None else [prior]):
            raise CollectionAssessmentError("supersedes must name exactly the prior assessment")
        if prior == identity:
            raise CollectionAssessmentError("assessment cannot supersede itself")
        trigger = body["manual_reassessment_trigger"]
        if body["status"] == "reassessment_needed":
            _text(trigger, "manual_reassessment_trigger")
            if prior is None:
                raise CollectionAssessmentError("manual reassessment requires a prior assessment")
        elif trigger is not None:
            raise CollectionAssessmentError("manual trigger requires reassessment_needed status")
        self._review(body, trusted_human_review)
        self._snapshot(body, snapshot, source_root)
        evidence = body["evidence_references"]
        if not isinstance(evidence, list) or not evidence:
            raise CollectionAssessmentError("assessment requires evidence references")
        keys = []
        for reference in evidence:
            if not isinstance(reference, dict) or set(reference) != {"source_id", "source_type", "reference", "observed_at", "claim"}:
                raise CollectionAssessmentError("invalid assessment evidence reference")
            try:
                item = Evidence(**{**reference, "observed_at": _time(reference["observed_at"], "evidence observed_at")})
            except (TypeError, ValueError) as error:
                raise CollectionAssessmentError("invalid assessment evidence reference") from error
            if item.observed_at > recorded:
                raise CollectionAssessmentError("evidence cannot follow recorded time")
            keys.append((item.source_id, item.reference, item.observed_at))
        if len(keys) != len(set(keys)):
            raise CollectionAssessmentError("duplicate assessment evidence reference")
        source = body["source"]
        if not isinstance(source, dict) or set(source) != {"relative_path", "sha256", "json_pointer"}:
            raise CollectionAssessmentError("invalid assessment source binding")
        if not isinstance(source["sha256"], str) or not _HASH.fullmatch(source["sha256"]):
            raise CollectionAssessmentError("invalid source SHA-256")
        try:
            raw = _bound_path(source_root, source["relative_path"]).read_bytes()
            source_document = json.loads(raw)
        except (OSError, ValueError) as error:
            raise CollectionAssessmentError("retained assessment source is unavailable or malformed") from error
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise CollectionAssessmentError("retained assessment source digest mismatch")
        if isinstance(source_document, dict) and "captured_at" in source_document and \
                _time(source_document["captured_at"], "source captured_at") > recorded:
            raise CollectionAssessmentError("source capture cannot follow recorded time")
        if body["human_review"]["kind"] == "synthetic_mock" and (
                not isinstance(source_document, dict) or source_document.get("synthetic") is not True):
            raise CollectionAssessmentError("mocked review requires an explicitly synthetic source")
        if not assessment_inventory_compatible(body, source=snapshot.get("source", {})):
            raise CollectionAssessmentError("mocked review requires an explicitly synthetic inventory")
        if body["human_review"]["approved"] and isinstance(source_document, dict) and source_document.get("synthetic") is True:
            raise CollectionAssessmentError("synthetic source cannot establish actual human approval")
        claim = {k: v for k, v in body.items() if k not in {"schema_version", "assessment_id", "source"}}
        if canonical_json(_pointer(source_document, source["json_pointer"])) != canonical_json(claim):
            raise CollectionAssessmentError("assessment does not match its exact retained claim")
        object.__setattr__(self, "payload", freeze(body))
        object.__setattr__(self, "source_root", Path(source_root))
        object.__setattr__(self, "snapshot", freeze(snapshot))
        object.__setattr__(self, "trusted_human_review", trusted_human_review)

    @staticmethod
    def _review(body: dict, trusted: bool) -> None:
        review = body["human_review"]
        if type(trusted) is not bool or not isinstance(review, dict) or set(review) != {"kind", "approved", "reviewer", "review_reference"}:
            raise CollectionAssessmentError("invalid human review boundary")
        if type(review["approved"]) is not bool or not isinstance(review["kind"], str) or \
                review["kind"] not in {"human", "synthetic_mock", "not_applicable"}:
            raise CollectionAssessmentError("invalid human review state")
        for field in ("reviewer", "review_reference"):
            if review[field] is not None:
                _text(review[field], field)
        if review["kind"] != "human" and review["approved"]:
            raise CollectionAssessmentError("synthetic or absent review is not human approval")
        if review["approved"]:
            if not trusted:
                raise CollectionAssessmentError("human approval requires a trusted review caller")
            _text(review["reviewer"], "reviewer")
            _text(review["review_reference"], "review_reference")
            if any(review[key].strip().casefold() in {"unknown", "null"} for key in ("reviewer", "review_reference")):
                raise CollectionAssessmentError("affirmative human review requires known reviewer and reference")
        if body["status"] == "reviewed":
            _text(body["outcome"], "reviewed outcome")
            if review["kind"] != "synthetic_mock" and not review["approved"]:
                raise CollectionAssessmentError("reviewed claims require explicit human or mocked synthetic review")

    @staticmethod
    def _snapshot(body: dict, snapshot: Mapping[str, Any], source_root: Path) -> None:
        if not isinstance(snapshot, Mapping):
            raise CollectionAssessmentError("retained ownership snapshot required")
        snapshot = thaw(freeze(snapshot))
        claimed = snapshot.pop("snapshot_digest", None)
        if claimed != digest(snapshot) or snapshot.get("schema_version") != "collection-snapshot-v1":
            raise CollectionAssessmentError("ownership snapshot digest or schema mismatch")
        if snapshot.get("collection_id") != body["collection_id"]:
            raise CollectionAssessmentError("assessment belongs to another collection")
        binding = body["snapshot_binding"]
        fields = {"snapshot_id", "snapshot_digest", "source_import_digest", "canonical_snapshot_id", "resolved_printing_ids", "source_import_reference"}
        if not isinstance(binding, dict) or set(binding) != fields:
            raise CollectionAssessmentError("invalid ownership snapshot binding")
        for name in fields - {"resolved_printing_ids", "source_import_reference"}:
            _text(binding[name], name)
            expected = claimed if name == "snapshot_digest" else snapshot.get(name)
            if binding[name] != expected:
                raise CollectionAssessmentError(f"ownership snapshot {name} mismatch")
        source = binding["source_import_reference"]
        if not isinstance(source, dict) or set(source) != {"relative_path", "sha256"} or \
                not isinstance(source["sha256"], str) or not _HASH.fullmatch(source["sha256"]):
            raise CollectionAssessmentError("original ownership import reference required")
        try:
            imported = read_import(_bound_path(source_root, source["relative_path"]))
        except (OSError, ValueError) as error:
            raise CollectionAssessmentError("original ownership import is unavailable or malformed") from error
        if imported["source_import_digest"] != source["sha256"] or source["sha256"] != binding["source_import_digest"] or \
                imported["collection_id"] != body["collection_id"] or imported["source"] != snapshot.get("source"):
            raise CollectionAssessmentError("original ownership import binding mismatch")
        for field in ("resolved_holdings", "unresolved_holdings"):
            if not isinstance(snapshot.get(field), list) or any(not isinstance(x, dict) or
                    not isinstance(x.get("row"), dict) for x in snapshot[field]):
                raise CollectionAssessmentError("ownership evidence must contain explicit source rows")
        rows = [*snapshot["resolved_holdings"], *snapshot["unresolved_holdings"]]
        try:
            rows.sort(key=lambda x: x["row"]["row_number"])
            actual_rows = [{k: v for k, v in x["row"].items() if k != "_invalid"} for x in rows]
            expected_rows = [{k: v for k, v in _normalize_row(raw, number).items() if k != "_invalid"}
                             for number, raw in enumerate(imported["entries"], 1)]
            if canonical_json(actual_rows) != canonical_json(expected_rows):
                raise CollectionAssessmentError("ownership snapshot does not reproduce original import rows")
            for holding in snapshot.get("resolved_holdings", []):
                row = holding["row"]
                if holding.get("status") != "resolved" or \
                        (row.get("printing_id") is not None and row["printing_id"] != holding.get("printing_id")) or \
                        (row.get("identity_constraints", {}).get("card_id") is not None and
                         row["identity_constraints"]["card_id"] != holding.get("card_id")):
                    raise CollectionAssessmentError("resolved ownership contradicts exact source identity")
        except (KeyError, TypeError) as error:
            raise CollectionAssessmentError("malformed original ownership evidence") from error
        printings = binding["resolved_printing_ids"]
        if not isinstance(printings, list) or not printings or any(not isinstance(x, str) or not x for x in printings):
            raise CollectionAssessmentError("resolved exact Printing references required")
        holdings = [x for x in snapshot.get("resolved_holdings", []) if x.get("card_id") == body["card_id"]]
        if printings != sorted({x.get("printing_id") for x in holdings}):
            raise CollectionAssessmentError("assessment Card or Printing does not match ownership evidence")
        for holding in holdings:
            reference = holding.get("canonical_reference", {})
            if reference.get("snapshot_id") != binding["canonical_snapshot_id"] or \
                    reference.get("card", {}).get("canonical_identity") != body["card_id"] or \
                    reference.get("printing", {}).get("canonical_identity") != holding["printing_id"]:
                raise CollectionAssessmentError("exact canonical Card/Printing evidence required")

    def to_dict(self) -> dict:
        return thaw(self.payload)

    @classmethod
    def from_source(cls, source_path: Path, source_root: Path, *, snapshot: Mapping[str, Any],
                    trusted_human_review: bool = False, json_pointer: str = "/claim") -> "CollectionAssessment":
        """Bind a caller-supplied retained claim; source JSON cannot grant trust."""
        try:
            path = Path(source_path).resolve()
            relative = path.relative_to(Path(source_root).resolve()).as_posix()
            raw = _bound_path(source_root, relative).read_bytes()
            claim = _pointer(json.loads(raw), json_pointer)
        except (OSError, ValueError) as error:
            raise CollectionAssessmentError("invalid retained claim source") from error
        if not isinstance(claim, dict):
            raise CollectionAssessmentError("retained claim must be an object")
        body = {"schema_version": ASSESSMENT_VERSION, **claim,
            "source": {"relative_path": relative, "sha256": hashlib.sha256(raw).hexdigest(),
                       "json_pointer": json_pointer}}
        if set(claim) != _FIELDS - {"schema_version", "assessment_id", "source"}:
            raise CollectionAssessmentError("retained claim has missing or unexpected fields")
        body["assessment_id"] = "sha256:" + digest(body)
        return cls(body, source_root, snapshot=snapshot, trusted_human_review=trusted_human_review)

    def validate(self) -> "CollectionAssessment":
        return CollectionAssessment(self.to_dict(), self.source_root, snapshot=self.snapshot,
                                    trusted_human_review=self.trusted_human_review)


def validate_assessment_history(assessments: Iterable[CollectionAssessment]) -> tuple[CollectionAssessment, ...]:
    records = tuple(assessments)
    if any(not isinstance(x, CollectionAssessment) for x in records):
        raise CollectionAssessmentError("history requires validated CollectionAssessment records")
    documents = [x.to_dict() for x in records]
    by_id = {x["assessment_id"]: x for x in documents}
    if len(by_id) != len(documents):
        raise CollectionAssessmentError("duplicate assessment identity")
    children: dict[str, str] = {}
    roots: set[tuple[str, str, str]] = set()
    for record in documents:
        subject = (record["collection_id"], record["card_id"], record["purpose"])
        prior = record["prior_assessment_id"]
        if prior is None:
            if subject in roots:
                raise CollectionAssessmentError("conflicting assessment roots")
            roots.add(subject)
            continue
        if prior not in by_id:
            raise CollectionAssessmentError("missing prior assessment")
        old = by_id[prior]
        if subject != (old["collection_id"], old["card_id"], old["purpose"]):
            raise CollectionAssessmentError("supersession must preserve collection, Card, and purpose")
        if _time(record["recorded_at"], "recorded_at") <= _time(old["recorded_at"], "recorded_at"):
            raise CollectionAssessmentError("supersession must advance recorded time")
        if prior in children:
            raise CollectionAssessmentError("assessment history fork")
        children[prior] = record["assessment_id"]
        if record["status"] == "reassessment_needed":
            if old["status"] not in {"reviewed", "reassessment_needed"} or any(record[key] != old[key]
                    for key in ("outcome", "assessed_at", "assessment_version", "human_review")):
                raise CollectionAssessmentError("manual reassessment must preserve the prior reviewed assessment")
    # Strictly advancing recorded time also excludes cycles, without selecting a
    # latest branch or pretending a new snapshot identifies the same physical copy.
    return tuple(sorted(records, key=lambda x: (x.payload["collection_id"], x.payload["card_id"],
        x.payload["purpose"], _time(x.payload["recorded_at"], "recorded_at"), x.payload["assessment_id"])))


def assessment_review_states(assessments: Iterable[CollectionAssessment], *, collection_id: str,
                             inventory_source: Mapping[str, Any] | None = None) -> dict[str, dict]:
    history = validate_assessment_history(assessments)
    grouped: dict[str, list[dict]] = {}
    for item in history:
        record = item.to_dict()
        if record["collection_id"] == collection_id:
            grouped.setdefault(record["card_id"], []).append(record)
    result = {}
    for card_id, records in sorted(grouped.items()):
        purposes = {x["purpose"] for x in records}
        if len(purposes) != 1:
            raise CollectionAssessmentError("Card review projection requires one explicit purpose")
        operative = [x for x in records if inventory_source is None or
                     assessment_inventory_compatible(x, source=inventory_source)]
        current = operative[-1] if operative else None
        reviewed = [x for x in operative if x["status"] == "reviewed"]
        result[card_id] = {"status": current["status"] if current else "pending", "ever_reviewed": bool(reviewed),
            "assessment_id": current["assessment_id"] if current else None,
            "history_ids": [x["assessment_id"] for x in records],
            "review_basis": reviewed[-1]["human_review"]["kind"] if reviewed else None}
    return result


class CollectionAssessmentRepository:
    """Create-only Collection history; identical replay creates no new record."""

    def __init__(self, data_root: Path, source_root: Path | None = None, *, trusted_human_review: bool = False,
                 assessment_root: Path | None = None, resolver=None, game: str = "magic"):
        self.data_root = Path(data_root)
        boundary = self.data_root / "collections" / "assessments"
        self.root = Path(assessment_root) if assessment_root is not None else boundary
        if not self.root.resolve().is_relative_to(boundary.resolve()):
            raise CollectionAssessmentError("assessment repository must stay below data/collections/assessments")
        self.source_root = Path(source_root) if source_root is not None else self.data_root.parent
        self.trusted_human_review = trusted_human_review
        self._resolver = resolver
        self.game = game

    def _verify_snapshot_source(self, document: dict, snapshot: dict) -> dict:
        # Reuse the same read-only reconstruction boundary as audit consumers.
        # A self-consistent snapshot cannot establish canonical Card membership.
        from .audit import CollectionAudit
        if self._resolver is None:
            self._resolver = CanonicalCollectionResolver(self.game, self.data_root)
        try:
            return CollectionAudit(self._resolver).verify_source_snapshot(snapshot,
                source_path=document["snapshot_binding"]["source_import_reference"]["relative_path"],
                source_root=self.source_root)
        except (OSError, ValueError) as error:
            raise CollectionAssessmentError("original ownership snapshot does not replay against canonical state") from error

    def _path(self, assessment: CollectionAssessment) -> Path:
        return self.root / f"{assessment.payload['assessment_id'].removeprefix('sha256:')}.json"

    def load(self, path: Path) -> CollectionAssessment:
        try:
            raw = Path(path).read_bytes()
            document = json.loads(raw)
            snapshot_id = document["snapshot_binding"]["snapshot_id"]
            if not isinstance(snapshot_id, str) or not re.fullmatch(r"[a-zA-Z0-9._:-]+", snapshot_id):
                raise CollectionAssessmentError("invalid referenced snapshot identity")
            snapshot = json.loads((self.data_root / "collections" / "snapshots" / f"{snapshot_id}.json").read_bytes())
            snapshot = self._verify_snapshot_source(document, snapshot)
            assessment = CollectionAssessment(document, self.source_root, snapshot=snapshot,
                trusted_human_review=self.trusted_human_review)
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise CollectionAssessmentError(f"invalid retained assessment: {path}") from error
        if Path(path).resolve() != self._path(assessment).resolve() or raw != canonical_json(assessment.to_dict()):
            raise CollectionAssessmentError("assessment path or canonical bytes mismatch")
        return assessment

    def all(self) -> tuple[CollectionAssessment, ...]:
        return validate_assessment_history(self.load(path) for path in sorted(self.root.glob("*.json")))

    def for_collection(self, collection_id: str) -> tuple[CollectionAssessment, ...]:
        """Scope a projection only after verifying every retained source and chain."""
        _text(collection_id, "collection_id")
        history = self.all()
        return tuple(x for x in history if x.payload["collection_id"] == collection_id)

    def append(self, assessment: CollectionAssessment) -> Path:
        if not isinstance(assessment, CollectionAssessment):
            raise CollectionAssessmentError("only CollectionAssessment records may be appended")
        assessment.validate()
        path = self._path(assessment)
        content = canonical_json(assessment.to_dict())
        path.parent.mkdir(parents=True, exist_ok=True)
        lock = self.root / ".append.lock"
        try:
            lock_descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise CollectionAssessmentError("concurrent assessment append is blocked") from error
        os.close(lock_descriptor)
        try:
            existing = self.all()
            if path.exists():
                if path.read_bytes() != content:
                    raise CollectionAssessmentError("assessment identity has conflicting bytes")
                return path
            document = assessment.to_dict()
            snapshot_id = document["snapshot_binding"]["snapshot_id"]
            if not re.fullmatch(r"[a-zA-Z0-9._:-]+", snapshot_id):
                raise CollectionAssessmentError("invalid referenced snapshot identity")
            try:
                retained = json.loads((self.data_root / "collections" / "snapshots" / f"{snapshot_id}.json").read_bytes())
            except (OSError, ValueError) as error:
                raise CollectionAssessmentError("original ownership snapshot is not retained") from error
            retained = self._verify_snapshot_source(document, retained)
            CollectionAssessment(document, self.source_root, snapshot=retained,
                                 trusted_human_review=self.trusted_human_review)
            validate_assessment_history((*existing, assessment))
            try:
                descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            except FileExistsError as error:
                raise CollectionAssessmentError("assessment identity already exists") from error
            try:
                with os.fdopen(descriptor, "wb") as stream:
                    stream.write(content)
            except BaseException:
                path.unlink(missing_ok=True)
                raise
        finally:
            lock.unlink(missing_ok=True)
        return path
