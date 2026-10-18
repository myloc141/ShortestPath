"""Dataset-neutral preprocessing schemas, readers, and Seervada adapter (Module M4.1)."""

from .dataset import (
    ObservationLike,
    ObservationSplits,
    SpeedObservationLike,
    TemporalDataset,
    aggregate_hourly,
    clean_speed_series,
    observations_to_speed_frame,
    prepare_observation_splits,
    prepare_temporal_splits,
    render_data_dictionary,
    save_temporal_dataset,
)
from .observations import (
    SupervisedDataset,
    TrafficObservation,
    edge_key,
    feature_rows_as_mappings,
    load_observations,
    load_supervised_dataset,
)
from .seervada import (
    load_traffic_observations,
)

__all__ = [
    "ObservationLike",
    "ObservationSplits",
    "SpeedObservationLike",
    "SupervisedDataset",
    "TemporalDataset",
    "TrafficObservation",
    "aggregate_hourly",
    "clean_speed_series",
    "observations_to_speed_frame",
    "edge_key",
    "feature_rows_as_mappings",
    "load_observations",
    "load_supervised_dataset",
    "load_traffic_observations",
    "prepare_temporal_splits",
    "prepare_observation_splits",
    "render_data_dictionary",
    "save_temporal_dataset",
]
