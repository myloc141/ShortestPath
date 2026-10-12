"""Load the Seervada network CSV into typed network records."""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_NETWORK_CSV = (
    REPOSITORY_ROOT / "data" / "processed_seervada" / "seervada_network.csv"
)
REQUIRED_COLUMNS = {"node_u", "node_v", "distance", "directed"}


@dataclass(frozen=True)
class SeervadaEdge:
    """A single edge in the Seervada network."""

    edge_id: str
    u: str
    v: str
    distance: float
    directed: bool


@dataclass(frozen=True)
class SeervadaNetwork:
    """Nodes and edges loaded from the Seervada network CSV."""

    nodes: tuple[str, ...]
    edges: tuple[SeervadaEdge, ...]


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


def load_seervada_network(
    csv_path: str | Path = DEFAULT_NETWORK_CSV,
) -> SeervadaNetwork:
    """Read and validate a Seervada network CSV.

    The input columns are ``node_u``, ``node_v``, ``distance``, and
    ``directed``. Edge IDs are assigned in input-row order.
    """
    path = Path(csv_path)
    nodes: set[str] = set()
    edges: list[SeervadaEdge] = []

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        columns = set(reader.fieldnames or ())
        missing_columns = REQUIRED_COLUMNS - columns
        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise ValueError(f"{path}: missing required CSV columns: {missing}")

        for line_number, row in enumerate(reader, start=2):
            node_u = (row.get("node_u") or "").strip()
            node_v = (row.get("node_v") or "").strip()
            distance_value = (row.get("distance") or "").strip()
            directed_value = (row.get("directed") or "").strip()

            if not node_u or not node_v:
                raise ValueError(
                    f"{path}:{line_number}: node_u and node_v must not be empty"
                )
            if not distance_value:
                raise ValueError(f"{path}:{line_number}: distance must not be empty")

            try:
                distance = float(distance_value)
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number}: invalid distance {distance_value!r}"
                ) from exc
            if not math.isfinite(distance) or distance < 0:
                raise ValueError(
                    f"{path}:{line_number}: distance must be a finite "
                    "non-negative number"
                )

            directed = _parse_bool(
                directed_value, path=path, line_number=line_number
            )
            edges.append(
                SeervadaEdge(
                    edge_id=f"edge_{len(edges) + 1:03d}",
                    u=node_u,
                    v=node_v,
                    distance=distance,
                    directed=directed,
                )
            )
            nodes.update((node_u, node_v))

    return SeervadaNetwork(nodes=tuple(sorted(nodes)), edges=tuple(edges))
