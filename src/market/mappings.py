"""Provider-independent external identifier mappings and deterministic storage."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping

from .models import MarketValidationError, _immutable, mutable_metadata, validate_identifier


MAPPING_STATUSES = frozenset({"active", "pending", "rejected", "retired"})


def _optional_text(value: Any, label: str) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    if not result or any(character in result for character in "\r\n\0"):
        raise MarketValidationError(f"{label} must be non-empty single-line text")
    return result


@dataclass(frozen=True)
class ExternalIdentifierMapping:
    """Reviewed association between one canonical printing and provider identity."""

    canonical_printing_id: str
    provider_name: str
    provider_product_id: str
    provider_sku_id: str | None = None
    finish: str | None = None
    language: str | None = None
    mapping_status: str = "pending"
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "canonical_printing_id",
                           validate_identifier(self.canonical_printing_id,
                                               "canonical_printing_id"))
        object.__setattr__(self, "provider_name",
                           validate_identifier(self.provider_name, "provider_name"))
        object.__setattr__(self, "provider_product_id",
                           _optional_text(self.provider_product_id, "provider_product_id"))
        object.__setattr__(self, "provider_sku_id",
                           _optional_text(self.provider_sku_id, "provider_sku_id"))
        finish = _optional_text(self.finish, "finish")
        language = _optional_text(self.language, "language")
        object.__setattr__(self, "finish", finish.lower() if finish else None)
        object.__setattr__(self, "language", language.lower() if language else None)
        status = str(self.mapping_status).strip().lower()
        if status not in MAPPING_STATUSES:
            raise MarketValidationError(
                f"mapping_status must be one of: {', '.join(sorted(MAPPING_STATUSES))}")
        object.__setattr__(self, "mapping_status", status)
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise MarketValidationError("mapping provenance must be a non-empty object")
        object.__setattr__(self, "provenance", _immutable(self.provenance))

    @property
    def identity(self) -> tuple[str, str, str | None, str | None]:
        return (self.provider_name, self.canonical_printing_id, self.finish, self.language)

    def to_dict(self) -> dict[str, Any]:
        return {
            "canonical_printing_id": self.canonical_printing_id,
            "provider_name": self.provider_name,
            "provider_product_id": self.provider_product_id,
            "provider_sku_id": self.provider_sku_id,
            "finish": self.finish,
            "language": self.language,
            "mapping_status": self.mapping_status,
            "provenance": mutable_metadata(self.provenance),
        }


@dataclass(frozen=True)
class MappingSet:
    """Versioned, immutable collection suitable for reproducible imports."""

    version: str
    mappings: tuple[ExternalIdentifierMapping, ...]
    provenance: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(self, "version", validate_identifier(self.version, "version"))
        records = tuple(self.mappings)
        if any(not isinstance(item, ExternalIdentifierMapping) for item in records):
            raise MarketValidationError("mappings must contain ExternalIdentifierMapping values")
        identities = [item.identity for item in records]
        if len(identities) != len(set(identities)):
            raise MarketValidationError("mapping set contains duplicate mapping identities")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise MarketValidationError("mapping set provenance must be a non-empty object")
        object.__setattr__(self, "mappings", tuple(sorted(
            records, key=lambda item: tuple(value or "" for value in item.identity))))
        object.__setattr__(self, "provenance", _immutable(self.provenance))

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": "external-market-mappings-v1", "version": self.version,
                "provenance": mutable_metadata(self.provenance),
                "mappings": [item.to_dict() for item in self.mappings]}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "MappingSet":
        try:
            if data.get("schema_version") != "external-market-mappings-v1":
                raise MarketValidationError("unsupported external mapping schema")
            mappings = tuple(ExternalIdentifierMapping(**item) for item in data["mappings"])
            return cls(str(data["version"]), mappings, data["provenance"])
        except (KeyError, TypeError, AttributeError) as error:
            raise MarketValidationError("invalid external mapping document") from error


class ExternalMappingRepository:
    """Loads and resolves immutable mapping-set versions without network access."""

    def __init__(self, root: Path, canonical_repository=None):
        self.root = Path(root)
        self.canonical_repository = canonical_repository

    def import_document(self, document: Mapping[str, Any] | str | bytes) -> Path:
        """Validate then append a canonical JSON version; existing versions never change."""
        try:
            data = json.loads(document) if isinstance(document, (str, bytes)) else document
        except json.JSONDecodeError as error:
            raise MarketValidationError("invalid external mapping JSON") from error
        mapping_set = MappingSet.from_dict(data)
        self._validate_canonical_ids(mapping_set.mappings)
        providers = {item.provider_name for item in mapping_set.mappings}
        if len(providers) != 1:
            raise MarketValidationError("a mapping set must contain exactly one provider")
        provider = next(iter(providers))
        path = self.root / provider / f"{mapping_set.version}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(mapping_set.to_dict(), indent=2, sort_keys=True) + "\n"
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError as error:
            raise MarketValidationError(
                f"mapping version already exists: {provider}/{mapping_set.version}") from error
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
        return path

    def load(self, provider: str, version: str) -> MappingSet:
        provider = validate_identifier(provider, "provider")
        version = validate_identifier(version, "version")
        path = self.root / provider / f"{version}.json"
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise MarketValidationError(f"cannot load mapping set: {provider}/{version}") from error
        mapping_set = MappingSet.from_dict(data)
        if mapping_set.version != version or any(
                item.provider_name != provider for item in mapping_set.mappings):
            raise MarketValidationError("mapping content does not match repository path")
        self._validate_canonical_ids(mapping_set.mappings)
        return mapping_set

    def versions(self, provider: str) -> tuple[str, ...]:
        provider = validate_identifier(provider, "provider")
        return tuple(path.stem for path in sorted((self.root / provider).glob("*.json")))

    def resolve(self, canonical_printing_id: str, provider: str, *, version: str,
                finish: str | None = None,
                language: str | None = None) -> ExternalIdentifierMapping:
        canonical_printing_id = validate_identifier(canonical_printing_id,
                                                     "canonical_printing_id")
        finish = finish.strip().lower() if finish else None
        language = language.strip().lower() if language else None
        matches = [item for item in self.load(provider, version).mappings
                   if item.canonical_printing_id == canonical_printing_id
                   and item.mapping_status == "active"
                   and item.finish == finish and item.language == language]
        if not matches:
            raise MarketValidationError("no exact active external mapping")
        if len(matches) != 1:
            raise MarketValidationError("external mapping is ambiguous")
        return matches[0]

    def validate(self, provider: str, version: str) -> tuple[str, ...]:
        mapping_set = self.load(provider, version)
        return tuple(f"{item.canonical_printing_id}: mapping is {item.mapping_status}"
                     for item in mapping_set.mappings if item.mapping_status != "active")

    def _validate_canonical_ids(self, mappings: Iterable[ExternalIdentifierMapping]) -> None:
        if self.canonical_repository is None:
            return
        for item in mappings:
            try:
                self.canonical_repository.get_printing(item.canonical_printing_id)
            except KeyError as error:
                raise MarketValidationError(
                    f"unknown canonical printing: {item.canonical_printing_id}") from error
