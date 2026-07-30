"""Provider-agnostic external dataset ingestion boundary."""

from .framework import (
    AdapterRegistry,
    DatasetManifest,
    ExternalDatasetError,
    ExternalDatasetIngestor,
)
from .mtgjson import MTGJSONAdapter, detect_mtgjson, generate_manifest

__all__ = ["AdapterRegistry", "DatasetManifest", "ExternalDatasetError", "ExternalDatasetIngestor",
           "MTGJSONAdapter", "detect_mtgjson", "generate_manifest"]
