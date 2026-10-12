"""Presentation helpers for evaluation and routing results."""

from .markdown import markdown_table, render_routing_summary
from .plots import (
    plot_main_slot_actual_time,
    plot_modal_route_map,
    plot_nn_training_history,
    plot_regret_by_slot,
)

__all__ = [
    "markdown_table",
    "plot_main_slot_actual_time",
    "plot_modal_route_map",
    "plot_nn_training_history",
    "plot_regret_by_slot",
    "render_routing_summary",
]
