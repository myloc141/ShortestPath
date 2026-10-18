"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_temporal_split.py
Kiểm thử tính toàn vẹn và không rò rỉ dữ liệu theo thời gian (Zero Temporal Data Leakage).
"""

from pathlib import Path
import pandas as pd
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"
DATA_RAW_DIR = WS3_DIR / "data" / "raw"

@pytest.fixture
def datasets():
    train_path = DATA_PROCESSED_DIR / "train.csv" if (DATA_PROCESSED_DIR / "train.csv").exists() else WS3_DIR / "train.csv"
    test_path = DATA_PROCESSED_DIR / "test.csv" if (DATA_PROCESSED_DIR / "test.csv").exists() else WS3_DIR / "test.csv"
    sim_path = DATA_RAW_DIR / "seervada_travel_time_SIMULATED.csv" if (DATA_RAW_DIR / "seervada_travel_time_SIMULATED.csv").exists() else WS3_DIR / "seervada_travel_time_SIMULATED.csv"
    
    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    sim_df = pd.read_csv(sim_path)
    return train_df, test_df, sim_df

def test_strictly_chronological_split(datasets):
    train_df, test_df, _ = datasets
    max_train_day = train_df["day"].max()
    min_test_day = test_df["day"].min()
    assert max_train_day < min_test_day, (
        f"LỖI RÒ RỈ THỜI GIAN: Ngày lớn nhất trong Train ({max_train_day}) >= Ngày nhỏ nhất trong Test ({min_test_day})"
    )

def test_no_temporal_overlap(datasets):
    train_df, test_df, _ = datasets
    train_days = set(train_df["day"].unique())
    test_days = set(test_df["day"].unique())
    overlap = train_days.intersection(test_days)
    assert len(overlap) == 0, f"LỖI OVERLAP: Tồn tại ngày xuất hiện ở cả Train và Test: {overlap}"
    assert train_days == set(range(1, 25)), f"Train days không đúng khoảng 1-24: {train_days}"
    assert test_days == set(range(25, 31)), f"Test days không đúng khoảng 25-30: {test_days}"

def test_split_completeness_and_proportions(datasets):
    train_df, test_df, sim_df = datasets
    assert len(train_df) == 1440, f"Số dòng Train phải là 1.440, thực tế: {len(train_df)}"
    assert len(test_df) == 360, f"Số dòng Test phải là 360, thực tế: {len(test_df)}"
    assert len(train_df) + len(test_df) == len(sim_df) == 1800, "Tổng dòng Train + Test không bằng tập gốc 1.800 dòng"

def test_category_balance_across_splits(datasets):
    train_df, test_df, _ = datasets
    # Kiểm tra 12 cạnh
    train_edges = set(train_df["edge_id"].unique())
    test_edges = set(test_df["edge_id"].unique())
    assert len(train_edges) == 12, f"Train thiếu cạnh: {train_edges}"
    assert train_edges == test_edges, "Tập Test có cạnh không nằm trong tập Train hoặc ngược lại"
    
    # Kiểm tra 5 khung giờ
    train_slots = set(train_df["time_slot"].unique())
    test_slots = set(test_df["time_slot"].unique())
    assert len(train_slots) == 5, f"Train thiếu khung giờ: {train_slots}"
    assert train_slots == test_slots, "Khung giờ không khớp giữa Train và Test"

def test_row_identity_with_simulated_source(datasets):
    train_df, test_df, sim_df = datasets
    reconstructed = pd.concat([train_df, test_df], ignore_index=True)
    assert reconstructed.equals(sim_df), "Ghép Train + Test không khớp chính xác 100% với seervada_travel_time_SIMULATED.csv gốc"
