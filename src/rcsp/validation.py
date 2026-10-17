"""Validation and arc expansion for resource-constrained (RCSP) network data."""

from __future__ import annotations

from dataclasses import dataclass
import math

from ..network.validation import validate_network
from .schema import RCSPProblem, ResourceArc


@dataclass(frozen=True)
class RCSPValidation:
    errors: tuple[str, ...]
    node_count: int
    edge_count: int
    arc_count: int

    @property
    def is_valid(self) -> bool:
        return not self.errors


def validate_problem(
    problem: RCSPProblem,
    *,
    source: str | None = None,
    target: str | None = None,
    expected_edge_count: int | None = None,
    require_connected: bool = False,
) -> RCSPValidation:
    """Check the underlying graph and resource-cost coverage."""
    network_report = validate_network(
        problem.network,
        expected_edge_count=expected_edge_count,
        require_connected=require_connected,
    )
    errors = list(network_report.errors)
    node_set = set(problem.network.nodes)
    if (source is None) != (target is None):
        errors.append("Provide both source and target, or neither")
    if source is not None and source not in node_set:
        errors.append(f"Source node {source!r} is not in the network")
    if target is not None and target not in node_set:
        errors.append(f"Target node {target!r} is not in the network")
    if not problem.resource_unit.strip():
        errors.append("The resource unit must not be empty")

    edge_ids = {edge.edge_id for edge in problem.network.edges}
    resource_ids: set[str] = set()
    for cost in problem.edge_resources:
        if not cost.edge_id.strip():
            errors.append("Resource edge identifiers must not be empty")
        if cost.edge_id in resource_ids:
            errors.append(f"Duplicate resource cost for edge {cost.edge_id!r}")
        resource_ids.add(cost.edge_id)
        if not math.isfinite(cost.value) or cost.value < 0:
            errors.append(
                f"Resource cost for edge {cost.edge_id!r} "
                "must be finite and non-negative"
            )

    missing = edge_ids - resource_ids
    extra = resource_ids - edge_ids
    if missing:
        errors.append(f"Missing resource costs for edges: {sorted(missing)}")
    if extra:
        errors.append(f"Resource costs refer to unknown edges: {sorted(extra)}")

    return RCSPValidation(
        errors=tuple(errors),
        node_count=network_report.node_count,
        edge_count=network_report.edge_count,
        arc_count=network_report.arc_count,
    )


def build_rcsp_arcs(problem: RCSPProblem) -> tuple[ResourceArc, ...]:
    """Expand each undirected edge into two directed resource-cost arcs."""
    report = validate_problem(problem, require_connected=False)
    if not report.is_valid:
        raise ValueError("Invalid RCSP problem: " + "; ".join(report.errors))

    resource_by_id = {
        cost.edge_id: cost.value for cost in problem.edge_resources
    }
    arcs: list[ResourceArc] = []
    for edge in problem.network.edges:
        endpoints = [(edge.u, edge.v)]
        if not edge.directed:
            endpoints.append((edge.v, edge.u))
        for u, v in endpoints:
            arcs.append(
                ResourceArc(
                    u=u,
                    v=v,
                    edge_id=edge.edge_id,
                    distance=edge.distance,
                    resource=resource_by_id[edge.edge_id],
                )
            )
    return tuple(arcs)
