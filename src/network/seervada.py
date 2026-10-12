"""Load and validate the Seervada network from its project CSV."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from .schema import Network, NetworkEdge
from .validation import validate_network


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEERVADA_CSV = (
    REPOSITORY_ROOT / "data" / "processed_seervada" / "seervada_network.csv"
)
REQUIRED_COLUMNS = {"node_u", "node_v", "distance", "directed"}


def _parse_directed(value: str, *, path: Path, line_number: int) -> bool:
    normalized = value.strip().casefold()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(
        f"{path}:{line_number}: directed must be True or False, got {value!r}"
    )


def load_seervada_network(
    csv_path: str | Path = DEFAULT_SEERVADA_CSV,
    *,
    source: str = "O",
    target: str = "T",
    expected_edge_count: int | None = 12,
) -> Network:
    """Read Seervada CSV rows into the canonical ``Network`` schema."""
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
                    f"{path}:{line_number}: distance must be finite and positive"
                )

            directed = _parse_directed(
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
