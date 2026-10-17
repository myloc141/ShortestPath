"""Prepare chronological train/validation/test features for a dataset."""

from __future__ import annotations

import json

from _runner_utils import (
    load_dataset_adapter,
    load_network_artifact,
    parse_workstream_args,
    resolve_artifacts_root,
    stage_dir,
    validate_with_error_report,
    write_frame,
)
from src.common.validators import validate_i4
from src.preprocess.dataset import prepare_observation_splits


def main() -> None:
    args = parse_workstream_args(3, __doc__ or "Run Workstream 03")
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    adapter, config = load_dataset_adapter(args.dataset, root=root)
    prepared = prepare_observation_splits(
        adapter.build_observations(
            network=load_network_artifact(args.dataset, adapter, root=root)
        ),
        train_fraction=config.train_fraction,
        valid_fraction=config.valid_fraction,
    )
    output = stage_dir(args.dataset, "processed", root)
    output.mkdir(parents=True, exist_ok=True)
    validate_with_error_report(
        validate_i4,
        prepared.raw_splits["train"],
        prepared.raw_splits["valid"],
        prepared.raw_splits["test"],
        prepared.split_manifest,
        output_dir=stage_dir(args.dataset, "_errors", root),
        dataset=args.dataset,
        stage="workstream03",
    )
    for name in ("train", "valid", "test"):
        write_frame(
            output / f"{name}.csv",
            prepared.raw_splits[name],
            with_meta=args.with_meta,
            dataset=args.dataset,
            interface_id="I4",
        )
        write_frame(
            output / f"X_{name}_preprocessed.csv",
            prepared.features[name],
            with_meta=args.with_meta,
            dataset=args.dataset,
            interface_id="I4",
        )
        write_frame(
            output / f"y_{name}.csv",
            prepared.targets[name].to_frame(name="travel_time"),
            with_meta=args.with_meta,
            dataset=args.dataset,
            interface_id="I4",
        )

    write_frame(
        output / "split_manifest.csv",
        prepared.split_manifest,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I4",
    )
    metadata = {
        **prepared.pipeline_metadata,
        "source": config.observations_path or config.traffic_parquet,
    }
    (output / "preprocessing_pipeline.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    counts = prepared.pipeline_metadata
    print(
        f"Prepared {counts['train_rows']} train, {counts['valid_rows']} "
        f"validation, and {counts['test_rows']} test rows in {output}"
    )


if __name__ == "__main__":
    main()
