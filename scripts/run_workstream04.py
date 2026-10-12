"""Fit WS4 Group Mean and Linear Regression baselines from WS3 outputs."""

from __future__ import annotations

import pandas as pd

from _runner_utils import REPOSITORY_ROOT, workstream_output, write_json
from src.evaluation.regression import evaluate_by_time_slot
from src.models.baselines.group_mean import GroupMeanModel
from src.models.baselines.linear_regression import (
    DEFAULT_DROP_COLUMNS,
    LinearRegressionModel,
)
from src.preprocess.seervada import (
    feature_rows_as_mappings,
    load_supervised_dataset,
    load_traffic_observations,
)


WS3_OUTPUT = REPOSITORY_ROOT / "workstream03" / "outputs"


def _decode_keys(frame: pd.DataFrame) -> pd.DataFrame:
    decoded: dict[str, list[object]] = {}
    for column, prefix in (
        ("edge_id", "edge_id_"),
        ("time_slot", "time_slot_"),
        ("day_of_week", "day_of_week_"),
    ):
        columns = [name for name in frame.columns if name.startswith(prefix)]
        if not columns:
            raise ValueError(f"Feature matrix is missing {prefix!r} columns")
        values = frame[columns].idxmax(axis=1).str.removeprefix(prefix)
        decoded[column] = values.astype(int).tolist() if column == "time_slot" else values.tolist()
    return pd.DataFrame(decoded)


def main() -> None:
    x_train = load_supervised_dataset(
        WS3_OUTPUT / "X_train_preprocessed.csv", WS3_OUTPUT / "y_train.csv"
    )
    x_test = load_supervised_dataset(
        WS3_OUTPUT / "X_test_preprocessed.csv", WS3_OUTPUT / "y_test.csv"
    )
    if x_train.feature_names != x_test.feature_names:
        raise ValueError("Train/test feature columns or order differ")
    if len(x_test.target) != len(x_test.features):
        raise ValueError("Test feature and target rows are misaligned")

    test_observations = load_traffic_observations(WS3_OUTPUT / "test.csv")
    if len(test_observations) != len(x_test.features):
        raise ValueError("Test observations and feature rows are misaligned")

    output = workstream_output(4)
    train_mappings = feature_rows_as_mappings(x_train)
    test_mappings = feature_rows_as_mappings(x_test)
    group_model = GroupMeanModel.fit(train_mappings, x_train.target)
    group_predictions = group_model.predict(test_mappings)
    group_values = [item.value for item in group_predictions]
    group_keys = _decode_keys(pd.DataFrame(x_test.features, columns=x_test.feature_names))
    group_keyed = group_keys.assign(
        y_true=x_test.target,
        y_pred=group_values,
        fallback_level=[item.fallback_level for item in group_predictions],
    )
    pd.DataFrame({"y_pred": group_values}).to_csv(
        output / "pred_groupmean_raw.csv", index=False
    )
    group_keyed.to_csv(output / "pred_groupmean_withkey.csv", index=False)
    group_metrics = pd.DataFrame(
        evaluate_by_time_slot(
            test_observations, group_values, model_name="GroupMean"
        )
    )
    group_metrics.to_csv(output / "metrics_groupmean.csv", index=False)

    linear_model = LinearRegressionModel.fit(
        x_train.feature_names, x_train.features, x_train.target
    )
    linear_values = linear_model.predict(x_test.feature_names, x_test.features)
    linear_keyed = group_keys.assign(y_true=x_test.target, y_pred=linear_values)
    pd.DataFrame({"y_pred": linear_values}).to_csv(
        output / "pred_linearreg_raw.csv", index=False
    )
    linear_keyed.to_csv(output / "pred_linearreg_withkey.csv", index=False)
    linear_metrics = pd.DataFrame(
        evaluate_by_time_slot(
            test_observations, linear_values, model_name="LinearRegression"
        )
    )
    linear_metrics.to_csv(output / "metrics_linearreg.csv", index=False)

    coefficients = pd.DataFrame(
        {
            "feature": linear_model.feature_names,
            "coef": linear_model.estimator.coef_,
        }
    )
    coefficients["note"] = coefficients["feature"].map(
        lambda name: (
            "reference" if name in DEFAULT_DROP_COLUMNS else "coef_vs_reference"
        )
    )
    coefficients.to_csv(output / "coef_linearreg.csv", index=False)

    metrics_output = []
    for model_name, metrics in (
        ("GroupMean", group_metrics),
        ("LinearRegression", linear_metrics),
    ):
        overall = metrics.loc[metrics["time_slot"] == "all"].iloc[0]
        by_slot = metrics.loc[metrics["time_slot"] != "all"]
        metric_columns = ["MAE", "RMSE", "MSE", "MAPE_percent", "n_obs"]
        item = {
            "workstream": "workstream04",
            "model_name": model_name,
            **{column: overall[column] for column in metric_columns},
            "by_time_slot": {
                str(row["time_slot"]): {
                    column: row[column] for column in metric_columns
                }
                for _, row in by_slot.iterrows()
            },
        }
        metrics_output.append(item)
    write_json(output / "workstream04_metrics.json", metrics_output)
    print(f"Saved WS4 predictions, metrics, and coefficients to {output}")


if __name__ == "__main__":
    main()
