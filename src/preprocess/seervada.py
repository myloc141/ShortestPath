"""Module M4.1: Preprocess Adapter for Seervada Traffic Data.

Provides the canonical schemas and loader functions for Seervada observations
and supervised datasets without relying on external workstream directories.
"""

from .observations import (
    TrafficObservation,
    SupervisedDataset,
    edge_key,
    load_observations,
    load_supervised_dataset,
    feature_rows_as_mappings,
)

load_traffic_observations = load_observations

__all__ = [
    "TrafficObservation",
    "SupervisedDataset",
    "edge_key",
    "load_traffic_observations",
    "load_observations",
    "load_supervised_dataset",
    "feature_rows_as_mappings",
]
