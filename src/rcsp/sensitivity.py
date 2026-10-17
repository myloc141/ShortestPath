"""RCSP resource-limit sensitivity analysis without implicit file writes."""

from __future__ import annotations

from dataclasses import dataclass

from .schema import RCSPProblem
from .solver import brute_force_rcsp


@dataclass(frozen=True)
class SensitivityRow:
    resource_limit: float | None
    status: str
    optimal_path: tuple[str, ...] | None
    total_distance: float | None
    total_resource: float | None
    route_changed_vs_previous: bool


def sensitivity_analysis(
    problem: RCSPProblem,
    resource_limits: list[float | None] | tuple[float | None, ...],
    *,
    source: str = "O",
    target: str = "T",
    max_paths: int | None = 1_000_000,
) -> tuple[SensitivityRow, ...]:
    """Solve for each resource limit and flag changes in the chosen route.

    This function is pure with respect to the filesystem: callers decide
    whether and where to persist the returned rows.
    """
    rows: list[SensitivityRow] = []
    previous_path: tuple[str, ...] | None = None
    for limit in resource_limits:
        result = brute_force_rcsp(
            problem,
            limit,
            source=source,
            target=target,
            max_paths=max_paths,
        )
        path = result.best_paths[0] if result.best_paths else None
        rows.append(
            SensitivityRow(
                resource_limit=limit,
                status=result.status,
                optimal_path=path,
                total_distance=result.best_distance,
                total_resource=(
                    _resource_for_path(problem, path) if path is not None else None
                ),
                route_changed_vs_previous=path != previous_path,
            )
        )
        previous_path = path
    return tuple(rows)


def _resource_for_path(
    problem: RCSPProblem,
    path: tuple[str, ...],
) -> float:
    resource_by_id = {
        item.edge_id: item.value for item in problem.edge_resources
    }
    edge_by_pair: dict[tuple[str, str], str] = {}
    for edge in problem.network.edges:
        edge_by_pair[(edge.u, edge.v)] = edge.edge_id
        if not edge.directed:
            edge_by_pair[(edge.v, edge.u)] = edge.edge_id
    return sum(
        resource_by_id[edge_by_pair[(u, v)]]
        for u, v in zip(path, path[1:])
    )
