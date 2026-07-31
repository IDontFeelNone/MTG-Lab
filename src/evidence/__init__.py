"""Provider-neutral, non-canonical evidence acquisition framework."""

from .contracts import (
    AcquisitionMetadata, AcquisitionRequest, AcquisitionResult, EvidenceArtifact,
    EvidenceDataset, EvidenceProvider, EvidenceSource, LicensingMetadata, ReviewMetadata,
    SCHEMA_VERSION, sha256_identity,
)
from .provider import EvidenceProviderAdapter, ProviderCapabilities, ProviderRegistry
from .registry import ReferenceDatasetRegistry, RegistryValidationError

__all__ = [
    "AcquisitionMetadata", "AcquisitionRequest", "AcquisitionResult", "EvidenceArtifact",
    "EvidenceDataset", "EvidenceProvider", "EvidenceProviderAdapter", "EvidenceSource",
    "LicensingMetadata", "ProviderCapabilities", "ProviderRegistry", "ReferenceDatasetRegistry",
    "RegistryValidationError", "ReviewMetadata", "SCHEMA_VERSION", "sha256_identity",
]
