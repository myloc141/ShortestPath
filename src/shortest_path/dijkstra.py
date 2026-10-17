"""Dijkstra shortest-path search for the canonical network schema."""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass
from typing import Mapping

from ..network.encoding import build_adjacency
from ..network.schema import Network


@dataclass(frozen=True)
class ShortestPathResult:
    """Shortest route and the reachable-distance/predecessor maps."""

    source: str
    target: str
    distance: float
    path: tuple[str, ...]
    distances: dict[str, float]
    predecessors: dict[str, str | None]

    @property
    def is_reachable(self) -> bool:
        return math.isfinite(self.distance)


def dijkstra(
    network: Network,
    source: str,
    target: str,
    *,
    weights: Mapping[str, float] | None = None,
) -> ShortestPathResult:
    """Find a shortest path, breaking ties by lexicographic node sequence.

    When ``weights`` is provided, it maps every edge ID to that edge's
    non-negative traversal weight. Otherwise, the network distances are used.
    """
    adjacency = build_adjacency(network, weights=weights)
    if source not in adjacency:
        raise ValueError(f"Source node {source!r} is not in the network")
    if target not in adjacency:
        raise ValueError(f"Target node {target!r} is not in the network")

    distances = {node: math.inf for node in adjacency}
    best_paths: dict[str, tuple[str, ...]] = {}
    predecessors: dict[str, str | None] = {node: None for node in adjacency}
    initial_path = (source,)
    distances[source] = 0.0
    best_paths[source] = initial_path
    pending: list[tuple[float, tuple[str, ...], str]] = [
        (0.0, initial_path, source)
    ]

    while pending:
        distance, path, current = heapq.heappop(pending)
        if distance != distances[current] or path != best_paths.get(current):
            continue
        if current == target:
            break

        for neighbor, edge_distance in adjacency[current]:
            if neighbor in path:
                continue
            candidate_distance = distance + edge_distance
            candidate_path = path + (neighbor,)
            current_best = distances[neighbor], best_paths.get(neighbor, ())
            if (candidate_distance, candidate_path) < current_best:
                distances[neighbor] = candidate_distance
                best_paths[neighbor] = candidate_path
                predecessors[neighbor] = current
                heapq.heappush(
                    pending, (candidate_distance, candidate_path, neighbor)
                )

    path_to_target = best_paths.get(target, ())
    return ShortestPathResult(
        source=source,
        target=target,
        distance=distances[target],
        path=path_to_target,
        distances=distances,
        predecessors=predecessors,
    )
