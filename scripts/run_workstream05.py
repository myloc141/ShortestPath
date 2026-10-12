"""Train, evaluate, and export the WS5 neural-network baseline."""

from __future__ import annotations

import pickle

import pandas as pd

from _runner_utils import REPOSITORY_ROOT, workstream_output, write_json
from src.evaluation.regression import evaluate_by_time_slot
from src.models.nn.neural_network import NeuralNetworkModel
from src.preprocess.seervada import load_supervised_dataset, load_traffic_observations
from src.report.plots import plot_nn_training_history


WS3_OUTPUT = REPOSITORY_ROOT / "workstream03" / "outputs"


def main() -> None:
    train = load_supervised_dataset(
        WS3_OUTPUT / "X_train_preprocessed.csv", WS3_OUTPUT / "y_train.csv"
    )
    test = load_supervised_dataset(
        WS3_OUTPUT / "X_test_preprocessed.csv", WS3_OUTPUT / "y_test.csv"
    )
    if train.feature_names != test.feature_names:
        raise ValueError("Train/test feature columns or order differ")
    observations = load_traffic_observations(WS3_OUTPUT / "test.csv")
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
    predictions = model.predict(test.feature_names, test.features)
    output = workstream_output(5)
    pd.DataFrame({"y_pred": predictions}).to_csv(
        output / "pred_nn.csv", index=False
    )
    metrics = evaluate_by_time_slot(
        observations, predictions, model_name="Neural_Network_MLP"
    )
    pd.DataFrame(metrics).to_csv(output / "metrics_nn.csv", index=False)
    with (output / "nn_model.pkl").open("wb") as file:
        pickle.dump(model, file)

    estimator = model.estimator
    validation_scores = getattr(estimator, "validation_scores_", None)
    plot_nn_training_history(
        estimator.loss_curve_,
        validation_scores,
        output / "loss_curve.png",
    )
    overall = metrics[0]
    write_json(
        output / "workstream05_metrics.json",
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
    print(f"Saved WS5 model, predictions, metrics, and loss plot to {output}")


if __name__ == "__main__":
    main()
