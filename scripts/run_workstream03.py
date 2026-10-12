"""Split simulated Seervada observations and export train-fitted features."""

from __future__ import annotations

import json

import pandas as pd

from _runner_utils import REPOSITORY_ROOT, workstream_output


SOURCE = (
    REPOSITORY_ROOT
    / "data"
    / "processed_seervada"
    / "seervada_travel_time_SIMULATED.csv"
)


def main() -> None:
    frame = pd.read_csv(SOURCE)
    required = {
        "day",
        "day_of_week",
        "is_weekend",
        "time_slot",
        "time_slot_name",
        "edge_id",
        "node_u",
        "node_v",
        "distance",
        "travel_time",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{SOURCE}: missing columns: {sorted(missing)}")
    if frame.empty or frame[list(required)].isna().any().any():
        raise ValueError(f"{SOURCE}: empty dataset or missing required values")

    output = workstream_output(3)
    train = frame.loc[frame["day"] <= 24].reset_index(drop=True)
    test = frame.loc[frame["day"] > 24].reset_index(drop=True)
    if train.empty or test.empty:
        raise ValueError("Time split produced an empty train or test set")
    if set(train["edge_id"]) != set(test["edge_id"]):
        raise ValueError("Train/test splits do not contain the same edge IDs")
    if set(train["time_slot"]) != set(test["time_slot"]):
        raise ValueError("Train/test splits do not contain the same time slots")

    train.to_csv(output / "train.csv", index=False)
    test.to_csv(output / "test.csv", index=False)

    categorical = ("edge_id", "time_slot", "day_of_week")
    categories = {
        column: sorted(train[column].unique().tolist())
        for column in categorical
    }
    distance_mean = float(train["distance"].mean())
    distance_std = float(train["distance"].std())
    if distance_std <= 0:
        distance_std = 1.0

    feature_names = ["distance", "is_weekend"]
    for column in categorical:
        feature_names.extend(f"{column}_{value}" for value in categories[column])

    def encode(split: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
        features: dict[str, pd.Series] = {
            "distance": (split["distance"] - distance_mean) / distance_std,
            "is_weekend": split["is_weekend"].astype(float),
        }
        for column in categorical:
            for category in categories[column]:
                features[f"{column}_{category}"] = (
                    split[column] == category
                ).astype(float)
        return pd.DataFrame(features, columns=feature_names), split["travel_time"]

    x_train, y_train = encode(train)
    x_test, y_test = encode(test)
    x_train.to_csv(output / "X_train_preprocessed.csv", index=False)
    y_train.to_frame(name="travel_time").to_csv(output / "y_train.csv", index=False)
    x_test.to_csv(output / "X_test_preprocessed.csv", index=False)
    y_test.to_frame(name="travel_time").to_csv(output / "y_test.csv", index=False)

    metadata = {
        "source": str(SOURCE),
        "train_days": 24,
        "feature_names": feature_names,
        "categories": categories,
        "distance_scaler": {"mean": distance_mean, "std": distance_std},
        "train_rows": len(train),
        "test_rows": len(test),
        "target": "travel_time",
    }
    (output / "preprocessing_pipeline.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Prepared {len(train)} training and {len(test)} test rows in {output}")


if __name__ == "__main__":
    main()
