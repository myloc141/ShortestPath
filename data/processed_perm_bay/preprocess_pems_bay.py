"""Inspect, validate, align, and export the PeMS-Bay source datasets.

This module is intentionally side-effect free on import. Run ``main`` to
process files. Pickle input is executable serialization and must be trusted.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import csv
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import json
import logging
import math
import os
from pathlib import Path
import pickle
import re
import tempfile
from typing import Any, Generator, Iterator, Mapping, Sequence

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


LOGGER = logging.getLogger("pems_bay_preprocessing")
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = REPOSITORY_ROOT / "data" / "raw_perm_bay"
DEFAULT_OUTPUT_DIR = REPOSITORY_ROOT / "data" / "processed_perm_bay"
TRAFFIC_BASENAME = "pems-bay"
ADJACENCY_BASENAME = "adj_mx_bay"
LOCATIONS_BASENAME = "graph_sensor_locations_bay"
TRAFFIC_CHUNK_ROWS = 2048
SUPPORTED_EXTENSIONS = {".h5", ".hdf5", ".hdf", ".pkl", ".pickle", ".csv", ".parquet"}
HDF5_SIGNATURE = b"\x89HDF\r\n\x1a\n"
PARQUET_SIGNATURE = b"PAR1"
OUTPUT_NAMES = (
    "traffic_speed_long.parquet",
    "sensor_metadata.parquet",
    "adjacency_matrix.parquet",
    "sensor_id_mapping.parquet",
)

LOCATION_COLUMN_ALIASES = {
    "sensor_id": {"sensorid", "sensor", "id", "index"},
    "latitude": {"latitude", "lat", "y"},
    "longitude": {"longitude", "lon", "lng", "long", "x"},
}
LONG_TRAFFIC_ALIASES = {
    "sensor_id": {"sensorid", "sensor"},
    "speed": {"speed", "traffic_speed", "value"},
    "timestamp": {"timestamp", "datetime", "date_time", "time"},
    "time_index": {"time_index", "timestep", "time_step"},
}


class PipelineError(RuntimeError):
    """A validation or source-inspection error safe to report to the caller."""


@dataclass(frozen=True)
class InputFile:
    logical_name: str
    path: Path
    detected_format: str


@dataclass(frozen=True)
class AdjacencyData:
    sensor_ids: tuple[str, ...]
    matrix: np.ndarray
    input_path: Path
    source_shape: tuple[int, int]
    symmetric: bool
    has_self_loops: bool
    is_binary: bool
    nonzero_count: int


@dataclass(frozen=True)
class LocationData:
    frame: pd.DataFrame
    input_path: Path
    detected_format: str
    duplicate_sensor_ids: tuple[str, ...]
    invalid_rows: tuple[int, ...]
    source_record_indices: Mapping[str, int]


def _normalized_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(value).strip().casefold())


def detect_format(path: Path) -> str:
    """Identify supported encodings by content signatures, not extensions."""
    try:
        with path.open("rb") as file:
            header = file.read(16384)
    except OSError as exc:
        raise PipelineError(f"Cannot read input {path}: {exc}") from exc
    if any(
        header[offset : offset + len(HDF5_SIGNATURE)] == HDF5_SIGNATURE
        for offset in (0, *range(512, min(len(header), 16384), 512))
    ):
        return "hdf5"
    if header.startswith(PARQUET_SIGNATURE):
        return "parquet"
    if not header:
        raise PipelineError(f"Input file is empty: {path}")
    if header[:1] == b"\x80":
        return "pickle"
    try:
        header.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PipelineError(
            f"Unsupported or unrecognized content format for {path}"
        ) from exc
    return "csv_text"


def discover_input(
    input_dir: Path,
    logical_name: str,
    basename: str,
    *,
    allowed_formats: set[str],
) -> InputFile:
    """Find exactly one input by recognized basename and inspect its content."""
    if not input_dir.is_dir():
        raise PipelineError(f"Input directory does not exist: {input_dir}")
    candidates = [
        path
        for path in input_dir.rglob("*")
        if path.is_file()
        and path.suffix.casefold() in SUPPORTED_EXTENSIONS
        and path.stem.casefold() == basename.casefold()
    ]
    if not candidates:
        raise PipelineError(
            f"Could not find {basename} with a supported extension under {input_dir}"
        )
    if len(candidates) != 1:
        listed = ", ".join(str(path) for path in sorted(candidates))
        raise PipelineError(f"Ambiguous {logical_name} inputs: {listed}")
    path = candidates[0]
    detected = detect_format(path)
    if detected not in allowed_formats:
        raise PipelineError(
            f"{path} has detected format {detected!r}, unsupported for {logical_name}"
        )
    LOGGER.info(
        "Discovered %s input: %s (extension=%s, detected=%s)",
        logical_name,
        path,
        path.suffix,
        detected,
    )
    return InputFile(logical_name, path, detected)


def inspect_hdf5(path: Path) -> dict[str, Any]:
    """List HDF5 keys and inspect pandas-compatible table dimensions."""
    try:
        with pd.HDFStore(path, mode="r") as store:
            descriptions = []
            for key in store.keys():
                storer = store.get_storer(key)
                description: dict[str, Any] = {
                    "key": key,
                    "storer_type": type(storer).__name__,
                    "is_table": bool(getattr(storer, "is_table", False)),
                }
                if hasattr(storer, "nrows"):
                    description["nrows"] = storer.nrows
                if hasattr(storer, "non_index_axes"):
                    axes = storer.non_index_axes
                    if axes and len(axes[0]) > 1:
                        description["columns"] = [str(item) for item in axes[0][1]]
                descriptions.append(description)
    except (ImportError, OSError, ValueError) as exc:
        raise PipelineError(
            f"Cannot inspect HDF5 file {path} with pandas/PyTables: {exc}"
        ) from exc
    if not descriptions:
        raise PipelineError(f"HDF5 file contains no inspectable keys: {path}")
    return {"keys": descriptions}


def _candidate_numeric_matrix(value: object) -> np.ndarray | None:
    """Convert only clearly two-dimensional numeric matrix candidates."""
    try:
        from scipy import sparse

        if sparse.issparse(value):
            matrix = value.toarray()
        else:
            matrix = np.asarray(value)
    except ImportError:
        matrix = np.asarray(value)
    except (TypeError, ValueError):
        return None
    if matrix.ndim != 2 or not np.issubdtype(matrix.dtype, np.number):
        return None
    return np.asarray(matrix, dtype=np.float64)


def _candidate_sensor_ids(value: object) -> tuple[str, ...] | None:
    if not isinstance(value, (tuple, list, np.ndarray)):
        return None
    try:
        items = list(value)
    except TypeError:
        return None
    if not items or any(isinstance(item, (tuple, list, dict, np.ndarray)) for item in items):
        return None
    identifiers = tuple(str(item).strip() for item in items)
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        return None
    return identifiers


def _extract_adjacency_payload(payload: object, path: Path) -> tuple[tuple[str, ...], np.ndarray]:
    """Find one unambiguous sensor-ID list and one square matrix in a pickle."""
    objects: list[object] = []
    if isinstance(payload, Mapping):
        objects.extend(payload.values())
    elif isinstance(payload, (tuple, list)):
        objects.extend(payload)
    else:
        objects.append(payload)

    named_ids: list[tuple[str, ...]] = []
    named_matrices: list[np.ndarray] = []
    if isinstance(payload, Mapping):
        for key, value in payload.items():
            key_name = _normalized_name(key)
            identifiers = _candidate_sensor_ids(value)
            matrix = _candidate_numeric_matrix(value)
            if identifiers is not None and any(
                token in key_name for token in ("sensorid", "sensors", "ids")
            ):
                named_ids.append(identifiers)
            if matrix is not None and any(
                token in key_name for token in ("adj", "matrix", "weight")
            ):
                named_matrices.append(matrix)

    id_candidates = named_ids or [
        identifiers
        for value in objects
        if (identifiers := _candidate_sensor_ids(value)) is not None
    ]
    matrix_candidates = named_matrices or [
        matrix
        for value in objects
        if (matrix := _candidate_numeric_matrix(value)) is not None
    ]

    if len(id_candidates) != 1:
        raise PipelineError(
            f"{path}: expected one unambiguous sensor ID sequence in pickle; "
            f"found {len(id_candidates)} candidates"
        )
    if len(matrix_candidates) != 1:
        raise PipelineError(
            f"{path}: expected one unambiguous numeric adjacency matrix in pickle; "
            f"found {len(matrix_candidates)} candidates"
        )
    sensor_ids, matrix = id_candidates[0], matrix_candidates[0]
    if matrix.shape != (len(sensor_ids), len(sensor_ids)):
        raise PipelineError(
            f"{path}: matrix shape {matrix.shape} does not match "
            f"{len(sensor_ids)} sensor IDs"
        )
    return sensor_ids, matrix


def load_adjacency(input_file: InputFile) -> AdjacencyData:
    """Load a trusted pickle or an explicit sensor-indexed matrix table."""
    if input_file.detected_format == "pickle":
        try:
            with input_file.path.open("rb") as file:
                payload = pickle.load(file)
        except Exception as exc:
            raise PipelineError(
                f"Cannot load trusted adjacency pickle {input_file.path}: {exc}"
            ) from exc
        sensor_ids, matrix = _extract_adjacency_payload(payload, input_file.path)
    elif input_file.detected_format in {"parquet", "csv_text"}:
        frame = _read_tabular(input_file.path, input_file.detected_format)
        if len(frame.columns) < 2:
            raise PipelineError(
                f"{input_file.path}: matrix table needs a row sensor ID and "
                "at least one sensor column"
            )
        row_id_column = _resolve_columns(
            list(frame.columns),
            {"sensor_id": LOCATION_COLUMN_ALIASES["sensor_id"]},
            required={"sensor_id"},
            path=input_file.path,
        )["sensor_id"]
        sensor_ids = tuple(
            frame[row_id_column].astype("string").str.strip().astype(str)
        )
        matrix_columns = [column for column in frame.columns if column != row_id_column]
        column_ids = tuple(str(column).strip() for column in matrix_columns)
        if len(set(sensor_ids)) != len(sensor_ids) or len(set(column_ids)) != len(column_ids):
            raise PipelineError(f"{input_file.path}: duplicated matrix sensor IDs")
        if set(sensor_ids) != set(column_ids):
            raise PipelineError(
                f"{input_file.path}: row and column sensor IDs do not match"
            )
        numeric = frame.loc[:, matrix_columns].apply(pd.to_numeric, errors="coerce")
        if numeric.isna().any().any():
            raise PipelineError(f"{input_file.path}: non-numeric matrix weights")
        matrix = numeric.loc[:, list(sensor_ids)].to_numpy(dtype=np.float64)
    else:
        raise PipelineError(
            f"Unsupported adjacency format {input_file.detected_format!r}"
        )
    if not np.isfinite(matrix).all():
        raise PipelineError("Adjacency matrix contains NaN or infinite weights")
    if (matrix < 0).any():
        raise PipelineError("Adjacency matrix contains negative weights")
    symmetric = bool(np.allclose(matrix, matrix.T, rtol=1e-9, atol=1e-12))
    diagonal = np.diag(matrix)
    has_self_loops = bool(np.any(diagonal != 0))
    nonzero = matrix[matrix != 0]
    is_binary = bool(np.isin(nonzero, (0.0, 1.0)).all())
    return AdjacencyData(
        sensor_ids=sensor_ids,
        matrix=matrix,
        input_path=input_file.path,
        source_shape=(int(matrix.shape[0]), int(matrix.shape[1])),
        symmetric=symmetric,
        has_self_loops=has_self_loops,
        is_binary=is_binary,
        nonzero_count=int(np.count_nonzero(matrix)),
    )


def _read_tabular(path: Path, detected_format: str) -> pd.DataFrame:
    if detected_format == "csv_text":
        return pd.read_csv(path)
    if detected_format == "parquet":
        try:
            return pd.read_parquet(path)
        except Exception as exc:
            raise PipelineError(
                f"Detected Parquet signature but cannot read {path}: {exc}"
            ) from exc
    raise PipelineError(f"Unsupported tabular format {detected_format!r} for {path}")


def _resolve_columns(
    columns: Sequence[object],
    aliases: Mapping[str, set[str]],
    *,
    required: set[str],
    path: Path,
) -> dict[str, object]:
    resolved: dict[str, object] = {}
    normalized = {_normalized_name(column): column for column in columns}
    for standard_name, candidates in aliases.items():
        matches = [normalized[candidate] for candidate in candidates if candidate in normalized]
        if len(matches) > 1:
            raise PipelineError(
                f"{path}: ambiguous columns for {standard_name}: {matches}"
            )
        if matches:
            resolved[standard_name] = matches[0]
    missing = required - resolved.keys()
    if missing:
        raise PipelineError(
            f"{path}: could not identify required columns: {sorted(missing)}"
        )
    return resolved


def load_locations(input_file: InputFile) -> LocationData:
    """Normalize location columns and retain every record for auditing."""
    frame = _read_tabular(input_file.path, input_file.detected_format)
    resolved = _resolve_columns(
        list(frame.columns),
        LOCATION_COLUMN_ALIASES,
        required={"sensor_id", "latitude", "longitude"},
        path=input_file.path,
    )
    normalized = pd.DataFrame(
        {
            "sensor_id": frame[resolved["sensor_id"]].astype("string").str.strip(),
            "latitude": pd.to_numeric(frame[resolved["latitude"]], errors="coerce"),
            "longitude": pd.to_numeric(frame[resolved["longitude"]], errors="coerce"),
        }
    )
    normalized["location_record_index"] = np.arange(len(normalized), dtype=np.int64)
    duplicates = tuple(
        sorted(
            normalized.loc[
                normalized["sensor_id"].duplicated(keep=False), "sensor_id"
            ]
            .dropna()
            .astype(str)
            .unique()
        )
    )
    valid = (
        normalized["sensor_id"].notna()
        & normalized["sensor_id"].ne("")
        & normalized["latitude"].between(-90, 90)
        & normalized["longitude"].between(-180, 180)
    )
    invalid_indices = tuple(
        int(index) for index in normalized.index[~valid].tolist()
    )
    source_indices = {
        str(row.sensor_id): int(row.location_record_index)
        for row in normalized.loc[valid].itertuples(index=False)
        if str(row.sensor_id) not in duplicates
    }
    return LocationData(
        frame=normalized,
        input_path=input_file.path,
        detected_format=input_file.detected_format,
        duplicate_sensor_ids=duplicates,
        invalid_rows=invalid_indices,
        source_record_indices=source_indices,
    )


def _inspect_traffic_source(input_file: InputFile) -> dict[str, Any]:
    if input_file.detected_format == "hdf5":
        inspection = inspect_hdf5(input_file.path)
        candidates = [
            item for item in inspection["keys"] if item.get("nrows") is not None
        ]
        if len(candidates) != 1:
            raise PipelineError(
                f"{input_file.path}: expected one pandas table key, "
                f"found {len(candidates)}; keys={inspection['keys']}"
            )
        inspection["selected_key"] = candidates[0]["key"]
        inspection["selected_shape"] = [
            candidates[0]["nrows"],
            len(candidates[0].get("columns", [])),
        ]
        return inspection
    if input_file.detected_format == "parquet":
        parquet_file = pq.ParquetFile(input_file.path)
        return {
            "shape": [
                int(parquet_file.metadata.num_rows),
                len(parquet_file.schema_arrow.names),
            ],
            "columns": list(parquet_file.schema_arrow.names),
            "schema": str(parquet_file.schema_arrow),
        }
    if input_file.detected_format == "csv_text":
        frame = pd.read_csv(input_file.path, nrows=32)
        with input_file.path.open("rb") as file:
            row_count = max(
                sum(
                    1
                    for row in csv.reader(
                        (line.decode("utf-8-sig") for line in file)
                    )
                    if row and any(value.strip() for value in row)
                )
                - 1,
                0,
            )
        return {
            "shape": [max(row_count, 0), int(len(frame.columns))],
            "columns": [str(column) for column in frame.columns],
            "dtypes_sample": {
                str(name): str(dtype) for name, dtype in frame.dtypes.items()
            },
        }
    frame = _read_tabular(input_file.path, input_file.detected_format)
    return {
        "shape": [int(frame.shape[0]), int(frame.shape[1])],
        "columns": [str(column) for column in frame.columns],
        "dtypes": {str(name): str(dtype) for name, dtype in frame.dtypes.items()},
        "index_type": type(frame.index).__name__,
        "index_name": str(frame.index.name) if frame.index.name is not None else None,
    }


@contextmanager
def _traffic_chunks(
    input_file: InputFile,
    inspection: Mapping[str, Any],
) -> Generator[Iterator[pd.DataFrame], None, None]:
    if input_file.detected_format == "csv_text":
        reader = pd.read_csv(input_file.path, chunksize=TRAFFIC_CHUNK_ROWS)
        try:
            yield iter(reader)
        finally:
            reader.close()
        return
    if input_file.detected_format == "parquet":
        parquet_file = pq.ParquetFile(input_file.path)

        def parquet_frames() -> Iterator[pd.DataFrame]:
            for batch in parquet_file.iter_batches(batch_size=TRAFFIC_CHUNK_ROWS):
                yield batch.to_pandas()

        yield parquet_frames()
        return
    if input_file.detected_format == "hdf5":
        key = str(inspection["selected_key"])
        try:
            store = pd.HDFStore(input_file.path, mode="r")
        except (ImportError, OSError, ValueError) as exc:
            raise PipelineError(f"Cannot reopen HDF5 input: {exc}") from exc
        try:
            storer = store.get_storer(key)
            if not getattr(storer, "is_table", False):
                def fixed_format_frames() -> Iterator[pd.DataFrame]:
                    frame = store.get(key)
                    for start in range(0, len(frame), TRAFFIC_CHUNK_ROWS):
                        yield frame.iloc[start : start + TRAFFIC_CHUNK_ROWS]

                yield fixed_format_frames()
            else:
                row_count = int(getattr(storer, "nrows", 0))

                def table_frames() -> Iterator[pd.DataFrame]:
                    for start in range(0, row_count, TRAFFIC_CHUNK_ROWS):
                        yield store.select(
                            key,
                            start=start,
                            stop=min(start + TRAFFIC_CHUNK_ROWS, row_count),
                        )

                yield table_frames()
        finally:
            store.close()
        return
    raise PipelineError(f"Unsupported traffic format {input_file.detected_format!r}")


def _detect_time_column(columns: Sequence[object]) -> object | None:
    matches = [
        column
        for column in columns
        if _normalized_name(column) in {"timestamp", "datetime", "datetimeindex", "time"}
    ]
    if len(matches) > 1:
        raise PipelineError(f"Ambiguous timestamp columns: {matches}")
    return matches[0] if matches else None


def _as_timestamp(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime, date, np.datetime64)):
        return pd.Timestamp(value).isoformat()
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        parsed = pd.to_datetime(text, errors="coerce", utc=False)
        if pd.isna(parsed):
            return None
        return pd.Timestamp(parsed).isoformat()
    return None


def _parse_time_index(value: object, path: Path) -> int:
    try:
        numeric = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        raise PipelineError(f"{path}: time_index values must be integers") from None
    if (
        not numeric.is_finite()
        or numeric != numeric.to_integral_value()
        or numeric < 0
        or numeric > 2**63 - 1
    ):
        raise PipelineError(
            f"{path}: time_index values must be finite, non-negative int64 values"
        )
    return int(numeric)


def _classify_traffic_frame(
    frame: pd.DataFrame,
    sensor_ids: tuple[str, ...],
    path: Path,
) -> tuple[str, dict[str, object], tuple[int, ...]]:
    aliases = _resolve_columns(
        list(frame.columns),
        LONG_TRAFFIC_ALIASES,
        required=set(),
        path=path,
    )
    if set(aliases) >= {"sensor_id", "speed"}:
        return "long", aliases, ()

    excluded: set[object] = set()
    timestamp_column = _detect_time_column(list(frame.columns))
    if timestamp_column is not None:
        excluded.add(timestamp_column)
    sensor_columns = [
        column for column in frame.columns if str(column).strip() in set(sensor_ids)
    ]
    if len(sensor_columns) != len(sensor_ids):
        raise PipelineError(
            f"{path}: traffic columns cannot be aligned to the adjacency sensor IDs; "
            f"matched {len(sensor_columns)} of {len(sensor_ids)}"
        )
    if set(sensor_columns) != set(frame.columns) - excluded:
        extra = set(frame.columns) - excluded - set(sensor_columns)
        raise PipelineError(
            f"{path}: wide traffic data has unrecognized columns: "
            f"{[str(value) for value in sorted(extra, key=str)]}"
        )
    ordered_columns = tuple(frame.columns.get_loc(sensor_id) if sensor_id in frame.columns
                            else next(index for index, column in enumerate(frame.columns)
                                      if str(column).strip() == sensor_id)
                            for sensor_id in sensor_ids)
    return "wide", {"timestamp": timestamp_column}, ordered_columns


def _load_traffic_data(
    input_file: InputFile,
    inspection: Mapping[str, Any],
    sensor_ids: tuple[str, ...],
    output_path: Path,
) -> dict[str, Any]:
    """Write wide or long source traffic data in bounded Parquet row groups."""
    output_schema = pa.schema(
        [
            ("time_index", pa.int64()),
            ("timestamp", pa.string()),
            ("sensor_id", pa.string()),
            ("speed", pa.float64()),
        ]
    )
    writer: pq.ParquetWriter | None = None
    traffic_sensor_ids: set[str] = set()
    traffic_column_indices: dict[str, int] = {}
    timestamps_seen: list[str] = []
    parsed_timestamps: list[pd.Timestamp] = []
    timestamp_indices: dict[pd.Timestamp, int] = {}
    long_sensor_presence: dict[int, bytearray] = {}
    sensor_index = {sensor_id: index for index, sensor_id in enumerate(sensor_ids)}
    time_count = 0
    rows_written = 0
    missing_speeds = 0
    invalid_speeds = 0
    min_speed: float | None = None
    max_speed: float | None = None
    layout: str | None = None
    first_frame = True
    order_is_monotonic = True
    previous_timestamp: pd.Timestamp | None = None
    previous_time_index: int | None = None
    timestamp_available = False
    time_source = "integer row index; source has no verified timestamps"

    try:
        with _traffic_chunks(input_file, inspection) as chunks:
            for frame in chunks:
                if first_frame:
                    layout, layout_info, wide_indices = _classify_traffic_frame(
                        frame, sensor_ids, input_file.path
                    )
                    first_frame = False
                    if layout == "wide":
                        time_column = layout_info["timestamp"]
                        timestamp_available = time_column is not None
                        for sensor_index, sensor_id in enumerate(sensor_ids):
                            traffic_column_indices[sensor_id] = wide_indices[sensor_index]
                        if timestamp_available:
                            time_source = f"timestamp column {time_column!s}"
                        elif isinstance(frame.index, pd.DatetimeIndex):
                            timestamp_available = True
                            time_source = "datetime index"
                    else:
                        timestamp_available = "timestamp" in layout_info
                        time_source = (
                            f"timestamp column {layout_info['timestamp']!s}"
                            if timestamp_available
                            else "integer row index; source has no verified timestamps"
                        )
                else:
                    next_layout, layout_info, wide_indices = _classify_traffic_frame(
                        frame, sensor_ids, input_file.path
                    )
                    if next_layout != layout:
                        raise PipelineError(
                            f"{input_file.path}: traffic layout changes between chunks"
                        )

                if layout == "wide":
                    time_column = layout_info["timestamp"]
                    speed_frame = (
                        frame.iloc[:, list(wide_indices)]
                        if wide_indices
                        else frame.loc[:, list(sensor_ids)]
                    )
                    raw_values = speed_frame.apply(
                        pd.to_numeric, errors="coerce"
                    ).to_numpy(dtype=np.float64, copy=False)
                    missing_speeds += int(pd.isna(speed_frame).to_numpy().sum())
                    invalid_speeds += int(
                        np.isnan(raw_values).sum()
                        - pd.isna(speed_frame).to_numpy().sum()
                    )
                    invalid_speeds += int(np.isinf(raw_values).sum())
                    invalid_speeds += int((raw_values < 0).sum())
                    finite_mask = np.isfinite(raw_values)
                    if finite_mask.any():
                        chunk_min = float(raw_values[finite_mask].min())
                        chunk_max = float(raw_values[finite_mask].max())
                        min_speed = chunk_min if min_speed is None else min(min_speed, chunk_min)
                        max_speed = chunk_max if max_speed is None else max(max_speed, chunk_max)
                    row_count = raw_values.shape[0]
                    raw_times: Sequence[object]
                    if time_column is not None:
                        raw_times = frame[time_column].tolist()
                    elif isinstance(frame.index, pd.DatetimeIndex):
                        raw_times = frame.index.tolist()
                    else:
                        raw_times = [None] * row_count
                    timestamps = [_as_timestamp(value) for value in raw_times]
                    for timestamp in timestamps:
                        if timestamp is not None:
                            parsed_timestamp = pd.Timestamp(timestamp)
                            if (
                                previous_timestamp is not None
                                and parsed_timestamp <= previous_timestamp
                            ):
                                order_is_monotonic = False
                            previous_timestamp = parsed_timestamp
                            timestamps_seen.append(timestamp)
                            parsed_timestamps.append(parsed_timestamp)
                    repeated_times = [
                        timestamps[index]
                        for index in range(1, len(timestamps))
                        if timestamps[index] is not None
                        and timestamps[index] == timestamps[index - 1]
                    ]
                    if repeated_times:
                        raise PipelineError(
                            f"{input_file.path}: duplicate timestamps found in traffic data"
                        )

                    indices = np.repeat(
                        np.arange(time_count, time_count + row_count, dtype=np.int64),
                        len(sensor_ids),
                    )
                    speeds = raw_values.reshape(-1)
                    timestamp_values = [
                        timestamp
                        for timestamp in timestamps
                        for _ in sensor_ids
                    ]
                    ids = list(sensor_ids) * row_count
                    batch = pa.RecordBatch.from_arrays(
                        [
                            pa.array(indices, type=pa.int64()),
                            pa.array(timestamp_values, type=pa.string()),
                            pa.array(ids, type=pa.string()),
                            pa.array(
                                [
                                    float(value) if math.isfinite(float(value)) else None
                                    for value in speeds
                                ],
                                type=pa.float64(),
                            ),
                        ],
                        schema=output_schema,
                    )
                    time_count += row_count
                else:
                    sensor_column = layout_info["sensor_id"]
                    speed_column = layout_info["speed"]
                    timestamp_column = layout_info.get("timestamp")
                    time_index_column = layout_info.get("time_index")
                    frame_ids = frame[sensor_column].astype("string").str.strip()
                    unknown_ids = set(frame_ids.dropna().astype(str)) - set(sensor_ids)
                    if unknown_ids:
                        raise PipelineError(
                            f"{input_file.path}: traffic contains sensor IDs "
                            f"not present in adjacency: {sorted(unknown_ids)[:10]}"
                        )
                    values = pd.to_numeric(frame[speed_column], errors="coerce")
                    missing_speeds += int(frame[speed_column].isna().sum())
                    invalid_speeds += int(
                        values.isna().sum() - frame[speed_column].isna().sum()
                    )
                    invalid_speeds += int(np.isinf(values.to_numpy(dtype=np.float64)).sum())
                    invalid_speeds += int((values < 0).fillna(False).sum())
                    finite_values = values[np.isfinite(values)]
                    if not finite_values.empty:
                        chunk_min = float(finite_values.min())
                        chunk_max = float(finite_values.max())
                        min_speed = chunk_min if min_speed is None else min(min_speed, chunk_min)
                        max_speed = chunk_max if max_speed is None else max(max_speed, chunk_max)
                    if timestamp_column is not None:
                        timestamp_values = [
                            _as_timestamp(value)
                            for value in frame[timestamp_column].tolist()
                        ]
                        timestamp_available = True
                        time_source = f"timestamp column {timestamp_column!s}"
                        output_time_indices: list[int] = []
                        for timestamp in timestamp_values:
                            if timestamp is None:
                                raise PipelineError(
                                    f"{input_file.path}: null/unparseable timestamp "
                                    "in long traffic data"
                                )
                            parsed_timestamp = pd.Timestamp(timestamp)
                            if parsed_timestamp not in timestamp_indices:
                                if (
                                    previous_timestamp is not None
                                    and parsed_timestamp < previous_timestamp
                                ):
                                    order_is_monotonic = False
                                timestamp_indices[parsed_timestamp] = len(timestamp_indices)
                                if parsed_timestamp != previous_timestamp:
                                    timestamps_seen.append(timestamp)
                                    parsed_timestamps.append(parsed_timestamp)
                                previous_timestamp = parsed_timestamp
                            elif parsed_timestamp != previous_timestamp:
                                order_is_monotonic = False
                            output_time_indices.append(
                                timestamp_indices[parsed_timestamp]
                            )
                        if not order_is_monotonic:
                            raise PipelineError(
                                f"{input_file.path}: long-format timestamps are not "
                                "non-decreasing"
                            )
                    elif time_index_column is not None:
                        output_time_indices = [
                            _parse_time_index(value, input_file.path)
                            for value in frame[time_index_column]
                        ]
                        if any(
                            current < previous
                            for previous, current in zip(
                                [previous_time_index, *output_time_indices[:-1]],
                                output_time_indices,
                            )
                            if previous is not None
                        ):
                            order_is_monotonic = False
                        if not order_is_monotonic:
                            raise PipelineError(
                                f"{input_file.path}: time_index values are not "
                                "monotonically increasing"
                            )
                        previous_time_index = output_time_indices[-1] if output_time_indices else previous_time_index
                        timestamp_values = [None] * len(frame)
                        time_source = f"integer time index column {time_index_column!s}"
                    else:
                        raise PipelineError(
                            f"{input_file.path}: long traffic layout needs an explicit "
                            "timestamp or time_index column"
                        )
                    ids_values = frame_ids.fillna("").astype(str).tolist()
                    for time_index, sensor_id in zip(output_time_indices, ids_values):
                        if not sensor_id:
                            raise PipelineError(
                                f"{input_file.path}: missing sensor ID in traffic data"
                            )
                        traffic_sensor_ids.add(sensor_id)
                        presence = long_sensor_presence.setdefault(
                            time_index, bytearray(len(sensor_ids))
                        )
                        index = sensor_index[sensor_id]
                        if presence[index]:
                            raise PipelineError(
                                f"{input_file.path}: duplicate observation for "
                                f"time_index={time_index}, sensor_id={sensor_id}"
                            )
                        presence[index] = 1
                    batch = pa.RecordBatch.from_arrays(
                        [
                            pa.array(output_time_indices, type=pa.int64()),
                            pa.array(timestamp_values, type=pa.string()),
                            pa.array(ids_values, type=pa.string()),
                            pa.array(
                                [
                                    float(value) if pd.notna(value) and math.isfinite(float(value)) else None
                                    for value in values.tolist()
                                ],
                                type=pa.float64(),
                            ),
                        ],
                        schema=output_schema,
                    )
                    time_count += len(frame)

                if writer is None:
                    writer = pq.ParquetWriter(output_path, output_schema, compression="zstd")
                writer.write_batch(batch)
                rows_written += batch.num_rows
    finally:
        if writer is not None:
            writer.close()

    if first_frame or writer is None:
        raise PipelineError(f"{input_file.path}: no traffic observations found")
    if layout == "wide":
        traffic_sensor_ids = set(sensor_ids)
    if layout == "long":
        incomplete_times = [
            time_index
            for time_index, presence in long_sensor_presence.items()
            if not all(presence)
        ]
        if incomplete_times:
            raise PipelineError(
                f"{input_file.path}: incomplete sensor coverage at "
                f"{len(incomplete_times)} time indices; examples={incomplete_times[:10]}"
            )
        time_count = len(long_sensor_presence)

    timestamp_differences = {
        int((right - left).total_seconds() * 1_000_000_000)
        for left, right in zip(parsed_timestamps, parsed_timestamps[1:])
    }
    sampling_interval_ns = (
        next(iter(timestamp_differences))
        if timestamp_differences and len(timestamp_differences) == 1
        else None
    )

    return {
        "layout": layout,
        "n_time_steps_or_rows": time_count,
        "n_sensor_ids": len(traffic_sensor_ids),
        "sensor_ids": sorted(traffic_sensor_ids),
        "traffic_column_indices": traffic_column_indices,
        "timestamps_available": timestamp_available,
        "time_source": time_source,
        "temporal_order_valid": order_is_monotonic,
        "first_timestamp": timestamps_seen[0] if timestamps_seen else None,
        "last_timestamp": timestamps_seen[-1] if timestamps_seen else None,
        "sampling_interval_ns": sampling_interval_ns,
        "missing_speed_values": missing_speeds,
        "invalid_speed_values": invalid_speeds,
        "speed_min": min_speed,
        "speed_max": max_speed,
        "output_rows": rows_written,
    }


def _make_id_mapping(
    adjacency: AdjacencyData,
    location: LocationData,
    traffic_info: Mapping[str, Any],
) -> pd.DataFrame:
    traffic_indices = traffic_info.get("traffic_column_indices", {})
    location_indices = location.source_record_indices
    traffic_ids = set(traffic_info.get("sensor_ids", []))
    rows = []
    for adjacency_index, sensor_id in enumerate(adjacency.sensor_ids):
        rows.append(
            {
                "sensor_id": sensor_id,
                "traffic_column_index": traffic_indices.get(sensor_id),
                "adjacency_index": adjacency_index,
                "location_record_index": location_indices.get(sensor_id),
                "in_traffic": sensor_id in traffic_ids,
                "in_locations": sensor_id in location_indices,
            }
        )
    return pd.DataFrame(rows)


def _write_parquet_frame(frame: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, path, compression="zstd")


def _output_validation(output_paths: Mapping[str, Path]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for logical_name, path in output_paths.items():
        parquet_file = pq.ParquetFile(path)
        row_count = sum(
            batch.num_rows
            for batch in parquet_file.iter_batches(batch_size=TRAFFIC_CHUNK_ROWS)
        )
        results[logical_name] = {
            "path": str(path),
            "rows": row_count,
            "schema": str(parquet_file.schema_arrow),
        }
    return results


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _render_quality_markdown(report: Mapping[str, Any]) -> str:
    inputs = report.get("inputs", {})
    traffic = report.get("traffic", {})
    adjacency = report.get("adjacency", {})
    validation = report.get("validation", {})
    lines = [
        "# PeMS-BAY data quality report",
        "",
        "## Inputs",
    ]
    for name, details in inputs.items():
        lines.append(
            f"- **{name}:** `{details.get('path', 'unavailable')}` "
            f"(format: {details.get('detected_format', 'unknown')})"
        )
    lines.extend(
        [
            "",
            "## Traffic",
            f"- Layout: {traffic.get('layout', 'unavailable')}",
            f"- Time steps/rows: {traffic.get('n_time_steps_or_rows', 'unavailable')}",
            f"- Sensors: {traffic.get('n_sensor_ids', 'unavailable')}",
            f"- Timestamp source: {traffic.get('time_source', 'unavailable')}",
            f"- Temporal ordering valid: {traffic.get('temporal_order_valid', 'unavailable')}",
            f"- First timestamp: {traffic.get('first_timestamp', 'unavailable')}",
            f"- Last timestamp: {traffic.get('last_timestamp', 'unavailable')}",
            f"- Uniform sampling interval (ns): {traffic.get('sampling_interval_ns', 'unavailable')}",
            f"- Missing speed values: {traffic.get('missing_speed_values', 'unavailable')}",
            "- Invalid speed values (non-numeric, infinite, or negative): "
            f"{traffic.get('invalid_speed_values', 'unavailable')}",
            "",
            "## Adjacency",
            f"- Shape: {adjacency.get('shape', 'unavailable')}",
            f"- Symmetric: {adjacency.get('symmetric', 'unavailable')}",
            f"- Contains self-loops: {adjacency.get('has_self_loops', 'unavailable')}",
            f"- Binary weights: {adjacency.get('is_binary', 'unavailable')}",
            f"- Nonzero weights: {adjacency.get('nonzero_count', 'unavailable')}",
            "",
            "## Cross-source validation",
        ]
    )
    for issue in validation.get("issues", []):
        lines.append(f"- {issue}")
    if not validation.get("issues"):
        lines.append("- All required checks passed.")
    if report.get("outputs"):
        lines.extend(["", "## Outputs"])
        for name, details in report["outputs"].items():
            lines.append(f"- `{name}`: {details.get('rows')} rows")
    lines.extend(
        [
            "",
            "## Transformations and assumptions",
            "- Sensor data is aligned by explicit sensor ID, never by assumed row order.",
            "- Missing speed values are preserved as Parquet nulls; no imputation is performed.",
            "- Traffic timestamps are preserved only when present and parseable; otherwise time_index is used.",
            "- The adjacency edge table preserves every nonzero matrix entry, including self-loops.",
            "- The original adjacency direction, weights, and sensor ordering are preserved.",
            "",
        ]
    )
    return "\n".join(lines)


def run_pipeline(
    *,
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> dict[str, Any]:
    """Run inspection, source validation, alignment, export, and read-back checks."""
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "inputs": {},
        "traffic": {},
        "adjacency": {},
        "locations": {},
        "validation": {"issues": []},
        "transformations": [
            "Content-based format detection",
            "Sensor alignment by explicit sensor IDs",
            "Long-format traffic export in bounded chunks",
            "No traffic imputation or adjacency normalization",
        ],
        "outputs": {},
    }
    temp_paths: dict[str, Path] = {}
    processing_error: Exception | None = None

    try:
        traffic_input = discover_input(
            input_dir,
            "traffic",
            TRAFFIC_BASENAME,
            allowed_formats={"hdf5", "parquet", "csv_text"},
        )
        adjacency_input = discover_input(
            input_dir,
            "adjacency",
            ADJACENCY_BASENAME,
            allowed_formats={"pickle", "parquet", "csv_text"},
        )
        locations_input = discover_input(
            input_dir,
            "locations",
            LOCATIONS_BASENAME,
            allowed_formats={"parquet", "csv_text"},
        )
        for item in (traffic_input, adjacency_input, locations_input):
            report["inputs"][item.logical_name] = {
                "path": str(item.path),
                "extension": item.path.suffix,
                "detected_format": item.detected_format,
            }

        traffic_inspection = _inspect_traffic_source(traffic_input)
        report["inputs"]["traffic"]["inspection"] = traffic_inspection
        adjacency = load_adjacency(adjacency_input)
        report["adjacency"] = {
            "path": str(adjacency.input_path),
            "shape": adjacency.source_shape,
            "sensor_count": len(adjacency.sensor_ids),
            "sensor_ids": adjacency.sensor_ids,
            "symmetric": adjacency.symmetric,
            "has_self_loops": adjacency.has_self_loops,
            "is_binary": adjacency.is_binary,
            "nonzero_count": adjacency.nonzero_count,
            "negative_weight_count": int(np.count_nonzero(adjacency.matrix < 0)),
            "non_finite_weight_count": int(np.count_nonzero(~np.isfinite(adjacency.matrix))),
        }
        location = load_locations(locations_input)
        report["locations"] = {
            "path": str(location.input_path),
            "detected_format": location.detected_format,
            "record_count": int(len(location.frame)),
            "unique_sensor_count": int(location.frame["sensor_id"].nunique(dropna=True)),
            "duplicate_sensor_ids": location.duplicate_sensor_ids,
            "invalid_record_indices": location.invalid_rows,
        }

        if location.duplicate_sensor_ids:
            report["validation"]["issues"].append(
                "Duplicate sensor IDs in locations; no duplicate-resolution policy was applied"
            )
        if location.invalid_rows:
            report["validation"]["issues"].append(
                f"Invalid or missing location rows: {list(location.invalid_rows)}"
            )

        location_ids = set(location.source_record_indices)
        adjacency_ids = set(adjacency.sensor_ids)
        if location_ids != adjacency_ids:
            report["validation"]["issues"].append(
                "Location and adjacency sensor IDs differ "
                f"(missing_locations={sorted(adjacency_ids - location_ids)}, "
                f"locations_only={sorted(location_ids - adjacency_ids)})"
            )
        if report["validation"]["issues"]:
            raise PipelineError("Source consistency checks failed; see quality report")

        with tempfile.NamedTemporaryFile(
            prefix="traffic_speed_long.",
            suffix=".tmp.parquet",
            dir=output_dir,
            delete=False,
        ) as temp_file:
            traffic_temp = Path(temp_file.name)
        temp_paths["traffic_speed_long.parquet"] = traffic_temp
        traffic_info = _load_traffic_data(
            traffic_input,
            traffic_inspection,
            adjacency.sensor_ids,
            traffic_temp,
        )
        report["traffic"] = traffic_info
        traffic_ids = set(traffic_info["sensor_ids"])
        if traffic_ids != adjacency_ids:
            report["validation"]["issues"].append(
                "Traffic and adjacency sensor IDs differ "
                f"(missing_traffic={sorted(adjacency_ids - traffic_ids)}, "
                f"traffic_only={sorted(traffic_ids - adjacency_ids)})"
            )
        if not traffic_info["temporal_order_valid"]:
            report["validation"]["issues"].append(
                "Traffic timestamps/time indices are not in valid order"
            )
        if traffic_info["invalid_speed_values"]:
            report["validation"]["issues"].append(
                f"Invalid speed values found: {traffic_info['invalid_speed_values']}"
            )
        if report["validation"]["issues"]:
            raise PipelineError("Traffic validation failed; see quality report")

        valid_locations = location.frame.loc[
            location.frame["sensor_id"].isin(adjacency_ids),
            ["sensor_id", "latitude", "longitude", "location_record_index"],
        ].copy()
        valid_locations = valid_locations.sort_values(
            "sensor_id", kind="stable"
        ).reset_index(drop=True)
        metadata_frame = valid_locations[["sensor_id", "latitude", "longitude"]].copy()

        nonzero_rows, nonzero_cols = np.nonzero(adjacency.matrix)
        adjacency_frame = pd.DataFrame(
            {
                "source_sensor_id": [
                    adjacency.sensor_ids[index] for index in nonzero_rows
                ],
                "target_sensor_id": [
                    adjacency.sensor_ids[index] for index in nonzero_cols
                ],
                "weight": adjacency.matrix[nonzero_rows, nonzero_cols],
            }
        )
        mapping_frame = _make_id_mapping(adjacency, location, traffic_info)
        frames = {
            "sensor_metadata.parquet": metadata_frame,
            "adjacency_matrix.parquet": adjacency_frame,
            "sensor_id_mapping.parquet": mapping_frame,
        }
        for name, frame in frames.items():
            with tempfile.NamedTemporaryFile(
                prefix=f"{Path(name).stem}.",
                suffix=".tmp.parquet",
                dir=output_dir,
                delete=False,
            ) as temp_file:
                temp_path = Path(temp_file.name)
            temp_paths[name] = temp_path
            _write_parquet_frame(frame, temp_path)

        # Validate temporary outputs before replacing any prior final outputs.
        temp_output_details = _output_validation(
            {name: path for name, path in temp_paths.items()}
        )
        if (
            temp_output_details["traffic_speed_long.parquet"]["rows"]
            != traffic_info["output_rows"]
        ):
            raise PipelineError(
                "Traffic output row count does not match the number of rows written"
            )
        for name, temporary_path in temp_paths.items():
            os.replace(temporary_path, output_dir / name)
        report["outputs"] = _output_validation(
            {
                name: output_dir / name
                for name in ("traffic_speed_long.parquet", *frames.keys())
            }
        )
        report["validation"]["passed"] = True
        report["validation"]["checks"] = [
            "adjacency matrix is square and matches its sensor ID list",
            "source sensor IDs align exactly",
            "all location coordinates are valid and unique",
            "traffic ordering is preserved",
            "Parquet outputs were read back and schemas/row counts recorded",
        ]
        report["temporary_output_validation"] = temp_output_details
    except Exception as exc:
        processing_error = exc
        if not isinstance(exc, PipelineError):
            report["validation"]["issues"].append(
                f"{type(exc).__name__}: {exc}"
            )
        report["validation"]["passed"] = False
        LOGGER.exception("PEMS-BAY preprocessing failed")
    finally:
        for temporary_path in temp_paths.values():
            if temporary_path.exists():
                temporary_path.unlink()
        json_path = output_dir / "data_quality_report.json"
        markdown_path = output_dir / "data_quality_report.md"
        _write_json_atomic(json_path, report)
        markdown_path.write_text(
            _render_quality_markdown(report),
            encoding="utf-8",
        )

    if processing_error is not None:
        raise PipelineError(
            f"Preprocessing failed: {processing_error}. "
            f"See {output_dir / 'data_quality_report.md'}"
        ) from processing_error
    return report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect and preprocess trusted PeMS-BAY input files."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    report = run_pipeline(input_dir=args.input_dir, output_dir=args.output_dir)
    LOGGER.info(
        "Preprocessing complete: %s sensors, %s time steps",
        report["traffic"]["n_sensor_ids"],
        report["traffic"]["n_time_steps_or_rows"],
    )


if __name__ == "__main__":
    main()
