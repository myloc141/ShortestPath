"""Optional Matplotlib plots for WS5 training and WS6 routing summaries."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path

from ..routing.experiment import RoutingSummary


def plot_nn_training_history(
    loss_curve: Sequence[float],
    validation_scores: Sequence[float] | None,
    output_path: str | Path,
) -> None:
    """Save training loss and, when available, one-minus-validation-score."""
    if len(loss_curve) == 0:
        raise ValueError("loss_curve must contain at least one value")
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plot generation requires Matplotlib") from exc

    figure, axis = plt.subplots(figsize=(8, 5))
    axis.plot(loss_curve, label="Training loss")
    if validation_scores is not None and len(validation_scores) > 0:
        axis.plot(
            [1.0 - score for score in validation_scores],
            label="Validation loss (1 - score)",
        )
    axis.set_title("Neural Network training history")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Loss")
    axis.legend()
    axis.grid(True)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_main_slot_actual_time(
    summaries: Sequence[RoutingSummary],
    main_slots: Mapping[str, int],
    methods: Sequence[str],
    slot_names: Mapping[int, str],
    output_path: str | Path,
) -> None:
    """Plot mean actual route time with across-day standard deviations."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plot generation requires Matplotlib") from exc
    summary_map = {
        (item.time_slot, item.method): item for item in summaries
    }
    if not main_slots:
        raise ValueError("main_slots must not be empty")

    figure, axes = plt.subplots(
        1,
        len(main_slots),
        figsize=(6.2 * len(main_slots), 4.8),
        sharey=True,
        squeeze=False,
    )
    for axis, (label, slot) in zip(axes[0], main_slots.items()):
        data = [summary_map[(slot, method)] for method in methods]
        axis.bar(
            range(len(methods)),
            [item.mean_actual_time for item in data],
            yerr=[item.std_actual_time or 0.0 for item in data],
            capsize=3,
            color="#4C78A8",
        )
        axis.set_xticks(range(len(methods)))
        axis.set_xticklabels(
            [method.replace("_", "\n") for method in methods],
            fontsize=8,
        )
        axis.set_title(f"Slot {slot} ({slot_names.get(slot, str(slot))}) - {label}")
        axis.grid(axis="y", alpha=0.3)
    axes[0][0].set_ylabel("Actual travel time (minutes), mean ± SD")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_regret_by_slot(
    summaries: Sequence[RoutingSummary],
    methods: Sequence[str],
    slots: Sequence[int],
    output_path: str | Path,
    *,
    oracle_name: str = "Oracle",
) -> None:
    """Plot mean regret for each non-Oracle method across time slots."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plot generation requires Matplotlib") from exc
    selected_methods = [method for method in methods if method != oracle_name]
    if not selected_methods or not slots:
        raise ValueError("At least one non-Oracle method and one slot are required")
    summary_map = {
        (item.time_slot, item.method): item for item in summaries
    }

    figure, axis = plt.subplots(figsize=(9, 4.8))
    width = 0.8 / len(selected_methods)
    for method_index, method in enumerate(selected_methods):
        values = [summary_map[(slot, method)].mean_regret for slot in slots]
        positions = [
            slot_index + method_index * width
            for slot_index in range(len(slots))
        ]
        axis.bar(positions, values, width, label=method)
    axis.set_xticks(
        [
            slot_index + 0.4 - width / 2
            for slot_index in range(len(slots))
        ]
    )
    axis.set_xticklabels([f"Slot {slot}" for slot in slots])
    axis.set_ylabel("Mean regret (minutes) vs same-day Oracle")
    axis.set_title("Mean route regret by time slot (lower is better)")
    axis.legend(fontsize=8)
    axis.grid(axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(output_path, dpi=150)
    plt.close(figure)


def plot_modal_route_map(
    summaries: Sequence[RoutingSummary],
    methods: Sequence[str],
    slots: Sequence[int],
    output_path: str | Path,
) -> None:
    """Plot modal route IDs by method and time slot."""
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise RuntimeError("Plot generation requires Matplotlib") from exc
    summary_map = {
        (item.time_slot, item.method): item for item in summaries
    }
    routes = sorted(
        {
            summary_map[(slot, method)].modal_route
            for method in methods
            for slot in slots
        }
    )
    route_ids = {route: index for index, route in enumerate(routes)}
    matrix = [
        [route_ids[summary_map[(slot, method)].modal_route] for slot in slots]
        for method in methods
    ]

    figure, axis = plt.subplots(
        figsize=(1.5 * len(slots) + 5, 0.6 * len(methods) + 2)
    )
    color_map = plt.get_cmap("tab20", max(len(routes), 1))
    axis.imshow(
        matrix,
        cmap=color_map,
        vmin=-0.5,
        vmax=len(routes) - 0.5,
        aspect="auto",
    )
    for row_index, method in enumerate(methods):
        for column_index in range(len(slots)):
            axis.text(
                column_index,
                row_index,
                f"R{matrix[row_index][column_index] + 1}",
                ha="center",
                va="center",
                fontsize=9,
            )
    axis.set_xticks(range(len(slots)))
    axis.set_xticklabels([f"Slot {slot}" for slot in slots])
    axis.set_yticks(range(len(methods)))
    axis.set_yticklabels(methods)
    legend = "\n".join(
        f"R{index + 1} = {'-'.join(route)}" for index, route in enumerate(routes)
    )
    axis.text(1.02, 0.5, legend, transform=axis.transAxes, va="center", fontsize=8)
    axis.set_title("Modal route by method and time slot")
    figure.tight_layout()
    figure.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(figure)
