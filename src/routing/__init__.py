"""Route-selection experiments and routing-result summaries."""

from .experiment import (
    RouteReference,
    RoutingResult,
    RoutingSummary,
    parse_route_path,
    run_routing_experiment,
    shortest_route_with_weights,
    summarize_routing_results,
)
from .comparison import PairwiseRoutingComparison, compare_routing_pairs

__all__ = [
    "PairwiseRoutingComparison",
    "RouteReference",
    "RoutingResult",
    "RoutingSummary",
    "compare_routing_pairs",
    "parse_route_path",
    "run_routing_experiment",
    "shortest_route_with_weights",
    "summarize_routing_results",
]
