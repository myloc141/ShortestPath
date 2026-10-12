"""Regression metric summaries and row-alignment checks."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from ..common.metrics import evaluate_all
from ..preprocess.seervada import TrafficObservation
from ..routing.experiment import RoutingResult


@dataclass(frozen=True)
class PredictionRow:
    prediction: float
    edge_id: str | None = None
    time_slot: int | None = None
    day: int | None = None
    y_true: float | None = None


@dataclass(frozen=True)
class PredictionAlignment:
    aligned: bool
    messages: tuple[str, ...]


@dataclass(frozen=True)
class PairwiseRoutingComparison:
    method_a: str
    method_b: str
    time_slot: int
    n_days: int
    days_route_differs: int
    days_same_route_but_different_predicted_time: int
    mean_actual_a_minus_b: float


def evaluate_by_time_slot(
    observations: Sequence[TrafficObservation],
    predictions: Sequence[float],
    *,
    model_name: str,
) -> tuple[dict[str, float | int | str], ...]:
    """Calculate overall and per-slot metrics for aligned predictions."""
    if len(observations) != len(predictions):
        raise ValueError("Prediction count does not match observation count")
    if not observations:
        raise ValueError("Cannot evaluate an empty dataset")

    def row(label: str, indices: Sequence[int]) -> dict[str, float | int | str]:
        truth = [observations[index].travel_time for index in indices]
        predicted = [float(predictions[index]) for index in indices]
        if any(not math.isfinite(value) for value in predicted):
            raise ValueError("Predictions must contain only finite values")
        return {
            "time_slot": label,
            "model": model_name,
            **evaluate_all(truth, predicted),
            "n_obs": len(indices),
        }

    result = [row("all", tuple(range(len(observations))))]
    slots = sorted({item.time_slot for item in observations})
    for slot in slots:
        indices = tuple(
            index
            for index, item in enumerate(observations)
            if item.time_slot == slot
        )
        result.append(row(str(slot), indices))
    return tuple(result)


def check_prediction_alignment(
    observations: Sequence[TrafficObservation],
    raw_predictions: Sequence[float],
    keyed_predictions: Sequence[PredictionRow],
    *,
    tolerance: float = 1e-6,
) -> PredictionAlignment:
    """Compare keyed prediction files against the canonical observation order.

    Key fields are checked when present; target and prediction values are
    always checked. This supports existing WS4 keyed files, which omit day.
    """
    messages: list[str] = []
    if len(observations) != len(raw_predictions):
        return PredictionAlignment(False, ("Raw prediction row count differs",))
    if len(observations) != len(keyed_predictions):
        return PredictionAlignment(False, ("Keyed prediction row count differs",))

    for index, (observation, raw, keyed) in enumerate(
        zip(observations, raw_predictions, keyed_predictions)
    ):
        if keyed.edge_id is not None and keyed.edge_id != observation.edge_id:
            messages.append(f"Row {index}: edge_id mismatch")
        if keyed.time_slot is not None and keyed.time_slot != observation.time_slot:
            messages.append(f"Row {index}: time_slot mismatch")
        if keyed.day is not None and keyed.day != observation.day:
            messages.append(f"Row {index}: day mismatch")
        if keyed.y_true is not None and not math.isclose(
            keyed.y_true,
            observation.travel_time,
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            messages.append(f"Row {index}: y_true mismatch")
        if not math.isclose(
            keyed.prediction,
            float(raw),
            rel_tol=0.0,
            abs_tol=tolerance,
        ):
            messages.append(f"Row {index}: raw/keyed prediction mismatch")

    if not messages:
        messages.append("Prediction rows align with observations")
    return PredictionAlignment(not any("mismatch" in item for item in messages), tuple(messages))


def select_routing_models(
    validation_metrics: Mapping[str, Mapping[str, float]],
    train_mean_by_slot: Mapping[int, float],
    *,
    baseline_names: tuple[str, str] = ("GroupMean", "LinearRegression"),
    neural_network_name: str = "NeuralNet",
) -> dict[str, object]:
    """Apply WS6 model/slot selection rules using validation metrics only.

    Callers must pass validation-set metrics, not final test-set metrics, for
    unbiased model selection.
    """
    needed = set(baseline_names) | {neural_network_name}
    missing = needed - validation_metrics.keys()
    if missing:
        raise ValueError(f"Missing validation metrics for: {sorted(missing)}")
    for name in needed:
        if not {"MAE", "RMSE"} <= validation_metrics[name].keys():
            raise ValueError(f"{name} metrics must include MAE and RMSE")

    first, second = baseline_names
    first_metrics, second_metrics = validation_metrics[first], validation_metrics[second]
    if (
        first_metrics["MAE"] <= second_metrics["MAE"]
        and first_metrics["RMSE"] <= second_metrics["RMSE"]
    ):
        baseline = first
        note = f"{first} is no worse on MAE and RMSE"
    elif (
        second_metrics["MAE"] <= first_metrics["MAE"]
        and second_metrics["RMSE"] <= first_metrics["RMSE"]
    ):
        baseline = second
        note = f"{second} is no worse on MAE and RMSE"
    else:
        baseline = first
        note = "Validation metrics conflict; use the first, simpler baseline"

    nn_metrics = validation_metrics[neural_network_name]
    nn_included = (
        nn_metrics["MAE"] < validation_metrics[baseline]["MAE"]
        and nn_metrics["RMSE"] < validation_metrics[baseline]["RMSE"]
    )
    if not train_mean_by_slot:
        raise ValueError("train_mean_by_slot must not be empty")
    peak = max(train_mean_by_slot, key=train_mean_by_slot.__getitem__)
    offpeak = min(train_mean_by_slot, key=train_mean_by_slot.__getitem__)
    return {
        "metrics_on_validation": {
            name: dict(validation_metrics[name]) for name in sorted(needed)
        },
        "primary_baseline": baseline,
        "primary_baseline_note": note,
        "nn_included_in_main_comparison": nn_included,
        "train_mean_travel_time_by_slot": dict(train_mean_by_slot),
        "main_slots": {"peak": peak, "offpeak": offpeak},
    }


def compare_routing_pairs(
    results: Sequence[RoutingResult],
    method_pairs: Sequence[tuple[str, str]],
) -> tuple[PairwiseRoutingComparison, ...]:
    """Compare selected routes and actual scores per slot/day and model pair."""
    by_key = {
        (item.time_slot, item.day, item.method): item for item in results
    }
    slots = sorted({item.time_slot for item in results})
    days = sorted({item.day for item in results})
    comparisons: list[PairwiseRoutingComparison] = []
    for method_a, method_b in method_pairs:
        for slot in slots:
            paired: list[tuple[RoutingResult, RoutingResult]] = []
            for day in days:
                first = by_key.get((slot, day, method_a))
                second = by_key.get((slot, day, method_b))
                if first is not None and second is not None:
                    paired.append((first, second))
            if not paired:
                continue
            route_differs = [
                first.route != second.route for first, second in paired
            ]
            predicted_differs = [
                first.predicted_time is not None
                and second.predicted_time is not None
                and abs(first.predicted_time - second.predicted_time) > 1e-6
                for first, second in paired
            ]
            actual_differences = [
                first.actual_time - second.actual_time
                for first, second in paired
            ]
            comparisons.append(
                PairwiseRoutingComparison(
                    method_a=method_a,
                    method_b=method_b,
                    time_slot=slot,
                    n_days=len(paired),
                    days_route_differs=sum(route_differs),
                    days_same_route_but_different_predicted_time=sum(
                        not differs and pred_diff
                        for differs, pred_diff in zip(
                            route_differs, predicted_differs
                        )
                    ),
                    mean_actual_a_minus_b=(
                        sum(actual_differences) / len(actual_differences)
                    ),
                )
            )
    return tuple(comparisons)
