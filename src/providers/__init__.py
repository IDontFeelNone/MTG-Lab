"""Concrete providers for the provider-neutral evidence acquisition framework."""

from evidence import ProviderRegistry

from .mtgjson import MTGJSONProvider


def provider_registry() -> ProviderRegistry:
    """Return the explicit registry of supported evidence providers."""
    registry = ProviderRegistry()
    registry.register(MTGJSONProvider())
    return registry


__all__ = ["MTGJSONProvider", "provider_registry"]
