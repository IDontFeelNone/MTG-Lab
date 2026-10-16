"""Non-admissible, metadata-only Gameplay Rules source review.

Importing this module does not retrieve sources, select a release or activate
real gameplay rules. The fictional gameplay kernel does not depend on it.
"""
from .contracts import (SourceReference, ReleaseCandidate, SourceReview,
                        EvidenceIndex, VersionSelection)
from .selection import select_version

__all__ = ["SourceReference", "ReleaseCandidate", "SourceReview", "EvidenceIndex",
           "VersionSelection", "select_version"]
