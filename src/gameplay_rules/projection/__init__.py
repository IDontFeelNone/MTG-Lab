"""Review-only foundational CR projection, independent of executable snapshots.

No projection in this package can be passed to the fictional gameplay engine.
Source-aware construction requires the exact externally supplied artifact.
"""

from .contracts import FoundationalProjection
from .package import load_projection_package
from .source import build_projection, verify_projection_source

__all__ = ["FoundationalProjection", "build_projection", "verify_projection_source",
           "load_projection_package"]
