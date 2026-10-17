"""Train, evaluate, and export the WS5 neural-network baseline."""

from __future__ import annotations

import pickle

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
from src.models.nn.neural_network import NeuralNetworkModel
from src.preprocess.observations import (
    load_observations,
    load_supervised_dataset,
)
from src.report.plots import plot_nn_training_history


def main() -> None:
    args = parse_workstream_args(5, __doc__ or "Run Workstream 05")
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
    train = load_supervised_dataset(
        ws3_files["X_train_preprocessed.csv"], ws3_files["y_train.csv"]
    )
    valid = load_supervised_dataset(
        ws3_files["X_valid_preprocessed.csv"], ws3_files["y_valid.csv"]
    )
    test = load_supervised_dataset(
        ws3_files["X_test_preprocessed.csv"], ws3_files["y_test.csv"]
    )
    if (
        train.feature_names != valid.feature_names
        or train.feature_names != test.feature_names
    ):
        raise ValueError("Train/validation/test feature columns or order differ")
    if (
        len(valid.target) != len(valid.features)
        or len(test.target) != len(test.features)
    ):
        raise ValueError("Validation/test features and targets are misaligned")
    valid_observations = load_observations(
        ws3_files["valid.csv"], network=network
    )
    observations = load_observations(
        ws3_files["test.csv"], network=network
    )
    if len(valid_observations) != len(valid.features):
        raise ValueError("Validation observations and features are misaligned")
    if len(observations) != len(test.features):
        raise ValueError("Test observations and features are misaligned")

    model = NeuralNetworkModel.fit(
        train.feature_names,
        train.features,
        train.target,
        hidden_layer_sizes=(64, 32),
        max_iter=500,
        validation_fraction=0.1,
        n_iter_no_change=10,
        random_state=42,
    )
    valid_predictions = model.predict(valid.feature_names, valid.features)
    predictions = model.predict(test.feature_names, test.features)
    predictions_output = stage_dir(args.dataset, "predictions", root)
    metrics_output = stage_dir(args.dataset, "metrics", root)
    errors_output = stage_dir(args.dataset, "_errors", root)
    predictions_output.mkdir(parents=True, exist_ok=True)
    metrics_output.mkdir(parents=True, exist_ok=True)
    valid_keyed = pd.DataFrame(
        {
            "edge_id": [item.edge_id for item in valid_observations],
            "day": [item.day for item in valid_observations],
            "time_slot": [item.time_slot for item in valid_observations],
            "y_pred": valid_predictions,
        }
    )
    validate_with_error_report(
        validate_i5,
        valid_keyed,
        output_dir=errors_output,
        dataset=args.dataset,
        stage="workstream05",
    )
    write_frame(
        predictions_output / "pred_nn_valid_withkey.csv",
        valid_keyed,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    pd.DataFrame({"y_pred": predictions}).to_csv(
        predictions_output / "pred_nn.csv", index=False
    )
    test_keyed = pd.DataFrame(
        {
            "edge_id": [item.edge_id for item in observations],
            "day": [item.day for item in observations],
            "time_slot": [item.time_slot for item in observations],
            "y_pred": predictions,
        }
    )
    validate_with_error_report(
        validate_i5,
        test_keyed,
        output_dir=errors_output,
        dataset=args.dataset,
        stage="workstream05",
    )
    write_frame(
        predictions_output / "pred_nn_withkey.csv",
        test_keyed,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I5",
    )
    metrics = evaluate_by_time_slot(
        observations, predictions, model_name="Neural_Network_MLP"
    )
    write_frame(
        metrics_output / "metrics_nn.csv",
        pd.DataFrame(metrics),
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I6",
    )
    with (predictions_output / "nn_model.pkl").open("wb") as file:
        pickle.dump(model, file)

    estimator = model.estimator
    validation_scores = getattr(estimator, "validation_scores_", None)
    plot_nn_training_history(
        estimator.loss_curve_,
        validation_scores,
        predictions_output / "loss_curve.png",
    )
    overall = metrics[0]
    write_json(
        metrics_output / "workstream05_metrics.json",
        {
            "workstream": "workstream05",
            "model_name": "Neural_Network_MLP",
            **{
                key: overall[key]
                for key in ("MAE", "RMSE", "MSE", "MAPE_percent", "n_obs")
            },
            "by_time_slot": {
                str(row["time_slot"]): {
                    key: row[key]
                    for key in ("MAE", "RMSE", "MSE", "MAPE_percent", "n_obs")
                }
                for row in metrics[1:]
            },
        },
    )
    print(
        f"Saved WS5 predictions to {predictions_output} and metrics to "
        f"{metrics_output}"
    )


if __name__ == "__main__":
    main()
