"""Deterministic reports derived from caller-supplied domain snapshots."""

from .models import AnalyticsReport
from .service import AnalyticsService

__all__ = ["AnalyticsReport", "AnalyticsService"]
