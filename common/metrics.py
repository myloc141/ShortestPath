"""Proxy module for common/metrics.py to preserve backward compatibility for WS4 and WS5."""

from WS.common.metrics import (
    mean_squared_error,
    root_mean_squared_error,
    mean_absolute_error,
    mean_absolute_percentage_error,
    evaluate_all,
)

__all__ = [
    "mean_squared_error",
    "root_mean_squared_error",
    "mean_absolute_error",
    "mean_absolute_percentage_error",
    "evaluate_all",
]
