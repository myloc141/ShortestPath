"""Evaluation, metric aggregation, and prediction alignment utilities."""

from .regression import (
    ObservationLike,
    PredictionAlignment,
    PredictionRow,
    check_prediction_alignment,
    evaluate_by_time_slot,
    select_routing_models,
)

__all__ = [
    "ObservationLike",
    "PredictionAlignment",
    "PredictionRow",
    "check_prediction_alignment",
    "evaluate_by_time_slot",
    "select_routing_models",
]
