"""Convert a normalized network into an adjacency-list representation."""

from __future__ import annotations

import math
from typing import Mapping

from .schema import Network


Adjacency = dict[str, tuple[tuple[str, float], ...]]


def build_adjacency(
    network: Network,
    *,
    weights: Mapping[str, float] | None = None,
) -> Adjacency:
    """Build adjacency lists, expanding undirected edges into two arcs.

    Optional weights override edge distances and are keyed by edge ID.
    """
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
        if weights is None:
            edge_weight = edge.distance
            if not math.isfinite(edge_weight) or edge_weight < 0:
                raise ValueError(
                    f"Edge {edge.edge_id!r} must have a finite, "
                    "non-negative distance"
                )
        else:
            try:
                raw_weight = weights[edge.edge_id]
            except KeyError as error:
                raise ValueError(
                    f"Missing weight for edge {edge.edge_id!r}"
                ) from error
            if isinstance(raw_weight, (str, bytes, bool)):
                raise ValueError(
                    f"Weight for edge {edge.edge_id!r} must be a finite, "
                    "non-negative number"
                )
            try:
                edge_weight = float(raw_weight)
            except (TypeError, ValueError, OverflowError) as error:
                raise ValueError(
                    f"Weight for edge {edge.edge_id!r} must be a finite, "
                    "non-negative number"
                ) from error
            if not math.isfinite(edge_weight) or edge_weight < 0:
                raise ValueError(
                    f"Weight for edge {edge.edge_id!r} must be finite and "
                    "non-negative"
                )

        adjacency[edge.u].append((edge.v, edge_weight))
        if not edge.directed:
            adjacency[edge.v].append((edge.u, edge_weight))

    return {
        node: tuple(sorted(neighbors, key=lambda item: (item[0], item[1])))
        for node, neighbors in adjacency.items()
    }
