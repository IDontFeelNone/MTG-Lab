"""Source-agnostic, non-canonical raw data acquisition framework."""

from .framework import (
    AcquisitionEngine, AcquisitionError, AcquisitionProvider, FixtureProvider,
    ProviderRequest, ProviderResponse, ProviderTrustPolicy, RawSnapshotStore,
    SnapshotRef, assertions_from_normalized, compare_assertions, normalize_snapshot,
)
from .knowledge import (ProviderPolicy, build_review_package, dataset_identity,
                        generate_reports, validate_pipeline, validate_review_package, write_json)
from .promotion import CanonicalPromotionEngine, PromotionDecision, PromotionError

__all__ = [
    "AcquisitionEngine", "AcquisitionError", "AcquisitionProvider", "FixtureProvider",
    "ProviderRequest", "ProviderResponse", "ProviderTrustPolicy", "RawSnapshotStore",
    "SnapshotRef", "assertions_from_normalized", "compare_assertions", "normalize_snapshot",
    "ProviderPolicy", "build_review_package", "dataset_identity", "generate_reports",
    "validate_pipeline", "validate_review_package", "write_json",
    "CanonicalPromotionEngine", "PromotionDecision", "PromotionError",
]
