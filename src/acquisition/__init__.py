"""Source-agnostic, non-canonical raw data acquisition framework."""

from .framework import (
    AcquisitionEngine, AcquisitionError, AcquisitionProvider, FixtureProvider,
    ProviderRequest, ProviderResponse, ProviderTrustPolicy, RawSnapshotStore,
    SnapshotRef, assertions_from_normalized, compare_assertions, normalize_snapshot,
)

__all__ = [
    "AcquisitionEngine", "AcquisitionError", "AcquisitionProvider", "FixtureProvider",
    "ProviderRequest", "ProviderResponse", "ProviderTrustPolicy", "RawSnapshotStore",
    "SnapshotRef", "assertions_from_normalized", "compare_assertions", "normalize_snapshot",
]
