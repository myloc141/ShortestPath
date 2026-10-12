"""Independent checks for RCSP solver results."""

from __future__ import annotations

import math

from ..network.encoding import build_adjacency
from ..shortest_path.dijkstra import dijkstra
from .schema import RCSPCrossCheck, RCSPProblem, RCSPResult, SolutionVerification
from .solver import (
    TOLERANCE,
    _path_costs,
    brute_force_rcsp,
    reconstruct_path_from_arcs,
)


def verify_solution(
    problem: RCSPProblem,
    result: RCSPResult,
    *,
    source: str = "O",
    target: str = "T",
) -> SolutionVerification:
    """Check route validity, reported totals, and the resource constraint."""
    checks: list[tuple[str, bool]] = [
        ("is_optimal_result", result.is_optimal),
        ("source_matches", result.source == source),
        ("target_matches", result.target == target),
    ]
    path = result.path
    if path is None:
        checks.append(("path_exists", False))
        return SolutionVerification(checks=tuple(checks))
    if not path:
        checks.extend(
            (
                ("path_exists", False),
                ("costs_recomputed", False),
            )
        )
        return SolutionVerification(checks=tuple(checks))

    adjacency = build_adjacency(problem.network)
    selected_path = (
        reconstruct_path_from_arcs(result.selected_arcs, source, target)
        if result.selected_arcs
        else ((source,) if source == target else None)
    )
    checks.extend(
        (
            ("starts_at_source", path[0] == source),
            ("ends_at_target", path[-1] == target),
            ("has_no_repeated_nodes", len(path) == len(set(path))),
            ("selected_arcs_match_path", selected_path == path),
            (
                "all_arcs_exist",
                all(
                    v in {neighbor for neighbor, _ in adjacency.get(u, ())}
                    for u, v in zip(path, path[1:])
                ),
            ),
        )
    )
    try:
        distance, resource = _path_costs(problem, path)
    except ValueError:
        checks.append(("costs_recomputed", False))
        return SolutionVerification(checks=tuple(checks))

    checks.extend(
        (
            (
                "distance_matches",
                result.total_distance is not None
                and math.isclose(
                    distance,
                    result.total_distance,
                    rel_tol=TOLERANCE,
                    abs_tol=TOLERANCE,
                ),
            ),
            (
                "resource_matches",
                result.total_resource is not None
                and math.isclose(
                    resource,
                    result.total_resource,
                    rel_tol=TOLERANCE,
                    abs_tol=TOLERANCE,
                ),
            ),
            (
                "resource_within_limit",
                result.resource_limit is None
                or resource <= result.resource_limit + TOLERANCE,
            ),
        )
    )
    return SolutionVerification(checks=tuple(checks))


def cross_check_with_brute_force(
    problem: RCSPProblem,
    result: RCSPResult,
    *,
    source: str = "O",
    target: str = "T",
    max_paths: int | None = 1_000_000,
) -> RCSPCrossCheck:
    """Check solver feasibility and objective against exhaustive enumeration."""
    exhaustive = brute_force_rcsp(
        problem,
        result.resource_limit,
        source=source,
        target=target,
        max_paths=max_paths,
    )
    if result.status != exhaustive.status:
        return RCSPCrossCheck(
            solver_result=result,
            brute_force_result=exhaustive,
            objective_matches=False,
            path_is_brute_force_optimal=False,
        )
    if result.status != "Optimal":
        return RCSPCrossCheck(
            solver_result=result,
            brute_force_result=exhaustive,
            objective_matches=True,
            path_is_brute_force_optimal=True,
        )

    objective_matches = (
        result.total_distance is not None
        and exhaustive.best_distance is not None
        and math.isclose(
            result.total_distance,
            exhaustive.best_distance,
            rel_tol=TOLERANCE,
            abs_tol=TOLERANCE,
        )
    )
    path_is_optimal = (
        result.path in exhaustive.best_paths
        and verify_solution(
            problem, result, source=source, target=target
        ).is_valid
    )
    return RCSPCrossCheck(
        solver_result=result,
        brute_force_result=exhaustive,
        objective_matches=objective_matches,
        path_is_brute_force_optimal=path_is_optimal,
    )


def unconstrained_shortest_path_resource(
    problem: RCSPProblem,
    *,
    source: str = "O",
    target: str = "T",
) -> tuple[float, float | None, tuple[str, ...]]:
    """Return the distance-shortest route and its resource use as a baseline."""
    result = dijkstra(problem.network, source, target)
    if not result.is_reachable:
        return result.distance, None, result.path
    _, resource = _path_costs(problem, result.path)
    return result.distance, resource, result.path
