"""Run Seervada network validation and shortest-path analyses."""

from __future__ import annotations

from _runner_utils import workstream_output, write_csv
from src.network.seervada import DEFAULT_SEERVADA_CSV, load_seervada_network
from src.network.validation import validate_network
from src.shortest_path.dijkstra import dijkstra
from src.shortest_path.simple_paths import enumerate_simple_paths
from src.shortest_path.verify import verify_shortest_path


def main() -> None:
    network = load_seervada_network(DEFAULT_SEERVADA_CSV)
    validation = validate_network(
        network,
        source="O",
        target="T",
        expected_edge_count=12,
        require_connected=True,
    )
    if not validation.is_valid:
        raise RuntimeError("Invalid network: " + "; ".join(validation.errors))

    result = dijkstra(network, "O", "T")
    verification = verify_shortest_path(network, "O", "T")
    if not verification.matches:
        raise RuntimeError("Dijkstra and exhaustive path search disagree")

    paths = enumerate_simple_paths(network, "O", "T")
    best_distance = paths[0].distance
    rows = [
        {
            "rank": rank,
            "source": "O",
            "target": "T",
            "path": "-".join(item.nodes),
            "total_distance": item.distance,
            "num_nodes": len(item.nodes),
            "num_edges": len(item.nodes) - 1,
            "algorithm": "brute_force",
            "is_optimal": item.distance == best_distance,
        }
        for rank, item in enumerate(paths, start=1)
    ]

    output = workstream_output(1)
    write_csv(output / "results_paths.csv", rows)
    write_csv(
        output / "shortest_path_summary.csv",
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
    )
    print(f"Validated {validation.node_count} nodes, {validation.edge_count} edges.")
    print(f"Shortest route O -> T: {' -> '.join(result.path)} ({result.distance:g} km)")
    print(f"Saved outputs to {output}")


if __name__ == "__main__":
    main()
