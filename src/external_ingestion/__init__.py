"""Provider-agnostic external dataset ingestion boundary."""

from .framework import (
    AdapterRegistry,
    DatasetManifest,
    ExternalDatasetError,
    ExternalDatasetIngestor,
)

__all__ = ["AdapterRegistry", "DatasetManifest", "ExternalDatasetError", "ExternalDatasetIngestor"]
