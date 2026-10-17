"""WS6-style route selection and evaluation on simulated traffic observations."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from ..network.schema import Network
from ..preprocess.observations import TrafficObservation, edge_key
from ..shortest_path.dijkstra import dijkstra
from ..shortest_path.simple_paths import iter_simple_paths


@dataclass(frozen=True)
class RouteReference:
    name: str
    path: tuple[str, ...]


@dataclass(frozen=True)
class RoutingResult:
    time_slot: int
    slot_name: str
    day: int
    day_of_week: str
    method: str
    route: tuple[str, ...]
    distance_km: float
    objective: float | None
    predicted_time: float | None
    actual_time: float
    oracle_route: tuple[str, ...]
    oracle_time: float
    regret: float
    matches_oracle: bool
    n_ties: int
    selection_warning: str | None = None
    method_family: str = "reference"


@dataclass(frozen=True)
class RoutingSummary:
    time_slot: int
    method: str
    modal_route: tuple[str, ...]
    modal_route_days: int
    n_distinct_routes: int
    mean_distance_km: float
    mean_predicted_time: float | None
    mean_actual_time: float
    std_actual_time: float | None
    mean_regret: float
    days_equal_oracle: int
    n_days: int


def _network_edge_maps(
    network: Network,
) -> tuple[dict[tuple[str, str], float], dict[tuple[str, str], float]]:
    edge_distances: dict[tuple[str, str], float] = {}
    arc_distances: dict[tuple[str, str], float] = {}
    for edge in network.edges:
        key = edge_key(edge.u, edge.v)
        if key in edge_distances:
            raise ValueError(f"Parallel/duplicate network edge is unsupported: {key}")
        edge_distances[key] = edge.distance
        arc_distances[(edge.u, edge.v)] = edge.distance
        if not edge.directed:
            arc_distances[(edge.v, edge.u)] = edge.distance
        else:
            raise ValueError(
                "This route experiment requires an undirected network"
            )
    return edge_distances, arc_distances


def _route_cost(
    path: Sequence[str],
    weights: Mapping[tuple[str, str], float],
) -> float:
    total = 0.0
    for u, v in zip(path, path[1:]):
        key = edge_key(u, v)
        if key not in weights:
            raise ValueError(f"Route uses edge missing from weights: {key}")
        total += weights[key]
    return total


def _best_route(
    paths: Sequence[tuple[str, ...]],
    weights: Mapping[tuple[str, str], float],
) -> tuple[tuple[str, ...], float, int]:
    if not paths:
        raise ValueError("Cannot select a route from an empty path collection")
    scored = [
        (round(_route_cost(path, weights), 9), len(path) - 1, path)
        for path in paths
    ]
    scored.sort()
    best_cost = scored[0][0]
    ties = sum(abs(cost - best_cost) <= 1e-8 for cost, _, _ in scored)
    return scored[0][2], best_cost, ties


def shortest_route_with_weights(
    network: Network,
    weights: Mapping[str, float],
    source: str,
    target: str,
) -> tuple[str, ...]:
    """Return the Dijkstra route using weights keyed by network edge ID."""
    return dijkstra(network, source, target, weights=weights).path


def parse_route_path(value: str) -> tuple[str, ...]:
    """Parse a hyphen-delimited node path such as ``O-A-B-T``.

    Empty strings, empty nodes, and repeated nodes are rejected with a
    ``ValueError`` so malformed RCSP rows cannot silently become routes.
    """
    if not isinstance(value, str):
        raise ValueError("Route path must be a hyphen-delimited string")
    parts = tuple(node.strip() for node in value.split("-"))
    if len(parts) < 2 or any(not node for node in parts):
        raise ValueError(
            f"Invalid route path {value!r}: expected at least two non-empty nodes"
        )
    if len(set(parts)) != len(parts):
        raise ValueError(
            f"Invalid route path {value!r}: repeated nodes are not allowed"
        )
    return parts


def _edge_id_weights(
    network: Network,
    pair_weights: Mapping[tuple[str, str], float],
) -> dict[str, float]:
    return {
        edge.edge_id: pair_weights[edge_key(edge.u, edge.v)]
        for edge in network.edges
    }


def run_routing_experiment(
    network: Network,
    train: Sequence[TrafficObservation],
    test: Sequence[TrafficObservation],
    predictions: Mapping[str, Sequence[float]],
    *,
    source: str = "O",
    target: str = "T",
    route_references: Sequence[RouteReference] = (),
    rcsp_routes: Sequence[RouteReference] = (),
    max_paths: int | None = 1_000_000,
) -> tuple[RoutingResult, ...]:
    """Run fixed, predicted, Oracle, RCSP, and optional reference routes.

    Prediction arrays must align row-for-row with ``test``. Test actual values
    are used only to score selected routes, except for the explicitly labeled
    Oracle lower-bound route. Fixed and predicted routes are selected by
    Dijkstra; ``selection_warning`` records any difference from brute-force
    selection under the same weights. RCSP routes are included as references
    and scored against actual test travel times.
    """
    if not train or not test:
        raise ValueError("Training and test traffic observations must be non-empty")
    edge_distances, _ = _network_edge_maps(network)
    expected_edges = set(edge_distances)
    for split_name, observations in (("train", train), ("test", test)):
        for item in observations:
            if edge_key(item.u, item.v) not in expected_edges:
                raise ValueError(
                    f"{split_name} observation uses unknown edge "
                    f"{edge_key(item.u, item.v)}"
                )
    for name, values in predictions.items():
        if len(values) != len(test):
            raise ValueError(
                f"Prediction {name!r} has {len(values)} rows; expected {len(test)}"
            )
        if any(not math.isfinite(float(value)) for value in values):
            raise ValueError(f"Prediction {name!r} contains non-finite values")

    training_sum: dict[tuple[str, str], float] = {}
    training_count: dict[tuple[str, str], int] = Counter()
    for item in train:
        key = edge_key(item.u, item.v)
        training_sum[key] = training_sum.get(key, 0.0) + item.travel_time
        training_count[key] = training_count.get(key, 0) + 1
    if set(training_count) != expected_edges:
        raise ValueError("Training data does not cover every network edge")
    fixed_mean = {
        key: training_sum[key] / training_count[key] for key in expected_edges
    }

    paths = tuple(
        item.nodes
        for item in iter_simple_paths(
            network, source, target, max_paths=max_paths
        )
    )
    if not paths:
        raise ValueError(f"No simple path exists from {source!r} to {target!r}")
    all_references = (*route_references, *rcsp_routes)
    reference_names: set[str] = set()
    for reference in all_references:
        if not reference.name.strip():
            raise ValueError("Reference route name must not be empty")
        if reference.name in reference_names:
            raise ValueError(f"Duplicate reference route name {reference.name!r}")
        reference_names.add(reference.name)
        if (
            len(reference.path) < 2
            or reference.path[0] != source
            or reference.path[-1] != target
        ):
            raise ValueError(f"Reference route {reference.name!r} has wrong endpoints")
        try:
            _route_cost(reference.path, edge_distances)
        except ValueError as error:
            raise ValueError(
                f"Reference route {reference.name!r} is invalid: {error}"
            ) from error

    groups: dict[tuple[int, int], list[tuple[int, TrafficObservation]]] = {}
    seen: set[tuple[int, int, str]] = set()
    for index, item in enumerate(test):
        key = (item.day, item.time_slot, item.edge_id)
        if key in seen:
            raise ValueError(f"Duplicate test observation key {key}")
        seen.add(key)
        groups.setdefault((item.time_slot, item.day), []).append((index, item))

    results: list[RoutingResult] = []
    for (slot, day), indexed_rows in sorted(groups.items()):
        actual: dict[tuple[str, str], float] = {}
        slot_names: set[str] = set()
        days_of_week: set[str] = set()
        for _, item in indexed_rows:
            key = edge_key(item.u, item.v)
            if key in actual:
                raise ValueError(
                    f"Slot {slot}, day {day}: multiple observations for {key}"
                )
            actual[key] = item.travel_time
            slot_names.add(item.slot_name)
            days_of_week.add(item.day_of_week)
        if set(actual) != expected_edges:
            raise ValueError(
                f"Slot {slot}, day {day} edge coverage differs from network"
            )
        if len(slot_names) != 1 or len(days_of_week) != 1:
            raise ValueError(f"Slot {slot}, day {day} metadata is inconsistent")
        slot_name = next(iter(slot_names))
        day_of_week = next(iter(days_of_week))
        day_predictions = {
            name: {
                edge_key(test[index].u, test[index].v): float(values[index])
                for index, _ in indexed_rows
            }
            for name, values in predictions.items()
        }

        oracle_route, oracle_time, _ = _best_route(paths, actual)
        weight_sets: list[tuple[str, Mapping[tuple[str, str], float], bool]] = [
            ("Fixed_distance", edge_distances, False),
            ("Fixed_trainmean", fixed_mean, True),
        ]
        weight_sets.extend(
            (f"Pred_{name}", values, True)
            for name, values in day_predictions.items()
        )
        weight_sets.append(("Oracle", actual, False))

        def append_result(
            method: str,
            route: tuple[str, ...],
            objective: float | None,
            predicted_time: float | None,
            n_ties: int,
            selection_warning: str | None = None,
        ) -> None:
            actual_time = _route_cost(route, actual)
            distance = _route_cost(route, edge_distances)
            results.append(
                RoutingResult(
                    time_slot=slot,
                    slot_name=slot_name,
                    day=day,
                    day_of_week=day_of_week,
                    method=method,
                    method_family=_method_family(method),
                    route=route,
                    distance_km=distance,
                    objective=objective,
                    predicted_time=predicted_time,
                    actual_time=actual_time,
                    oracle_route=oracle_route,
                    oracle_time=oracle_time,
                    regret=actual_time - oracle_time,
                    matches_oracle=math.isclose(
                        actual_time, oracle_time, rel_tol=0.0, abs_tol=1e-9
                    ),
                    n_ties=n_ties,
                    selection_warning=selection_warning,
                )
            )

        for method, weights, has_prediction in weight_sets:
            brute_route, brute_objective, n_ties = _best_route(paths, weights)
            dijkstra_route = shortest_route_with_weights(
                network,
                _edge_id_weights(network, weights),
                source,
                target,
            )
            selection_warning = None
            if method == "Oracle":
                route = brute_route
                objective = brute_objective
            else:
                route = dijkstra_route
                objective = round(_route_cost(route, weights), 9)
            if dijkstra_route != brute_route:
                selection_warning = (
                    f"Dijkstra route {dijkstra_route!r} differs from "
                    f"brute-force route {brute_route!r} for {method} weights"
                )
            prediction = objective if has_prediction else None
            append_result(
                method,
                route,
                objective,
                prediction,
                n_ties,
                selection_warning,
            )
        for reference in all_references:
            append_result(reference.name, reference.path, None, None, 1)

    return tuple(results)


def _method_family(method: str) -> str:
    """Classify a route method for downstream result tables."""
    if method in {"Fixed_distance", "Fixed_trainmean"}:
        return "fixed"
    if method.startswith("Pred_"):
        return "predicted"
    if method == "Oracle":
        return "oracle"
    if method.startswith("RCSP"):
        return "rcsp"
    return "reference"


def summarize_routing_results(
    results: Sequence[RoutingResult],
) -> tuple[RoutingSummary, ...]:
    """Aggregate route metrics per time slot and method."""
    groups: dict[tuple[int, str], list[RoutingResult]] = {}
    for item in results:
        groups.setdefault((item.time_slot, item.method), []).append(item)
    summaries: list[RoutingSummary] = []
    for (slot, method), items in sorted(groups.items()):
        counts = Counter(item.route for item in items)
        modal_route = min(
            counts,
            key=lambda route: (-counts[route], len(route), route),
        )
        actuals = [item.actual_time for item in items]
        predictions = [
            item.predicted_time
            for item in items
            if item.predicted_time is not None
        ]
        mean_actual = sum(actuals) / len(actuals)
        std_actual = (
            math.sqrt(
                sum((value - mean_actual) ** 2 for value in actuals)
                / (len(actuals) - 1)
            )
            if len(actuals) > 1
            else None
        )
        summaries.append(
            RoutingSummary(
                time_slot=slot,
                method=method,
                modal_route=modal_route,
                modal_route_days=counts[modal_route],
                n_distinct_routes=len(counts),
                mean_distance_km=sum(item.distance_km for item in items) / len(items),
                mean_predicted_time=(
                    sum(predictions) / len(predictions) if predictions else None
                ),
                mean_actual_time=mean_actual,
                std_actual_time=std_actual,
                mean_regret=sum(item.regret for item in items) / len(items),
                days_equal_oracle=sum(item.matches_oracle for item in items),
                n_days=len(items),
            )
        )
    return tuple(summaries)
