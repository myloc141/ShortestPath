"""Load RCSP resource costs and attach them to the canonical network schema."""

from __future__ import annotations

import csv
import math
from pathlib import Path

from ..network.schema import Network, NetworkEdge
from .schema import EdgeResource, RCSPProblem
from .validation import validate_problem


REQUIRED_COLUMNS = {"node_u", "node_v", "distance", "time", "directed"}
DEFAULT_RESOURCE_UNIT = "minutes"


def _edge_key(u: str, v: str, directed: bool) -> tuple[str, str, str]:
    if directed:
        return ("directed", u, v)
    first, second = sorted((u, v))
    return ("undirected", first, second)


def load_rcsp_problem(
    csv_path: str | Path,
    *,
    network: Network | None = None,
    resource_unit: str = DEFAULT_RESOURCE_UNIT,
) -> RCSPProblem:
    """Read ``node_u,node_v,distance,time,directed`` into a shared RCSP schema.

    When ``network`` is supplied, its topology, edge direction, and distances
    must match the CSV. Resource costs are then keyed to its edge IDs, rather
    than relying on the row order of the two files.
    """
    path = Path(csv_path)
    rows: list[tuple[str, str, float, float, bool]] = []

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or ())
        if missing:
            raise ValueError(
                f"{path}: missing required columns: {', '.join(sorted(missing))}"
            )

        for line_number, row in enumerate(reader, start=2):
            u = (row.get("node_u") or "").strip()
            v = (row.get("node_v") or "").strip()
            raw_distance = (row.get("distance") or "").strip()
            raw_resource = (row.get("time") or "").strip()
            raw_directed = (row.get("directed") or "").strip().casefold()
            if not u or not v or not raw_distance or not raw_resource:
                raise ValueError(
                    f"{path}:{line_number}: node_u, node_v, distance, and time "
                    "must not be empty"
                )
            if raw_directed not in {"true", "false"}:
                raise ValueError(
                    f"{path}:{line_number}: directed must be True or False"
                )
            try:
                distance = float(raw_distance)
                resource = float(raw_resource)
            except ValueError as exc:
                raise ValueError(
                    f"{path}:{line_number}: distance and time must be numeric"
                ) from exc
            if (
                not math.isfinite(distance)
                or distance <= 0
                or not math.isfinite(resource)
                or resource < 0
            ):
                raise ValueError(
                    f"{path}:{line_number}: distance must be positive and time "
                    "must be finite and non-negative"
                )
            rows.append((u, v, distance, resource, raw_directed == "true"))

    if not rows:
        raise ValueError(f"{path}: no RCSP edge rows found")

    csv_keys: dict[tuple[str, str, str], tuple[str, str, float, float, bool]] = {}
    for row in rows:
        u, v, _, _, directed = row
        key = _edge_key(u, v, directed)
        if key in csv_keys:
            raise ValueError(f"{path}: duplicate edge {u!r} - {v!r}")
        csv_keys[key] = row

    if network is None:
        nodes = tuple(sorted({node for u, v, *_ in rows for node in (u, v)}))
        network_edges = tuple(
            NetworkEdge(
                edge_id=f"edge_{index:03d}",
                u=u,
                v=v,
                distance=distance,
                directed=directed,
            )
            for index, (u, v, distance, _, directed) in enumerate(rows, start=1)
        )
        network = Network(
            nodes=nodes,
            edges=network_edges,
            distance_unit="km",
            distance_is_approximate=False,
            distance_method=f"Distance values from {path.name}",
        )

    network_by_key: dict[tuple[str, str, str], NetworkEdge] = {}
    for edge in network.edges:
        key = _edge_key(edge.u, edge.v, edge.directed)
        if key in network_by_key:
            raise ValueError(f"Network contains duplicate edge {edge.u!r} - {edge.v!r}")
        network_by_key[key] = edge

    if network_by_key.keys() != csv_keys.keys():
        missing_from_csv = sorted(network_by_key.keys() - csv_keys.keys())
        missing_from_network = sorted(csv_keys.keys() - network_by_key.keys())
        raise ValueError(
            "RCSP CSV topology/direction does not match the supplied network "
            f"(missing from CSV: {missing_from_csv}; "
            f"missing from network: {missing_from_network})"
        )

    resources: list[EdgeResource] = []
    for key, edge in network_by_key.items():
        _, _, csv_distance, resource, _ = csv_keys[key]
        if not math.isclose(edge.distance, csv_distance, rel_tol=1e-9, abs_tol=1e-9):
            raise ValueError(
                f"Distance mismatch for edge {edge.u!r} - {edge.v!r}: "
                f"network={edge.distance}, RCSP CSV={csv_distance}"
            )
        resources.append(EdgeResource(edge_id=edge.edge_id, value=resource))

    problem = RCSPProblem(
        network=network,
        edge_resources=tuple(resources),
        resource_unit=resource_unit,
    )
    report = validate_problem(problem)
    if not report.is_valid:
        raise ValueError("Invalid RCSP problem: " + "; ".join(report.errors))
    return problem
