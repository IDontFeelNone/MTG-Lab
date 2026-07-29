"""JSON Schema validation for versioned canonical records."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any, Mapping

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import ValidationError

from schemas import schema_path


class SchemaValidationError(ValueError):
    """Raised when a document does not satisfy its canonical schema."""


@lru_cache(maxsize=None)
def load_schema(schema_name: str, version: str = "v1") -> Mapping[str, Any]:
    """Load an immutable-by-convention schema document from the packaged registry."""
    with schema_path(schema_name, version).open(encoding="utf-8") as schema_file:
        return json.load(schema_file)


def validate_document(
    document: Mapping[str, Any], schema_name: str, version: str = "v1"
) -> None:
    """Validate one canonical document or raise a concise domain error."""
    validator = Draft202012Validator(load_schema(schema_name, version), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path))
    if not errors:
        return

    first_error: ValidationError = errors[0]
    location = ".".join(str(part) for part in first_error.absolute_path) or "<root>"
    raise SchemaValidationError(f"{schema_name} validation failed at {location}: {first_error.message}")


__all__ = ["SchemaValidationError", "load_schema", "validate_document"]
