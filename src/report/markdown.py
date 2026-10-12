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
) -> str:
    """Render the core explanatory sections used by the WS6 report."""
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
        "",
    ]
    return "\n".join(sections)
