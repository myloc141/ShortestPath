"""Exact resource-constrained shortest-path solvers."""

from __future__ import annotations

import math
from typing import Sequence

from .schema import BruteForceResult, RCSPProblem, RCSPResult
from .validation import build_rcsp_arcs, validate_problem


TOLERANCE = 1e-9


def reconstruct_path_from_arcs(
    selected_arcs: Sequence[tuple[str, str]],
    source: str,
    target: str,
) -> tuple[str, ...] | None:
    """Join selected arcs into one simple path; reject branches or extra arcs."""
    successors: dict[str, str] = {}
    for u, v in selected_arcs:
        if u in successors or v in successors.values():
            return None
        successors[u] = v

    path = [source]
    visited = {source}
    current = source
    while current != target:
        if current not in successors:
            return None
        current = successors[current]
        if current in visited:
            return None
        visited.add(current)
        path.append(current)

    if len(selected_arcs) != len(path) - 1:
        return None
    return tuple(path)


def _path_costs(
    problem: RCSPProblem,
    path: Sequence[str],
) -> tuple[float, float]:
    arc_by_pair: dict[tuple[str, str], tuple[float, float]] = {}
    for arc in build_rcsp_arcs(problem):
        arc_by_pair[(arc.u, arc.v)] = (arc.distance, arc.resource)

    total_distance = 0.0
    total_resource = 0.0
    for u, v in zip(path, path[1:]):
        costs = arc_by_pair.get((u, v))
        if costs is None:
            raise ValueError(f"Path contains a non-network arc {u!r} -> {v!r}")
        total_distance += costs[0]
        total_resource += costs[1]
    return total_distance, total_resource


def brute_force_rcsp(
    problem: RCSPProblem,
    resource_limit: float | None,
    *,
    source: str = "O",
    target: str = "T",
    max_paths: int | None = 1_000_000,
) -> BruteForceResult:
    """Enumerate simple paths, filter by resource limit, and keep all optima."""
    if resource_limit is not None and (
        not math.isfinite(resource_limit) or resource_limit < 0
    ):
        raise ValueError("resource_limit must be finite and non-negative, or None")
    report = validate_problem(problem, source=source, target=target)
    if not report.is_valid:
        raise ValueError("Invalid RCSP problem: " + "; ".join(report.errors))

    from ..shortest_path.simple_paths import iter_simple_paths

    scored: list[tuple[tuple[str, ...], float, float]] = []
    for path_result in iter_simple_paths(
        problem.network, source, target, max_paths=max_paths
    ):
        distance, resource = _path_costs(problem, path_result.nodes)
        scored.append((path_result.nodes, distance, resource))

    feasible = [
        (path, distance, resource)
        for path, distance, resource in scored
        if resource_limit is None or resource <= resource_limit + TOLERANCE
    ]
    if not feasible:
        return BruteForceResult(
            status="Infeasible",
            source=source,
            target=target,
            resource_limit=resource_limit,
            best_distance=None,
            best_paths=(),
            n_paths_total=len(scored),
            n_paths_feasible=0,
        )

    best_distance = min(distance for _, distance, _ in feasible)
    best_paths = tuple(
        sorted(
            path
            for path, distance, _ in feasible
            if math.isclose(
                distance, best_distance, rel_tol=TOLERANCE, abs_tol=TOLERANCE
            )
        )
    )
    return BruteForceResult(
        status="Optimal",
        source=source,
        target=target,
        resource_limit=resource_limit,
        best_distance=best_distance,
        best_paths=best_paths,
        n_paths_total=len(scored),
        n_paths_feasible=len(feasible),
    )


def solve_rcsp_milp(
    problem: RCSPProblem,
    resource_limit: float | None,
    *,
    source: str = "O",
    target: str = "T",
    solver_msg: bool = False,
) -> RCSPResult:
    """Solve a 0-1 flow MILP with PuLP and its bundled CBC solver.

    PuLP is imported only when this function is called. Missing solver
    dependencies raise an actionable error; use ``brute_force_rcsp`` for a
    dependency-free exact solver on small networks.
    """
    if resource_limit is not None and (
        not math.isfinite(resource_limit) or resource_limit < 0
    ):
        raise ValueError("resource_limit must be finite and non-negative, or None")
    report = validate_problem(problem, source=source, target=target)
    if not report.is_valid:
        raise ValueError("Invalid RCSP problem: " + "; ".join(report.errors))

    try:
        import pulp
    except ImportError as exc:
        raise RuntimeError(
            "solve_rcsp_milp requires PuLP; install the project MILP dependency "
            "or use brute_force_rcsp for small networks"
        ) from exc

    arcs = build_rcsp_arcs(problem)
    model = pulp.LpProblem("ResourceConstrainedShortestPath", pulp.LpMinimize)
    variables = {
        index: pulp.LpVariable(f"arc_{index}", cat=pulp.LpBinary)
        for index in range(len(arcs))
    }
    model += pulp.lpSum(
        arcs[index].distance * variables[index] for index in range(len(arcs))
    )

    for node in problem.network.nodes:
        outgoing = pulp.lpSum(
            variables[index] for index, arc in enumerate(arcs) if arc.u == node
        )
        incoming = pulp.lpSum(
            variables[index] for index, arc in enumerate(arcs) if arc.v == node
        )
        rhs = (
            0
            if source == target
            else 1
            if node == source
            else -1
            if node == target
            else 0
        )
        model += outgoing - incoming == rhs, f"flow_{node}"

    if resource_limit is not None:
        model += (
            pulp.lpSum(
                arcs[index].resource * variables[index]
                for index in range(len(arcs))
            )
            <= resource_limit,
            "ResourceLimit",
        )

    model.solve(pulp.PULP_CBC_CMD(msg=solver_msg))
    status = pulp.LpStatus.get(model.status, str(model.status))
    if status != "Optimal":
        return RCSPResult(
            status=status,
            source=source,
            target=target,
            resource_limit=resource_limit,
            path=None,
            total_distance=None,
            total_resource=None,
        )

    selected_arcs = tuple(
        (arcs[index].u, arcs[index].v)
        for index, variable in variables.items()
        if variable.value() is not None and variable.value() > 0.5
    )
    path = reconstruct_path_from_arcs(selected_arcs, source, target)
    if path is None:
        raise RuntimeError(
            "CBC reported an optimal solution, but selected arcs do not form "
            "one source-to-target path"
        )
    total_distance, total_resource = _path_costs(problem, path)
    return RCSPResult(
        status=status,
        source=source,
        target=target,
        resource_limit=resource_limit,
        path=path,
        total_distance=total_distance,
        total_resource=total_resource,
        selected_arcs=selected_arcs,
    )
