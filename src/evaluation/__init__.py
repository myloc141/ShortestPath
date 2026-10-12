"""Evaluation, metric aggregation, and prediction alignment utilities."""

from .regression import (
    PairwiseRoutingComparison,
    PredictionAlignment,
    PredictionRow,
    check_prediction_alignment,
    compare_routing_pairs,
    evaluate_by_time_slot,
    select_routing_models,
)

__all__ = [
    "PredictionAlignment",
    "PredictionRow",
    "check_prediction_alignment",
    "compare_routing_pairs",
    "evaluate_by_time_slot",
    "PairwiseRoutingComparison",
    "select_routing_models",
]
