"""Provider interface and deterministic provider registry."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple

from .contracts import AcquisitionRequest, EvidenceArtifact, EvidenceDataset, EvidenceProvider


@dataclass(frozen=True)
class ProviderCapabilities:
    artifact_registration: bool = True
    dataset_registration: bool = True
    acquisition_planning: bool = True
    artifact_validation: bool = True
    dataset_validation: bool = True


class EvidenceProviderAdapter(ABC):
    @abstractmethod
    def metadata(self) -> EvidenceProvider: ...

    @abstractmethod
    def capabilities(self) -> ProviderCapabilities: ...

    @abstractmethod
    def register_artifact(self, artifact: EvidenceArtifact) -> EvidenceArtifact: ...

    @abstractmethod
    def register_dataset(self, dataset: EvidenceDataset) -> EvidenceDataset: ...

    @abstractmethod
    def plan(self, request: AcquisitionRequest) -> Tuple[str, ...]: ...

    @abstractmethod
    def validate_artifact(self, artifact: EvidenceArtifact) -> Tuple[str, ...]: ...

    @abstractmethod
    def validate_dataset(self, dataset: EvidenceDataset) -> Tuple[str, ...]: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, EvidenceProviderAdapter] = {}

    def register(self, provider: EvidenceProviderAdapter) -> None:
        identifier = provider.metadata().provider_identifier
        if identifier in self._providers:
            raise ValueError(f"duplicate provider identifier: {identifier}")
        if not provider.metadata().licensing.is_supported():
            raise ValueError(f"unsupported licensing state for provider: {identifier}")
        self._providers[identifier] = provider

    def get(self, identifier: str) -> EvidenceProviderAdapter:
        try:
            return self._providers[identifier]
        except KeyError as error:
            raise KeyError(f"unknown provider identifier: {identifier}") from error

    def providers(self) -> Tuple[EvidenceProviderAdapter, ...]:
        return tuple(self._providers[key] for key in sorted(self._providers))
