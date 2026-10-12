"""Convert a normalized network into an adjacency-list representation."""

from __future__ import annotations

import math

from .schema import Network


Adjacency = dict[str, tuple[tuple[str, float], ...]]


def build_adjacency(network: Network) -> Adjacency:
    """Build adjacency lists, expanding each undirected edge into two arcs."""
    adjacency: dict[str, list[tuple[str, float]]] = {
        node: [] for node in network.nodes
    }

    for edge in network.edges:
        if edge.u not in adjacency or edge.v not in adjacency:
            raise ValueError(
                f"Edge {edge.edge_id!r} refers to a node outside network.nodes"
            )
        if edge.u == edge.v:
            raise ValueError(f"Edge {edge.edge_id!r} is a self-loop")
        if not math.isfinite(edge.distance) or edge.distance < 0:
            raise ValueError(
                f"Edge {edge.edge_id!r} must have a finite, non-negative distance"
            )

        adjacency[edge.u].append((edge.v, edge.distance))
        if not edge.directed:
            adjacency[edge.v].append((edge.u, edge.distance))

    return {
        node: tuple(sorted(neighbors, key=lambda item: (item[0], item[1])))
        for node, neighbors in adjacency.items()
    }
