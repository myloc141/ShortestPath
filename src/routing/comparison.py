"""Pairwise comparisons of selected routing methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .experiment import RoutingResult


@dataclass(frozen=True)
class PairwiseRoutingComparison:
    method_a: str
    method_b: str
    time_slot: int
    n_days: int
    days_route_differs: int
    days_same_route_but_different_predicted_time: int
    mean_actual_a_minus_b: float


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


__all__ = ["PairwiseRoutingComparison", "compare_routing_pairs"]
