"""Acquisition-only support for approved official reference datasets."""

from .acquisition import AcquisitionError, OfficialDatasetAcquisition
from .configuration import DatasetDefinition, definitions, get_definition

__all__ = [
    "AcquisitionError", "DatasetDefinition", "OfficialDatasetAcquisition", "definitions",
    "get_definition",
]
