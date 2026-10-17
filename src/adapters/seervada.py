"""Seervada dataset adapter for canonical network and observation schemas."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from ..network.schema import Network, NetworkEdge
from ..network.validation import validate_network
from ..preprocess.observations import (
    TrafficObservation,
    load_observations,
)
from .base import DatasetAdapter

REQUIRED_COLUMNS = frozenset({"node_u", "node_v", "distance", "directed"})


def _parse_bool(value: str, *, path: Path, line_number: int) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(
        f"{path}:{line_number}: expected 'True' or 'False' for directed, "
        f"got {value!r}"
    )


def _load_network(
    csv_path: str | Path,
    *,
    source: str,
    target: str,
    expected_edge_count: int | None,
) -> Network:
    """Read Seervada network rows into the canonical schema."""
    path = Path(csv_path)
    nodes: set[str] = set()
    edges: list[NetworkEdge] = []

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing = REQUIRED_COLUMNS - columns
        if missing:
            raise ValueError(
                f"{path}: missing required columns: {', '.join(sorted(missing))}"
            )

        for line_number, row in enumerate(reader, start=2):
            u = (row.get("node_u") or "").strip()
            v = (row.get("node_v") or "").strip()
            raw_distance = (row.get("distance") or "").strip()
            if not u or not v or not raw_distance:
                raise ValueError(
                    f"{path}:{line_number}: node_u, node_v, and distance "
                    "must not be empty"
                )
            try:
                distance = float(raw_distance)
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid distance {raw_distance!r}"
                ) from exc
            if not math.isfinite(distance) or distance <= 0:
                raise ValueError(
                    f"{path}:{line_number}: distance must be a finite "
                    "positive number"
                )
            directed = _parse_bool(
                row.get("directed") or "", path=path, line_number=line_number
            )
            edges.append(
                NetworkEdge(
                    edge_id=f"edge_{len(edges) + 1:03d}",
                    u=u,
                    v=v,
                    distance=distance,
                    directed=directed,
                )
            )
            nodes.update((u, v))

    network = Network(
        nodes=tuple(sorted(nodes)),
        edges=tuple(edges),
        distance_unit="km",
        distance_is_approximate=False,
        distance_method="Distance values from the Seervada network CSV",
    )
    report = validate_network(
        network,
        source=source,
        target=target,
        expected_edge_count=expected_edge_count,
    )
    if not report.is_valid:
        raise ValueError("Invalid Seervada network: " + "; ".join(report.errors))
    return network


class SeervadaAdapter(DatasetAdapter):
    """Adapter for Seervada network and simulated traffic CSV inputs."""

    name = "seervada"
    distance_unit = "km"
    time_unit = "minutes"

    def __init__(
        self,
        network_csv: str | Path,
        observations_csv: str | Path,
        *,
        source: str = "O",
        target: str = "T",
        expected_edge_count: int | None = 12,
    ) -> None:
        self.network_csv = Path(network_csv)
        self.observations_csv = Path(observations_csv)
        self.source = source
        self.target = target
        self.expected_edge_count = expected_edge_count

    def build_network(self) -> Network:
        return _load_network(
            self.network_csv,
            source=self.source,
            target=self.target,
            expected_edge_count=self.expected_edge_count,
        )

    def build_observations(
        self,
        *,
        network: Network | None = None,
    ) -> list[TrafficObservation]:
        network = network or self.build_network()
        return list(load_observations(self.observations_csv, network=network))


def load_seervada_network(
    csv_path: str | Path,
    *,
    source: str = "O",
    target: str = "T",
    expected_edge_count: int | None = 12,
) -> Network:
    """Compatibility wrapper returning the canonical network schema."""
    return _load_network(
        csv_path,
        source=source,
        target=target,
        expected_edge_count=expected_edge_count,
    )


__all__ = [
    "SeervadaAdapter",
    "load_seervada_network",
]
