"""Build a directed PEMS-BAY sensor subnetwork using Haversine estimates."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import pickle
from typing import Sequence

from .schema import Network, NetworkEdge
from .validation import validate_network


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PEMS_LOCATIONS_CSV = (
    REPOSITORY_ROOT / "data" / "raw_perm_bay" / "graph_sensor_locations_bay.csv"
)
DEFAULT_PEMS_ADJACENCY_PICKLE = (
    REPOSITORY_ROOT / "data" / "raw_perm_bay" / "adj_mx_bay.pkl"
)
EARTH_RADIUS_KM = 6371.0088


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
        payload = pickle.load(pickle_file)
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


def load_pems_bay_subnetwork(
    selected_sensor_ids: Sequence[str],
    *,
    locations_csv: str | Path = DEFAULT_PEMS_LOCATIONS_CSV,
    adjacency_pickle: str | Path = DEFAULT_PEMS_ADJACENCY_PICKLE,
    require_connected: bool = True,
) -> Network:
    """Build a 20–30 sensor subnetwork from caller-selected sensor IDs.

    A non-zero adjacency-matrix element creates one directed edge in that
    matrix's direction. Distances are Haversine straight-line estimates in km,
    not measured road lengths.
    """
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
    for u in selected:
        for v in selected:
            if u == v:
                continue
            raw_weight = matrix[index_by_id[u]][index_by_id[v]]
            try:
                weight = float(raw_weight)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"Adjacency value for {u!r} -> {v!r} is not numeric"
                ) from exc
            if not math.isfinite(weight):
                raise ValueError(f"Adjacency value for {u!r} -> {v!r} is not finite")
            if weight == 0:
                continue

            edges.append(
                NetworkEdge(
                    edge_id=f"edge_{len(edges) + 1:03d}",
                    u=u,
                    v=v,
                    distance=_haversine_km(locations[u], locations[v]),
                    directed=True,
                )
            )

    network = Network(
        nodes=selected,
        edges=tuple(edges),
        distance_unit="km",
        distance_is_approximate=True,
        distance_method=(
            "Haversine great-circle distance from sensor coordinates; "
            "approximation of road distance"
        ),
    )
    report = validate_network(network, require_connected=require_connected)
    if not report.is_valid:
        raise ValueError("Invalid PEMS-BAY subnetwork: " + "; ".join(report.errors))
    return network
