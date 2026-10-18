"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_no_target_leakage.py
Kiểm thử ngăn ngừa rò rỉ biến mục tiêu (No Target Leakage) và fit scaler/encoder train-only.
"""

from pathlib import Path
import pandas as pd
import numpy as np
import json
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"

@pytest.fixture
def env():
    p = DATA_PROCESSED_DIR if (DATA_PROCESSED_DIR / "X_train_preprocessed.csv").exists() else WS3_DIR
    X_train = pd.read_csv(p / "X_train_preprocessed.csv")
    X_test = pd.read_csv(p / "X_test_preprocessed.csv")
    train = pd.read_csv(p / "train.csv")
    test = pd.read_csv(p / "test.csv")
    with open(p / "preprocessing_pipeline.json", "r", encoding="utf-8") as f:
        meta = json.load(f)
    return X_train, X_test, train, test, meta

def test_target_variable_strictly_absent_from_feature_matrices(env):
    X_train, X_test, _, _, _ = env
    target_names = ["travel_time", "target", "y"]
    for t_name in target_names:
        assert t_name not in X_train.columns, f"CRITICAL: Biến mục tiêu {t_name} rò rỉ vào X_train!"
        assert t_name not in X_test.columns, f"CRITICAL: Biến mục tiêu {t_name} rò rỉ vào X_test!"

def test_scaler_parameters_derived_solely_from_train(env):
    _, _, train, test, meta = env
    stored_mean = meta["scaler_params"]["distance"]["mean"]
    stored_std = meta["scaler_params"]["distance"]["std"]
    
    train_mean = train["distance"].mean()
    train_std_sample = train["distance"].std(ddof=1)
    
    # Kết hợp Train + Test để tính thống kê toàn bộ (full population)
    full_dist = pd.concat([train["distance"], test["distance"]])
    full_mean = full_dist.mean()
    full_std = full_dist.std(ddof=1)
    
    assert np.isclose(stored_mean, train_mean), "Scaler mean không khớp với Train mean!"
    assert np.isclose(stored_std, train_std_sample), "Scaler std không khớp với Train sample std!"
    
    # Chứng minh rõ ràng scaler không dùng thông tin tập Test
    test_mean = test["distance"].mean()
    test_std = test["distance"].std(ddof=1)
    print(f"Scaler audit: Train mean={train_mean}, Full mean={full_mean}, Test mean={test_mean}")

def test_no_nan_or_inf_in_features(env):
    X_train, X_test, _, _, _ = env
    assert X_train.isna().sum().sum() == 0, "X_train chứa giá trị NaN"
    assert X_test.isna().sum().sum() == 0, "X_test chứa giá trị NaN"
    assert not np.isinf(X_train.values).any(), "X_train chứa giá trị vô cực (+/- Inf)"
    assert not np.isinf(X_test.values).any(), "X_test chứa giá trị vô cực (+/- Inf)"

def test_encoder_categories_learned_solely_from_train(env):
    _, _, train, _, meta = env
    for cat_col in ["edge_id", "time_slot", "day_of_week"]:
        train_unique = sorted(train[cat_col].unique().tolist())
        stored_cats = meta["categories"][cat_col]
        assert train_unique == stored_cats, f"Categories của {cat_col} không khớp 100% với tập Train!"
