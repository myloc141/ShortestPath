"""Combine available workstream result files into one Markdown report."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from _runner_utils import (
    add_artifacts_root_arguments,
    resolve_artifacts_root,
    stage_dir,
    stage_input_file,
)
from src.report import build_report


def _read_csv(path: Path) -> list[dict[str, object]] | None:
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        return [dict(row) for row in csv.DictReader(file)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        default="seervada",
        choices=("seervada", "pemsbay"),
    )
    add_artifacts_root_arguments(parser)
    args = parser.parse_args()
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    metric_rows = [
        row
        for path in (
            stage_input_file(
                args.dataset, "metrics", "metrics_groupmean.csv",
                root=root, legacy_workstream=4,
            ),
            stage_input_file(
                args.dataset, "metrics", "metrics_linearreg.csv",
                root=root, legacy_workstream=4,
            ),
            stage_input_file(
                args.dataset, "metrics", "metrics_nn.csv",
                root=root, legacy_workstream=5,
            ),
        )
        for row in (_read_csv(path) or ())
    ]

    report = build_report(
        dataset=args.dataset,
        i2_paths=_read_csv(
            stage_input_file(
                args.dataset, "paths", "results_paths.csv",
                root=root, legacy_workstream=1,
            )
        ),
        i2_shortest=_read_csv(
            stage_input_file(
                args.dataset, "paths", "shortest_path_summary.csv",
                root=root, legacy_workstream=1,
            )
        ),
        i3_rcsp=_read_csv(
            stage_input_file(
                args.dataset, "rcsp", "rcsp_verification.csv",
                root=root, legacy_workstream=2,
            )
        ),
        i3_sensitivity=_read_csv(
            stage_input_file(
                args.dataset, "rcsp", "rcsp_sensitivity.csv",
                root=root, legacy_workstream=2,
            )
        ),
        i6_metrics=metric_rows or None,
        i8_routing=_read_csv(
            stage_input_file(
                args.dataset, "routing", "routing_results_all.csv",
                root=root, legacy_workstream=6,
            )
        ),
    )
    output_dir = stage_dir(args.dataset, "report", root)
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{args.dataset}_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"Saved combined report to {report_path}")


if __name__ == "__main__":
    main()
