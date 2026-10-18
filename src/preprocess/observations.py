"""Dataset-neutral readers for travel-time observations and feature CSV files."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, TYPE_CHECKING

from ..network.schema import Network

if TYPE_CHECKING:
    from numpy.typing import ArrayLike


_DISTANCE_TO_KM = {"km": 1.0, "m": 0.001, "mi": 1.609344}
_TIME_TO_MINUTES = {
    "minutes": 1.0,
    "minute": 1.0,
    "min": 1.0,
    "seconds": 1.0 / 60.0,
    "s": 1.0 / 60.0,
    "hours": 60.0,
    "hour": 60.0,
    "h": 60.0,
}


@dataclass(frozen=True)
class TrafficObservation:
    day: int
    day_of_week: str
    time_slot: int
    slot_name: str
    edge_id: str
    u: str
    v: str
    distance: float
    travel_time: float
    timestamp: str | None = None
    speed_mph: float | None = None
    is_imputed: bool = False
    sample_count: int | None = None
    coverage: float | None = None


@dataclass(frozen=True)
class SupervisedDataset:
    feature_names: tuple[str, ...]
    features: ArrayLike
    target: ArrayLike

    def __post_init__(self) -> None:
        if len(self.features) != len(self.target):
            raise ValueError("Feature and target row counts differ")
        shape = getattr(self.features, "shape", None)
        if shape is not None:
            if len(shape) != 2 or shape[1] != len(self.feature_names):
                raise ValueError("Feature matrix width does not match feature_names")
        elif any(len(row) != len(self.feature_names) for row in self.features):
            raise ValueError("Feature row width does not match feature_names")


def edge_key(u: str, v: str) -> tuple[str, str]:
    return tuple(sorted((str(u), str(v))))


def load_observations(
    csv_path: str | Path,
    *,
    network: Network | None = None,
    expected_edge_ids: set[str] | None = None,
    distance_unit: str = "km",
    time_unit: str = "minutes",
) -> tuple[TrafficObservation, ...]:
    """Read observations and normalize distances to km and times to minutes."""
    path = Path(csv_path)
    distance_factor = _DISTANCE_TO_KM.get(distance_unit.casefold())
    time_factor = _TIME_TO_MINUTES.get(time_unit.casefold())
    if distance_factor is None:
        raise ValueError(f"Unsupported distance unit {distance_unit!r}")
    if time_factor is None:
        raise ValueError(f"Unsupported time unit {time_unit!r}")
    required = {
        "day",
        "day_of_week",
        "time_slot",
        "edge_id",
        "node_u",
        "node_v",
        "distance",
        "travel_time",
    }
    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                f"{path}: missing columns: {', '.join(sorted(missing))}"
            )

        rows: list[TrafficObservation] = []
        seen: set[tuple[int, int, str]] = set()
        for line_number, row in enumerate(reader, start=2):
            try:
                day = int(row["day"])
                slot = int(row["time_slot"])
                distance = float(row["distance"]) * distance_factor
                travel_time = float(row["travel_time"]) * time_factor
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{path}:{line_number}: invalid numeric value") from exc
            edge_id = row["edge_id"].strip()
            u = row["node_u"].strip()
            v = row["node_v"].strip()
            dow = row["day_of_week"].strip()
            if day < 1 or slot < 1 or not edge_id or not u or not v or not dow:
                raise ValueError(f"{path}:{line_number}: invalid key fields")
            if (
                not math.isfinite(distance)
                or distance <= 0
                or not math.isfinite(travel_time)
                or travel_time < 0
            ):
                raise ValueError(f"{path}:{line_number}: invalid distance or travel_time")
            key = (day, slot, edge_id)
            if key in seen:
                raise ValueError(f"{path}:{line_number}: duplicate observation {key}")
            seen.add(key)

            slot_name = (row.get("time_slot_name") or "").strip()
            rows.append(
                TrafficObservation(
                    day=day,
                    day_of_week=dow,
                    time_slot=slot,
                    slot_name=slot_name or str(slot),
                    edge_id=edge_id,
                    u=u,
                    v=v,
                    distance=distance,
                    travel_time=travel_time,
                )
            )

    if network is not None:
        network_edges = {edge_key(edge.u, edge.v): edge for edge in network.edges}
        for item in rows:
            key = edge_key(item.u, item.v)
            if key not in network_edges:
                raise ValueError(f"{path}: unknown network edge {key}")
            if not math.isclose(
                item.distance,
                network_edges[key].distance,
                rel_tol=1e-9,
                abs_tol=1e-9,
            ):
                raise ValueError(f"{path}: distance mismatch for edge {key}")

    if expected_edge_ids is not None:
        observed_ids = {item.edge_id for item in rows}
        if observed_ids != expected_edge_ids:
            raise ValueError(
                f"{path}: edge ID mismatch "
                f"(missing={sorted(expected_edge_ids - observed_ids)}, "
                f"unexpected={sorted(observed_ids - expected_edge_ids)})"
            )
    return tuple(rows)


def load_supervised_dataset(
    features_csv: str | Path,
    target_csv: str | Path,
) -> SupervisedDataset:
    """Read numeric X/y as NumPy arrays to avoid per-value Python objects."""
    import numpy as np
    import pandas as pd

    feature_path = Path(features_csv)
    target_path = Path(target_csv)
    feature_frame = pd.read_csv(feature_path, encoding="utf-8-sig")
    feature_names = tuple(str(column) for column in feature_frame.columns)
    if not feature_names:
        raise ValueError(f"{feature_path}: missing feature header")
    try:
        features = feature_frame.to_numpy(dtype=np.float64, copy=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{feature_path}: all features must be numeric") from error
    invalid_features = np.argwhere(~np.isfinite(features))
    if invalid_features.size:
        line_number = int(invalid_features[0, 0]) + 2
        raise ValueError(f"{feature_path}:{line_number}: non-finite feature")

    target_frame = pd.read_csv(target_path, encoding="utf-8-sig")
    target_columns = tuple(target_frame.columns)
    if len(target_columns) != 1:
        raise ValueError(
            f"{target_path}: expected exactly one target column, "
            f"got {target_columns}"
        )
    try:
        targets = target_frame.iloc[:, 0].to_numpy(dtype=np.float64, copy=False)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{target_path}: target must be numeric") from error
    invalid_targets = np.flatnonzero(~np.isfinite(targets))
    if invalid_targets.size:
        raise ValueError(
            f"{target_path}:{int(invalid_targets[0]) + 2}: non-finite target"
        )

    return SupervisedDataset(
        feature_names=feature_names,
        features=features,
        target=targets,
    )


def feature_rows_as_mappings(
    dataset: SupervisedDataset,
) -> tuple[Mapping[str, float], ...]:
    """Expose feature rows by name for models that use categorical one-hot keys."""
    return tuple(
        dict(zip(dataset.feature_names, values)) for values in dataset.features
    )
