"""Module M4.1: Preprocess Adapter for Seervada Traffic Data.

Implements the exact interface contract specified in team_sheets/sheet_module_specification.csv:
- TrafficObservation: immutable record of one observation.
- SupervisedDataset: feature matrix + target vector with shape validation.
- edge_key(u, v): canonical unordered edge key.
- load_traffic_observations(csv_path, ...): loads and validates raw/cleaned observations.
- load_supervised_dataset(features_csv, target_csv): loads paired X, y CSV files.
- feature_rows_as_mappings(dataset): converts feature matrix to list of dict mappings.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set, Tuple

DAY_NAME_TO_INT = {
    "Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3, "Fri": 4, "Sat": 5, "Sun": 6,
    "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3, "Friday": 4, "Saturday": 5, "Sunday": 6
}


@dataclass(frozen=True)
class TrafficObservation:
    """Immutable record for a single traffic observation."""
    day: int
    day_of_week: int
    time_slot: int
    edge_id: str
    node_u: str
    node_v: str
    distance: float
    travel_time: float
    time_slot_name: Optional[str] = None


@dataclass(frozen=True)
class SupervisedDataset:
    """Container for paired feature matrix and target vector."""
    feature_names: Tuple[str, ...]
    features: Tuple[Tuple[float, ...], ...]
    target: Tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.features) != len(self.target):
            raise ValueError(
                f"Features count ({len(self.features)}) does not match target count ({len(self.target)})"
            )
        expected_width = len(self.feature_names)
        for idx, row in enumerate(self.features):
            if len(row) != expected_width:
                raise ValueError(
                    f"Row {idx} width ({len(row)}) does not match feature names count ({expected_width})"
                )


def edge_key(u: str, v: str) -> str:
    """Creates a canonical edge key by sorting the two nodes alphabetically."""
    u_str, v_str = str(u).strip(), str(v).strip()
    return f"{u_str}-{v_str}" if u_str < v_str else f"{v_str}-{u_str}"


def load_traffic_observations(
    csv_path: str | Path,
    expected_edge_ids: Optional[Set[str]] = None,
) -> Tuple[TrafficObservation, ...]:
    """Loads and validates a CSV of traffic observations.
    
    Required columns: day, day_of_week, time_slot, edge_id, node_u, node_v, distance, travel_time.
    Validates absence of duplicates by (day, time_slot, edge_id) and non-negative travel times.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"Observations CSV not found: {path}")

    observations: List[TrafficObservation] = []
    seen_keys: Set[Tuple[int, int, str]] = set()

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required_cols = {"day", "day_of_week", "time_slot", "edge_id", "node_u", "node_v", "distance", "travel_time"}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Missing required columns. Found: {reader.fieldnames}")

        for row_idx, row in enumerate(reader, start=2):
            day = int(row["day"])
            dow_val = row["day_of_week"].strip()
            if dow_val.isdigit():
                day_of_week = int(dow_val)
            elif dow_val in DAY_NAME_TO_INT:
                day_of_week = DAY_NAME_TO_INT[dow_val]
            else:
                raise ValueError(f"Row {row_idx}: Unknown day_of_week value: '{dow_val}'")

            time_slot = int(row["time_slot"])
            edge_id = row["edge_id"].strip()
            node_u = row["node_u"].strip()
            node_v = row["node_v"].strip()
            distance = float(row["distance"])
            travel_time = float(row["travel_time"])
            time_slot_name = row.get("time_slot_name", None)

            if travel_time <= 0:
                raise ValueError(f"Row {row_idx}: travel_time must be positive, got {travel_time}")
            if distance <= 0:
                raise ValueError(f"Row {row_idx}: distance must be positive, got {distance}")

            key = (day, time_slot, edge_id)
            if key in seen_keys:
                raise ValueError(f"Row {row_idx}: Duplicate observation for (day, slot, edge): {key}")
            seen_keys.add(key)

            if expected_edge_ids is not None and edge_id not in expected_edge_ids:
                raise ValueError(f"Row {row_idx}: Unexpected edge_id '{edge_id}'")

            obs = TrafficObservation(
                day=day,
                day_of_week=day_of_week,
                time_slot=time_slot,
                edge_id=edge_id,
                node_u=node_u,
                node_v=node_v,
                distance=distance,
                travel_time=travel_time,
                time_slot_name=time_slot_name,
            )
            observations.append(obs)

    return tuple(observations)


def load_supervised_dataset(
    features_csv: str | Path,
    target_csv: str | Path,
) -> SupervisedDataset:
    """Loads paired features CSV and target CSV into an immutable SupervisedDataset."""
    f_path = Path(features_csv)
    t_path = Path(target_csv)

    if not f_path.exists():
        raise FileNotFoundError(f"Features file not found: {f_path}")
    if not t_path.exists():
        raise FileNotFoundError(f"Target file not found: {t_path}")

    # Read features
    with open(f_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        feature_names = tuple(next(reader))
        features_list = []
        for row in reader:
            features_list.append(tuple(float(val) for val in row))

    # Read target
    with open(t_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        target_header = next(reader)
        if len(target_header) != 1:
            raise ValueError(f"Target CSV must have exactly one column, got: {target_header}")
        target_list = []
        for row in reader:
            target_list.append(float(row[0]))

    return SupervisedDataset(
        feature_names=feature_names,
        features=tuple(features_list),
        target=tuple(target_list),
    )


def feature_rows_as_mappings(dataset: SupervisedDataset) -> List[Dict[str, float]]:
    """Converts feature matrix to a list of dictionaries mapping feature_name -> value."""
    names = dataset.feature_names
    return [dict(zip(names, row)) for row in dataset.features]
