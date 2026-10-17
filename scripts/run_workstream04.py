"""Fit WS4 Group Mean and Linear Regression baselines from WS3 outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import pandas as pd

from _runner_utils import (
    load_dataset_adapter,
    load_network_artifact,
    parse_workstream_args,
    resolve_artifacts_root,
    stage_dir,
    stage_input_file,
    validate_with_error_report,
    write_frame,
    write_json,
)
from src.common.validators import validate_i5
from src.evaluation.regression import evaluate_by_time_slot
from src.models.baselines.group_mean import GroupMeanModel
from src.models.baselines.linear_regression import (
    DEFAULT_DROP_COLUMNS,
    LinearRegressionModel,
)
from src.preprocess.observations import (
    TrafficObservation,
    feature_rows_as_mappings,
    load_supervised_dataset,
    load_observations,
)


def _keyed_predictions(
    observations: Sequence[TrafficObservation],
    predictions: Sequence[float],
    *,
    output_dir: Path,
    dataset: str,
) -> pd.DataFrame:
    if len(observations) != len(predictions):
        raise ValueError("Prediction count does not match observation keys")
    frame = pd.DataFrame(
        {
            "edge_id": [item.edge_id for item in observations],
            "day": [item.day for item in observations],
            "time_slot": [item.time_slot for item in observations],
            "y_pred": predictions,
        }
    )
    validate_with_error_report(
        validate_i5,
        frame,
        output_dir=output_dir,
        dataset=dataset,
        stage="workstream04",
    )
    return frame


def main() -> None:
    args = parse_workstream_args(4, __doc__ or "Run Workstream 04")
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    adapter, _ = load_dataset_adapter(args.dataset, root=root)
    network = load_network_artifact(args.dataset, adapter, root=root)
    ws3_files = {
        name: stage_input_file(
            args.dataset, "processed", name, root=root, legacy_workstream=3
        )
        for name in (
            "X_train_preprocessed.csv",
            "y_train.csv",
            "X_valid_preprocessed.csv",
            "y_valid.csv",
            "X_test_preprocessed.csv",
            "y_test.csv",
            "valid.csv",
            "test.csv",
        )
    }
    x_train = load_supervised_dataset(
        ws3_files["X_train_preprocessed.csv"], ws3_files["y_train.csv"]
    )
    x_valid = load_supervised_dataset(
        ws3_files["X_valid_preprocessed.csv"], ws3_files["y_valid.csv"]
    )
    x_test = load_supervised_dataset(
        ws3_files["X_test_preprocessed.csv"], ws3_files["y_test.csv"]
    )
    if x_train.feature_names != x_valid.feature_names or (
        x_train.feature_names != x_test.feature_names
    ):
        raise ValueError("Train/validation/test feature columns or order differ")
    if (
        len(x_valid.target) != len(x_valid.features)
        or len(x_test.target) != len(x_test.features)
    ):
        raise ValueError("Validation/test feature and target rows are misaligned")

    valid_observations = load_observations(
        ws3_files["valid.csv"], network=network
    )
    test_observations = load_observations(
        ws3_files["test.csv"], network=network
    )
    if len(valid_observations) != len(x_valid.features):
        raise ValueError("Validation observations and feature rows are misaligned")
    if len(test_observations) != len(x_test.features):
        raise ValueError("Test observations and feature rows are misaligned")

    predictions_output = stage_dir(args.dataset, "predictions", root)
    metrics_dir = stage_dir(args.dataset, "metrics", root)
    errors_output = stage_dir(args.dataset, "_errors", root)
    predictions_output.mkdir(parents=True, exist_ok=True)
    metrics_dir.mkdir(parents=True, exist_ok=True)
    train_mappings = feature_rows_as_mappings(x_train)
    test_mappings = feature_rows_as_mappings(x_test)
    group_model = GroupMeanModel.fit(train_mappings, x_train.target)
    group_valid_predictions = tuple(
        item.value
        for item in group_model.predict(feature_rows_as_mappings(x_valid))
    )
    group_predictions = group_model.predict(test_mappings)
    group_values = [item.value for item in group_predictions]
    write_frame(
        predictions_output / "pred_groupmean_valid_withkey.csv",
        _keyed_predictions(
            valid_observations,
            group_valid_predictions,
            output_dir=errors_output,
            dataset=args.dataset,
        ),
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    group_keyed = _keyed_predictions(
        test_observations,
        tuple(group_values),
        output_dir=errors_output,
        dataset=args.dataset,
    )
    pd.DataFrame({"y_pred": group_values}).to_csv(
        predictions_output / "pred_groupmean_raw.csv", index=False
    )
    write_frame(
        predictions_output / "pred_groupmean_withkey.csv",
        group_keyed,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    group_metrics = pd.DataFrame(
        evaluate_by_time_slot(
            test_observations, group_values, model_name="GroupMean"
        )
    )
    write_frame(
        metrics_dir / "metrics_groupmean.csv",
        group_metrics,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I6",
    )

    linear_model = LinearRegressionModel.fit(
        x_train.feature_names, x_train.features, x_train.target
    )
    linear_valid_values = linear_model.predict(
        x_valid.feature_names, x_valid.features
    )
    linear_values = linear_model.predict(x_test.feature_names, x_test.features)
    write_frame(
        predictions_output / "pred_linearreg_valid_withkey.csv",
        _keyed_predictions(
            valid_observations,
            linear_valid_values,
            output_dir=errors_output,
            dataset=args.dataset,
        ),
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    linear_keyed = _keyed_predictions(
        test_observations,
        linear_values,
        output_dir=errors_output,
        dataset=args.dataset,
    )
    pd.DataFrame({"y_pred": linear_values}).to_csv(
        predictions_output / "pred_linearreg_raw.csv", index=False
    )
    write_frame(
        predictions_output / "pred_linearreg_withkey.csv",
        linear_keyed,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    linear_metrics = pd.DataFrame(
        evaluate_by_time_slot(
            test_observations, linear_values, model_name="LinearRegression"
        )
    )
    write_frame(
        metrics_dir / "metrics_linearreg.csv",
        linear_metrics,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I6",
    )

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
    write_frame(
        metrics_dir / "coef_linearreg.csv",
        coefficients,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I6",
    )

    metrics_summary = []
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
        metrics_summary.append(item)
    write_json(metrics_dir / "workstream04_metrics.json", metrics_summary)
    print(
        f"Saved WS4 predictions to {predictions_output} and metrics to "
        f"{metrics_dir}"
    )


if __name__ == "__main__":
    main()
