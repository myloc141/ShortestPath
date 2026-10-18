"""PEMS-BAY adapter and Haversine network construction."""

from __future__ import annotations

import csv
import json
import math
from collections import deque
from pathlib import Path
import pickle
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    import pandas as pd

from ..common.config import load_config
from ..network.schema import Network, NetworkEdge
from ..network.validation import validate_network
from ..preprocess.dataset import (
    aggregate_hourly,
    observations_to_speed_frame,
    prepare_temporal_splits,
    render_data_dictionary,
    save_temporal_dataset,
)
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


def _read_adjacency(path: Path) -> tuple[list[str], object]:
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


def select_pemsbay_sensors(
    *,
    locations_csv: str | Path,
    adjacency_pickle: str | Path,
    traffic_parquet: str | Path,
    n_sensors: int = 25,
    seed_sensor: str | None = None,
) -> tuple[str, ...]:
    """Choose a deterministic connected sensor set by BFS.

    Sensors without valid coordinates, an adjacency entry, or any traffic
    samples are excluded. With no ``seed_sensor``, BFS tries eligible sensors
    in descending eligible degree, breaking ties by sensor ID, until a
    component can provide the requested count. Neighbor traversal is lexical
    and uses weak adjacency so the resulting node subset is connected
    regardless of edge direction.
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

    adjacency_index = {
        sensor_id: index for index, sensor_id in enumerate(adjacency_ids)
    }
    neighbors: dict[str, set[str]] = {sensor_id: set() for sensor_id in eligible}
    for source in sorted(eligible):
        source_index = adjacency_index[source]
        for target in eligible:
            if source == target:
                continue
            target_index = adjacency_index[target]
            if (
                float(matrix[source_index][target_index]) != 0
                or float(matrix[target_index][source_index]) != 0
            ):
                neighbors[source].add(target)

    if seed_sensor is not None:
        start = str(seed_sensor).strip()
        if start not in eligible:
            raise ValueError(
                f"seed_sensor {start!r} is not present in valid locations, "
                "adjacency, and traffic data"
            )
        starts = (start,)
    else:
        starts = tuple(
            sorted(
                eligible,
                key=lambda sensor_id: (-len(neighbors[sensor_id]), sensor_id),
            )
        )

    selected: list[str] = []
    selected_start: str | None = None
    reached_count = 0
    for start in starts:
        candidate: list[str] = []
        seen = {start}
        pending = deque([start])
        while pending and len(candidate) < n_sensors:
            current = pending.popleft()
            candidate.append(current)
            for neighbor in sorted(neighbors[current]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    pending.append(neighbor)
        reached_count = max(reached_count, len(candidate))
        if len(candidate) == n_sensors:
            selected = candidate
            selected_start = start
            break
    if selected_start is None:
        raise ValueError(
            f"BFS could select at most {reached_count} eligible sensors; "
            f"{n_sensors} are required"
        )
    return tuple(selected)


def load_pems_bay_subnetwork(
    selected_sensor_ids: Sequence[str],
    *,
    locations_csv: str | Path,
    adjacency_pickle: str | Path,
    require_connected: bool = True,
    direction_policy: str = "directed",
) -> Network:
    """Build a 20–30 sensor subnetwork from caller-selected sensor IDs.

    ``direction_policy="directed"`` preserves each non-zero matrix entry.
    ``"undirected"`` creates one undirected edge when either direction is
    present. Distances are Haversine straight-line estimates in km, not
    measured road lengths.
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

    edges: list[NetworkEdge] = []
    pairs = (
        ((u, v) for u in selected for v in selected if u != v)
        if direction_policy == "directed"
        else (
            (selected[first], selected[second])
            for first in range(len(selected))
            for second in range(first + 1, len(selected))
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
    max_paths: int,
) -> tuple[str, str, int]:
    """Choose a deterministic reachable endpoint pair within the path cap."""
    adjacency: dict[str, list[str]] = {node: [] for node in network.nodes}
    for edge in network.edges:
        adjacency[edge.u].append(edge.v)
        if not edge.directed:
            adjacency[edge.v].append(edge.u)
    for neighbors in adjacency.values():
        neighbors.sort()

    def path_count(start: str, end: str) -> tuple[int, int] | None:
        """Return shortest hop count and bounded simple-path count."""
        distances = {start: 0}
        pending = deque([start])
        while pending:
            current = pending.popleft()
            for neighbor in adjacency[current]:
                if neighbor not in distances:
                    distances[neighbor] = distances[current] + 1
                    pending.append(neighbor)
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
            for neighbor in adjacency[current]:
                if neighbor not in path:
                    visit(neighbor, path | {neighbor})
                    if count > max_paths:
                        return

        visit(start, frozenset({start}))
        if count > max_paths:
            return None
        return distances[end], count

    if source is not None and target is not None:
        if source not in adjacency or target not in adjacency or source == target:
            raise ValueError(
                f"Configured routing endpoints {source!r}, {target!r} are invalid"
            )
        selected = path_count(source, target)
        if selected is None:
            raise ValueError(
                f"No route exists from {source!r} to {target!r} within "
                f"max_paths={max_paths}"
            )
        return source, target, selected[1]

    candidates: list[tuple[int, int, str, str]] = []
    for start in sorted(adjacency):
        for end in sorted(adjacency):
            if start == end:
                continue
            result = path_count(start, end)
            if result is not None:
                hops, count = result
                candidates.append((hops, count, start, end))
    if not candidates:
        raise ValueError(
            f"No reachable routing endpoint pair has at most "
            f"max_paths={max_paths} simple paths"
        )
    hops, count, selected_source, selected_target = min(
        candidates, key=lambda item: (-item[0], -item[1], item[2], item[3])
    )
    return selected_source, selected_target, count


class PemsBayAdapter(DatasetAdapter):
    """Adapt PEMS-BAY inputs to canonical network and travel-time observations.

    Speeds in the long Parquet are interpreted as mph by default. They are
    converted to travel time in minutes using the Haversine edge length in km:
    ``distance_km / (speed_mph * 1.609344) * 60``. This is an approximate
    straight-line travel-time estimate. Edge direction follows
    ``direction_policy``: preserve adjacency arcs (``directed``) or use one
    undirected edge when either matrix direction is nonzero (``undirected``).
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
        max_paths: int = 1_000_000,
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
            not isinstance(max_paths, int)
            or isinstance(max_paths, bool)
            or max_paths < 1
        ):
            raise ValueError("max_paths must be positive")
        if (
            not isinstance(sample_interval_minutes, int)
            or isinstance(sample_interval_minutes, bool)
            or sample_interval_minutes <= 0
            or 60 % sample_interval_minutes != 0
        ):
            raise ValueError(
                "sample_interval_minutes must be a positive divisor of 60"
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
        self.max_paths = max_paths
        self.direction_policy = direction_policy
        self.configured_source = source
        self.configured_target = target
        self.sample_interval_minutes = sample_interval_minutes
        self.max_speed_imputation_gap = max_speed_imputation_gap
        self.timezone = timezone
        self.metadata: dict[str, object] = {
            "direction_policy": direction_policy,
            "max_paths": max_paths,
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
        selected = self.selected_sensor_ids
        if not selected:
            selected = select_pemsbay_sensors(
                locations_csv=self.locations_csv,
                adjacency_pickle=self.adjacency_pickle,
                traffic_parquet=self.traffic_parquet,
                n_sensors=self.n_sensors,
                seed_sensor=self.seed_sensor,
            )
            self.metadata["sensor_selection"] = (
                "BFS from highest-degree eligible seed whose component is "
                "large enough (or configured seed), lexical neighbor order; "
                "sensors without usable traffic are excluded"
            )
        else:
            self.metadata["sensor_selection"] = "explicit configured sensor_ids"
        self.selected_sensor_ids = tuple(selected)
        self.metadata["selected_sensor_ids"] = self.selected_sensor_ids
        self.metadata["n_sensors"] = len(selected)
        self.metadata["sensor_selection_seed"] = selected[0]
        network = load_pems_bay_subnetwork(
            selected,
            locations_csv=self.locations_csv,
            adjacency_pickle=self.adjacency_pickle,
            require_connected=self.require_connected,
            direction_policy=self.direction_policy,
        )
        source, target, path_count = _select_routing_endpoints(
            network,
            source=self.configured_source,
            target=self.configured_target,
            max_paths=self.max_paths,
        )
        self.metadata.update(
            {
                "source": source,
                "target": target,
                "endpoint_selection": (
                    "configured pair"
                    if self.configured_source is not None
                    else "maximum shortest-path hop distance, then most simple "
                    "paths, then lexical node pair"
                ),
                "selected_pair_simple_paths": path_count,
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
        """Read, clean, and convert each downstream sensor speed to travel time.

        Every edge receives the speed measured at its ``edge.v`` sensor (the
        downstream sensor for directed edges). Zero and non-finite speeds are
        treated as missing; only internal gaps up to
        ``max_speed_imputation_gap`` samples are interpolated. Remaining gaps
        are omitted. Speed is mph by default; Haversine edge length is in km
        and travel time is returned in minutes. When timestamps are absent,
        ``time_index`` supplies a synthetic timeline in the configured
        timezone and is not a verified calendar date.
        """
        import pandas as pd

        network = network or self.build_network()
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

        observations: list[TrafficObservation] = []
        edge_by_id = {edge.edge_id: edge for edge in network.edges}
        for row in frame.itertuples(index=False):
            timestamp = pd.Timestamp(row.timestamp)
            speed_mph = float(row.speed_mph)
            speed_kmh = speed_mph * MPH_TO_KMH
            day = timestamp.date().toordinal()
            slot = (
                timestamp.hour * (60 // self.sample_interval_minutes)
                + timestamp.minute // self.sample_interval_minutes
                + 1
            )
            day_of_week = timestamp.strftime("%A")
            edge = edge_by_id.get(row.edge_id)
            if edge is None:
                raise ValueError(
                    f"{self.traffic_parquet}: mapped unknown edge {row.edge_id!r}"
                )
            observations.append(
                TrafficObservation(
                    day=day,
                    day_of_week=day_of_week,
                    time_slot=slot,
                    slot_name=str(slot),
                    edge_id=edge.edge_id,
                    u=edge.u,
                    v=edge.v,
                    distance=edge.distance,
                    travel_time=edge.distance / speed_kmh * 60.0,
                    timestamp=timestamp.isoformat(),
                    speed_mph=speed_mph,
                    is_imputed=bool(row.is_imputed),
                )
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
    """Build hourly, time-split model data from configured long-form Parquet.

    This entry point reads long-form Parquet and either a supplied I1 network
    from WS1 or the graph inputs configured for the adapter; it does not load
    the raw HDF5 file. It obtains enriched five-minute records through
    ``PemsBayAdapter.build_observations``; the adapter uses the shared cleaner
    and maps the sensor at each edge's stored downstream endpoint.
    Dataset-neutral preprocessing then aggregates hourly, creates lag
    features, and splits chronologically.
    """
    config = load_config(config_path)
    if config.dataset.casefold() != "pemsbay":
        raise ValueError(
            f"{config_path}: expected dataset 'pemsbay', got {config.dataset!r}"
        )
    if len(config.routing_windows) < 2:
        raise ValueError(
            f"{config_path}: configure at least two routing_windows"
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
            max_paths=config.max_paths,
            direction_policy=config.direction_policy,
            source=config.source,
            target=config.target,
            sample_interval_minutes=config.sample_interval_minutes,
            max_speed_imputation_gap=config.max_speed_imputation_gap,
            timezone=config.timezone,
        )
        adapter.build_network()
    observations = adapter.build_observations(network=network)
    sample_frame = observations_to_speed_frame(observations)
    hourly = aggregate_hourly(
        sample_frame,
        routing_windows=config.routing_windows,
        sample_interval_minutes=config.sample_interval_minutes,
        timezone=config.timezone,
    )
    dataset = prepare_temporal_splits(
        hourly,
        lag_steps=config.lag_steps,
        train_fraction=config.train_fraction,
        valid_fraction=config.valid_fraction,
    )
    dictionary = render_data_dictionary(
        max_imputation_gap=config.max_speed_imputation_gap,
        lag_steps=config.lag_steps,
        routing_windows=config.routing_windows,
        timezone=config.timezone,
    )
    destination = repository_path(output_dir)
    save_temporal_dataset(
        dataset,
        destination,
        data_dictionary=dictionary,
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
