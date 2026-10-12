"""Static validation for normalized networks and routing endpoints."""

from __future__ import annotations

from dataclasses import dataclass
import math

from .encoding import build_adjacency
from .schema import Network


@dataclass(frozen=True)
class NetworkValidation:
    """Validation results; an empty errors tuple means the network is valid."""

    errors: tuple[str, ...]
    node_count: int
    edge_count: int
    arc_count: int

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_network(
    network: Network,
    *,
    source: str | None = None,
    target: str | None = None,
    expected_edge_count: int | None = None,
    expected_distance_unit: str = "km",
    require_connected: bool = True,
) -> NetworkValidation:
    """Check identifiers, edges, units, connectivity, and optional endpoints.

    Connectivity is checked on the underlying undirected graph. If both
    ``source`` and ``target`` are provided, directed reachability from source
    to target is checked separately.
    """
    errors: list[str] = []
    node_set = set(network.nodes)
    edge_ids: set[str] = set()
    directed_pairs: set[tuple[str, str]] = set()
    undirected_pairs: set[frozenset[str]] = set()
    arc_count = 0

    if not network.nodes:
        errors.append("The network has no nodes")
    if len(node_set) != len(network.nodes):
        errors.append("Node identifiers must be unique")
    if any(not isinstance(node, str) or not node.strip() for node in network.nodes):
        errors.append("Node identifiers must be non-empty strings")
    if not network.distance_unit.strip():
        errors.append("The distance unit must not be empty")
    elif network.distance_unit != expected_distance_unit:
        errors.append(
            f"Expected distance unit {expected_distance_unit!r}, "
            f"got {network.distance_unit!r}"
        )
    if expected_edge_count is not None and len(network.edges) != expected_edge_count:
        errors.append(
            f"Expected {expected_edge_count} edges, got {len(network.edges)}"
        )

    undirected_adjacency: dict[str, set[str]] = {
        node: set() for node in network.nodes
    }
    directed_adjacency: dict[str, set[str]] = {
        node: set() for node in network.nodes
    }

    for edge in network.edges:
        if not edge.edge_id.strip():
            errors.append("Edge identifiers must not be empty")
        elif edge.edge_id in edge_ids:
            errors.append(f"Duplicate edge identifier {edge.edge_id!r}")
        edge_ids.add(edge.edge_id)

        if edge.u not in node_set or edge.v not in node_set:
            errors.append(
                f"Edge {edge.edge_id!r} has an endpoint not listed in network.nodes"
            )
            continue
        if edge.u == edge.v:
            errors.append(f"Edge {edge.edge_id!r} is a self-loop")
        if not math.isfinite(edge.distance) or edge.distance <= 0:
            errors.append(
                f"Edge {edge.edge_id!r} must have a finite, positive distance"
            )

        if edge.directed:
            pair = (edge.u, edge.v)
            if pair in directed_pairs:
                errors.append(f"Duplicate directed edge {edge.u!r} -> {edge.v!r}")
            directed_pairs.add(pair)
            directed_adjacency[edge.u].add(edge.v)
            arc_count += 1
        else:
            pair = frozenset((edge.u, edge.v))
            if pair in undirected_pairs:
                errors.append(
                    f"Duplicate undirected edge between {edge.u!r} and {edge.v!r}"
                )
            undirected_pairs.add(pair)
            directed_adjacency[edge.u].add(edge.v)
            directed_adjacency[edge.v].add(edge.u)
            arc_count += 2

        undirected_adjacency[edge.u].add(edge.v)
        undirected_adjacency[edge.v].add(edge.u)

    if (source is None) != (target is None):
        errors.append("Provide both source and target, or neither")
    if source is not None and source not in node_set:
        errors.append(f"Source node {source!r} is not in the network")
    if target is not None and target not in node_set:
        errors.append(f"Target node {target!r} is not in the network")

    if require_connected and node_set:
        first_node = next(iter(network.nodes))
        visited = {first_node}
        pending = [first_node]
        while pending:
            current = pending.pop()
            for neighbor in undirected_adjacency[current] - visited:
                visited.add(neighbor)
                pending.append(neighbor)
        if visited != node_set:
            errors.append("The network is not weakly connected")

    if (
        source is not None
        and target is not None
        and source in node_set
        and target in node_set
    ):
        reachable = {source}
        pending = [source]
        while pending:
            current = pending.pop()
            for neighbor in directed_adjacency[current] - reachable:
                reachable.add(neighbor)
                pending.append(neighbor)
        if target not in reachable:
            errors.append(f"No directed route exists from {source!r} to {target!r}")

    try:
        build_adjacency(network)
    except ValueError as exc:
        errors.append(str(exc))

    return NetworkValidation(
        errors=tuple(errors),
        node_count=len(network.nodes),
        edge_count=len(network.edges),
        arc_count=arc_count,
    )
