"""Build an auxiliary model-data branch from PEMS-BAY Parquet.

Pipeline order: raw H5/PKL/CSV -> ``run_preprocess_pems_bay.py`` ->
long-form Parquet and quality reports -> WS1 I1 network -> this optional
branch's edge/day/time-slot observations and chronological splits. WS4–WS6
read the I4 files produced by WS3 instead of this ``model_dataset`` output.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from _runner_utils import (
    REPOSITORY_ROOT,
    add_artifacts_root_arguments,
    load_dataset_adapter,
    load_network_artifact,
    resolve_artifacts_root,
    stage_dir,
)
from src.adapters.pemsbay import build_pemsbay_dataset


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a cleaned time-series dataset using a YAML config."
    )
    parser.add_argument(
        "--dataset",
        default="pemsbay",
        choices=("pemsbay",),
        help="dataset to build (default: pemsbay)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Dataset configuration YAML (default: configs/<dataset>.yaml)",
    )
    add_artifacts_root_arguments(parser)
    arguments = parser.parse_args()
    root = resolve_artifacts_root(
        arguments.artifacts_root, arguments.output_dir
    )
    config_path = arguments.config or (
        REPOSITORY_ROOT / "configs" / f"{arguments.dataset}.yaml"
    )
    adapter, _ = load_dataset_adapter(
        arguments.dataset,
        root=root,
        config_path=config_path,
    )
    adapter.build_network()
    network = load_network_artifact(arguments.dataset, adapter, root=root)
    destination = build_pemsbay_dataset(
        config_path,
        output_dir=stage_dir(arguments.dataset, "model_dataset", root),
        traffic_parquet=(
            stage_dir(arguments.dataset, "processed", root)
            / "traffic_speed_long.parquet"
        ),
        network=network,
        adapter=adapter,
    )
    print(f"Built dataset files in {destination}")


if __name__ == "__main__":
    main()
