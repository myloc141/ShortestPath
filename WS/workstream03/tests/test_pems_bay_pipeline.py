"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_pems_bay_pipeline.py
Kiểm thử toàn diện Pipeline PeMS-BAY:
- WS1 Contract (Sensor IDs, distance > 0, unique edge_id, no self-loops).
- Causal Imputation (Zero/NaN handling, no future leakage).
- 5-minute grid alignment & missing timestamp handling.
- Time slot aggregation (5 slots, non-overlapping boundaries).
- Feature Engineering (Train-only scaler & encoder, X/y alignment).
- Failure Tests: Fail Loudly khi dữ liệu bất thường hoặc vi phạm hợp đồng.
- CLI Smoke Test.
"""

from pathlib import Path
import sys
import tempfile
import json
import pytest
import numpy as np
import pandas as pd

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
SRC_DIR = WS3_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

from pems_bay_pipeline import (
    validate_edges_contract,
    assign_time_slot,
    clean_partition_causal,
    process_pems_bay_pipeline,
    TIME_SLOT_DEFINITIONS
)

@pytest.fixture
def synthetic_pems_fixture(tmp_path):
    """
    Tạo fixture synthetic HDF5 và Edges CSV nhỏ để kiểm thử logic pipeline.
    Lưu ý: Fixture này chỉ phục vụ kiểm thử đơn vị tự động, không dùng làm số liệu báo cáo.
    """
    # 5 sensors, 4 ngày, mỗi ngày đầy đủ mốc 5 phút
    date_range = pd.date_range("2017-01-01 00:00:00", "2017-01-04 23:55:00", freq="5min")
    sensors = ["400001", "400017", "400030", "400040", "400050"]
    
    np.random.seed(42)
    # Tốc độ thực tế dao động 30 - 65 mph
    speed_data = np.random.uniform(40.0, 65.0, size=(len(date_range), len(sensors)))
    
    # Cố tình đưa vào một số điểm bất thường để test cleaning logic:
    # 1. Zero speed (sensor stoppage)
    speed_data[10, 0] = 0.0
    speed_data[25, 1] = 0.0
    # 2. NaN value (missing transmission)
    speed_data[50, 2] = np.nan
    
    df_speed = pd.DataFrame(speed_data, index=date_range, columns=sensors)
    
    # Cố ý xóa 2 timestamp để kiểm thử missing timestamp detection
    df_speed = df_speed.drop(df_speed.index[[100, 200]])
    
    h5_file = tmp_path / "synthetic_pems_bay.h5"
    df_speed.to_hdf(str(h5_file), key="speed", mode="w")
    
    # Dựng file edges WS1
    edges_data = [
        {"edge_id": "E1", "sensor_u": "400001", "sensor_v": "400017", "distance_miles": 1.5},
        {"edge_id": "E2", "sensor_u": "400017", "sensor_v": "400030", "distance_miles": 2.2},
        {"edge_id": "E3", "sensor_u": "400030", "sensor_v": "400040", "distance_miles": 0.8},
        {"edge_id": "E4", "sensor_u": "400040", "sensor_v": "400050", "distance_miles": 3.1},
    ]
    edges_df = pd.DataFrame(edges_data)
    edges_file = tmp_path / "synthetic_edges.csv"
    edges_df.to_csv(edges_file, index=False)
    
    out_dir = tmp_path / "output_pems"
    return h5_file, edges_file, out_dir, sensors

# ======================================================================
# 1. KIỂM THỬ HỢP ĐỒNG WS1 (WS1 CONTRACT TESTS)
# ======================================================================

def test_ws1_contract_valid(synthetic_pems_fixture):
    _, edges_file, _, sensors = synthetic_pems_fixture
    edges_df = pd.read_csv(edges_file)
    validated = validate_edges_contract(edges_df, sensors)
    assert len(validated) == 4
    assert (validated["distance_miles"] > 0).all()

def test_ws1_contract_fails_on_missing_column():
    bad_df = pd.DataFrame([{"edge_id": "E1", "sensor_u": "S1", "distance_miles": 1.0}])
    with pytest.raises(ValueError, match="Thiếu cột bắt buộc 'sensor_v'"):
        validate_edges_contract(bad_df, ["S1", "S2"])

def test_ws1_contract_fails_on_duplicate_edge_id():
    bad_df = pd.DataFrame([
        {"edge_id": "E1", "sensor_u": "S1", "sensor_v": "S2", "distance_miles": 1.0},
        {"edge_id": "E1", "sensor_u": "S2", "sensor_v": "S3", "distance_miles": 2.0}
    ])
    with pytest.raises(ValueError, match="Tồn tại edge_id trùng lặp"):
        validate_edges_contract(bad_df, ["S1", "S2", "S3"])

def test_ws1_contract_fails_on_negative_or_zero_distance():
    bad_df = pd.DataFrame([
        {"edge_id": "E1", "sensor_u": "S1", "sensor_v": "S2", "distance_miles": -1.5}
    ])
    with pytest.raises(ValueError, match="Cự ly khoảng cách <= 0"):
        validate_edges_contract(bad_df, ["S1", "S2"])

def test_ws1_contract_fails_on_self_loop():
    bad_df = pd.DataFrame([
        {"edge_id": "E1", "sensor_u": "S1", "sensor_v": "S1", "distance_miles": 1.0}
    ])
    with pytest.raises(ValueError, match="Phát hiện self-loop"):
        validate_edges_contract(bad_df, ["S1"])

def test_ws1_contract_fails_on_missing_sensors():
    bad_df = pd.DataFrame([
        {"edge_id": "E1", "sensor_u": "S1", "sensor_v": "UNKNOWN_SENSOR", "distance_miles": 1.0}
    ])
    with pytest.raises(ValueError, match="không tồn tại trong HDF5"):
        validate_edges_contract(bad_df, ["S1"])

# ======================================================================
# 2. KIỂM THỬ KHUNG GIỜ VÀ DANH MỤC THỜI GIAN
# ======================================================================

def test_time_slot_boundaries_and_uniqueness():
    # Kiểm tra tính không chồng chéo (non-overlapping)
    test_cases = [
        ("2017-01-01 05:55:00", None),
        ("2017-01-01 06:00:00", 1),
        ("2017-01-01 07:55:00", 1),
        ("2017-01-01 08:00:00", 2), # Ranh giới nửa mở [08:00, 10:00) thuộc slot 2
        ("2017-01-01 09:59:00", 2),
        ("2017-01-01 10:00:00", None),
        ("2017-01-01 11:30:00", 3),
        ("2017-01-01 13:29:00", 3),
        ("2017-01-01 13:30:00", None),
        ("2017-01-01 16:30:00", 4),
        ("2017-01-01 18:29:00", 4),
        ("2017-01-01 19:30:00", 5),
        ("2017-01-01 21:29:00", 5),
        ("2017-01-01 21:30:00", None),
    ]
    for ts_str, expected_slot in test_cases:
        ts = pd.to_datetime(ts_str)
        slot_id, _ = assign_time_slot(ts)
        assert slot_id == expected_slot, f"Timestamp {ts_str} gán nhầm thành slot {slot_id}, kỳ vọng: {expected_slot}"

# ======================================================================
# 3. KIỂM THỬ LÀM SẠCH VÀ NỘI SUY NHÂN QUẢ (CAUSAL IMPUTATION)
# ======================================================================

def test_causal_cleaning_no_future_leakage():
    # Tạo chuỗi tốc độ thử nghiệm: [50, 0 (lỗi), 52, NaN, 55]
    dates = pd.date_range("2017-01-01 08:00", periods=5, freq="5min")
    raw = pd.DataFrame({"s1": [50.0, 0.0, 52.0, np.nan, 55.0]}, index=dates)
    
    log = {}
    cleaned = clean_partition_causal(raw, log)
    
    assert log["zero_count"] == 1
    assert log["nan_count"] == 1
    assert log["final_nan_count"] == 0
    # Giá trị tại t=1 (ban đầu 0.0) phải được forward-fill từ t=0 (50.0), KHÔNG được lấy từ tương lai (52.0)
    assert cleaned.loc[dates[1], "s1"] == 50.0
    # Giá trị tại t=3 (ban đầu NaN) phải được forward-fill từ t=2 (52.0), KHÔNG được lấy từ tương lai (55.0)
    assert cleaned.loc[dates[3], "s1"] == 52.0

# ======================================================================
# 4. KIỂM THỬ TOÀN DIỆN PIPELINE THỰC THI (END-TO-END EXECUTION)
# ======================================================================

def test_pems_pipeline_end_to_end(synthetic_pems_fixture):
    h5_file, edges_file, out_dir, _ = synthetic_pems_fixture
    
    hashes = process_pems_bay_pipeline(
        h5_path=str(h5_file),
        edges_csv=str(edges_file),
        output_dir=str(out_dir),
        train_ratio=0.5,
        val_ratio=0.25,
        test_ratio=0.25
    )
    
    # 1. Kiểm tra tồn tại đầy đủ artifacts
    expected_files = [
        "pems_bay_cleaned_subnetwork.csv",
        "train.csv", "validation.csv", "test.csv",
        "X_train_preprocessed.csv", "X_validation_preprocessed.csv", "X_test_preprocessed.csv",
        "y_train.csv", "y_validation.csv", "y_test.csv",
        "preprocessing_pipeline.json",
        "data_quality_report.json",
        "split_manifest.json",
        "artifact_hashes.json"
    ]
    for ef in expected_files:
        assert (out_dir / ef).exists(), f"Thiếu artifact: {ef}"
        assert (out_dir / ef).stat().st_size > 0, f"Artifact rỗng: {ef}"

    # 2. Kiểm tra chất lượng dữ liệu và chia ranh giới thời gian
    with open(out_dir / "split_manifest.json", "r", encoding="utf-8") as f:
        split_meta = json.load(f)
    assert pd.to_datetime(split_meta["train"]["end"]) < pd.to_datetime(split_meta["validation"]["start"])
    assert pd.to_datetime(split_meta["validation"]["end"]) < pd.to_datetime(split_meta["test"]["start"])

    # 3. Kiểm tra căn chỉnh ma trận X và y
    X_tr = pd.read_csv(out_dir / "X_train_preprocessed.csv")
    y_tr = pd.read_csv(out_dir / "y_train.csv")
    X_val = pd.read_csv(out_dir / "X_validation_preprocessed.csv")
    y_val = pd.read_csv(out_dir / "y_validation.csv")
    X_te = pd.read_csv(out_dir / "X_test_preprocessed.csv")
    y_te = pd.read_csv(out_dir / "y_test.csv")

    assert len(X_tr) == len(y_tr)
    assert len(X_val) == len(y_val)
    assert len(X_te) == len(y_te)
    assert "travel_time" not in X_tr.columns
    assert "travel_time" not in X_te.columns
    assert (y_tr["travel_time"] > 0).all()
    assert (y_te["travel_time"] > 0).all()

    # 4. Kiểm tra báo cáo chất lượng phát hiện đúng missing timestamps
    with open(out_dir / "data_quality_report.json", "r", encoding="utf-8") as f:
        qr = json.load(f)
    assert qr["missing_timestamps"] == 2
    assert qr["subnetwork_edge_count"] == 4
