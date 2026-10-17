"""Markdown table and summary rendering without filesystem side effects."""

from __future__ import annotations

import math
from typing import Mapping, Sequence


def markdown_table(
    rows: Sequence[Mapping[str, object]],
    *,
    columns: Sequence[str] | None = None,
    digits: int = 3,
) -> str:
    """Render mappings as a Markdown table, escaping embedded pipe characters."""
    if not rows and columns is None:
        return ""
    headers = tuple(columns or rows[0].keys())
    if not headers:
        return ""

    def format_value(value: object) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            if math.isnan(value):
                return ""
            return f"{value:.{digits}f}"
        return str(value).replace("|", "\\|").replace("\n", "<br>")

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| " + " | ".join(format_value(row.get(name)) for name in headers) + " |"
        )
    return "\n".join(lines)


def render_i2_report(
    simple_paths: Sequence[Mapping[str, object]] | None,
    shortest_path_rows: Sequence[Mapping[str, object]] | None,
) -> str:
    """Render I2 simple-path results and the shortest-path summary."""
    return "\n".join(
        [
            "## I2 — Simple paths và shortest path",
            "",
            "### Simple paths",
            markdown_table(simple_paths) if simple_paths else "chưa có kết quả",
            "",
            "### Shortest-path summary",
            (
                markdown_table(shortest_path_rows)
                if shortest_path_rows
                else "chưa có kết quả"
            ),
        ]
    )


def render_i3_report(
    rcsp_rows: Sequence[Mapping[str, object]] | None,
    sensitivity_rows: Sequence[Mapping[str, object]] | None,
) -> str:
    """Render I3 RCSP verification and resource-limit sensitivity tables."""
    return "\n".join(
        [
            "## I3 — RCSP và sensitivity",
            "",
            "### RCSP results",
            markdown_table(rcsp_rows) if rcsp_rows else "chưa có kết quả",
            "",
            "### Sensitivity by resource limit",
            (
                markdown_table(sensitivity_rows)
                if sensitivity_rows
                else "chưa có kết quả"
            ),
        ]
    )


def render_i6_report(
    metric_rows: Sequence[Mapping[str, object]] | None,
) -> str:
    """Render I6 evaluation metrics."""
    return "\n".join(
        [
            "## I6 — Evaluation metrics",
            "",
            markdown_table(metric_rows) if metric_rows else "chưa có kết quả",
        ]
    )


def render_i8_report(
    routing_rows: Sequence[Mapping[str, object]] | None,
) -> str:
    """Render I8 routing results by slot and weight source."""
    return "\n".join(
        [
            "## I8 — Routing results",
            "",
            markdown_table(routing_rows) if routing_rows else "chưa có kết quả",
        ]
    )


def build_report(
    *,
    dataset: str,
    i2_paths: Sequence[Mapping[str, object]] | None = None,
    i2_shortest: Sequence[Mapping[str, object]] | None = None,
    i3_rcsp: Sequence[Mapping[str, object]] | None = None,
    i3_sensitivity: Sequence[Mapping[str, object]] | None = None,
    i6_metrics: Sequence[Mapping[str, object]] | None = None,
    i8_routing: Sequence[Mapping[str, object]] | None = None,
) -> str:
    """Build the M9 Markdown report from available I2/I3/I6/I8 results."""
    return "\n".join(
        [
            f"# Pipeline report — {dataset}",
            "",
            render_i2_report(i2_paths, i2_shortest),
            "",
            render_i3_report(i3_rcsp, i3_sensitivity),
            "",
            render_i6_report(i6_metrics),
            "",
            render_i8_report(i8_routing),
            "",
        ]
    )


def render_routing_summary(
    *,
    source: str,
    target: str,
    path_count: int,
    test_day_count: int,
    primary_baseline: str,
    neural_network_included: bool,
    peak_slot: int,
    offpeak_slot: int,
    alignment_messages: Sequence[str],
    main_slot_rows: Sequence[Mapping[str, object]],
    pair_comparison_rows: Sequence[Mapping[str, object]],
    rcsp_rows: Sequence[Mapping[str, object]] | None = None,
    rcsp_route_rows: Sequence[Mapping[str, object]] | None = None,
    sensitivity_rows: Sequence[Mapping[str, object]] | None = None,
) -> str:
    """Render the WS6 report, including optional RCSP and sensitivity tables."""
    nn_status = "in the main comparison" if neural_network_included else "reference only"
    sections = [
        "# Routing experiment summary",
        (
            f"- Simple routes from `{source}` to `{target}`: **{path_count}**; "
            f"test days: **{test_day_count}**."
        ),
        f"- Primary baseline: **{primary_baseline}**; Neural Network: {nn_status}.",
        f"- Peak slot: **{peak_slot}**; off-peak slot: **{offpeak_slot}**.",
        "- Simulated travel times are not real-world traffic measurements.",
        "",
        "## Prediction alignment",
        *[f"- {message}" for message in alignment_messages],
        "",
        "## Main-slot results",
        markdown_table(main_slot_rows),
        "",
        "## Pairwise method comparison",
        markdown_table(pair_comparison_rows),
    ]
    if rcsp_rows:
        sections.extend(
            [
                "",
                "## RCSP vs unconstrained shortest path",
                markdown_table(rcsp_rows),
            ]
        )
    if rcsp_route_rows:
        sections.extend(
            [
                "",
                "## RCSP route scores on actual test travel time",
                markdown_table(rcsp_route_rows),
            ]
        )
    if sensitivity_rows:
        sections.extend(
            [
                "",
                "## RCSP sensitivity by resource limit",
                markdown_table(sensitivity_rows),
            ]
        )
    sections.append("")
    return "\n".join(sections)
