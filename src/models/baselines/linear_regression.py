"""Linear Regression baseline matching the WS4 drop-first feature treatment."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from numpy.typing import ArrayLike


DEFAULT_DROP_COLUMNS = (
    "edge_id_A-B",
    "time_slot_1",
    "day_of_week_Fri",
    "is_weekend",
)


class _Regressor(Protocol):
    coef_: Sequence[float]
    intercept_: float

    def fit(self, features: ArrayLike, targets: ArrayLike) -> object: ...

    def predict(self, features: ArrayLike) -> ArrayLike: ...


@dataclass
class LinearRegressionModel:
    feature_names: tuple[str, ...]
    estimator: _Regressor

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        features: ArrayLike,
        targets: ArrayLike,
        *,
        drop_columns: Sequence[str] = DEFAULT_DROP_COLUMNS,
    ) -> "LinearRegressionModel":
        if len(features) != len(targets) or len(targets) == 0:
            raise ValueError("Training features and targets must be non-empty and aligned")
        import numpy as np

        feature_matrix = np.asarray(features, dtype=float)
        target_values = np.asarray(targets, dtype=float)
        if feature_matrix.ndim != 2 or feature_matrix.shape[1] != len(feature_names):
            raise ValueError("Training matrix width does not match feature_names")
        if not np.isfinite(feature_matrix).all() or not np.isfinite(target_values).all():
            raise ValueError("Training features and targets must be finite")
        names = tuple(name for name in feature_names if name not in set(drop_columns))
        selected_indices = tuple(
            index for index, name in enumerate(feature_names) if name in names
        )
        if not names:
            raise ValueError("No feature columns remain after drop-first selection")

        try:
            from sklearn.linear_model import LinearRegression
        except ImportError as exc:
            raise RuntimeError("LinearRegressionModel requires scikit-learn") from exc

        estimator = LinearRegression()
        estimator.fit(feature_matrix[:, selected_indices], target_values)
        return cls(feature_names=names, estimator=estimator)

    def predict(
        self,
        feature_names: Sequence[str],
        features: ArrayLike,
    ) -> tuple[float, ...]:
        import numpy as np

        feature_matrix = np.asarray(features, dtype=float)
        if feature_matrix.ndim != 2 or feature_matrix.shape[1] != len(feature_names):
            raise ValueError("Prediction matrix width does not match feature_names")
        if not np.isfinite(feature_matrix).all():
            raise ValueError("Prediction features must be finite")
        if tuple(feature_names) == self.feature_names:
            selected_features = feature_matrix
        else:
            indices = {name: index for index, name in enumerate(feature_names)}
            missing = set(self.feature_names) - indices.keys()
            if missing:
                raise ValueError(f"Prediction data missing features: {sorted(missing)}")
            selected_features = feature_matrix[
                :, [indices[name] for name in self.feature_names]
            ]
        predictions = self.estimator.predict(selected_features)
        return tuple(float(value) for value in predictions)
