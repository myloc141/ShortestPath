"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_pipeline_reproducibility.py
Kiểm thử tính tái lập 100% (Reproducibility) và tính bất biến (Determinism) của Feature Pipeline.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
SRC_DIR = WS3_DIR / "src"
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"

sys.path.insert(0, str(SRC_DIR))
from feature_pipeline import SeervadaFeaturePipeline

@pytest.fixture
def raw_splits():
    p = DATA_PROCESSED_DIR if (DATA_PROCESSED_DIR / "train.csv").exists() else WS3_DIR
    train_df = pd.read_csv(p / "train.csv")
    test_df = pd.read_csv(p / "test.csv")
    return train_df, test_df

def test_pipeline_fails_if_not_fitted(raw_splits):
    train_df, _ = raw_splits
    pipeline = SeervadaFeaturePipeline()
    with pytest.raises(AssertionError, match="Pipeline chưa được fit"):
        pipeline.transform(train_df)

def test_deterministic_feature_regeneration(raw_splits):
    train_df, test_df = raw_splits
    
    # Chạy lần 1
    p1 = SeervadaFeaturePipeline(ddof=1)
    p1.fit(train_df)
    X1_tr, y1_tr = p1.transform(train_df)
    X1_te, y1_te = p1.transform(test_df)
    
    # Chạy lần 2
    p2 = SeervadaFeaturePipeline(ddof=1)
    p2.fit(train_df)
    X2_tr, y2_tr = p2.transform(train_df)
    X2_te, y2_te = p2.transform(test_df)
    
    np.testing.assert_array_equal(X1_tr.values, X2_tr.values, err_msg="Tái lập Train ma trận không xác định (non-deterministic)!")
    np.testing.assert_array_equal(X1_te.values, X2_te.values, err_msg="Tái lập Test ma trận không xác định (non-deterministic)!")
    np.testing.assert_array_equal(y1_tr.values, y2_tr.values)
    np.testing.assert_array_equal(y1_te.values, y2_te.values)

def test_reproduced_matrix_matches_saved_csv(raw_splits):
    train_df, test_df = raw_splits
    p = DATA_PROCESSED_DIR if (DATA_PROCESSED_DIR / "X_train_preprocessed.csv").exists() else WS3_DIR
    saved_X_train = pd.read_csv(p / "X_train_preprocessed.csv")
    saved_X_test = pd.read_csv(p / "X_test_preprocessed.csv")
    
    pipeline = SeervadaFeaturePipeline(ddof=1)
    pipeline.fit(train_df)
    fresh_X_train, _ = pipeline.transform(train_df)
    fresh_X_test, _ = pipeline.transform(test_df)
    
    np.testing.assert_allclose(
        fresh_X_train.values,
        saved_X_train.values,
        rtol=1e-5,
        atol=1e-5,
        err_msg="Ma trận sinh mới không khớp với file X_train_preprocessed.csv đã lưu!"
    )
    np.testing.assert_allclose(
        fresh_X_test.values,
        saved_X_test.values,
        rtol=1e-5,
        atol=1e-5,
        err_msg="Ma trận sinh mới không khớp với file X_test_preprocessed.csv đã lưu!"
    )
