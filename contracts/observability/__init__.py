"""Observability contracts — cross-module DTOs for health and metrics."""

from contracts.observability.health_result import HealthResult
from contracts.observability.metrics import MetricsData

__all__ = ["HealthResult", "MetricsData"]
