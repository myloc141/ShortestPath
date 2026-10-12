"""Scikit-learn MLP regressor matching the WS5 neural-network baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence


class _Regressor(Protocol):
    loss_curve_: Sequence[float]
    validation_scores_: Sequence[float] | None

    def fit(self, features: Sequence[Sequence[float]], targets: Sequence[float]) -> object: ...

    def predict(self, features: Sequence[Sequence[float]]) -> Sequence[float]: ...


@dataclass
class NeuralNetworkModel:
    feature_names: tuple[str, ...]
    estimator: _Regressor

    @classmethod
    def fit(
        cls,
        feature_names: Sequence[str],
        features: Sequence[Sequence[float]],
        targets: Sequence[float],
        *,
        hidden_layer_sizes: tuple[int, ...] = (64, 32),
        max_iter: int = 500,
        validation_fraction: float = 0.1,
        n_iter_no_change: int = 10,
        random_state: int = 42,
    ) -> "NeuralNetworkModel":
        if len(features) != len(targets) or not targets:
            raise ValueError("Training features and targets must be non-empty and aligned")
        if any(len(row) != len(feature_names) for row in features):
            raise ValueError("Training row width does not match feature_names")
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
        estimator.fit(
            [[float(value) for value in row] for row in features],
            [float(value) for value in targets],
        )
        return cls(feature_names=tuple(feature_names), estimator=estimator)

    def predict(
        self,
        feature_names: Sequence[str],
        features: Sequence[Sequence[float]],
    ) -> tuple[float, ...]:
        if tuple(feature_names) != self.feature_names:
            raise ValueError("Prediction feature order does not match fitted model")
        if any(len(row) != len(self.feature_names) for row in features):
            raise ValueError("Prediction row width does not match feature_names")
        return tuple(
            float(value)
            for value in self.estimator.predict(
                [[float(item) for item in row] for row in features]
            )
        )
