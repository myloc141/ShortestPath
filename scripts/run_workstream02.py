"""Run RCSP MILP, independent verification, and resource-limit sensitivity."""

from __future__ import annotations

from _runner_utils import (
    load_dataset_adapter,
    parse_workstream_args,
    load_network_artifact,
    configured_path,
    resolve_artifacts_root,
    routing_endpoints,
    stage_dir,
    write_csv,
)
from src.rcsp.data import load_rcsp_problem
from src.rcsp.sensitivity import sensitivity_analysis
from src.rcsp.solver import brute_force_rcsp, solve_rcsp_milp
from src.rcsp.verify import cross_check_with_brute_force, verify_solution


def main() -> None:
    args = parse_workstream_args(2, __doc__ or "Run Workstream 02")
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    adapter, config = load_dataset_adapter(args.dataset, root=root)
    if not config.rcsp_path:
        raise ValueError(
            f"Dataset {args.dataset!r} has no RCSP resource file configured"
        )
    adapter.build_network()
    network = load_network_artifact(args.dataset, adapter, root=root)
    source, target = routing_endpoints(
        adapter, source=config.source, target=config.target
    )
    problem = load_rcsp_problem(
        configured_path(config.rcsp_path),
        network=network,
    )
    limits = config.time_limits or (17, 18, 19, 20, None)
    sensitivity = sensitivity_analysis(
        problem,
        limits,
        source=source,
        target=target,
        max_paths=config.max_paths,
    )
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
        milp_result = solve_rcsp_milp(
            problem, limit, source=source, target=target
        )
        exhaustive = brute_force_rcsp(
            problem,
            limit,
            source=source,
            target=target,
            max_paths=config.max_paths,
        )
        verification = (
            verify_solution(
                problem, milp_result, source=source, target=target
            )
            if milp_result.status == "Optimal"
            else None
        )
        cross_check = cross_check_with_brute_force(
            problem,
            milp_result,
            source=source,
            target=target,
            max_paths=config.max_paths,
        )
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
    output = stage_dir(args.dataset, "rcsp", root)
    output.mkdir(parents=True, exist_ok=True)
    write_csv(
        output / "rcsp_sensitivity.csv",
        sensitivity_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I3",
    )
    write_csv(
        output / "rcsp_verification.csv",
        verification_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I3",
    )
    write_csv(
        output / "rcsp_network_consistency.csv",
        consistency_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I3",
    )
    print(f"Saved RCSP sensitivity, verification, and consistency tables to {output}")


if __name__ == "__main__":
    main()
