"""Canonical network schema shared by network and routing modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NetworkEdge:
    """One source edge; undirected edges are stored once."""

    edge_id: str
    u: str
    v: str
    distance: float
    directed: bool = False


@dataclass(frozen=True)
class Network:
    """Normalized graph data used by all network and routing functions."""

    nodes: tuple[str, ...]
    edges: tuple[NetworkEdge, ...]
    distance_unit: str
    distance_is_approximate: bool = False
    distance_method: str = "Provided by source data"
