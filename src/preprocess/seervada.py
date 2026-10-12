"""Typed readers for Seervada traffic and preprocessed feature CSV files."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from ..network.schema import Network


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRAIN_CSV = REPOSITORY_ROOT / "workstream03" / "train.csv"
DEFAULT_TEST_CSV = REPOSITORY_ROOT / "workstream03" / "test.csv"


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


@dataclass(frozen=True)
class SupervisedDataset:
    feature_names: tuple[str, ...]
    features: tuple[tuple[float, ...], ...]
    target: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.features) != len(self.target):
            raise ValueError("Feature and target row counts differ")
        if any(len(row) != len(self.feature_names) for row in self.features):
            raise ValueError("Feature row width does not match feature_names")


def edge_key(u: str, v: str) -> tuple[str, str]:
    return tuple(sorted((str(u), str(v))))


def load_traffic_observations(
    csv_path: str | Path,
    *,
    network: Network | None = None,
    expected_edge_ids: set[str] | None = None,
) -> tuple[TrafficObservation, ...]:
    """Read WS3 train/test rows and validate them against an optional network."""
    path = Path(csv_path)
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
                distance = float(row["distance"])
                travel_time = float(row["travel_time"])
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
    """Read one numeric X/y split exported by the WS3 preprocessing pipeline."""
    feature_path = Path(features_csv)
    target_path = Path(target_csv)

    with feature_path.open("r", encoding="utf-8-sig", newline="") as file:
        feature_reader = csv.DictReader(file)
        feature_names = tuple(feature_reader.fieldnames or ())
        if not feature_names:
            raise ValueError(f"{feature_path}: missing feature header")
        feature_rows: list[tuple[float, ...]] = []
        for line_number, row in enumerate(feature_reader, start=2):
            try:
                values = tuple(float(row[name]) for name in feature_names)
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{feature_path}:{line_number}: all features must be numeric"
                ) from exc
            if any(not math.isfinite(value) for value in values):
                raise ValueError(f"{feature_path}:{line_number}: non-finite feature")
            feature_rows.append(values)

    with target_path.open("r", encoding="utf-8-sig", newline="") as file:
        target_reader = csv.DictReader(file)
        target_columns = tuple(target_reader.fieldnames or ())
        if len(target_columns) != 1:
            raise ValueError(
                f"{target_path}: expected exactly one target column, "
                f"got {target_columns}"
            )
        target_name = target_columns[0]
        targets: list[float] = []
        for line_number, row in enumerate(target_reader, start=2):
            try:
                value = float(row[target_name])
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    f"{target_path}:{line_number}: target must be numeric"
                ) from exc
            if not math.isfinite(value):
                raise ValueError(f"{target_path}:{line_number}: non-finite target")
            targets.append(value)

    return SupervisedDataset(
        feature_names=feature_names,
        features=tuple(feature_rows),
        target=tuple(targets),
    )


def feature_rows_as_mappings(
    dataset: SupervisedDataset,
) -> tuple[Mapping[str, float], ...]:
    """Expose feature rows by name for models that use categorical one-hot keys."""
    return tuple(
        dict(zip(dataset.feature_names, values)) for values in dataset.features
    )
