"""Run Seervada network validation and shortest-path analyses."""

from __future__ import annotations

from _runner_utils import (
    load_dataset_adapter,
    parse_workstream_args,
    routing_endpoints,
    resolve_artifacts_root,
    stage_dir,
    validate_with_error_report,
    write_csv,
)
from src.common.validators import validate_i1
from src.network.validation import validate_network
from src.shortest_path.dijkstra import dijkstra
from src.shortest_path.simple_paths import enumerate_simple_paths
from src.shortest_path.verify import verify_shortest_path


def main() -> None:
    args = parse_workstream_args(1, __doc__ or "Run Workstream 01")
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    adapter, config = load_dataset_adapter(args.dataset, root=root)
    network = adapter.build_network()
    source, target = routing_endpoints(
        adapter, source=config.source, target=config.target
    )
    validation = validate_network(
        network,
        source=source,
        target=target,
        require_connected=True,
    )
    if not validation.is_valid:
        raise RuntimeError("Invalid network: " + "; ".join(validation.errors))

    result = dijkstra(network, source, target)
    verification = verify_shortest_path(
        network, source, target, max_paths=config.max_paths
    )
    if not verification.matches:
        raise RuntimeError("Dijkstra and exhaustive path search disagree")

    paths = enumerate_simple_paths(
        network, source, target, max_paths=config.max_paths
    )
    best_distance = paths[0].distance
    rows = [
        {
            "rank": rank,
            "source": source,
            "target": target,
            "path": "-".join(item.nodes),
            "total_distance": item.distance,
            "num_nodes": len(item.nodes),
            "num_edges": len(item.nodes) - 1,
            "algorithm": "brute_force",
            "is_optimal": item.distance == best_distance,
        }
        for rank, item in enumerate(paths, start=1)
    ]

    network_output = stage_dir(args.dataset, "network", root)
    paths_output = stage_dir(args.dataset, "paths", root)
    errors_output = stage_dir(args.dataset, "_errors", root)
    network_output.mkdir(parents=True, exist_ok=True)
    paths_output.mkdir(parents=True, exist_ok=True)
    node_rows = [{"node_id": node} for node in network.nodes]
    edge_rows = [
        {
            "edge_id": edge.edge_id,
            "u": edge.u,
            "v": edge.v,
            "distance": edge.distance,
            "directed": edge.directed,
        }
        for edge in network.edges
    ]
    validate_with_error_report(
        validate_i1,
        node_rows,
        edge_rows,
        output_dir=errors_output,
        dataset=args.dataset,
        stage="workstream01",
    )
    write_csv(
        network_output / "network_nodes.csv",
        node_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I1",
    )
    write_csv(
        network_output / "network_edges.csv",
        edge_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I1",
    )
    write_csv(
        paths_output / "results_paths.csv",
        rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I2",
    )
    write_csv(
        paths_output / "shortest_path_summary.csv",
        [
            {
                "source": result.source,
                "target": result.target,
                "path": "-".join(result.path),
                "total_distance": result.distance,
                "paths_checked": verification.paths_checked,
                "verified": verification.matches,
            }
        ],
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I2",
    )
    print(f"Validated {validation.node_count} nodes, {validation.edge_count} edges.")
    print(
        f"Shortest route {source} -> {target}: "
        f"{' -> '.join(result.path)} ({result.distance:g} km)"
    )
    print(f"Saved network outputs to {network_output} and path outputs to {paths_output}")


if __name__ == "__main__":
    main()
