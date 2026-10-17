"""Network schemas, adjacency encoding, and validation."""

from .encoding import Adjacency, build_adjacency
from .schema import Network, NetworkEdge
from .validation import NetworkValidation, validate_network

__all__ = [
    "Adjacency",
    "Network",
    "NetworkEdge",
    "NetworkValidation",
    "build_adjacency",
    "validate_network",
]
