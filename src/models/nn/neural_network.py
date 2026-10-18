"""Scikit-learn MLP regressor matching the WS5 neural-network baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from numpy.typing import ArrayLike


class _Regressor(Protocol):
    loss_curve_: Sequence[float]
    validation_scores_: Sequence[float] | None

    def fit(self, features: ArrayLike, targets: ArrayLike) -> object: ...

    def predict(self, features: ArrayLike) -> ArrayLike: ...


@dataclass
class NeuralNetworkModel:
    feature_names: tuple[str, ...]
    estimator: _Regressor

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        features: ArrayLike,
        targets: ArrayLike,
        *,
        hidden_layer_sizes: tuple[int, ...] = (64, 32),
        max_iter: int = 500,
        validation_fraction: float = 0.1,
        n_iter_no_change: int = 10,
        random_state: int = 42,
    ) -> "NeuralNetworkModel":
        if len(features) != len(targets) or len(targets) == 0:
            raise ValueError("Training features and targets must be non-empty and aligned")
        import numpy as np

        feature_matrix = np.asarray(features, dtype=float)
        target_values = np.asarray(targets, dtype=float)
        if feature_matrix.ndim != 2 or feature_matrix.shape[1] != len(feature_names):
            raise ValueError("Training matrix width does not match feature_names")
        if not np.isfinite(feature_matrix).all() or not np.isfinite(target_values).all():
            raise ValueError("Training features and targets must be finite")
        if not 0 < validation_fraction < 1:
            raise ValueError("validation_fraction must be between 0 and 1")

        try:
            from sklearn.neural_network import MLPRegressor
        except ImportError as exc:
            raise RuntimeError("NeuralNetworkModel requires scikit-learn") from exc

        estimator = MLPRegressor(
            hidden_layer_sizes=hidden_layer_sizes,
            activation="relu",
            solver="adam",
            max_iter=max_iter,
            early_stopping=True,
            validation_fraction=validation_fraction,
            n_iter_no_change=n_iter_no_change,
            random_state=random_state,
        )
        estimator.fit(feature_matrix, target_values)
        return cls(feature_names=tuple(feature_names), estimator=estimator)

    def predict(
        self,
        feature_names: Sequence[str],
        features: ArrayLike,
    ) -> tuple[float, ...]:
        if tuple(feature_names) != self.feature_names:
            raise ValueError("Prediction feature order does not match fitted model")
        import numpy as np

        feature_matrix = np.asarray(features, dtype=float)
        if feature_matrix.ndim != 2 or feature_matrix.shape[1] != len(self.feature_names):
            raise ValueError("Prediction matrix width does not match feature_names")
        if not np.isfinite(feature_matrix).all():
            raise ValueError("Prediction features must be finite")
        return tuple(float(value) for value in self.estimator.predict(feature_matrix))
