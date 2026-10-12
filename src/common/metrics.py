"""Dependency-free regression metrics shared by model and evaluation modules."""

from __future__ import annotations

import math
from typing import Sequence


def _paired_values(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> tuple[tuple[float, float], ...]:
    if len(y_true) != len(y_pred):
        raise ValueError(
            f"Target/prediction lengths differ: {len(y_true)} != {len(y_pred)}"
        )
    if len(y_true) == 0:
        raise ValueError("Metrics require at least one observation")

    pairs = tuple((float(actual), float(predicted)) for actual, predicted in zip(y_true, y_pred))
    if any(not math.isfinite(value) for pair in pairs for value in pair):
        raise ValueError("Targets and predictions must contain only finite values")
    return pairs


def mean_squared_error(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    pairs = _paired_values(y_true, y_pred)
    return sum((predicted - actual) ** 2 for actual, predicted in pairs) / len(pairs)


def root_mean_squared_error(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    return math.sqrt(mean_squared_error(y_true, y_pred))


def mean_absolute_error(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    pairs = _paired_values(y_true, y_pred)
    return sum(abs(predicted - actual) for actual, predicted in pairs) / len(pairs)


def mean_absolute_percentage_error(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> float:
    pairs = _paired_values(y_true, y_pred)
    nonzero_pairs = [(actual, predicted) for actual, predicted in pairs if actual != 0]
    if not nonzero_pairs:
        return 0.0
    return (
        sum(abs((actual - predicted) / actual) for actual, predicted in nonzero_pairs)
        / len(nonzero_pairs)
        * 100
    )


def evaluate_all(
    y_true: Sequence[float],
    y_pred: Sequence[float],
) -> dict[str, float]:
    """Return the WS4/WS5 metric names and rounding convention."""
    return {
        "MAE": round(mean_absolute_error(y_true, y_pred), 4),
        "RMSE": round(root_mean_squared_error(y_true, y_pred), 4),
        "MSE": round(mean_squared_error(y_true, y_pred), 4),
        "MAPE_percent": round(mean_absolute_percentage_error(y_true, y_pred), 2),
    }


__all__ = [
    "evaluate_all",
    "mean_absolute_error",
    "mean_absolute_percentage_error",
    "mean_squared_error",
    "root_mean_squared_error",
]
