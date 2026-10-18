"""Group Mean baseline with the four-level WS4 backoff strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from numpy.typing import ArrayLike


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

    @classmethod
    def fit_encoded(
        cls,
        feature_names: Sequence[str],
        features: ArrayLike,
        targets: ArrayLike,
    ) -> "GroupMeanModel":
        """Fit from a dense feature matrix without materializing row mappings."""
        import numpy as np

        matrix = np.asarray(features, dtype=float)
        target_values = np.asarray(targets, dtype=float)
        if matrix.ndim != 2 or matrix.shape[0] != len(target_values):
            raise ValueError("Training matrix and targets must be aligned")
        if not len(target_values):
            raise ValueError("Training rows and targets must be non-empty")
        if matrix.shape[1] != len(feature_names):
            raise ValueError("Feature matrix width does not match feature_names")
        if not np.isfinite(matrix).all() or not np.isfinite(target_values).all():
            raise ValueError("Training features and targets must be finite")

        columns: dict[str, tuple[tuple[str, ...], Any]] = {}
        for prefix in ("edge_id_", "time_slot_", "day_of_week_"):
            indices = tuple(
                index
                for index, name in enumerate(feature_names)
                if name.startswith(prefix)
            )
            if not indices:
                raise ValueError(f"No encoded feature columns for {prefix!r}")
            active = matrix[:, indices] >= 0.5
            active_counts = active.sum(axis=1)
            if (active_counts != 1).any():
                raise ValueError(
                    f"Expected one active one-hot feature for {prefix!r}"
                )
            labels = tuple(feature_names[index][len(prefix) :] for index in indices)
            columns[prefix] = (
                labels,
                np.argmax(active, axis=1),
            )

        sums: tuple[dict[tuple[str, ...], list[float]], ...] = ({}, {}, {})
        total = float(target_values.sum())
        edge_labels, edge_indexes = columns["edge_id_"]
        slot_labels, slot_indexes = columns["time_slot_"]
        day_labels, day_indexes = columns["day_of_week_"]
        for row_index, raw_target in enumerate(target_values):
            edge = edge_labels[int(edge_indexes[row_index])]
            slot = slot_labels[int(slot_indexes[row_index])]
            day = day_labels[int(day_indexes[row_index])]
            keys = ((edge, slot, day), (edge, slot), (edge,))
            target = float(raw_target)
            for groups, group_key in zip(sums, keys):
                aggregate = groups.setdefault(group_key, [0.0, 0.0])
                aggregate[0] += target
                aggregate[1] += 1

        means = tuple(
            {key: aggregate[0] / aggregate[1] for key, aggregate in groups.items()}
            for groups in sums
        )
        return cls(
            level1=means[0],
            level2=means[1],
            level3=means[2],
            global_mean=total / len(target_values),
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

    def predict_encoded(
        self,
        feature_names: Sequence[str],
        features: ArrayLike,
    ) -> tuple[GroupMeanPrediction, ...]:
        """Predict from a dense feature matrix without row dictionaries."""
        import numpy as np

        matrix = np.asarray(features, dtype=float)
        if matrix.ndim != 2 or matrix.shape[1] != len(feature_names):
            raise ValueError("Prediction matrix width does not match feature_names")
        if not np.isfinite(matrix).all():
            raise ValueError("Prediction features must be finite")

        category_values: dict[
            str, tuple[tuple[str, ...], Any | None, Any | None]
        ] = {}
        for prefix in ("edge_id_", "time_slot_", "day_of_week_"):
            indices = tuple(
                index
                for index, name in enumerate(feature_names)
                if name.startswith(prefix)
            )
            labels = tuple(feature_names[index][len(prefix) :] for index in indices)
            if not indices:
                category_values[prefix] = (labels, None, None)
                continue
            active = matrix[:, indices] >= 0.5
            counts = active.sum(axis=1)
            if (counts > 1).any():
                raise ValueError(
                    f"Expected at most one active one-hot feature for {prefix!r}"
                )
            category_values[prefix] = (
                labels,
                np.argmax(active, axis=1),
                counts,
            )

        predictions: list[GroupMeanPrediction] = []
        for row_index in range(matrix.shape[0]):
            row_categories: list[str | None] = []
            for prefix in ("edge_id_", "time_slot_", "day_of_week_"):
                labels, indexes, counts = category_values[prefix]
                if indexes is None or counts[row_index] == 0:
                    row_categories.append(None)
                else:
                    row_categories.append(labels[int(indexes[row_index])])
            edge, slot, day = row_categories
            keys = (
                (edge, slot, day)
                if edge is not None and slot is not None and day is not None
                else None,
                (edge, slot)
                if edge is not None and slot is not None
                else None,
                (edge,) if edge is not None else None,
            )
            prediction: GroupMeanPrediction | None = None
            for level, groups, key in zip(
                ("level1", "level2", "level3"),
                (self.level1, self.level2, self.level3),
                keys,
            ):
                if key is not None and key in groups:
                    prediction = GroupMeanPrediction(groups[key], level)
                    break
            predictions.append(
                prediction
                or GroupMeanPrediction(self.global_mean, "level4")
            )
        return tuple(predictions)
