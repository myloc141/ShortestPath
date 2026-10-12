"""Launch the PeMS-BAY preprocessing pipeline from the repository root."""

from pathlib import Path
import runpy


def main() -> None:
    repository_root = Path(__file__).resolve().parents[1]
    preprocessing_script = (
        repository_root
        / "data"
        / "processed_perm_bay"
        / "preprocess_pems_bay.py"
    )
    runpy.run_path(str(preprocessing_script), run_name="__main__")


if __name__ == "__main__":
    main()
