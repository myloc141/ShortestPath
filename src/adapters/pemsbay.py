"""PEMS-BAY adapter and Haversine network construction."""

from __future__ import annotations

import csv
from heapq import heappop, heappush
import json
import math
from collections import deque
from pathlib import Path
import pickle
from typing import Any, TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import pandas as pd

from ..common.config import (
    DEFAULT_PEMS_BAY_TIME_SLOTS,
    RoutingTimeWindow,
    load_config,
)
from ..network.schema import Network, NetworkEdge
from ..network.validation import validate_network
from ..preprocess.dataset import prepare_observation_splits
from ..preprocess.observations import TrafficObservation
from .base import DatasetAdapter


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
EARTH_RADIUS_KM = 6371.0088
MPH_TO_KMH = 1.609344


def _read_locations(path: Path) -> dict[str, tuple[float, float]]:
    locations: dict[str, tuple[float, float]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.reader(csv_file)
        for line_number, row in enumerate(reader, start=1):
            if len(row) < 3:
                raise ValueError(
                    f"{path}:{line_number}: expected sensor_id, latitude, longitude"
                )
            sensor_id, raw_latitude, raw_longitude = (
                item.strip() for item in row[:3]
            )
            if line_number == 1 and (
                sensor_id.casefold() in {"sensor_id", "sensorid", "sensor"}
                or raw_latitude.casefold() in {"latitude", "lat"}
            ):
                continue
            try:
                latitude = float(raw_latitude)
                longitude = float(raw_longitude)
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid latitude/longitude"
                ) from exc
            if (
                not sensor_id
                or not math.isfinite(latitude)
                or not math.isfinite(longitude)
                or not -90 <= latitude <= 90
                or not -180 <= longitude <= 180
            ):
                raise ValueError(f"{path}:{line_number}: invalid sensor location")
            if sensor_id in locations:
                raise ValueError(
                    f"{path}:{line_number}: duplicate sensor ID {sensor_id!r}"
                )
            locations[sensor_id] = (latitude, longitude)
    return locations


def _read_adjacency(path: Path) -> tuple[list[str], Any]:
    """Read the DCRNN-style (sensor_ids, index_map, adjacency_matrix) pickle.

    Pickle files can execute code when loaded; use this only with trusted input.
    """
    with path.open("rb") as pickle_file:
        payload = pickle.load(pickle_file, encoding="latin1")
    if not isinstance(payload, (tuple, list)) or len(payload) != 3:
        raise ValueError(
            f"{path}: expected a (sensor_ids, index_map, adjacency_matrix) tuple"
        )

    raw_sensor_ids, index_map, matrix = payload
    if not isinstance(raw_sensor_ids, (tuple, list)):
        raise ValueError(f"{path}: sensor_ids must be a list or tuple")
    if not isinstance(index_map, dict):
        raise ValueError(f"{path}: sensor index map must be a dictionary")

    sensor_ids = [str(sensor_id).strip() for sensor_id in raw_sensor_ids]
    if not sensor_ids or len(set(sensor_ids)) != len(sensor_ids):
        raise ValueError(f"{path}: sensor_ids must be non-empty and unique")
    if len(matrix) != len(sensor_ids):
        raise ValueError(f"{path}: adjacency matrix row count does not match IDs")
    if any(len(matrix[row]) != len(sensor_ids) for row in range(len(sensor_ids))):
        raise ValueError(f"{path}: adjacency matrix must be square")

    return sensor_ids, matrix


def _haversine_km(
    first: tuple[float, float],
    second: tuple[float, float],
) -> float:
    latitude_1, longitude_1 = map(math.radians, first)
    latitude_2, longitude_2 = map(math.radians, second)
    delta_latitude = latitude_2 - latitude_1
    delta_longitude = longitude_2 - longitude_1
    haversine = (
        math.sin(delta_latitude / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(delta_longitude / 2) ** 2
    )
    central_angle = 2 * math.asin(min(1.0, math.sqrt(haversine)))
    return EARTH_RADIUS_KM * central_angle


def _eligible_sensor_ids(
    locations: dict[str, tuple[float, float]],
    adjacency_ids: Sequence[str],
    traffic_parquet: Path,
) -> set[str]:
    """Return sensors present in locations, adjacency, and long traffic data."""
    try:
        import pandas as pd
    except ImportError as error:
        raise RuntimeError(
            "Automatic PEMS-BAY sensor selection requires pandas and a Parquet engine"
        ) from error

    if not traffic_parquet.is_file():
        raise FileNotFoundError(
            f"Traffic Parquet not found at {traffic_parquet}; run "
            "scripts/run_preprocess_pems_bay.py first"
        )
    try:
        traffic = pd.read_parquet(
            traffic_parquet, columns=["sensor_id", "speed"]
        )
        numeric_speed = pd.to_numeric(traffic["speed"], errors="coerce")
        traffic_ids = traffic.loc[
            numeric_speed.notna()
            & numeric_speed.gt(0)
            & numeric_speed.map(math.isfinite),
            "sensor_id",
        ]
    except (KeyError, ValueError) as error:
        raise ValueError(
            f"{traffic_parquet}: expected a long-form sensor_id column"
        ) from error
    present_in_traffic = {
        str(sensor_id).strip()
        for sensor_id in traffic_ids.dropna().unique()
        if str(sensor_id).strip()
    }
    return set(locations) & set(adjacency_ids) & present_in_traffic


def _weak_adjacency(
    sensor_ids: Sequence[str],
    matrix: Any,
) -> dict[str, set[str]]:
    """Build deterministic weak adjacency, regardless of matrix direction."""
    index_by_id = {sensor_id: index for index, sensor_id in enumerate(sensor_ids)}
    neighbors = {sensor_id: set() for sensor_id in sensor_ids}
    for source in sorted(sensor_ids):
        for target in sorted(sensor_ids):
            if source == target:
                continue
            if (
                float(matrix[index_by_id[source]][index_by_id[target]]) != 0
                or float(matrix[index_by_id[target]][index_by_id[source]]) != 0
            ):
                neighbors[source].add(target)
    return neighbors


def _select_sensor_tree(
    candidates: Sequence[str],
    neighbors: dict[str, set[str]],
    *,
    n_sensors: int,
    seed_sensor: str | None,
) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...], str]:
    """Select nodes and their BFS spanning tree with stable tie-breaking."""
    if seed_sensor is not None:
        start = str(seed_sensor).strip()
        if start not in candidates:
            raise ValueError(
                f"seed_sensor {start!r} is not present among eligible sensors"
            )
        starts = (start,)
    else:
        starts = tuple(
            sorted(
                candidates,
                key=lambda sensor_id: (-len(neighbors[sensor_id]), sensor_id),
            )
        )

    largest_component = 0
    for start in starts:
        selected = [start]
        selected_set = {start}
        tree_edges: list[tuple[str, str]] = []
        pending = deque([start])
        while pending and len(selected) < n_sensors:
            current = pending.popleft()
            for neighbor in sorted(neighbors[current]):
                if neighbor in selected_set:
                    continue
                selected.append(neighbor)
                selected_set.add(neighbor)
                tree_edges.append(tuple(sorted((current, neighbor))))
                pending.append(neighbor)
                if len(selected) == n_sensors:
                    break
        largest_component = max(largest_component, len(selected))
        if len(selected) == n_sensors:
            return tuple(selected), tuple(tree_edges), start

    raise ValueError(
        f"BFS could select at most {largest_component} connected eligible "
        f"sensors; {n_sensors} are required"
    )


def _tree_path_distance(
    start: str,
    end: str,
    tree_edges: Sequence[tuple[str, str]],
    locations: dict[str, tuple[float, float]],
) -> float:
    tree: dict[str, list[tuple[str, float]]] = {}
    for first, second in tree_edges:
        distance = _haversine_km(locations[first], locations[second])
        tree.setdefault(first, []).append((second, distance))
        tree.setdefault(second, []).append((first, distance))
    pending = [(start, None, 0.0)]
    while pending:
        current, parent, distance_so_far = pending.pop()
        if current == end:
            return distance_so_far
        for neighbor, edge_distance in tree.get(current, ()):
            if neighbor != parent:
                pending.append(
                    (neighbor, current, distance_so_far + edge_distance)
                )
    raise ValueError(f"No spanning-tree path exists between {start!r} and {end!r}")


def _rank_cycle_edges(
    selected: Sequence[str],
    tree_edges: Sequence[tuple[str, str]],
    neighbors: dict[str, set[str]],
    locations: dict[str, tuple[float, float]],
) -> tuple[tuple[str, str], ...]:
    """Rank non-tree edges by Haversine cycle length, then endpoint IDs."""
    tree_edge_set = set(tree_edges)
    ranked: list[tuple[float, str, str]] = []
    for first_index, first in enumerate(selected):
        for second in selected[first_index + 1 :]:
            pair = tuple(sorted((first, second)))
            if second not in neighbors[first] or pair in tree_edge_set:
                continue
            cycle_length = _tree_path_distance(
                first, second, tree_edges, locations
            ) + _haversine_km(locations[first], locations[second])
            ranked.append((cycle_length, pair[0], pair[1]))
    ranked.sort()
    return tuple((first, second) for _, first, second in ranked)


def _select_sensor_topology(
    *,
    locations: dict[str, tuple[float, float]],
    adjacency_ids: Sequence[str],
    matrix: Any,
    candidates: Sequence[str],
    n_sensors: int,
    seed_sensor: str | None,
) -> tuple[
    tuple[str, ...],
    tuple[tuple[str, str], ...],
    tuple[tuple[str, str], ...],
    str,
]:
    """Return a BFS sensor subset/tree and ranked cycle-closing edges."""
    candidate_set = set(candidates)
    neighbors_all = _weak_adjacency(adjacency_ids, matrix)
    neighbors = {
        sensor_id: neighbors_all[sensor_id] & candidate_set
        for sensor_id in candidate_set
    }
    selected, tree_edges, start = _select_sensor_tree(
        tuple(sorted(candidate_set)),
        neighbors,
        n_sensors=n_sensors,
        seed_sensor=seed_sensor,
    )
    cycle_edges = _rank_cycle_edges(
        selected, tree_edges, neighbors, locations
    )
    return selected, tree_edges, cycle_edges, start


def select_pemsbay_sensors(
    *,
    locations_csv: str | Path,
    adjacency_pickle: str | Path,
    traffic_parquet: str | Path,
    n_sensors: int = 25,
    seed_sensor: str | None = None,
) -> tuple[str, ...]:
    """Choose a deterministic connected subset using a BFS spanning tree.

    Sensors without coordinates, adjacency, or valid traffic are excluded.
    Unless configured, BFS tries eligible sensors in descending degree order
    (ID breaks ties) until one can reach the requested size, then visits
    neighbors in ID order. Non-tree edges are ranked by Haversine cycle length
    and ID for subsequent bounded edge selection.
    """
    if (
        not isinstance(n_sensors, int)
        or isinstance(n_sensors, bool)
        or not 20 <= n_sensors <= 30
    ):
        raise ValueError("n_sensors must be between 20 and 30")

    location_path = Path(locations_csv)
    adjacency_path = Path(adjacency_pickle)
    traffic_path = Path(traffic_parquet)
    locations = _read_locations(location_path)
    adjacency_ids, matrix = _read_adjacency(adjacency_path)
    eligible = _eligible_sensor_ids(locations, adjacency_ids, traffic_path)
    if len(eligible) < n_sensors:
        raise ValueError(
            f"Cannot select {n_sensors} connected sensors: only "
            f"{len(eligible)} sensors have coordinates and traffic data"
        )

    selected, _, _, _ = _select_sensor_topology(
        locations=locations,
        adjacency_ids=adjacency_ids,
        matrix=matrix,
        candidates=tuple(sorted(eligible)),
        n_sensors=n_sensors,
        seed_sensor=seed_sensor,
    )
    return selected


def load_pems_bay_subnetwork(
    selected_sensor_ids: Sequence[str],
    *,
    locations_csv: str | Path,
    adjacency_pickle: str | Path,
    require_connected: bool = True,
    direction_policy: str = "directed",
    edge_pairs: Sequence[tuple[str, str]] | None = None,
) -> Network:
    """Build a 20–30 sensor subnetwork from caller-selected sensor IDs.

    ``direction_policy="directed"`` preserves each non-zero matrix entry.
    ``"undirected"`` creates one undirected edge when either direction is
    present. Distances are Haversine straight-line estimates in km, not
    measured road lengths. If ``edge_pairs`` is supplied, only those
    cycle-controlled undirected endpoint pairs are retained.
    """
    if not isinstance(direction_policy, str) or direction_policy not in {
        "directed",
        "undirected",
    }:
        raise ValueError("direction_policy must be 'directed' or 'undirected'")
    selected = tuple(str(sensor_id).strip() for sensor_id in selected_sensor_ids)
    if not 20 <= len(selected) <= 30:
        raise ValueError("Select between 20 and 30 PEMS-BAY sensor IDs")
    if any(not sensor_id for sensor_id in selected):
        raise ValueError("Selected sensor IDs must not be empty")
    if len(set(selected)) != len(selected):
        raise ValueError("Selected sensor IDs must be unique")

    location_path = Path(locations_csv)
    adjacency_path = Path(adjacency_pickle)
    locations = _read_locations(location_path)
    sensor_ids, matrix = _read_adjacency(adjacency_path)
    index_by_id = {sensor_id: index for index, sensor_id in enumerate(sensor_ids)}

    for sensor_id in selected:
        if sensor_id not in locations:
            raise ValueError(f"Sensor {sensor_id!r} is missing from {location_path}")
        if sensor_id not in index_by_id:
            raise ValueError(f"Sensor {sensor_id!r} is missing from {adjacency_path}")

    allowed_pairs: set[tuple[str, str]] | None = None
    if edge_pairs is not None:
        allowed_pairs = set()
        for first, second in edge_pairs:
            if first == second or first not in selected or second not in selected:
                raise ValueError(
                    f"Invalid selected edge pair {(first, second)!r}: "
                    "both distinct endpoints must be selected sensors"
                )
            pair = tuple(sorted((first, second)))
            if pair in allowed_pairs:
                raise ValueError(f"Duplicate selected edge pair {pair!r}")
            allowed_pairs.add(pair)

    edges: list[NetworkEdge] = []
    pairs = (
        (
            (u, v)
            for u in selected
            for v in selected
            if u != v
            and (allowed_pairs is None or tuple(sorted((u, v))) in allowed_pairs)
        )
        if direction_policy == "directed"
        else (
            (selected[first], selected[second])
            for first in range(len(selected))
            for second in range(first + 1, len(selected))
            if allowed_pairs is None
            or tuple(
                sorted((selected[first], selected[second]))
            )
            in allowed_pairs
        )
    )
    for u, v in pairs:
        raw_weight = matrix[index_by_id[u]][index_by_id[v]]
        try:
            weight = float(raw_weight)
            reverse_weight = float(matrix[index_by_id[v]][index_by_id[u]])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Adjacency value for {u!r} -> {v!r} is not numeric"
            ) from exc
        if not math.isfinite(weight) or not math.isfinite(reverse_weight):
            raise ValueError(f"Adjacency value for {u!r} -> {v!r} is not finite")
        if direction_policy == "undirected":
            if weight == 0 and reverse_weight == 0:
                continue
            weight = weight if weight != 0 else reverse_weight
        elif weight == 0:
            continue

        edges.append(
            NetworkEdge(
                edge_id=f"edge_{len(edges) + 1:03d}",
                u=u,
                v=v,
                distance=_haversine_km(locations[u], locations[v]),
                directed=direction_policy == "directed",
            )
        )

    network = Network(
        nodes=selected,
        edges=tuple(edges),
        distance_unit="km",
        distance_is_approximate=True,
        distance_method=(
            "Haversine great-circle distance from sensor coordinates; "
            "approximation of road distance; "
            f"direction policy: {direction_policy}"
        ),
    )
    report = validate_network(network, require_connected=require_connected)
    if not report.is_valid:
        raise ValueError("Invalid PEMS-BAY subnetwork: " + "; ".join(report.errors))
    return network


def _select_routing_endpoints(
    network: Network,
    *,
    source: str | None,
    target: str | None,
    max_paths: int = 2000,
    min_paths: int = 5,
) -> tuple[str, str, int]:
    """Choose a long-distance pair with a bounded number of simple paths.

    Counting stops as soon as ``max_paths + 1`` paths are found, so over-cap
    pairs are discarded without fully enumerating their routes. Eligible
    pairs are ranked by greatest Haversine shortest-path distance, then
    preference for 50–500 alternatives, closeness to 200 paths, and lexical
    node IDs.
    """
    if (
        not isinstance(min_paths, int)
        or isinstance(min_paths, bool)
        or min_paths < 1
    ):
        raise ValueError("min_paths must be a positive integer")
    if (
        not isinstance(max_paths, int)
        or isinstance(max_paths, bool)
        or max_paths < min_paths
    ):
        raise ValueError("max_paths must be an integer >= min_paths")

    adjacency: dict[str, list[tuple[str, float]]] = {
        node: [] for node in network.nodes
    }
    for edge in network.edges:
        adjacency[edge.u].append((edge.v, edge.distance))
        if not edge.directed:
            adjacency[edge.v].append((edge.u, edge.distance))
    for neighbors in adjacency.values():
        neighbors.sort(key=lambda item: item[0])

    def path_count(start: str, end: str) -> tuple[float, int] | None:
        """Return shortest distance and count capped at max_paths + 1."""
        distances = {start: 0.0}
        pending = [(0.0, start)]
        while pending:
            current_distance, current = heappop(pending)
            if current_distance > distances[current]:
                continue
            for neighbor, edge_distance in adjacency[current]:
                candidate_distance = current_distance + edge_distance
                if candidate_distance < distances.get(neighbor, math.inf):
                    distances[neighbor] = candidate_distance
                    heappush(pending, (candidate_distance, neighbor))
        if end not in distances:
            return None

        count = 0

        def visit(current: str, path: frozenset[str]) -> None:
            nonlocal count
            if count > max_paths:
                return
            if current == end:
                count += 1
                return
            for neighbor, _ in adjacency[current]:
                if neighbor not in path:
                    visit(neighbor, path | {neighbor})
                    if count > max_paths:
                        return

        visit(start, frozenset({start}))
        return distances[end], count

    if source is not None and target is not None:
        if source not in adjacency or target not in adjacency or source == target:
            raise ValueError(
                f"Configured routing endpoints {source!r}, {target!r} are invalid"
            )
        selected = path_count(source, target)
        if selected is None:
            raise ValueError(
                f"No route exists from {source!r} to {target!r}"
            )
        _, count = selected
        if not min_paths <= count <= max_paths:
            count_description = (
                f"more than {max_paths}"
                if count > max_paths
                else str(count)
            )
            raise ValueError(
                f"Configured route {source!r}->{target!r} has "
                f"{count_description} simple paths; required range is "
                f"[{min_paths}, {max_paths}]"
            )
        return source, target, selected[1]

    candidates: list[tuple[float, int, str, str]] = []
    for start in sorted(adjacency):
        for end in sorted(adjacency):
            if start == end:
                continue
            result = path_count(start, end)
            if result is not None:
                shortest_distance, count = result
                if min_paths <= count <= max_paths:
                    candidates.append((shortest_distance, count, start, end))
    if not candidates:
        raise ValueError(
            f"No endpoint pair has between {min_paths} and {max_paths} simple "
            "paths"
        )
    _, count, selected_source, selected_target = min(
        candidates,
        key=lambda item: (
            -item[0],
            0 if 50 <= item[1] <= 500 else 1,
            abs(item[1] - 200),
            item[2],
            item[3],
        ),
    )
    return selected_source, selected_target, count


class PemsBayAdapter(DatasetAdapter):
    """Adapt PEMS-BAY inputs to canonical network and travel-time observations.

    Speeds in the long Parquet are interpreted as mph by default. They are
    converted to travel time in minutes using the Haversine edge length in km:
    ``distance_km / (speed_mph * 1.609344) * 60``. This is an approximate
    straight-line travel-time estimate. Automatic subnetworks use a BFS
    spanning tree and add 3–9 non-tree edges in increasing order, ranked by
    Haversine cycle length and sensor IDs. Endpoints are selected only when
    their bounded simple-path count is in ``[min_paths, max_paths]``. Edge
    direction follows ``direction_policy``: preserve adjacency arcs
    (``directed``) or use one undirected edge when either matrix direction is
    nonzero (``undirected``).
    """

    name = "pemsbay"
    distance_unit = "km"
    time_unit = "minutes"

    def __init__(
        self,
        selected_sensor_ids: Sequence[str] = (),
        *,
        locations_csv: str | Path,
        adjacency_pickle: str | Path,
        traffic_parquet: str | Path,
        require_connected: bool = True,
        speed_unit: str = "mph",
        n_sensors: int = 25,
        seed_sensor: str | None = None,
        extra_edges: int = 3,
        min_paths: int = 5,
        max_paths: int = 2000,
        time_slots: Sequence[RoutingTimeWindow] = DEFAULT_PEMS_BAY_TIME_SLOTS,
        min_slot_coverage: float = 0.5,
        direction_policy: str = "directed",
        source: str | None = None,
        target: str | None = None,
        sample_interval_minutes: int = 5,
        max_speed_imputation_gap: int = 3,
        timezone: str = "UTC",
    ) -> None:
        self.selected_sensor_ids = tuple(selected_sensor_ids)
        self.locations_csv = Path(locations_csv)
        self.adjacency_pickle = Path(adjacency_pickle)
        self.traffic_parquet = Path(traffic_parquet)
        self.require_connected = require_connected
        if (
            not isinstance(n_sensors, int)
            or isinstance(n_sensors, bool)
            or not 20 <= n_sensors <= 30
        ):
            raise ValueError("n_sensors must be between 20 and 30")
        if (
            not isinstance(min_paths, int)
            or isinstance(min_paths, bool)
            or min_paths < 1
        ):
            raise ValueError("min_paths must be a positive integer")
        if (
            not isinstance(max_paths, int)
            or isinstance(max_paths, bool)
            or max_paths < min_paths
        ):
            raise ValueError("max_paths must be >= min_paths")
        if (
            not isinstance(extra_edges, int)
            or isinstance(extra_edges, bool)
            or not 0 <= extra_edges <= 9
        ):
            raise ValueError("extra_edges must be an integer from 0 to 9")
        if not time_slots:
            raise ValueError("time_slots must define a full-day partition")
        ordered_slots = sorted(time_slots, key=lambda slot: slot.start_hour)
        if (
            ordered_slots[0].start_hour != 0
            or ordered_slots[-1].end_hour != 24
            or any(
                previous.end_hour != current.start_hour
                for previous, current in zip(
                    ordered_slots, ordered_slots[1:]
                )
            )
        ):
            raise ValueError(
                "time_slots must partition the full day without gaps or overlaps"
            )
        if len({slot.name for slot in ordered_slots}) != len(ordered_slots):
            raise ValueError("time_slots names must be unique")
        if (
            not isinstance(min_slot_coverage, (int, float))
            or isinstance(min_slot_coverage, bool)
            or not math.isfinite(float(min_slot_coverage))
            or not 0 < float(min_slot_coverage) <= 1
        ):
            raise ValueError("min_slot_coverage must be in (0, 1]")
        if (
            not isinstance(sample_interval_minutes, int)
            or isinstance(sample_interval_minutes, bool)
            or sample_interval_minutes <= 0
            or 60 % sample_interval_minutes != 0
        ):
            raise ValueError(
                "sample_interval_minutes must be a positive divisor of 60"
            )
        if any(
            ((slot.end_hour - slot.start_hour) * 60)
            % sample_interval_minutes
            for slot in ordered_slots
        ):
            raise ValueError(
                "Each time slot duration must be divisible by "
                "sample_interval_minutes"
            )
        if (
            not isinstance(max_speed_imputation_gap, int)
            or isinstance(max_speed_imputation_gap, bool)
            or max_speed_imputation_gap < 0
        ):
            raise ValueError("max_speed_imputation_gap must be non-negative")
        if not isinstance(direction_policy, str) or direction_policy not in {
            "directed",
            "undirected",
        }:
            raise ValueError(
                "direction_policy must be 'directed' or 'undirected'"
            )
        if (source is None) != (target is None):
            raise ValueError("Configure both source and target, or neither")
        self.n_sensors = n_sensors
        self.seed_sensor = seed_sensor
        self.extra_edges = extra_edges
        self.min_paths = min_paths
        self.max_paths = max_paths
        self.time_slots = tuple(ordered_slots)
        self.min_slot_coverage = float(min_slot_coverage)
        self.direction_policy = direction_policy
        self.configured_source = source
        self.configured_target = target
        self.sample_interval_minutes = sample_interval_minutes
        self.max_speed_imputation_gap = max_speed_imputation_gap
        self.timezone = timezone
        self.metadata: dict[str, object] = {
            "direction_policy": direction_policy,
            "extra_edges_start": extra_edges,
            "min_paths": min_paths,
            "max_paths": max_paths,
            "time_slots": [
                {
                    "name": slot.name,
                    "start_hour": slot.start_hour,
                    "end_hour": slot.end_hour,
                }
                for slot in self.time_slots
            ],
            "min_slot_coverage": self.min_slot_coverage,
            "distance_unit": "km",
            "time_unit": "minutes",
            "speed_unit": speed_unit,
            "travel_time_conversion": (
                "distance_km / (speed_mph * 1.609344) * 60; "
                "Haversine distance is approximate"
            ),
        }
        if speed_unit not in {"mph", "km/h"}:
            raise ValueError("speed_unit must be 'mph' or 'km/h'")
        self.speed_unit = speed_unit

    def build_network(self) -> Network:
        locations = _read_locations(self.locations_csv)
        adjacency_ids, matrix = _read_adjacency(self.adjacency_pickle)
        configured_sensors = self.selected_sensor_ids
        if not configured_sensors:
            candidates = tuple(
                sorted(
                    _eligible_sensor_ids(
                        locations, adjacency_ids, self.traffic_parquet
                    )
                )
            )
            if len(candidates) < self.n_sensors:
                raise ValueError(
                    f"Cannot select {self.n_sensors} connected sensors: only "
                    f"{len(candidates)} sensors have coordinates and traffic data"
                )
            sensor_count = self.n_sensors
            selection_description = (
                "BFS from eligible sensors in descending degree order (ID "
                "tie-break; configured seed_sensor overrides), lexical "
                "neighbor order; "
                "sensors without coordinates, adjacency, or valid traffic "
                "are excluded"
            )
        else:
            candidates = configured_sensors
            sensor_count = len(candidates)
            selection_description = "explicit configured sensor_ids"

        selected, tree_edges, cycle_edges, start = _select_sensor_topology(
            locations=locations,
            adjacency_ids=adjacency_ids,
            matrix=matrix,
            candidates=candidates,
            n_sensors=sensor_count,
            seed_sensor=self.seed_sensor,
        )
        last_endpoint_error: ValueError | None = None
        network: Network | None = None
        source: str | None = None
        target: str | None = None
        path_count: int | None = None
        selected_extra_edges: int | None = None
        maximum_extra_edges = min(9, len(cycle_edges))
        if maximum_extra_edges < self.extra_edges:
            raise ValueError(
                f"Only {len(cycle_edges)} cycle-closing edges are available; "
                f"extra_edges starts at {self.extra_edges}"
            )
        for extra_edge_count in range(
            self.extra_edges, maximum_extra_edges + 1
        ):
            edge_pairs = (*tree_edges, *cycle_edges[:extra_edge_count])
            candidate_network = load_pems_bay_subnetwork(
                selected,
                locations_csv=self.locations_csv,
                adjacency_pickle=self.adjacency_pickle,
                require_connected=self.require_connected,
                direction_policy=self.direction_policy,
                edge_pairs=edge_pairs,
            )
            try:
                selected_source, selected_target, selected_path_count = (
                    _select_routing_endpoints(
                        candidate_network,
                        source=self.configured_source,
                        target=self.configured_target,
                        min_paths=self.min_paths,
                        max_paths=self.max_paths,
                    )
                )
            except ValueError as error:
                last_endpoint_error = error
                continue
            network = candidate_network
            source = selected_source
            target = selected_target
            path_count = selected_path_count
            selected_extra_edges = extra_edge_count
            break

        if network is None or source is None or target is None:
            if len(cycle_edges) < self.extra_edges:
                detail = (
                    f"only {len(cycle_edges)} cycle-closing edges are available; "
                    f"extra_edges starts at {self.extra_edges}"
                )
            else:
                detail = str(last_endpoint_error or "no eligible endpoint pair")
            raise ValueError(
                f"Unable to construct a PEMS-BAY route with "
                f"{self.min_paths}..{self.max_paths} simple paths after "
                f"trying extra_edges={self.extra_edges}.."
                f"{maximum_extra_edges}: {detail}"
            )

        self.selected_sensor_ids = selected
        self.metadata.update(
            {
                "sensor_selection": selection_description,
                "selected_sensor_ids": selected,
                "n_sensors": len(selected),
                "sensor_selection_seed": start,
                "spanning_tree_edge_count": len(tree_edges),
                "available_cycle_edges": len(cycle_edges),
                "extra_edges": selected_extra_edges,
                "selected_edge_pairs": (
                    *tree_edges,
                    *cycle_edges[: selected_extra_edges or 0],
                ),
                "edge_count": len(network.edges),
                "source": source,
                "target": target,
                "endpoint_selection": (
                    "configured pair"
                    if self.configured_source is not None
                    else "largest Haversine shortest-path distance; prefer 50–500 "
                    "simple paths, then count closest to 200, then lexical "
                    "node pair"
                ),
                "selected_pair_simple_paths": path_count,
                "topology_selection": (
                    "BFS spanning tree plus the shortest Haversine cycle "
                    "lengths; ties by endpoint IDs"
                ),
            }
        )
        return network

    def load_edge_speed_data(
        self,
        *,
        network: Network | None = None,
    ) -> pd.DataFrame:
        """Read long Parquet speeds and assign each sensor to its incoming edges.

        A sensor supplies speed to every edge whose ``edge.v`` endpoint equals
        its ID. For directed edges this is the downstream sensor; for an
        undirected edge the stored endpoint order determines the assignment.
        Edge distance is Haversine endpoint distance, an approximation rather
        than road length. The returned speed column is normalized to mph.
        """
        try:
            import pandas as pd
        except ImportError as error:
            raise RuntimeError(
                "Reading PEMS-BAY observations requires pandas and a Parquet engine"
            ) from error

        network = network or self.build_network()
        frame = pd.read_parquet(self.traffic_parquet)
        required = {"time_index", "sensor_id", "speed"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(
                f"{self.traffic_parquet}: missing Parquet columns "
                f"{sorted(missing)}"
            )
        frame = frame.copy()
        frame["sensor_id"] = frame["sensor_id"].astype(str).str.strip()
        edge_rows = [
            {
                "sensor_id": edge.v,
                "edge_id": edge.edge_id,
                "distance_km": edge.distance,
            }
            for edge in network.edges
        ]
        edge_map = pd.DataFrame(
            edge_rows, columns=["sensor_id", "edge_id", "distance_km"]
        )
        selected = frame.loc[frame["sensor_id"].isin(network.nodes)]
        mapped = selected.merge(
            edge_map,
            on="sensor_id",
            how="inner",
            validate="many_to_many",
        )
        if mapped.empty:
            raise ValueError(
                f"{self.traffic_parquet}: no observations map to selected edges"
            )

        speed = pd.to_numeric(mapped["speed"], errors="coerce")
        if self.speed_unit == "km/h":
            speed = speed / MPH_TO_KMH
        result_columns = ["time_index", "edge_id", "distance_km"]
        if "timestamp" in mapped.columns:
            result_columns.insert(1, "timestamp")
        result = mapped.loc[:, result_columns].copy()
        result["speed_mph"] = speed
        return result

    def build_observations(
        self,
        *,
        network: Network | None = None,
    ) -> list[TrafficObservation]:
        """Return daily edge/slot means of travel time with coverage checks.

        Every edge receives speed from its ``edge.v`` sensor. Zero and
        non-finite speeds are missing; only internal gaps up to
        ``max_speed_imputation_gap`` five-minute samples are interpolated.
        Remaining gaps are omitted. Valid samples are converted to travel
        time before averaging within configured calendar-day slots. A cell
        must meet ``min_slot_coverage``; a day is retained only when every
        network edge meets that threshold in every slot. Returned ``day``
        values are consecutive indices over retained calendar days. If source
        timestamps are absent, ``time_index`` supplies a synthetic timeline.
        """
        import pandas as pd

        network = network or self.build_network()
        self.metadata.setdefault("selected_sensor_ids", network.nodes)
        self.metadata.setdefault("n_sensors", len(network.nodes))
        self.metadata.setdefault("edge_count", len(network.edges))
        from ..preprocess.dataset import clean_speed_series

        frame = clean_speed_series(
            self.load_edge_speed_data(network=network),
            max_gap=self.max_speed_imputation_gap,
            group_columns=("edge_id",),
            sample_interval_minutes=self.sample_interval_minutes,
            timezone=self.timezone,
        )
        if frame.empty:
            raise ValueError(
                f"{self.traffic_parquet}: no valid speed observations remain "
                "after cleaning"
            )

        data = frame.loc[
            :,
            [
                "timestamp",
                "edge_id",
                "distance_km",
                "speed_mph",
                "is_imputed",
            ],
        ].copy()
        data["travel_time"] = (
            data["distance_km"] / (data["speed_mph"] * MPH_TO_KMH) * 60.0
        )
        data["calendar_day"] = data["timestamp"].dt.normalize()
        data["hour"] = data["timestamp"].dt.hour
        data["time_slot"] = 0
        data["slot_name"] = ""
        expected_samples: dict[int, int] = {}
        for slot_number, slot in enumerate(self.time_slots, start=1):
            mask = data["hour"].ge(slot.start_hour) & data["hour"].lt(
                slot.end_hour
            )
            data.loc[mask, "time_slot"] = slot_number
            data.loc[mask, "slot_name"] = slot.name
            expected_samples[slot_number] = (
                (slot.end_hour - slot.start_hour)
                * 60
                // self.sample_interval_minutes
            )
        data = data.loc[data["time_slot"].gt(0)].copy()
        if data.empty:
            raise ValueError(
                f"{self.traffic_parquet}: no observations fall within "
                "configured time_slots"
            )

        grouped = (
            data.groupby(
                ["calendar_day", "time_slot", "slot_name", "edge_id"],
                sort=True,
                as_index=False,
            )
            .agg(
                travel_time=("travel_time", "mean"),
                speed_mph=("speed_mph", "mean"),
                is_imputed=("is_imputed", "any"),
                sample_count=("speed_mph", "size"),
            )
        )
        grouped["coverage"] = (
            grouped["sample_count"]
            / grouped["time_slot"].map(expected_samples)
        ).clip(upper=1.0)
        eligible_cells = grouped.loc[
            grouped["coverage"].ge(self.min_slot_coverage)
        ].copy()
        expected_cells_per_day = len(network.edges) * len(self.time_slots)
        cell_counts = eligible_cells.groupby("calendar_day").size()
        retained_days = tuple(
            sorted(
                cell_counts.index[cell_counts.eq(expected_cells_per_day)]
            )
        )
        all_days = tuple(sorted(data["calendar_day"].unique()))
        excluded_days = tuple(day for day in all_days if day not in retained_days)
        if not retained_days:
            raise ValueError(
                f"No calendar day has sufficient coverage "
                f"(min_slot_coverage={self.min_slot_coverage:g}) for all "
                f"{len(network.edges)} edges and {len(self.time_slots)} slots"
            )

        grouped = eligible_cells.loc[
            eligible_cells["calendar_day"].isin(retained_days)
        ].copy()
        day_indices = {
            calendar_day: index
            for index, calendar_day in enumerate(retained_days, start=1)
        }
        grouped["day"] = grouped["calendar_day"].map(day_indices)
        slot_by_number = {
            index: slot for index, slot in enumerate(self.time_slots, start=1)
        }
        edge_by_id = {edge.edge_id: edge for edge in network.edges}
        observations: list[TrafficObservation] = []
        for row in grouped.itertuples(index=False):
            edge = edge_by_id.get(row.edge_id)
            if edge is None:
                raise ValueError(
                    f"{self.traffic_parquet}: mapped unknown edge {row.edge_id!r}"
                )
            slot_number = int(row.time_slot)
            slot = slot_by_number[slot_number]
            calendar_day = pd.Timestamp(row.calendar_day)
            slot_timestamp = calendar_day + pd.Timedelta(hours=slot.start_hour)
            observations.append(
                TrafficObservation(
                    day=int(row.day),
                    day_of_week=calendar_day.strftime("%A"),
                    time_slot=slot_number,
                    slot_name=slot.name,
                    edge_id=edge.edge_id,
                    u=edge.u,
                    v=edge.v,
                    distance=edge.distance,
                    travel_time=float(row.travel_time),
                    timestamp=slot_timestamp.isoformat(),
                    speed_mph=float(row.speed_mph),
                    is_imputed=bool(row.is_imputed),
                    sample_count=int(row.sample_count),
                    coverage=float(row.coverage),
                )
            )
        self.metadata.update(
            {
                "min_slot_coverage": self.min_slot_coverage,
                "time_slots": [
                    {
                        "time_slot": index,
                        "name": slot.name,
                        "start_hour": slot.start_hour,
                        "end_hour": slot.end_hour,
                    }
                    for index, slot in slot_by_number.items()
                ],
                "calendar_days_seen": len(all_days),
                "calendar_days_retained": len(retained_days),
                "days_dropped_for_slot_coverage": len(excluded_days),
                "excluded_calendar_days": [
                    pd.Timestamp(day).date().isoformat()
                    for day in excluded_days
                ],
                "retained_day_index": {
                    pd.Timestamp(day).date().isoformat(): index
                    for day, index in day_indices.items()
                },
            }
        )
        return observations


def build_pemsbay_dataset(
    config_path: str | Path,
    output_dir: str | Path,
    *,
    traffic_parquet: str | Path | None = None,
    network: Network | None = None,
    adapter: PemsBayAdapter | None = None,
) -> Path:
    """Build an auxiliary model-data branch from slot-aggregated observations.

    This entry point reads long-form Parquet and either a supplied I1 network
    from WS1 or the graph inputs configured for the adapter; it does not load
    the raw HDF5 file. It writes to ``model_dataset/`` and is not consumed by
    WS4–WS6; those stages use the split I4 files produced by WS3. Observations
    are already aggregated to configured edge/day/time-slot cells by the
    adapter, so this branch performs a chronological day split without
    re-aggregating them.
    """
    config = load_config(config_path)
    if config.dataset.casefold() != "pemsbay":
        raise ValueError(
            f"{config_path}: expected dataset 'pemsbay', got {config.dataset!r}"
        )
    if config.speed_unit not in {"mph", "km/h"}:
        raise ValueError(f"{config_path}: speed_unit must be 'mph' or 'km/h'")
    if config.sensor_ids and not 20 <= len(config.sensor_ids) <= 30:
        raise ValueError(
            f"{config_path}: sensor_ids must select between 20 and 30 sensors"
        )

    def repository_path(value: str | Path) -> Path:
        path = Path(value)
        return path if path.is_absolute() else REPOSITORY_ROOT / path

    if config.locations_path is None or config.adjacency_path is None:
        raise ValueError(f"{config_path}: locations_path and adjacency_path are required")
    if config.traffic_parquet is None:
        raise ValueError(f"{config_path}: traffic_parquet is required")

    if adapter is None:
        adapter = PemsBayAdapter(
            config.sensor_ids,
            locations_csv=repository_path(config.locations_path),
            adjacency_pickle=repository_path(config.adjacency_path),
            traffic_parquet=repository_path(
                traffic_parquet or config.traffic_parquet
            ),
            speed_unit=config.speed_unit,
            n_sensors=config.n_sensors,
            seed_sensor=config.seed_sensor,
            extra_edges=config.extra_edges,
            min_paths=config.min_paths,
            max_paths=config.max_paths,
            time_slots=config.time_slots,
            min_slot_coverage=config.min_slot_coverage,
            direction_policy=config.direction_policy,
            source=config.source,
            target=config.target,
            sample_interval_minutes=config.sample_interval_minutes,
            max_speed_imputation_gap=config.max_speed_imputation_gap,
            timezone=config.timezone,
        )
    network = network or adapter.build_network()
    observations = adapter.build_observations(network=network)
    prepared = prepare_observation_splits(
        observations,
        train_fraction=config.train_fraction,
        valid_fraction=config.valid_fraction,
    )
    destination = repository_path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("train", "valid", "test"):
        prepared.raw_splits[name].to_csv(destination / f"{name}.csv", index=False)
        prepared.features[name].to_csv(
            destination / f"X_{name}.csv", index=False
        )
        prepared.targets[name].to_frame("travel_time").to_csv(
            destination / f"y_{name}.csv", index=False
        )
    prepared.split_manifest.to_csv(
        destination / "split_manifest.csv", index=False
    )
    (destination / "preprocessing_pipeline.json").write_text(
        json.dumps(
            prepared.pipeline_metadata,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )
    (destination / "data_dictionary.md").write_text(
        "# PEMS-BAY auxiliary model dataset\n\n"
        "Rows are edge/day/time-slot mean travel times after 5-minute "
        "cleaning and minimum-coverage filtering. Splits are chronological "
        "whole-day blocks; categorical vocabularies and distance scaling "
        "are fit on train only.\n",
        encoding="utf-8",
    )
    (destination / "adapter_metadata.json").write_text(
        json.dumps(adapter.metadata, indent=2, ensure_ascii=False, default=str)
        + "\n",
        encoding="utf-8",
    )
    return destination


__all__ = [
    "PemsBayAdapter",
    "build_pemsbay_dataset",
    "load_pems_bay_subnetwork",
    "select_pemsbay_sensors",
]
