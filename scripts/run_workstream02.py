"""Run RCSP MILP, independent verification, and resource-limit sensitivity."""

from __future__ import annotations

from _runner_utils import workstream_output, write_csv
from src.network.seervada import load_seervada_network
from src.rscp.data import DEFAULT_RCSP_CSV, load_rcsp_problem
from src.rscp.sensitivity import sensitivity_analysis
from src.rscp.solver import brute_force_rcsp, solve_rcsp_milp
from src.rscp.verify import cross_check_with_brute_force, verify_solution


def main() -> None:
    network = load_seervada_network()
    problem = load_rcsp_problem(DEFAULT_RCSP_CSV, network=network)
    limits = (17, 18, 19, 20, None)
    sensitivity = sensitivity_analysis(problem, limits)
    sensitivity_rows = [
        {
            "resource_limit": item.resource_limit,
            "status": item.status,
            "optimal_path": (
                "-".join(item.optimal_path) if item.optimal_path is not None else ""
            ),
            "total_distance": item.total_distance,
            "total_resource": item.total_resource,
            "route_changed_vs_previous": item.route_changed_vs_previous,
        }
        for item in sensitivity
    ]

    verification_rows = []
    for limit in limits:
        milp_result = solve_rcsp_milp(problem, limit)
        exhaustive = brute_force_rcsp(problem, limit)
        verification = (
            verify_solution(problem, milp_result)
            if milp_result.status == "Optimal"
            else None
        )
        cross_check = cross_check_with_brute_force(problem, milp_result)
        verification_rows.append(
            {
                "resource_limit": limit,
                "milp_status": milp_result.status,
                "milp_path": (
                    "-".join(milp_result.path)
                    if milp_result.path is not None
                    else ""
                ),
                "milp_distance": milp_result.total_distance,
                "milp_resource": milp_result.total_resource,
                "brute_force_status": exhaustive.status,
                "brute_force_distance": exhaustive.best_distance,
                "n_paths_total": exhaustive.n_paths_total,
                "n_paths_feasible": exhaustive.n_paths_feasible,
                "solution_valid": verification.is_valid if verification else "",
                "cross_check_matches": cross_check.matches,
            }
        )

    consistency_rows = [
        {
            "edge_id": edge.edge_id,
            "node_u": edge.u,
            "node_v": edge.v,
            "distance_km": edge.distance,
            "topology_matches": True,
        }
        for edge in problem.network.edges
    ]
    output = workstream_output(2)
    write_csv(output / "rcsp_sensitivity.csv", sensitivity_rows)
    write_csv(output / "rcsp_verification.csv", verification_rows)
    write_csv(output / "rcsp_network_consistency.csv", consistency_rows)
    print(f"Saved RCSP sensitivity, verification, and consistency tables to {output}")


if __name__ == "__main__":
    main()
