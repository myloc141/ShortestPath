"""Dataset-neutral time-series cleaning, feature preparation, and persistence."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import pickle
from typing import TYPE_CHECKING, Any, Mapping, Protocol, Sequence

if TYPE_CHECKING:
    import pandas as pd

    from ..common.config import RoutingTimeWindow


@dataclass(frozen=True)
class TemporalDataset:
    """Prepared chronological splits and train-fitted feature transformer."""

    raw_splits: Mapping[str, pd.DataFrame]
    features: Mapping[str, pd.DataFrame]
    targets: Mapping[str, pd.Series]
    split_manifest: pd.DataFrame
    transformer: object


@dataclass(frozen=True)
class ObservationSplits:
    """Chronological train/validation/test data and train-fitted features."""

    raw_splits: Mapping[str, pd.DataFrame]
    features: Mapping[str, pd.DataFrame]
    targets: Mapping[str, pd.Series]
    split_manifest: pd.DataFrame
    pipeline_metadata: Mapping[str, Any]


class ObservationLike(Protocol):
    day: int
    day_of_week: str
    time_slot: int
    slot_name: str
    edge_id: str
    u: str
    v: str
    distance: float
    travel_time: float


class SpeedObservationLike(Protocol):
    timestamp: str | None
    edge_id: str
    distance: float
    speed_mph: float | None
    travel_time: float
    is_imputed: bool


def prepare_observation_splits(
    observations: Sequence[ObservationLike] | pd.DataFrame,
    *,
    train_fraction: float = 0.8,
    valid_fraction: float = 0.1,
) -> ObservationSplits:
    """Split observations by whole chronological days and encode features.

    Category vocabularies and the distance mean/standard deviation are learned
    from the training split only. The function is pure with respect to files:
    callers receive all splits and metadata in memory.
    """
    import pandas as pd

    if isinstance(observations, pd.DataFrame):
        data = observations.copy()
    else:
        data = pd.DataFrame(
            [
                {
                    "day": item.day,
                    "day_of_week": item.day_of_week,
                    "time_slot": item.time_slot,
                    "time_slot_name": item.slot_name,
                    "is_weekend": item.day_of_week in {"Saturday", "Sunday"},
                    "edge_id": item.edge_id,
                    "node_u": item.u,
                    "node_v": item.v,
                    "distance": item.distance,
                    "travel_time": item.travel_time,
                }
                for item in observations
            ]
        )

    required = {
        "day",
        "day_of_week",
        "time_slot",
        "time_slot_name",
        "is_weekend",
        "edge_id",
        "node_u",
        "node_v",
        "distance",
        "travel_time",
    }
    missing = required - set(data.columns)
    if missing:
        raise ValueError(
            f"observations are missing columns: {sorted(missing)}"
        )
    if data.empty or data[list(required)].isna().any().any():
        raise ValueError("observations are empty or contain missing required values")
    if not 0 < train_fraction < 1 or not 0 < valid_fraction < 1:
        raise ValueError("split fractions must be between zero and one")
    if train_fraction + valid_fraction >= 1:
        raise ValueError("train_fraction + valid_fraction must be less than one")

    days = sorted(
        value.item() if hasattr(value, "item") else value
        for value in data["day"].unique()
    )
    if len(days) < 3:
        raise ValueError("at least three distinct days are required for splitting")
    train_count = int(len(days) * train_fraction)
    valid_count = int(len(days) * valid_fraction)
    if train_count < 1 or valid_count < 1 or train_count + valid_count >= len(days):
        raise ValueError(
            "split fractions must leave at least one full day in each split"
        )

    day_groups = {
        "train": set(days[:train_count]),
        "valid": set(days[train_count : train_count + valid_count]),
        "test": set(days[train_count + valid_count :]),
    }
    raw_splits = {
        name: data.loc[data["day"].isin(group_days)]
        .reset_index(drop=True)
        for name, group_days in day_groups.items()
    }
    reference_edges = set(raw_splits["train"]["edge_id"])
    reference_slots = set(raw_splits["train"]["time_slot"])
    for name in ("valid", "test"):
        if set(raw_splits[name]["edge_id"]) != reference_edges:
            raise ValueError(f"Train/{name} splits contain different edge IDs")
        if set(raw_splits[name]["time_slot"]) != reference_slots:
            raise ValueError(f"Train/{name} splits contain different time slots")

    categorical = ("edge_id", "time_slot", "day_of_week")
    categories = {
        column: sorted(
            value.item() if hasattr(value, "item") else value
            for value in raw_splits["train"][column].unique()
        )
        for column in categorical
    }
    distance_mean = float(raw_splits["train"]["distance"].mean())
    distance_std = float(raw_splits["train"]["distance"].std())
    if not math.isfinite(distance_mean) or not math.isfinite(distance_std):
        raise ValueError("Training distances must have finite statistics")
    if distance_std <= 0:
        distance_std = 1.0

    feature_names = ["distance", "is_weekend"]
    for column in categorical:
        feature_names.extend(
            f"{column}_{value}" for value in categories[column]
        )

    features: dict[str, pd.DataFrame] = {}
    targets: dict[str, pd.Series] = {}
    for name, split in raw_splits.items():
        feature_columns: dict[str, pd.Series] = {
            "distance": (split["distance"] - distance_mean) / distance_std,
            "is_weekend": split["is_weekend"].astype(float),
        }
        for column in categorical:
            for category in categories[column]:
                feature_columns[f"{column}_{category}"] = (
                    split[column] == category
                ).astype(float)
        features[name] = pd.DataFrame(feature_columns, columns=feature_names)
        targets[name] = split["travel_time"].reset_index(drop=True)

    manifest = pd.DataFrame(
        [
            {
                "split": name,
                "start_day": split["day"].min(),
                "end_day": split["day"].max(),
                "n_days": int(split["day"].nunique()),
                "n_rows": len(split),
            }
            for name, split in raw_splits.items()
        ]
    )
    metadata = {
        "split_policy": "chronological whole-day blocks",
        "train_fraction": train_fraction,
        "valid_fraction": valid_fraction,
        "train_days": sorted(day_groups["train"]),
        "valid_days": sorted(day_groups["valid"]),
        "test_days": sorted(day_groups["test"]),
        "feature_names": feature_names,
        "categories": categories,
        "distance_scaler": {"mean": distance_mean, "std": distance_std},
        "train_rows": len(raw_splits["train"]),
        "valid_rows": len(raw_splits["valid"]),
        "test_rows": len(raw_splits["test"]),
        "target": "travel_time",
    }
    return ObservationSplits(
        raw_splits=raw_splits,
        features=features,
        targets=targets,
        split_manifest=manifest,
        pipeline_metadata=metadata,
    )


def _ensure_timestamp(
    frame: pd.DataFrame,
    *,
    sample_interval_minutes: int,
    timezone: str,
) -> pd.DataFrame:
    import pandas as pd

    if sample_interval_minutes <= 0 or 60 % sample_interval_minutes != 0:
        raise ValueError("sample_interval_minutes must be a positive divisor of 60")
    data = frame.copy()
    if "timestamp" in data.columns:
        present = (
            data["timestamp"].notna()
            & data["timestamp"].astype(str).str.strip().ne("")
        )
        if present.any() and not present.all():
            raise ValueError("timestamp values must all be valid or all be absent")
        if present.all():
            timestamps = pd.to_datetime(data["timestamp"], errors="coerce")
            if timestamps.isna().any():
                raise ValueError("timestamp contains invalid values")
            if isinstance(timestamps.dtype, pd.DatetimeTZDtype):
                timestamps = timestamps.dt.tz_convert(timezone)
            elif pd.api.types.is_datetime64_dtype(timestamps.dtype):
                if timezone == "UTC":
                    timestamps = timestamps.dt.tz_localize("UTC")
                else:
                    if "time_index" not in data.columns:
                        raise ValueError(
                            "naive local timestamps require time_index to "
                            "disambiguate daylight-saving transitions"
                        )
                    indices = pd.to_numeric(data["time_index"], errors="coerce")
                    if indices.isna().any() or (indices % 1 != 0).any():
                        raise ValueError(
                            "time_index must contain integers to disambiguate "
                            "local timestamps"
                        )
                    pairs = pd.DataFrame(
                        {
                            "time_index": indices.astype("int64"),
                            "timestamp": timestamps,
                        }
                    ).drop_duplicates()
                    if pairs.duplicated("time_index").any():
                        raise ValueError(
                            "a time_index maps to multiple timestamp values"
                        )
                    pairs.sort_values("time_index", kind="stable", inplace=True)
                    try:
                        localized = pairs["timestamp"].dt.tz_localize(
                            timezone,
                            ambiguous="infer",
                            nonexistent="raise",
                        )
                    except (TypeError, ValueError) as error:
                        raise ValueError(
                            "could not interpret naive timestamps in timezone "
                            f"{timezone!r}; daylight-saving transition is ambiguous"
                        ) from error
                    localized_by_index = dict(
                        zip(pairs["time_index"], localized)
                    )
                    timestamps = pd.Series(
                        [localized_by_index[int(index)] for index in indices],
                        index=data.index,
                    )
            else:
                converted = []
                for value in data["timestamp"]:
                    timestamp = pd.Timestamp(value)
                    if timestamp.tzinfo is None:
                        timestamp = timestamp.tz_localize(
                            timezone,
                            ambiguous="raise",
                            nonexistent="raise",
                        )
                    else:
                        timestamp = timestamp.tz_convert(timezone)
                    converted.append(timestamp)
                timestamps = pd.Series(
                    pd.DatetimeIndex(converted),
                    index=data.index,
                )
            data["timestamp"] = timestamps
            return data

    if "time_index" not in data.columns:
        raise ValueError("observations require timestamp or time_index")
    indices = pd.to_numeric(data["time_index"], errors="coerce")
    if indices.isna().any() or (indices % 1 != 0).any():
        raise ValueError("time_index must contain integers when timestamps are absent")
    data["timestamp"] = (
        pd.Timestamp("1970-01-01", tz=timezone)
        + pd.to_timedelta(
            indices.astype("int64") * sample_interval_minutes,
            unit="m",
        )
    )
    return data


def clean_speed_series(
    frame: pd.DataFrame,
    *,
    max_gap: int = 3,
    group_columns: Sequence[str] = ("edge_id",),
    sample_interval_minutes: int = 5,
    timezone: str = "UTC",
) -> pd.DataFrame:
    """Treat zero/non-finite speed as missing and fill only short internal gaps.

    Speeds are ordered by timestamp within each group. A missing run is linearly
    interpolated only when it is bracketed by valid readings and its full length
    is at most ``max_gap`` samples and the bounding timestamps confirm the
    expected sample cadence. Longer runs, irregularly spaced bounds, and
    leading/trailing gaps are retained as missing and then dropped.
    ``is_imputed`` is true only for readings filled by this rule; no endpoint
    extrapolation is performed.
    """
    import numpy as np
    import pandas as pd

    if max_gap < 0:
        raise ValueError("max_gap must be non-negative")
    required = {*group_columns, "speed_mph"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"speed observations are missing columns: {sorted(missing)}")

    data = _ensure_timestamp(
        frame,
        sample_interval_minutes=sample_interval_minutes,
        timezone=timezone,
    ).reset_index(drop=True)
    duplicate_keys = [*group_columns, "timestamp"]
    if data.duplicated(duplicate_keys).any():
        raise ValueError(f"duplicate speed observations for keys {duplicate_keys}")

    speeds = pd.to_numeric(data["speed_mph"], errors="coerce").astype(float)
    speeds.loc[~np.isfinite(speeds) | (speeds <= 0)] = np.nan
    data["speed_mph"] = speeds
    data["is_imputed"] = False
    data.sort_values([*group_columns, "timestamp"], kind="stable", inplace=True)
    data.reset_index(drop=True, inplace=True)

    for _, group in data.groupby(list(group_columns), sort=False, dropna=False):
        positions = group.index.to_list()
        values = data.loc[positions, "speed_mph"].to_numpy(dtype=float)
        timestamps = data.loc[positions, "timestamp"].tolist()
        cursor = 0
        while cursor < len(values):
            if np.isfinite(values[cursor]):
                cursor += 1
                continue
            gap_start = cursor
            while cursor < len(values) and not np.isfinite(values[cursor]):
                cursor += 1
            gap_end = cursor
            gap_length = gap_end - gap_start
            if (
                gap_length > max_gap
                or gap_start == 0
                or gap_end == len(values)
            ):
                continue

            left_value = values[gap_start - 1]
            right_value = values[gap_end]
            span = gap_length + 1
            expected_span = pd.Timedelta(
                minutes=sample_interval_minutes * span
            )
            if timestamps[gap_end] - timestamps[gap_start - 1] != expected_span:
                continue
            for offset in range(gap_length):
                value = left_value + (right_value - left_value) * (
                    (offset + 1) / span
                )
                row_position = positions[gap_start + offset]
                data.at[row_position, "speed_mph"] = value
                data.at[row_position, "is_imputed"] = True
                values[gap_start + offset] = value

    return data.dropna(subset=["speed_mph"]).reset_index(drop=True)


def aggregate_hourly(
    frame: pd.DataFrame,
    *,
    routing_windows: Sequence[RoutingTimeWindow],
    sample_interval_minutes: int = 5,
    timezone: str = "UTC",
) -> pd.DataFrame:
    """Aggregate cleaned samples by edge and clock hour, retaining routing windows.

    Timestamps and routing windows use ``timezone``. The hourly target is the
    arithmetic mean of the 5-minute edge travel times.
    ``routing_window`` labels configured ``[start_hour, end_hour)`` intervals;
    rows outside those intervals remain available as historical lag inputs and
    are removed only when constructing the final model splits. ``is_imputed``
    is true if any contributing sample was imputed.
    """
    import pandas as pd

    required = {
        "timestamp",
        "edge_id",
        "distance_km",
        "speed_mph",
        "travel_time_min",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"observations are missing columns: {sorted(missing)}")
    if len(routing_windows) < 2:
        raise ValueError("at least two routing time windows must be configured")

    data = _ensure_timestamp(
        frame,
        sample_interval_minutes=sample_interval_minutes,
        timezone=timezone,
    )
    utc_hour = data["timestamp"].dt.tz_convert("UTC").dt.floor("h")
    data["timestamp_hour"] = utc_hour.dt.tz_convert(timezone)
    data["day"] = data["timestamp_hour"].dt.strftime("%Y-%m-%d")
    data["day_of_week"] = data["timestamp_hour"].dt.day_name()
    data["time_slot"] = data["timestamp_hour"].dt.hour.astype(int)
    data["routing_window"] = None

    occupied_hours: set[int] = set()
    for window in routing_windows:
        if not 0 <= window.start_hour < window.end_hour <= 24:
            raise ValueError(
                f"invalid routing window {window.name!r}: "
                "hours must satisfy 0 <= start < end <= 24"
            )
        window_hours = set(range(window.start_hour, window.end_hour))
        if occupied_hours & window_hours:
            raise ValueError("routing time windows must not overlap")
        occupied_hours.update(window_hours)
        mask = data["time_slot"].between(
            window.start_hour, window.end_hour - 1, inclusive="both"
        )
        data.loc[mask, "routing_window"] = window.name

    grouping = [
        "timestamp_hour",
        "day",
        "day_of_week",
        "time_slot",
        "routing_window",
        "edge_id",
        "distance_km",
    ]
    hourly = (
        data.groupby(grouping, dropna=False, sort=False)
        .agg(
            speed_mph=("speed_mph", "mean"),
            travel_time_min=("travel_time_min", "mean"),
            is_imputed=("is_imputed", "any"),
            n_samples=("speed_mph", "size"),
        )
        .reset_index()
    )
    return hourly.reset_index(drop=True)


def observations_to_speed_frame(
    observations: Sequence[SpeedObservationLike],
) -> pd.DataFrame:
    """Convert enriched per-sample observations to the hourly-stage schema.

    Each item must carry ``timestamp``, ``edge_id``, ``distance``,
    ``speed_mph``, ``travel_time``, and ``is_imputed`` fields. This
    adapter-neutral bridge lets dataset pipelines reuse the same hourly,
    lag, and split transformations without re-reading source-specific files.
    """
    import pandas as pd

    rows: list[dict[str, object]] = []
    for row_number, item in enumerate(observations, start=1):
        timestamp = item.timestamp
        edge_id = item.edge_id
        distance = item.distance
        speed_mph = item.speed_mph
        travel_time = item.travel_time
        if (
            timestamp is None
            or not isinstance(edge_id, str)
            or distance is None
            or speed_mph is None
            or travel_time is None
        ):
            raise ValueError(
                f"Observation row {row_number} lacks enriched speed fields"
            )
        numeric_values = {
            "distance": float(distance),
            "speed_mph": float(speed_mph),
            "travel_time": float(travel_time),
        }
        if (
            any(not math.isfinite(value) for value in numeric_values.values())
            or numeric_values["distance"] <= 0
            or numeric_values["speed_mph"] <= 0
            or numeric_values["travel_time"] <= 0
        ):
            raise ValueError(
                f"Observation row {row_number} has invalid distance, speed, "
                "or travel time"
            )
        rows.append(
            {
                "timestamp": timestamp,
                "edge_id": edge_id,
                "distance_km": numeric_values["distance"],
                "speed_mph": numeric_values["speed_mph"],
                "travel_time_min": numeric_values["travel_time"],
                "is_imputed": item.is_imputed,
            }
        )
    return pd.DataFrame(
        rows,
        columns=[
            "timestamp",
            "edge_id",
            "distance_km",
            "speed_mph",
            "travel_time_min",
            "is_imputed",
        ],
    )


def _chronological_day_splits(
    frame: pd.DataFrame,
    *,
    train_fraction: float,
    valid_fraction: float,
) -> dict[str, pd.DataFrame]:
    days = sorted(frame["day"].unique())
    if not 0 < train_fraction < 1 or not 0 < valid_fraction < 1:
        raise ValueError("split fractions must be between zero and one")
    if train_fraction + valid_fraction >= 1:
        raise ValueError("train_fraction + valid_fraction must be less than one")
    if len(days) < 3:
        raise ValueError("at least three distinct days are required for time splits")

    train_count = int(len(days) * train_fraction)
    valid_count = int(len(days) * valid_fraction)
    if train_count < 1 or valid_count < 1 or train_count + valid_count >= len(days):
        raise ValueError(
            "time split fractions must leave at least one full day in train, "
            "validation, and test"
        )

    boundaries = {
        "train": set(days[:train_count]),
        "valid": set(days[train_count : train_count + valid_count]),
        "test": set(days[train_count + valid_count :]),
    }
    return {
        name: frame.loc[frame["day"].isin(split_days)]
        .sort_values(["timestamp_hour", "edge_id"], kind="stable")
        .reset_index(drop=True)
        for name, split_days in boundaries.items()
    }


def prepare_temporal_splits(
    hourly: pd.DataFrame,
    *,
    lag_steps: Sequence[int] = (),
    train_fraction: float = 0.7,
    valid_fraction: float = 0.15,
) -> TemporalDataset:
    """Create day-blocked splits and fit categorical/numeric transforms on train only.

    Lag features use the exact preceding hourly row for the same edge. Rows
    without every requested lag are dropped. Splits are assigned once by whole
    chronological day, without shuffling; validation and test never fit the
    one-hot encoder or scaler.
    """
    import pandas as pd
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder, StandardScaler

    if hourly.empty:
        raise ValueError("cannot split an empty hourly dataset")
    if hourly.duplicated(["edge_id", "timestamp_hour"]).any():
        raise ValueError("hourly dataset has duplicate edge/hour observations")
    if any(
        not isinstance(step, int) or isinstance(step, bool) or step <= 0
        for step in lag_steps
    ):
        raise ValueError("lag_steps must contain positive integers")
    if len(set(lag_steps)) != len(lag_steps):
        raise ValueError("lag_steps values must be unique")

    data = hourly.sort_values(
        ["timestamp_hour", "edge_id"], kind="stable"
    ).reset_index(drop=True)
    lag_columns: list[str] = []
    for step in lag_steps:
        column = f"travel_time_lag_{step}h"
        prior = data[["edge_id", "timestamp_hour", "travel_time_min"]].copy()
        prior["timestamp_hour"] += pd.Timedelta(hours=step)
        prior.rename(columns={"travel_time_min": column}, inplace=True)
        data = data.merge(
            prior,
            on=["edge_id", "timestamp_hour"],
            how="left",
            validate="one_to_one",
        )
        lag_columns.append(column)

    if "routing_window" in data.columns:
        data = data.loc[data["routing_window"].notna()].copy()
    if lag_columns:
        data.dropna(subset=lag_columns, inplace=True)
        data.reset_index(drop=True, inplace=True)

    raw_splits = _chronological_day_splits(
        data,
        train_fraction=train_fraction,
        valid_fraction=valid_fraction,
    )
    categorical_columns = ["edge_id", "time_slot", "day_of_week"]
    feature_columns = [*categorical_columns, *lag_columns]
    missing = set([*feature_columns, "travel_time_min"]) - set(data.columns)
    if missing:
        raise ValueError(f"hourly dataset is missing columns: {sorted(missing)}")

    transformers: list[tuple[str, Any, list[str]]] = [
        (
            "categorical",
            OneHotEncoder(handle_unknown="ignore"),
            categorical_columns,
        )
    ]
    if lag_columns:
        transformers.append(("numeric", StandardScaler(), lag_columns))
    transformer = ColumnTransformer(transformers, remainder="drop")

    train_features = raw_splits["train"][feature_columns]
    transformer.fit(train_features)
    feature_names = tuple(transformer.get_feature_names_out())
    features: dict[str, pd.DataFrame] = {}
    for name, split in raw_splits.items():
        transformed = transformer.transform(split[feature_columns])
        if hasattr(transformed, "toarray"):
            transformed = transformed.toarray()
        features[name] = pd.DataFrame(
            transformed,
            columns=feature_names,
            index=split.index,
        )
    targets = {
        name: split["travel_time_min"].reset_index(drop=True)
        for name, split in raw_splits.items()
    }
    manifest = pd.DataFrame(
        [
            {
                "split": name,
                "start_day": split["day"].min(),
                "end_day": split["day"].max(),
                "start_timestamp": split["timestamp_hour"].min(),
                "end_timestamp": split["timestamp_hour"].max(),
                "n_days": int(split["day"].nunique()),
                "n_rows": len(split),
            }
            for name, split in raw_splits.items()
        ]
    )
    return TemporalDataset(raw_splits, features, targets, manifest, transformer)


def render_data_dictionary(
    *,
    max_imputation_gap: int,
    lag_steps: Sequence[int],
    routing_windows: Sequence[RoutingTimeWindow],
    timezone: str = "UTC",
) -> str:
    """Return a Markdown data dictionary; this function does not write files."""
    windows = ", ".join(
        f"{window.name}: {window.start_hour:02d}:00–{window.end_hour:02d}:00"
        for window in routing_windows
    )
    lag_description = (
        ", ".join(f"{step}h" for step in lag_steps) if lag_steps else "none"
    )
    return f"""# Data dictionary

| Field | Meaning |
|---|---|
| `edge_id` | Stable directed-edge identifier from the network adapter. |
| `time_slot` | Hour of day (0–23), aggregated from the 5-minute readings in that hour. |
| `day_of_week` | Weekday derived from the observation timestamp. |
| `routing_window` | Configured routing period; retained only for selected periods: {windows}. |
| `distance_km` | Haversine endpoint distance in kilometres; an approximation, not road length. |
| `speed_mph` | Hourly mean speed in miles per hour after cleaning. Zero and non-finite values are treated as missing; only internal gaps of at most {max_imputation_gap} consecutive samples are linearly interpolated. Longer and boundary gaps are dropped. |
| `travel_time_min` | Hourly mean of `distance_km / (speed_mph * 1.609344) * 60`; distance remains an approximate Haversine length. |
| `is_imputed` | True if at least one contributing 5-minute speed was interpolated. |
| `travel_time_lag_*h` | Optional prior-hour travel-time feature for the same edge; configured lags: {lag_description}. Rows without all requested prior hours are dropped. |
| `n_samples` | Number of cleaned 5-minute samples contributing to the hourly aggregate. |

Splits are chronological blocks of whole days (train, validation, then test), with
no shuffling. The categorical encoder and numeric scaler are fitted only on
training rows; unseen categories in later splits are ignored by the encoder.
When source timestamps are unavailable, `time_index` is mapped to a synthetic
timeline in `{timezone}` using the configured sample interval, so its weekday
is not a verified calendar weekday. Naive source timestamps are interpreted in
`{timezone}` and daylight-saving ambiguities are inferred from `time_index`;
timezone-aware timestamps are converted to it before hourly grouping and
routing-window selection.
"""


def save_temporal_dataset(
    dataset: TemporalDataset,
    output_dir: str | Path,
    *,
    data_dictionary: str,
) -> None:
    """Persist raw hourly splits, encoded matrices, manifest, and fitted transformer."""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    for name in ("train", "valid", "test"):
        dataset.raw_splits[name].to_csv(destination / f"{name}.csv", index=False)
        dataset.features[name].to_csv(
            destination / f"X_{name}.csv", index=False
        )
        dataset.targets[name].to_frame("travel_time_min").to_csv(
            destination / f"y_{name}.csv", index=False
        )
    dataset.split_manifest.to_csv(destination / "split_manifest.csv", index=False)
    with (destination / "preprocessing_pipeline.pkl").open("wb") as pipeline_file:
        pickle.dump(dataset.transformer, pipeline_file)
    (destination / "data_dictionary.md").write_text(
        data_dictionary, encoding="utf-8"
    )


__all__ = [
    "ObservationLike",
    "SpeedObservationLike",
    "ObservationSplits",
    "TemporalDataset",
    "aggregate_hourly",
    "clean_speed_series",
    "observations_to_speed_frame",
    "prepare_observation_splits",
    "prepare_temporal_splits",
    "render_data_dictionary",
    "save_temporal_dataset",
]
