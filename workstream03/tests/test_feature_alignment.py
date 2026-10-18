"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_feature_alignment.py
Kiểm thử tính căn chỉnh dòng ma trận (Row Alignment) giữa X và y, tính hợp lệ của one-hot encoding.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"

@pytest.fixture
def matrices():
    p = DATA_PROCESSED_DIR if (DATA_PROCESSED_DIR / "X_train_preprocessed.csv").exists() else WS3_DIR
    X_train = pd.read_csv(p / "X_train_preprocessed.csv")
    X_test = pd.read_csv(p / "X_test_preprocessed.csv")
    y_train = pd.read_csv(p / "y_train.csv")
    y_test = pd.read_csv(p / "y_test.csv")
    train = pd.read_csv(p / "train.csv")
    test = pd.read_csv(p / "test.csv")
    return X_train, y_train, X_test, y_test, train, test

def test_row_count_alignment(matrices):
    X_train, y_train, X_test, y_test, _, _ = matrices
    assert len(X_train) == len(y_train) == 1440, "X_train và y_train không khớp số dòng (1.440)"
    assert len(X_test) == len(y_test) == 360, "X_test và y_test không khớp số dòng (360)"

def test_label_value_alignment_with_raw_data(matrices):
    _, y_train, _, y_test, train, test = matrices
    # Kiểm tra từng phần tử theo đúng thứ tự chỉ mục
    np.testing.assert_allclose(
        y_train["travel_time"].values,
        train["travel_time"].values,
        err_msg="y_train không khớp giá trị travel_time gốc trong train.csv"
    )
    np.testing.assert_allclose(
        y_test["travel_time"].values,
        test["travel_time"].values,
        err_msg="y_test không khớp giá trị travel_time gốc trong test.csv"
    )

def test_feature_column_consistency(matrices):
    X_train, _, X_test, _, _, _ = matrices
    assert list(X_train.columns) == list(X_test.columns), "Thứ tự và tên cột không khớp giữa X_train và X_test"
    assert X_train.shape[1] == 26, f"Số lượng features phải là 26, thực tế: {X_train.shape[1]}"

def test_one_hot_encoding_properties(matrices):
    X_train, _, X_test, _, _, _ = matrices
    for prefix, expected_count in [("edge_id_", 12), ("time_slot_", 5), ("day_of_week_", 7)]:
        cols = [c for c in X_train.columns if c.startswith(prefix)]
        assert len(cols) == expected_count, f"Số lượng cột one-hot cho {prefix} phải là {expected_count}"
        
        # Tổng hàng trong one-hot encoding luôn phải đúng bằng 1.0
        train_sums = X_train[cols].sum(axis=1)
        test_sums = X_test[cols].sum(axis=1)
        assert np.allclose(train_sums, 1.0), f"Phát hiện hàng trong Train có tổng one-hot {prefix} khác 1"
        assert np.allclose(test_sums, 1.0), f"Phát hiện hàng trong Test có tổng one-hot {prefix} khác 1"

def test_binary_feature_range(matrices):
    X_train, _, X_test, _, _, _ = matrices
    assert set(X_train["is_weekend"].unique()).issubset({0.0, 1.0}), "Cột is_weekend trong Train chứa giá trị ngoài {0, 1}"
    assert set(X_test["is_weekend"].unique()).issubset({0.0, 1.0}), "Cột is_weekend trong Test chứa giá trị ngoài {0, 1}"
