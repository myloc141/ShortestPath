"""Launch raw PeMS-BAY preprocessing from H5/PKL/CSV to long-form Parquet.

The export schema is ``time_index``, nullable ``timestamp``, ``sensor_id``,
and nullable ``speed``. Dataset adapter mapping and model preprocessing follow
this source-validation stage; importing the raw pipeline does not run it.
"""

import argparse
import logging
from pathlib import Path
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT_DIR = REPOSITORY_ROOT / "data" / "raw_pems_bay"
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from _runner_utils import (
    add_artifacts_root_arguments,
    resolve_artifacts_root,
    stage_dir,
)
from src.adapters.pemsbay_prepare import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect and preprocess trusted PeMS-BAY source files."
    )
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    add_artifacts_root_arguments(parser)
    parser.add_argument(
        "--log-level",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        default="INFO",
    )
    args = parser.parse_args()
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    output_dir = stage_dir("pemsbay", "processed", root)
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    report = run_pipeline(input_dir=args.input_dir, output_dir=output_dir)
    logging.getLogger("pems_bay_preprocessing").info(
        "Preprocessing complete: %s sensors, %s time steps",
        report["traffic"]["n_sensor_ids"],
        report["traffic"]["n_time_steps_or_rows"],
    )


if __name__ == "__main__":
    main()
