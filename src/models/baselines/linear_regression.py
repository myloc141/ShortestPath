"""Linear Regression baseline matching the WS4 drop-first feature treatment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


DEFAULT_DROP_COLUMNS = (
    "edge_id_A-B",
    "time_slot_1",
    "day_of_week_Fri",
    "is_weekend",
)


class _Regressor(Protocol):
    coef_: Sequence[float]
    intercept_: float

    def fit(self, features: Sequence[Sequence[float]], targets: Sequence[float]) -> object: ...

    def predict(self, features: Sequence[Sequence[float]]) -> Sequence[float]: ...


@dataclass
class LinearRegressionModel:
    feature_names: tuple[str, ...]
    estimator: _Regressor

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        features: Sequence[Sequence[float]],
        targets: Sequence[float],
        *,
        drop_columns: Sequence[str] = DEFAULT_DROP_COLUMNS,
    ) -> "LinearRegressionModel":
        if len(features) != len(targets) or not targets:
            raise ValueError("Training features and targets must be non-empty and aligned")
        names = tuple(name for name in feature_names if name not in set(drop_columns))
        selected_indices = tuple(
            index for index, name in enumerate(feature_names) if name in names
        )
        if not names:
            raise ValueError("No feature columns remain after drop-first selection")
        if any(len(row) != len(feature_names) for row in features):
            raise ValueError("Training row width does not match feature_names")

        try:
            from sklearn.linear_model import LinearRegression
        except ImportError as exc:
            raise RuntimeError("LinearRegressionModel requires scikit-learn") from exc

        estimator = LinearRegression()
        selected_features = [
            [float(row[index]) for index in selected_indices] for row in features
        ]
        estimator.fit(selected_features, [float(value) for value in targets])
        return cls(feature_names=names, estimator=estimator)

    def predict(
        self,
        feature_names: Sequence[str],
        features: Sequence[Sequence[float]],
    ) -> tuple[float, ...]:
        if any(len(row) != len(feature_names) for row in features):
            raise ValueError("Prediction row width does not match feature_names")
        if tuple(feature_names) == self.feature_names:
            selected_features = [[float(value) for value in row] for row in features]
        else:
            indices = {name: index for index, name in enumerate(feature_names)}
            missing = set(self.feature_names) - indices.keys()
            if missing:
                raise ValueError(f"Prediction data missing features: {sorted(missing)}")
            selected_features = [
                [float(row[indices[name]]) for name in self.feature_names]
                for row in features
            ]
        predictions = self.estimator.predict(selected_features)
        return tuple(float(value) for value in predictions)
