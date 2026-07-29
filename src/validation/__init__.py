"""Validation services for canonical MTG Lab datasets."""

from .json_schema import SchemaValidationError, validate_document

__all__ = ["SchemaValidationError", "validate_document"]
