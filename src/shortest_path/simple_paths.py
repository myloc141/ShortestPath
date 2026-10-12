"""Brute-force enumeration of simple routes for small networks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from ..network.encoding import build_adjacency
from ..network.schema import Network


@dataclass(frozen=True)
class SimplePath:
    nodes: tuple[str, ...]
    distance: float


class PathLimitExceeded(RuntimeError):
    """Raised when enumeration exceeds its explicit path-count limit."""


def iter_simple_paths(
    network: Network,
    source: str,
    target: str,
    *,
    max_paths: int | None = 1_000_000,
) -> Iterator[SimplePath]:
    """Yield simple source-to-target paths in deterministic traversal order.

    Enumeration is exponential in the worst case. ``max_paths`` prevents an
    accidental unbounded materialization; pass ``None`` only when unbounded
    enumeration is intended.
    """
    if max_paths is not None and max_paths < 1:
        raise ValueError("max_paths must be positive or None")
    adjacency = build_adjacency(network)
    if source not in adjacency:
        raise ValueError(f"Source node {source!r} is not in the network")
    if target not in adjacency:
        raise ValueError(f"Target node {target!r} is not in the network")

    emitted = 0

    def visit(
        current: str,
        path: tuple[str, ...],
        accumulated_distance: float,
    ) -> Iterator[SimplePath]:
        nonlocal emitted
        if current == target:
            if max_paths is not None and emitted >= max_paths:
                raise PathLimitExceeded(
                    f"Simple-path enumeration exceeded max_paths={max_paths}"
                )
            emitted += 1
            yield SimplePath(nodes=path, distance=accumulated_distance)
            return

        for neighbor, edge_distance in adjacency[current]:
            if neighbor not in path:
                yield from visit(
                    neighbor,
                    path + (neighbor,),
                    accumulated_distance + edge_distance,
                )

    yield from visit(source, (source,), 0.0)


def enumerate_simple_paths(
    network: Network,
    source: str,
    target: str,
    *,
    max_paths: int | None = 1_000_000,
) -> tuple[SimplePath, ...]:
    """Return all simple paths sorted by distance, then node sequence."""
    paths = tuple(
        iter_simple_paths(network, source, target, max_paths=max_paths)
    )
    return tuple(sorted(paths, key=lambda item: (item.distance, item.nodes)))
