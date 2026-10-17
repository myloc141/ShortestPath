"""Run the WS6 routing experiment and export tables, report, and plots."""

from __future__ import annotations

from dataclasses import asdict
import math
from pathlib import Path

import pandas as pd

from _runner_utils import (
    load_dataset_adapter,
    load_network_artifact,
    parse_workstream_args,
    resolve_artifacts_root,
    routing_endpoints,
    stage_dir,
    stage_input_file,
    validate_with_error_report,
    write_csv,
    write_json,
)
from src.common.metrics import evaluate_all
from src.common.validators import validate_i5, validate_i8
from src.evaluation.regression import (
    PredictionRow,
    check_prediction_alignment,
    select_routing_models,
)
from src.preprocess.observations import TrafficObservation, load_observations
from src.report.markdown import render_routing_summary
from src.report.plots import (
    plot_main_slot_actual_time,
    plot_modal_route_map,
    plot_regret_by_slot,
)
from src.routing.comparison import compare_routing_pairs
from src.routing.experiment import (
    RouteReference,
    parse_route_path,
    run_routing_experiment,
    summarize_routing_results,
)
from src.shortest_path.dijkstra import dijkstra
from src.shortest_path.simple_paths import enumerate_simple_paths


def _observation_key(item: TrafficObservation) -> tuple[str, int, int]:
    return item.edge_id, item.day, item.time_slot


def _load_keyed_predictions(
    path: Path,
    observations: tuple[TrafficObservation, ...],
    *,
    raw_path: Path | None = None,
    output_dir: Path,
    dataset: str,
) -> tuple[float, ...]:
    frame = pd.read_csv(path)
    required = {"edge_id", "day", "time_slot", "y_pred"}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{path}: missing keyed prediction columns "
            f"{sorted(missing_columns)}"
        )
    if frame.empty:
        raise ValueError(f"{path}: prediction file is empty")

    frame = frame.loc[:, ["edge_id", "day", "time_slot", "y_pred"]].copy()
    frame["edge_id"] = frame["edge_id"].astype(str).str.strip()
    for column in ("day", "time_slot", "y_pred"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
        if frame[column].isna().any():
            raise ValueError(f"{path}: {column} contains non-numeric values")
    for column in ("day", "time_slot"):
        if (frame[column] % 1 != 0).any():
            raise ValueError(f"{path}: {column} must contain integers")
        frame[column] = frame[column].astype(int)
    frame["y_pred"] = frame["y_pred"].astype(float)
    validate_with_error_report(
        validate_i5,
        frame,
        output_dir=output_dir,
        dataset=dataset,
        stage="workstream06",
    )

    expected_keys = [_observation_key(item) for item in observations]
    prediction_by_key = {
        (row.edge_id, int(row.day), int(row.time_slot)): float(row.y_pred)
        for row in frame.itertuples(index=False)
    }
    expected_key_set = set(expected_keys)
    prediction_key_set = set(prediction_by_key)
    missing_keys = expected_key_set - prediction_key_set
    unexpected_keys = prediction_key_set - expected_key_set
    if missing_keys or unexpected_keys:
        raise ValueError(
            f"{path}: prediction keys do not match observations "
            f"(missing={sorted(missing_keys)[:10]}, "
            f"unexpected={sorted(unexpected_keys)[:10]})"
        )

    aligned = tuple(prediction_by_key[key] for key in expected_keys)
    keyed_rows = tuple(
        PredictionRow(
            prediction=prediction,
            edge_id=item.edge_id,
            day=item.day,
            time_slot=item.time_slot,
        )
        for item, prediction in zip(observations, aligned)
    )
    raw_predictions = aligned
    if raw_path is not None:
        raw_frame = pd.read_csv(raw_path)
        if list(raw_frame.columns) != ["y_pred"]:
            raise ValueError(f"{raw_path}: expected exactly one y_pred column")
        if len(raw_frame) != len(observations):
            raise ValueError(
                f"{raw_path}: prediction rows={len(raw_frame)}, "
                f"expected={len(observations)}"
            )
        raw_predictions = tuple(
            float(value) for value in raw_frame["y_pred"]
        )

    alignment = check_prediction_alignment(
        observations,
        raw_predictions,
        keyed_rows,
    )
    if not alignment.aligned:
        raise ValueError(
            f"{path}: prediction alignment failed: "
            + "; ".join(alignment.messages)
        )
    return aligned


def main() -> None:
    args = parse_workstream_args(6, __doc__ or "Run Workstream 06")
    root = resolve_artifacts_root(args.artifacts_root, args.output_dir)
    adapter, config = load_dataset_adapter(args.dataset, root=root)
    output = stage_dir(args.dataset, "routing", root)
    errors_output = stage_dir(args.dataset, "_errors", root)
    output.mkdir(parents=True, exist_ok=True)
    adapter.build_network()
    network = load_network_artifact(args.dataset, adapter, root=root)
    source, target = routing_endpoints(
        adapter, source=config.source, target=config.target
    )

    def input_file(stage: str, filename: str, workstream: int) -> Path:
        return stage_input_file(
            args.dataset,
            stage,
            filename,
            root=root,
            legacy_workstream=workstream,
        )

    train = load_observations(
        input_file("processed", "train.csv", 3), network=network
    )
    valid = load_observations(
        input_file("processed", "valid.csv", 3), network=network
    )
    test = load_observations(
        input_file("processed", "test.csv", 3), network=network
    )
    validation_prediction_paths = {
        "GroupMean": input_file(
            "predictions", "pred_groupmean_valid_withkey.csv", 4
        ),
        "LinearRegression": input_file(
            "predictions", "pred_linearreg_valid_withkey.csv", 4
        ),
        "NeuralNet": input_file(
            "predictions", "pred_nn_valid_withkey.csv", 5
        ),
    }
    test_prediction_paths = {
        "GroupMean": (
            input_file("predictions", "pred_groupmean_withkey.csv", 4),
            input_file("predictions", "pred_groupmean_raw.csv", 4),
        ),
        "LinearRegression": (
            input_file("predictions", "pred_linearreg_withkey.csv", 4),
            input_file("predictions", "pred_linearreg_raw.csv", 4),
        ),
        "NeuralNet": (
            input_file("predictions", "pred_nn_withkey.csv", 5),
            input_file("predictions", "pred_nn.csv", 5),
        ),
    }
    validation_predictions = {
        name: _load_keyed_predictions(
            path,
            valid,
            output_dir=errors_output,
            dataset=args.dataset,
        )
        for name, path in validation_prediction_paths.items()
    }
    validation_metrics = {
        name: evaluate_all(
            [item.travel_time for item in valid],
            values,
        )
        for name, values in validation_predictions.items()
    }
    train_slot_means: dict[int, float] = {}
    for slot in sorted({item.time_slot for item in train}):
        values = [item.travel_time for item in train if item.time_slot == slot]
        train_slot_means[slot] = sum(values) / len(values)
    selection = select_routing_models(
        validation_metrics,
        train_slot_means,
    )
    primary_baseline = str(selection["primary_baseline"])
    selected_prediction_names = [primary_baseline]
    neural_network_included = bool(selection["nn_included_in_main_comparison"])
    if neural_network_included:
        selected_prediction_names.append("NeuralNet")

    selection_record = {
        **selection,
        "decision_source": "validation metrics only",
        "validation_days": sorted({item.day for item in valid}),
        "test_metrics_used": False,
        "routing_results_used": False,
        "selected_prediction_models": selected_prediction_names,
    }
    write_json(output / "routing_model_selection.json", selection_record)

    predictions = {
        name: _load_keyed_predictions(
            keyed_path,
            test,
            raw_path=raw_path,
            output_dir=errors_output,
            dataset=args.dataset,
        )
        for name, (keyed_path, raw_path) in test_prediction_paths.items()
        if name in selected_prediction_names
    }
    sensitivity_path = input_file("rcsp", "rcsp_sensitivity.csv", 2)
    sensitivity_rows: list[dict[str, object]] | None = None
    rcsp_routes: tuple[RouteReference, ...] = ()
    rcsp_rows: list[dict[str, object]] | None = None
    if sensitivity_path.exists():
        sensitivity_frame = pd.read_csv(sensitivity_path)
        sensitivity_rows = sensitivity_frame.to_dict("records")
        required_rcsp_columns = {
            "resource_limit",
            "status",
            "optimal_path",
        }
        missing_rcsp_columns = required_rcsp_columns - set(sensitivity_frame.columns)
        if missing_rcsp_columns:
            raise ValueError(
                f"{sensitivity_path}: missing RCSP sensitivity columns "
                f"{sorted(missing_rcsp_columns)}"
            )
        parsed_routes: list[RouteReference] = []
        unlimited_route: tuple[str, ...] | None = None
        for row_number, row in enumerate(sensitivity_rows, start=2):
            if str(row["status"]).strip() != "Optimal":
                continue
            raw_limit = row["resource_limit"]
            if pd.isna(raw_limit):
                limit_label = "unbounded"
            else:
                try:
                    numeric_limit = float(raw_limit)
                except (TypeError, ValueError) as error:
                    raise ValueError(
                        f"{sensitivity_path}:{row_number}: invalid resource_limit "
                        f"{raw_limit!r}"
                    ) from error
                if not math.isfinite(numeric_limit) or numeric_limit < 0:
                    raise ValueError(
                        f"{sensitivity_path}:{row_number}: resource_limit must "
                        "be finite and non-negative"
                    )
                limit_label = (
                    str(int(numeric_limit))
                    if numeric_limit.is_integer()
                    else str(numeric_limit)
                )
            route_name = f"RCSP_limit_{limit_label}"
            try:
                route = parse_route_path(str(row["optimal_path"]))
            except ValueError as error:
                raise ValueError(
                    f"{sensitivity_path}:{row_number}: invalid route for "
                    f"{route_name}: {error}"
                ) from error
            parsed_routes.append(RouteReference(name=route_name, path=route))
            if pd.isna(raw_limit):
                unlimited_route = route
        rcsp_routes = tuple(parsed_routes)
        if unlimited_route is not None:
            shortest = dijkstra(network, source, target)
            rcsp_rows = [
                {
                    "method": "RCSP_limit_unbounded",
                    "route": "-".join(unlimited_route),
                    "distance_km": next(
                        row["total_distance"]
                        for row in sensitivity_rows
                        if pd.isna(row["resource_limit"])
                        and str(row["status"]).strip() == "Optimal"
                    ),
                    "resource_limit": None,
                },
                {
                    "method": "Unconstrained shortest path",
                    "route": "-".join(shortest.path),
                    "distance_km": shortest.distance,
                    "resource_limit": None,
                },
            ]
    else:
        print(
            "Warning: RCSP sensitivity file not found at "
            f"{sensitivity_path}; continuing without RCSP route and tables."
        )

    results = run_routing_experiment(
        network,
        train,
        test,
        predictions,
        source=source,
        target=target,
        route_references=rcsp_routes,
        max_paths=config.max_paths,
    )
    summaries = summarize_routing_results(results)
    methods = tuple(dict.fromkeys(item.method for item in results))
    pairs = tuple(
        (methods[first], methods[second])
        for first in range(len(methods))
        for second in range(first + 1, len(methods))
    )
    comparisons = compare_routing_pairs(results, pairs)

    result_rows = []
    for result in results:
        row = asdict(result)
        row["route"] = "-".join(result.route)
        row["oracle_route"] = "-".join(result.oracle_route)
        result_rows.append(row)
    validate_with_error_report(
        validate_i8,
        result_rows,
        output_dir=errors_output,
        dataset=args.dataset,
        stage="workstream06",
    )
    write_csv(
        output / "routing_results_all.csv",
        result_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I8",
    )

    summary_rows = []
    for summary in summaries:
        row = asdict(summary)
        row["modal_route"] = "-".join(summary.modal_route)
        summary_rows.append(row)
    write_csv(
        output / "summary_by_slot_method.csv",
        summary_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I8",
    )
    write_csv(
        output / "route_by_slot.csv",
        summary_rows,
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I8",
    )
    write_csv(
        output / "model_comparison.csv",
        [asdict(item) for item in comparisons],
        with_meta=args.with_meta,
        dataset=args.dataset,
        interface_id="I8",
    )

    peak_slot = max(train_slot_means, key=train_slot_means.__getitem__)
    offpeak_slot = min(train_slot_means, key=train_slot_means.__getitem__)
    slot_names = {
        item.time_slot: item.slot_name for item in (*train, *test)
    }
    selected_methods = [
        "Fixed_distance",
        "Fixed_trainmean",
        *(f"Pred_{name}" for name in selected_prediction_names),
        "Oracle",
    ]
    selected_methods.extend(reference.name for reference in rcsp_routes)
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
    rcsp_route_rows = [
        {
            "method": item.method,
            "time_slot": item.time_slot,
            "day": item.day,
            "route": "-".join(item.route),
            "actual_time": item.actual_time,
            "oracle_time": item.oracle_time,
            "regret": item.regret,
            "method_family": item.method_family,
        }
        for item in results
        if item.method_family == "rcsp"
    ]
    (output / "results_summary.md").write_text(
        render_routing_summary(
            source=source,
            target=target,
            path_count=len(
                enumerate_simple_paths(
                    network, source, target, max_paths=config.max_paths
                )
            ),
            test_day_count=len({item.day for item in test}),
            primary_baseline=primary_baseline,
            neural_network_included=neural_network_included,
            peak_slot=peak_slot,
            offpeak_slot=offpeak_slot,
            alignment_messages=[
                f"{name}: {len(values)} predictions aligned with {len(test)} test observations"
                for name, values in predictions.items()
            ],
            main_slot_rows=main_summary_rows,
            pair_comparison_rows=pair_rows,
            rcsp_rows=rcsp_rows,
            rcsp_route_rows=rcsp_route_rows or None,
            sensitivity_rows=sensitivity_rows,
        ),
        encoding="utf-8",
    )
    (output / "precommitted_rules.md").write_text(
        "# Routing comparison rules\n\n"
        f"- `{primary_baseline}` is the primary baseline selected from validation metrics.\n"
        f"- Neural Network included: {neural_network_included}.\n"
        "- The decision is stored in `routing_model_selection.json` before routing.\n"
        "- Select routes using training-derived weights or model predictions only.\n"
        "- Use test actual travel times only to score routes; predicted times are "
        "never used as routing evaluation truth. `Oracle` is an explicitly "
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
