"""Presentation helpers for evaluation and routing results."""

from .markdown import (
    build_report,
    markdown_table,
    render_i2_report,
    render_i3_report,
    render_i6_report,
    render_i8_report,
    render_routing_summary,
)
from .plots import (
    plot_main_slot_actual_time,
    plot_modal_route_map,
    plot_nn_training_history,
    plot_regret_by_slot,
)

__all__ = [
    "build_report",
    "markdown_table",
    "plot_main_slot_actual_time",
    "plot_modal_route_map",
    "plot_nn_training_history",
    "plot_regret_by_slot",
    "render_i2_report",
    "render_i3_report",
    "render_i6_report",
    "render_i8_report",
    "render_routing_summary",
]
