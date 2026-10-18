"""Unit tests for Module M4.1 Seervada Preprocess Adapter."""

from pathlib import Path
import sys
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
SRC_DIR = WS3_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from seervada import (
    TrafficObservation,
    SupervisedDataset,
    edge_key,
    load_traffic_observations,
    load_supervised_dataset,
    feature_rows_as_mappings,
)


def test_edge_key():
    assert edge_key("A", "B") == "A-B"
    assert edge_key("B", "A") == "A-B"
    assert edge_key("O", "A") == "A-O"
    assert edge_key("A", "O") == "A-O"


def test_load_traffic_observations():
    train_csv = WS3_DIR / "train.csv"
    obs_train = load_traffic_observations(train_csv)
    assert len(obs_train) == 1440
    assert isinstance(obs_train[0], TrafficObservation)
    assert obs_train[0].day == 1
    assert obs_train[0].travel_time > 0
    assert obs_train[0].distance > 0

    test_csv = WS3_DIR / "test.csv"
    obs_test = load_traffic_observations(test_csv)
    assert len(obs_test) == 360


def test_load_supervised_dataset():
    x_train_csv = WS3_DIR / "X_train_preprocessed.csv"
    y_train_csv = WS3_DIR / "y_train.csv"
    ds = load_supervised_dataset(x_train_csv, y_train_csv)
    assert len(ds.features) == 1440
    assert len(ds.target) == 1440
    assert len(ds.feature_names) == 26

    mappings = feature_rows_as_mappings(ds)
    assert len(mappings) == 1440
    assert len(mappings[0]) == 26
