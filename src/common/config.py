"""Typed loading of pipeline configuration values from YAML."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class RoutingTimeWindow:
    name: str
    start_hour: int
    end_hour: int


@dataclass(frozen=True)
class PipelineConfig:
    dataset: str
    time_limits: tuple[float | None, ...] = ()
    slots: tuple[int, ...] = ()
    seed: int | None = None
    source: str | None = None
    target: str | None = None
    network_path: str | None = None
    observations_path: str | None = None
    rcsp_path: str | None = None
    locations_path: str | None = None
    adjacency_path: str | None = None
    traffic_parquet: str | None = None
    distance_unit: str = "km"
    time_unit: str = "minutes"
    speed_unit: str | None = None
    timezone: str = "UTC"
    sensor_ids: tuple[str, ...] = ()
    n_sensors: int = 25
    seed_sensor: str | None = None
    max_paths: int = 1_000_000
    direction_policy: str = "directed"
    routing_windows: tuple[RoutingTimeWindow, ...] = ()
    sample_interval_minutes: int = 5
    max_speed_imputation_gap: int = 3
    lag_steps: tuple[int, ...] = ()
    train_fraction: float = 0.7
    valid_fraction: float = 0.15


def load_config(path: str | Path) -> PipelineConfig:
    """Read supported pipeline and routing keys from a YAML file.

    Relative paths are resolved from the repository root, allowing paths such
    as a dataset configuration under ``configs/``. A legacy nested
    ``source.path`` is treated as the network input path. ``n_sensors``,
    ``seed_sensor``, ``max_paths``, and ``direction_policy`` control automatic
    sensor/network selection where applicable; defaults preserve existing
    callers and directed-network behavior.
    """
    config_path = Path(path)
    if not config_path.is_absolute():
        repository_root = Path(__file__).resolve().parents[2]
        config_path = repository_root / config_path
    try:
        import yaml
    except ImportError as error:
        raise RuntimeError("Loading YAML configuration requires PyYAML") from error

    with config_path.open("r", encoding="utf-8") as config_file:
        data = yaml.safe_load(config_file)
    if not isinstance(data, Mapping):
        raise ValueError(f"{config_path}: YAML root must be a mapping")

    dataset = data.get("dataset")
    if not isinstance(dataset, str) or not dataset.strip():
        raise ValueError(f"{config_path}: 'dataset' must be a non-empty string")

    def optional_string(key: str) -> str | None:
        value = data.get(key)
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{config_path}: {key!r} must be a non-empty string or null")
        return value

    raw_source = data.get("source")
    source = None if isinstance(raw_source, Mapping) else optional_string("source")
    target = optional_string("target")
    network_path = optional_string("network_path")
    if network_path is None and isinstance(raw_source, Mapping):
        configured_source_path = raw_source.get("path")
        if isinstance(configured_source_path, str) and configured_source_path.strip():
            network_path = configured_source_path
    observations_path = optional_string("observations_path")
    rcsp_path = optional_string("rcsp_path")
    locations_path = optional_string("locations_path")
    adjacency_path = optional_string("adjacency_path")
    traffic_parquet = optional_string("traffic_parquet")
    distance_unit = optional_string("distance_unit") or "km"
    time_unit = optional_string("time_unit") or "minutes"
    speed_unit = optional_string("speed_unit")
    timezone = optional_string("timezone") or "UTC"
    raw_sensor_ids = data.get("sensor_ids", ())
    if not isinstance(raw_sensor_ids, (list, tuple)) or any(
        not isinstance(sensor_id, str) or not sensor_id.strip()
        for sensor_id in raw_sensor_ids
    ):
        raise ValueError(f"{config_path}: 'sensor_ids' must be a sequence of strings")
    n_sensors = data.get("n_sensors", 25)
    if (
        not isinstance(n_sensors, int)
        or isinstance(n_sensors, bool)
        or not 20 <= n_sensors <= 30
    ):
        raise ValueError(
            f"{config_path}: 'n_sensors' must be an integer from 20 to 30"
        )
    seed_sensor = optional_string("seed_sensor")
    max_paths = data.get("max_paths", 1_000_000)
    if (
        not isinstance(max_paths, int)
        or isinstance(max_paths, bool)
        or max_paths < 1
    ):
        raise ValueError(f"{config_path}: 'max_paths' must be a positive integer")
    direction_policy = data.get("direction_policy", "directed")
    if not isinstance(direction_policy, str) or direction_policy not in {
        "directed",
        "undirected",
    }:
        raise ValueError(
            f"{config_path}: 'direction_policy' must be 'directed' or 'undirected'"
        )

    raw_limits = data.get("time_limits", ())
    if not isinstance(raw_limits, (list, tuple)):
        raise ValueError(f"{config_path}: 'time_limits' must be a sequence")
    time_limits: list[float | None] = []
    for limit in raw_limits:
        if limit is None:
            time_limits.append(None)
        elif (
            isinstance(limit, (int, float))
            and not isinstance(limit, bool)
            and math.isfinite(float(limit))
        ):
            time_limits.append(float(limit))
        else:
            raise ValueError(f"{config_path}: time limits must be finite numbers or null")

    raw_slots = data.get("slots", ())
    if not isinstance(raw_slots, (list, tuple)) or any(
        not isinstance(slot, int) or isinstance(slot, bool) for slot in raw_slots
    ):
        raise ValueError(f"{config_path}: 'slots' must be a sequence of integers")

    seed = data.get("seed")
    if seed is not None and (
        not isinstance(seed, int) or isinstance(seed, bool)
    ):
        raise ValueError(f"{config_path}: 'seed' must be an integer or null")

    raw_routing_windows = data.get("routing_windows", ())
    if not isinstance(raw_routing_windows, (list, tuple)):
        raise ValueError(f"{config_path}: 'routing_windows' must be a sequence")
    routing_windows: list[RoutingTimeWindow] = []
    for index, item in enumerate(raw_routing_windows):
        if not isinstance(item, Mapping):
            raise ValueError(
                f"{config_path}: routing_windows[{index}] must be a mapping"
            )
        name = item.get("name")
        start_hour = item.get("start_hour")
        end_hour = item.get("end_hour")
        if (
            not isinstance(name, str)
            or not name.strip()
            or not isinstance(start_hour, int)
            or isinstance(start_hour, bool)
            or not isinstance(end_hour, int)
            or isinstance(end_hour, bool)
            or not 0 <= start_hour < end_hour <= 24
        ):
            raise ValueError(
                f"{config_path}: routing_windows[{index}] requires a name and "
                "hours satisfying 0 <= start_hour < end_hour <= 24"
            )
        routing_windows.append(
            RoutingTimeWindow(name.strip(), start_hour, end_hour)
        )
    if len({window.name for window in routing_windows}) != len(routing_windows):
        raise ValueError(f"{config_path}: routing window names must be unique")
    occupied_hours: set[int] = set()
    for window in routing_windows:
        hours = set(range(window.start_hour, window.end_hour))
        if occupied_hours & hours:
            raise ValueError(f"{config_path}: routing windows must not overlap")
        occupied_hours.update(hours)

    sample_interval = data.get("sample_interval_minutes", 5)
    if (
        not isinstance(sample_interval, int)
        or isinstance(sample_interval, bool)
        or sample_interval <= 0
        or 60 % sample_interval != 0
    ):
        raise ValueError(
            f"{config_path}: 'sample_interval_minutes' must be a positive "
            "integer divisor of 60"
        )
    max_gap = data.get("max_speed_imputation_gap", 3)
    if not isinstance(max_gap, int) or isinstance(max_gap, bool) or max_gap < 0:
        raise ValueError(
            f"{config_path}: 'max_speed_imputation_gap' must be a non-negative integer"
        )
    raw_lag_steps = data.get("lag_steps", ())
    if not isinstance(raw_lag_steps, (list, tuple)) or any(
        not isinstance(step, int) or isinstance(step, bool) or step <= 0
        for step in raw_lag_steps
    ):
        raise ValueError(
            f"{config_path}: 'lag_steps' must contain positive integers"
        )
    if len(set(raw_lag_steps)) != len(raw_lag_steps):
        raise ValueError(f"{config_path}: 'lag_steps' values must be unique")

    def fraction(key: str, default: float) -> float:
        value = data.get(key, default)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(float(value))
            or not 0 < float(value) < 1
        ):
            raise ValueError(f"{config_path}: {key!r} must be between 0 and 1")
        return float(value)

    train_fraction = fraction("train_fraction", 0.7)
    valid_fraction = fraction("valid_fraction", 0.15)
    if train_fraction + valid_fraction >= 1:
        raise ValueError(
            f"{config_path}: train_fraction + valid_fraction must be less than 1"
        )

    return PipelineConfig(
        dataset=dataset,
        time_limits=tuple(time_limits),
        slots=tuple(raw_slots),
        seed=seed,
        source=source,
        target=target,
        network_path=network_path,
        observations_path=observations_path,
        rcsp_path=rcsp_path,
        locations_path=locations_path,
        adjacency_path=adjacency_path,
        traffic_parquet=traffic_parquet,
        distance_unit=distance_unit,
        time_unit=time_unit,
        speed_unit=speed_unit,
        timezone=timezone,
        sensor_ids=tuple(raw_sensor_ids),
        n_sensors=n_sensors,
        seed_sensor=seed_sensor,
        max_paths=max_paths,
        direction_policy=direction_policy,
        routing_windows=tuple(routing_windows),
        sample_interval_minutes=sample_interval,
        max_speed_imputation_gap=max_gap,
        lag_steps=tuple(raw_lag_steps),
        train_fraction=train_fraction,
        valid_fraction=valid_fraction,
    )


__all__ = ["PipelineConfig", "RoutingTimeWindow", "load_config"]
