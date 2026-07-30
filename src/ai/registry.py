"""Explicit, deterministic AI provider registry."""
import re

from .adapter import AIModelProvider
from .errors import (DuplicateProvider, IncompatibleProviderVersion, InvalidAIRequest,
                     InvalidProvider, ProviderNotFound, UnsupportedCapability)
from .models import (AIModelRequest, AIProviderCapabilities, AIProviderMetadata,
                     SCHEMA_VERSION, SUPPORTED_CAPABILITIES, SUPPORTED_SCHEMA_VERSIONS)

IDENTIFIER = re.compile(r"^[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*$")
VERSION = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?$")


class AIProviderRegistry:
    def __init__(self): self._providers = {}

    def register(self, provider: AIModelProvider) -> None:
        if not isinstance(provider, AIModelProvider): raise InvalidProvider("provider must implement AIModelProvider")
        metadata, capabilities = provider.metadata(), provider.capabilities()
        self._validate_contracts(metadata, capabilities)
        if metadata.provider_identifier in self._providers:
            raise DuplicateProvider(f"provider already registered: {metadata.provider_identifier}")
        self._providers[metadata.provider_identifier] = provider

    def lookup(self, identifier: str, version: str | None = None) -> AIModelProvider:
        provider = self._providers.get(identifier)
        if provider is None: raise ProviderNotFound(f"provider not registered: {identifier}")
        actual = provider.metadata().provider_version
        if version is not None and version != actual:
            raise IncompatibleProviderVersion(f"provider {identifier} version {actual} is incompatible with requested {version}")
        return provider

    def providers(self): return tuple(self._providers[key].metadata() for key in sorted(self._providers))

    def capability_discovery(self, capability: str | None = None):
        entries = tuple((provider.metadata(), provider.capabilities()) for provider in
                        (self._providers[key] for key in sorted(self._providers)))
        return tuple(entry for entry in entries if capability is None or capability in entry[1].capabilities)

    def versions(self): return {item.provider_identifier: item.provider_version for item in self.providers()}

    def validate_request(self, request: AIModelRequest) -> AIModelProvider:
        if not isinstance(request, AIModelRequest): raise InvalidAIRequest("request must be AIModelRequest")
        if request.schema_version not in SUPPORTED_SCHEMA_VERSIONS: raise InvalidAIRequest("unsupported request schema version")
        for name in ("provider_identifier", "provider_version", "model_identifier", "execution_identifier"):
            if not getattr(request, name): raise InvalidAIRequest(f"missing {name}")
        if not request.reasoning_context_identifier:
            raise InvalidAIRequest("missing reasoning_context_identifier")
        if not request.reasoning_context_identifier.startswith("sha256:"):
            raise InvalidAIRequest("reasoning_context_identifier must be content-addressed")
        provider = self.lookup(request.provider_identifier, request.provider_version)
        metadata, capabilities = provider.metadata(), provider.capabilities()
        if request.model_identifier not in metadata.model_identifiers: raise InvalidAIRequest("unsupported model identifier")
        unsupported = set(request.required_capabilities) - set(capabilities.capabilities)
        if unsupported: raise UnsupportedCapability("unsupported capabilities: " + ", ".join(sorted(unsupported)))
        return provider

    @staticmethod
    def _validate_contracts(metadata, capabilities):
        if not isinstance(metadata, AIProviderMetadata) or not isinstance(capabilities, AIProviderCapabilities):
            raise InvalidProvider("provider metadata and capabilities must use AI adapter contracts")
        if metadata.schema_version != SCHEMA_VERSION or capabilities.schema_version != SCHEMA_VERSION:
            raise InvalidProvider("unsupported provider schema version")
        if not IDENTIFIER.fullmatch(metadata.provider_identifier): raise InvalidProvider("malformed provider identifier")
        if not VERSION.fullmatch(metadata.provider_version): raise InvalidProvider("malformed provider version")
        if not metadata.model_identifiers or any(not IDENTIFIER.fullmatch(value) for value in metadata.model_identifiers):
            raise InvalidProvider("provider requires valid model identifiers")
        unsupported = set(capabilities.capabilities) - SUPPORTED_CAPABILITIES
        if unsupported: raise UnsupportedCapability("unsupported capabilities: " + ", ".join(sorted(unsupported)))
