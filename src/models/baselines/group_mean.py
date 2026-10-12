"""Group Mean baseline with the four-level WS4 backoff strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class GroupMeanPrediction:
    value: float
    fallback_level: str


def _category(
    row: Mapping[str, float],
    prefix: str,
    *,
    required: bool,
) -> str | None:
    active = [
        name[len(prefix) :]
        for name, value in row.items()
        if name.startswith(prefix) and float(value) >= 0.5
    ]
    if len(active) > 1:
        raise ValueError(f"Expected one active category for {prefix!r}")
    if not active:
        if required:
            raise ValueError(f"No active one-hot feature for {prefix!r}")
        return None
    return active[0]


def _key(
    row: Mapping[str, float],
    prefixes: tuple[str, ...],
    *,
    required: bool,
) -> tuple[str, ...] | None:
    values = tuple(
        _category(row, prefix, required=required) for prefix in prefixes
    )
    if any(value is None for value in values):
        return None
    return tuple(value for value in values if value is not None)


@dataclass
class GroupMeanModel:
    """Fitted grouped means, falling back from edge-slot-day to global mean."""

    level1: dict[tuple[str, ...], float]
    level2: dict[tuple[str, ...], float]
    level3: dict[tuple[str, ...], float]
    global_mean: float

    @classmethod
    def fit(
        cls,
        rows: Sequence[Mapping[str, float]],
        targets: Sequence[float],
    ) -> "GroupMeanModel":
        if len(rows) != len(targets) or not targets:
            raise ValueError("Training rows and targets must be non-empty and aligned")
        sums: tuple[dict[tuple[str, ...], list[float]], ...] = (
            {},
            {},
            {},
        )
        total = 0.0
        for row, raw_target in zip(rows, targets):
            target = float(raw_target)
            if target != target or target in (float("inf"), float("-inf")):
                raise ValueError("Training targets must be finite")
            keys = (
                _key(
                    row,
                    ("edge_id_", "time_slot_", "day_of_week_"),
                    required=True,
                ),
                _key(row, ("edge_id_", "time_slot_"), required=True),
                _key(row, ("edge_id_",), required=True),
            )
            total += target
            for groups, group_key in zip(sums, keys):
                assert group_key is not None
                values = groups.setdefault(group_key, [0.0, 0.0])
                values[0] += target
                values[1] += 1

        means = tuple(
            {key: aggregate[0] / aggregate[1] for key, aggregate in groups.items()}
            for groups in sums
        )
        return cls(
            level1=means[0],
            level2=means[1],
            level3=means[2],
            global_mean=total / len(targets),
        )

    def predict_one(self, row: Mapping[str, float]) -> GroupMeanPrediction:
        keys = (
            _key(
                row,
                ("edge_id_", "time_slot_", "day_of_week_"),
                required=False,
            ),
            _key(row, ("edge_id_", "time_slot_"), required=False),
            _key(row, ("edge_id_",), required=False),
        )
        for level, groups, key in zip(
            ("level1", "level2", "level3"),
            (self.level1, self.level2, self.level3),
            keys,
        ):
            if key is not None and key in groups:
                return GroupMeanPrediction(groups[key], level)
        return GroupMeanPrediction(self.global_mean, "level4")

    def predict(
        self,
        rows: Sequence[Mapping[str, float]],
    ) -> tuple[GroupMeanPrediction, ...]:
        return tuple(self.predict_one(row) for row in rows)
