"""Run the WS6 routing experiment and export tables, report, and plots."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

import pandas as pd

from _runner_utils import REPOSITORY_ROOT, workstream_output, write_csv
from src.evaluation.regression import compare_routing_pairs
from src.network.seervada import load_seervada_network
from src.preprocess.seervada import load_traffic_observations
from src.report.markdown import render_routing_summary
from src.report.plots import (
    plot_main_slot_actual_time,
    plot_modal_route_map,
    plot_regret_by_slot,
)
from src.shortest_path.simple_paths import enumerate_simple_paths
from src.routing.experiment import (
    run_routing_experiment,
    summarize_routing_results,
)


WS3_OUTPUT = REPOSITORY_ROOT / "workstream03" / "outputs"
WS4_OUTPUT = REPOSITORY_ROOT / "workstream04" / "outputs"
WS5_OUTPUT = REPOSITORY_ROOT / "workstream05" / "outputs"


def _load_predictions(path: Path, expected_rows: int) -> tuple[float, ...]:
    frame = pd.read_csv(path)
    if list(frame.columns) != ["y_pred"]:
        raise ValueError(f"{path}: expected exactly one y_pred column")
    if len(frame) != expected_rows:
        raise ValueError(
            f"{path}: prediction rows={len(frame)}, expected={expected_rows}"
        )
    predictions = tuple(float(value) for value in frame["y_pred"])
    return predictions


def main() -> None:
    network = load_seervada_network()
    train = load_traffic_observations(WS3_OUTPUT / "train.csv", network=network)
    test = load_traffic_observations(WS3_OUTPUT / "test.csv", network=network)
    predictions = {
        "GroupMean": _load_predictions(
            WS4_OUTPUT / "pred_groupmean_raw.csv", len(test)
        ),
        "LinearRegression": _load_predictions(
            WS4_OUTPUT / "pred_linearreg_raw.csv", len(test)
        ),
        "NeuralNet": _load_predictions(WS5_OUTPUT / "pred_nn.csv", len(test)),
    }
    results = run_routing_experiment(
        network,
        train,
        test,
        predictions,
        source="O",
        target="T",
    )
    summaries = summarize_routing_results(results)
    methods = tuple(dict.fromkeys(item.method for item in results))
    pairs = tuple(
        (methods[first], methods[second])
        for first in range(len(methods))
        for second in range(first + 1, len(methods))
    )
    comparisons = compare_routing_pairs(results, pairs)
    output = workstream_output(6)

    result_rows = []
    for result in results:
        row = asdict(result)
        row["route"] = "-".join(result.route)
        row["oracle_route"] = "-".join(result.oracle_route)
        result_rows.append(row)
    write_csv(output / "routing_results_all.csv", result_rows)

    summary_rows = []
    for summary in summaries:
        row = asdict(summary)
        row["modal_route"] = "-".join(summary.modal_route)
        summary_rows.append(row)
    write_csv(output / "summary_by_slot_method.csv", summary_rows)
    write_csv(output / "route_by_slot.csv", summary_rows)
    write_csv(
        output / "model_comparison.csv",
        [asdict(item) for item in comparisons],
    )

    train_slot_means: dict[int, float] = {}
    for slot in sorted({item.time_slot for item in train}):
        values = [
            item.travel_time for item in train if item.time_slot == slot
        ]
        train_slot_means[slot] = sum(values) / len(values)
    peak_slot = max(train_slot_means, key=train_slot_means.__getitem__)
    offpeak_slot = min(train_slot_means, key=train_slot_means.__getitem__)
    slot_names = {
        item.time_slot: item.slot_name for item in (*train, *test)
    }
    selected_methods = [
        "Fixed_distance",
        "Fixed_trainmean",
        "Pred_GroupMean",
        "Pred_LinearRegression",
        "Pred_NeuralNet",
        "Oracle",
    ]
    main_summary_rows = [
        {
            "slot": label,
            "time_slot": slot,
            "method": item.method,
            "mean_actual_time": item.mean_actual_time,
            "mean_regret": item.mean_regret,
            "days_equal_oracle": item.days_equal_oracle,
            "n_days": item.n_days,
        }
        for label, slot in (("peak", peak_slot), ("offpeak", offpeak_slot))
        for item in summaries
        if item.time_slot == slot and item.method in selected_methods
    ]
    pair_rows = [asdict(item) for item in comparisons]
    (output / "results_summary.md").write_text(
        render_routing_summary(
            source="O",
            target="T",
            path_count=len(enumerate_simple_paths(network, "O", "T")),
            test_day_count=len({item.day for item in test}),
            primary_baseline="GroupMean",
            neural_network_included=True,
            peak_slot=peak_slot,
            offpeak_slot=offpeak_slot,
            alignment_messages=[
                f"{name}: {len(values)} predictions aligned with {len(test)} test observations"
                for name, values in predictions.items()
            ],
            main_slot_rows=main_summary_rows,
            pair_comparison_rows=pair_rows,
        ),
        encoding="utf-8",
    )
    (output / "precommitted_rules.md").write_text(
        "# Routing comparison rules\n\n"
        "- `GroupMean` is the primary baseline, as selected before this run.\n"
        "- Include Linear Regression and Neural Network predictions for comparison.\n"
        "- Select routes using training-derived weights or model predictions only.\n"
        "- Use test actual travel times only to score routes; `Oracle` is an explicitly "
        "labeled lower-bound reference.\n",
        encoding="utf-8",
    )

    plot_main_slot_actual_time(
        summaries,
        {"peak": peak_slot, "offpeak": offpeak_slot},
        selected_methods,
        slot_names,
        output / "fig_actual_time_main_slots.png",
    )
    plot_regret_by_slot(
        summaries,
        selected_methods,
        sorted(train_slot_means),
        output / "fig_regret_all_slots.png",
    )
    plot_modal_route_map(
        summaries,
        selected_methods,
        sorted(train_slot_means),
        output / "fig_route_map.png",
    )
    print(f"Saved WS6 routing outputs and plots to {output}")


if __name__ == "__main__":
    main()
