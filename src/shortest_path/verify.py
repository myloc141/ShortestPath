"""Independent exhaustive cross-check of Dijkstra on simple paths."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ..network.schema import Network
from .dijkstra import ShortestPathResult, dijkstra
from .simple_paths import iter_simple_paths


@dataclass(frozen=True)
class ShortestPathVerification:
    dijkstra_result: ShortestPathResult
    exhaustive_path: tuple[str, ...]
    exhaustive_distance: float
    paths_checked: int
    matches: bool


def verify_shortest_path(
    network: Network,
    source: str,
    target: str,
    *,
    max_paths: int | None = 1_000_000,
) -> ShortestPathVerification:
    """Compare Dijkstra's route with exhaustive simple-path enumeration.

    Both methods use the same deterministic tie rule: minimum distance, then
    lexicographically smallest complete node sequence. A path limit is
    reported as ``PathLimitExceeded`` rather than returning a partial result.
    """
    dijkstra_result = dijkstra(network, source, target)
    best_path: tuple[str, ...] = ()
    best_distance = math.inf
    paths_checked = 0

    for candidate in iter_simple_paths(
        network, source, target, max_paths=max_paths
    ):
        paths_checked += 1
        if (candidate.distance, candidate.nodes) < (best_distance, best_path):
            best_distance = candidate.distance
            best_path = candidate.nodes

    matches = (
        dijkstra_result.distance == best_distance
        and dijkstra_result.path == best_path
    )
    return ShortestPathVerification(
        dijkstra_result=dijkstra_result,
        exhaustive_path=best_path,
        exhaustive_distance=best_distance,
        paths_checked=paths_checked,
        matches=matches,
    )
