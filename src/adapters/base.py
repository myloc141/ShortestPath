"""Abstract interface implemented by every dataset adapter."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..network.schema import Network
from ..preprocess.observations import TrafficObservation


class DatasetAdapter(ABC):
    """Build canonical network and travel-time observations for a dataset.

    Adapters expose distances in kilometers and travel times in minutes.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Canonical registry name for this dataset."""

    @property
    @abstractmethod
    def distance_unit(self) -> str:
        """Distance unit returned by ``build_network`` and observations."""

    @property
    @abstractmethod
    def time_unit(self) -> str:
        """Travel-time unit returned by ``build_observations``."""

    @abstractmethod
    def build_network(self) -> Network:
        """Build and return a canonical network conforming to I1."""

    @abstractmethod
    def build_observations(
        self,
        *,
        network: Network | None = None,
    ) -> list[TrafficObservation]:
        """Build I4-compatible edge travel-time observations."""


__all__ = ["DatasetAdapter"]
