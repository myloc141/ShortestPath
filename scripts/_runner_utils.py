"""Shared path and serialization helpers for workstream runner scripts."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable, Mapping, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from src.adapters.base import DatasetAdapter
from src.common.config import PipelineConfig
from src.common.exceptions import ContractViolation
from src.network.schema import Network, NetworkEdge


def parse_workstream_args(number: int, description: str) -> argparse.Namespace:
    """Read common runner options without performing workstream processing."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--dataset",
        default="seervada",
        choices=("seervada", "pemsbay"),
        help="dataset adapter to use (default: seervada)",
    )
    add_artifacts_root_arguments(parser)
    parser.add_argument(
        "--with-meta",
        action="store_true",
        help="write interface tables with JSON metadata sidecars",
    )
    return parser.parse_args()


_STAGE_LAYOUT = {
    "network": Path("artifacts"),
    "paths": Path("artifacts"),
    "rcsp": Path("artifacts"),
    "predictions": Path("artifacts"),
    "metrics": Path("artifacts"),
    "routing": Path("artifacts"),
    "_errors": Path("artifacts"),
    "processed": Path("data") / "processed",
    "model_dataset": Path("data") / "processed",
    "report": Path("docs") / "report",
}


def add_artifacts_root_arguments(parser: argparse.ArgumentParser) -> None:
    """Add the shared artifact-root option and its deprecated old alias."""
    parser.add_argument(
        "--artifacts-root",
        type=Path,
        default=None,
        help="repository-level root containing artifacts/, data/, and docs/",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="deprecated alias for --artifacts-root",
    )


def resolve_artifacts_root(
    artifacts_root: str | Path | None = None,
    legacy_output_dir: str | Path | None = None,
) -> Path:
    """Resolve the repository-level root and report use of the old option."""
    if artifacts_root is not None and legacy_output_dir is not None:
        raise ValueError("Use only one of --artifacts-root and --output-dir")
    if legacy_output_dir is not None:
        print(
            "Warning: --output-dir is deprecated; use --artifacts-root instead.",
            file=sys.stderr,
        )
        artifacts_root = legacy_output_dir
    root = Path(artifacts_root) if artifacts_root is not None else REPOSITORY_ROOT
    return root if root.is_absolute() else REPOSITORY_ROOT / root


def stage_dir(
    dataset: str,
    stage: str,
    root: str | Path | None = None,
) -> Path:
    """Return a canonical dataset-stage directory under the selected root."""
    normalized_stage = stage.casefold()
    if normalized_stage not in _STAGE_LAYOUT:
        raise ValueError(
            f"Unknown stage {stage!r}; expected one of "
            f"{', '.join(sorted(_STAGE_LAYOUT))}"
        )
    base = resolve_artifacts_root(root)
    if normalized_stage == "report":
        return base / _STAGE_LAYOUT[normalized_stage]
    path = base / _STAGE_LAYOUT[normalized_stage] / dataset.casefold()
    if normalized_stage == "processed":
        return path
    if normalized_stage == "model_dataset":
        return path / normalized_stage
    return path / normalized_stage


def configured_path(value: str | Path) -> Path:
    """Resolve a path declared in a repository config relative to repo root."""
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def stage_input_file(
    dataset: str,
    stage: str,
    filename: str,
    *,
    root: str | Path | None = None,
    legacy_workstream: int | None = None,
) -> Path:
    """Resolve a canonical input file, with a warned Seervada legacy fallback."""
    canonical = stage_dir(dataset, stage, root) / filename
    if canonical.is_file():
        return canonical
    if dataset.casefold() == "seervada" and legacy_workstream is not None:
        legacy = (
            REPOSITORY_ROOT
            / f"workstream{legacy_workstream:02d}"
            / "outputs"
            / filename
        )
        if legacy.is_file():
            print(
                f"Warning: using legacy input {legacy}; expected {canonical}.",
                file=sys.stderr,
            )
            return legacy
    return canonical


def load_network_artifact(
    dataset: str,
    adapter: DatasetAdapter,
    *,
    root: str | Path | None = None,
) -> Network:
    """Load the I1 network tables emitted by WS1, with legacy file fallback."""
    node_path = stage_input_file(
        dataset,
        "network",
        "network_nodes.csv",
        root=root,
        legacy_workstream=1,
    )
    edge_path = stage_input_file(
        dataset,
        "network",
        "network_edges.csv",
        root=root,
        legacy_workstream=1,
    )
    with node_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if "node_id" not in (reader.fieldnames or ()):
            raise ValueError(f"{node_path}: required column 'node_id' is missing")
        node_rows = [(row.get("node_id") or "").strip() for row in reader]
    if not node_rows or any(not node for node in node_rows):
        raise ValueError(f"{node_path}: network nodes must be non-empty")
    if len(set(node_rows)) != len(node_rows):
        raise ValueError(f"{node_path}: duplicate node_id values")
    nodes = tuple(sorted(node_rows))

    edges: list[NetworkEdge] = []
    edge_ids: set[str] = set()
    with edge_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        required = {"edge_id", "u", "v", "distance", "directed"}
        missing = required - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                f"{edge_path}: missing required columns {sorted(missing)}"
            )
        for line_number, row in enumerate(reader, start=2):
            edge_id = (row.get("edge_id") or "").strip()
            u = (row.get("u") or "").strip()
            v = (row.get("v") or "").strip()
            try:
                distance = float(row.get("distance") or "")
            except ValueError as error:
                raise ValueError(
                    f"{edge_path}:{line_number}: distance must be numeric"
                ) from error
            directed_value = (row.get("directed") or "").strip().casefold()
            if directed_value not in {"true", "false"}:
                raise ValueError(
                    f"{edge_path}:{line_number}: directed must be True or False"
                )
            if not edge_id or not u or not v:
                raise ValueError(
                    f"{edge_path}:{line_number}: edge_id, u, and v must be non-empty"
                )
            if edge_id in edge_ids:
                raise ValueError(
                    f"{edge_path}:{line_number}: duplicate edge_id {edge_id!r}"
                )
            if u not in nodes or v not in nodes:
                raise ValueError(
                    f"{edge_path}:{line_number}: edge endpoints must exist in "
                    "network_nodes.csv"
                )
            if not math.isfinite(distance) or distance <= 0:
                raise ValueError(
                    f"{edge_path}:{line_number}: distance must be finite and positive"
                )
            edge_ids.add(edge_id)
            edges.append(
                NetworkEdge(
                    edge_id=edge_id,
                    u=u,
                    v=v,
                    distance=distance,
                    directed=directed_value == "true",
                )
            )
    if not edges:
        raise ValueError(f"{edge_path}: network edges must not be empty")
    return Network(
        nodes=nodes,
        edges=tuple(edges),
        distance_unit=adapter.distance_unit,
        distance_is_approximate=adapter.name.casefold() == "pemsbay",
        distance_method=(
            "Haversine straight-line estimate from PEMS-BAY sensor locations"
            if adapter.name.casefold() == "pemsbay"
            else "Loaded from WS1 I1 network tables"
        ),
    )


def load_dataset_adapter(
    dataset: str,
    *,
    root: str | Path | None = None,
    config_path: str | Path | None = None,
) -> tuple[DatasetAdapter, PipelineConfig]:
    """Load a configured dataset adapter and its parsed pipeline config."""
    from src.adapters.registry import get_adapter
    from src.common.config import load_config

    name = dataset.casefold()
    if name not in {"seervada", "pemsbay"}:
        raise ValueError(f"Unsupported dataset {dataset!r}")
    selected_config = (
        configured_path(config_path)
        if config_path is not None
        else REPOSITORY_ROOT / "configs" / f"{name}.yaml"
    )
    config = load_config(selected_config)
    if name == "seervada":
        adapter = get_adapter(
            name,
            network_csv=(
                configured_path(config.network_path)
                if config.network_path
                else None
            ),
            observations_csv=(
                configured_path(config.observations_path)
                if config.observations_path
                else None
            ),
            source=config.source or "O",
            target=config.target or "T",
        )
    else:
        adapter = get_adapter(
            name,
            selected_sensor_ids=config.sensor_ids,
            locations_csv=(
                configured_path(config.locations_path)
                if config.locations_path
                else None
            ),
            adjacency_pickle=(
                configured_path(config.adjacency_path)
                if config.adjacency_path
                else None
            ),
            traffic_parquet=(
                stage_dir(name, "processed", root) / "traffic_speed_long.parquet"
            ),
            speed_unit=config.speed_unit or "mph",
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
    return adapter, config


def routing_endpoints(
    adapter: DatasetAdapter,
    *,
    source: str | None,
    target: str | None,
) -> tuple[str, str]:
    """Resolve configured or adapter-selected endpoints after network creation."""
    metadata = getattr(adapter, "metadata", {})
    resolved_source = source or metadata.get("source")
    resolved_target = target or metadata.get("target")
    if not isinstance(resolved_source, str) or not isinstance(resolved_target, str):
        raise ValueError(
            f"Dataset {adapter.name!r} must configure or deterministically "
            "select source and target"
        )
    return resolved_source, resolved_target


def _write_contract_error(
    error: ContractViolation,
    *,
    output_dir: Path,
    dataset: str,
    stage: str,
) -> None:
    print(
        f"Contract violation [{error.interface_id}]: {error.message}",
        file=sys.stderr,
    )
    error_dir = output_dir
    error_dir.mkdir(parents=True, exist_ok=True)
    error_path = error_dir / f"{stage}_contract_violation.json"
    error_path.write_text(
        json.dumps(
            {
                "interface_id": error.interface_id,
                "message": error.message,
                "dataset": dataset,
                "stage": stage,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _root_for_output_path(path: Path) -> Path:
    for parent in (path, *path.parents):
        if parent.name in {"artifacts", "data", "docs"}:
            return parent.parent
    return REPOSITORY_ROOT


def validate_with_error_report(
    validator: Callable[..., None],
    *data: object,
    output_dir: str | Path,
    dataset: str,
    stage: str,
) -> None:
    """Run an interface validator and persist/report contract failures."""
    destination = Path(output_dir)
    try:
        validator(*data)
    except ContractViolation as error:
        _write_contract_error(
            error,
            output_dir=destination,
            dataset=dataset,
            stage=stage,
        )
        raise SystemExit(1) from error


def write_frame(
    path: Path,
    frame: Any,
    *,
    with_meta: bool = False,
    dataset: str = "unknown",
    interface_id: str = "I1",
    schema_version: str = "1",
) -> None:
    """Write a DataFrame normally or via the opt-in metadata contract API."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not with_meta:
        frame.to_csv(path, index=False)
        return
    from src.common.io import write_with_meta

    try:
        write_with_meta(
            path,
            frame,
            {
                "interface_id": interface_id,
                "dataset": dataset,
                "schema_version": schema_version,
            },
        )
    except ContractViolation as error:
        _write_contract_error(
            error,
            output_dir=stage_dir(
                dataset,
                "_errors",
                _root_for_output_path(path.parent),
            ),
            dataset=dataset,
            stage=path.stem,
        )
        raise SystemExit(1) from error


def write_csv(
    path: Path,
    rows: Sequence[Mapping[str, Any]],
    *,
    fieldnames: Sequence[str] | None = None,
    with_meta: bool = False,
    dataset: str = "unknown",
    interface_id: str = "I1",
) -> None:
    if with_meta:
        import pandas as pd

        columns = list(fieldnames or (rows[0].keys() if rows else ()))
        write_frame(
            path,
            pd.DataFrame(rows, columns=columns),
            with_meta=True,
            dataset=dataset,
            interface_id=interface_id,
        )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(fieldnames or (rows[0].keys() if rows else ()))
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
