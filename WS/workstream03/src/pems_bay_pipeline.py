"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Tập lệnh: workstream03/src/pems_bay_pipeline.py
Pipeline Tiền xử lý, Làm sạch và Trích xuất Đặc trưng cho Bộ dữ liệu Thực tế PeMS-BAY.
Đảm bảo: Zero Data Leakage, Causal Imputation, Hợp đồng WS1 chuẩn mực, CLI độc lập, Tái lập 100%.

INPUT:
- --h5: File HDF5 lưu trữ chuỗi thời gian tốc độ cảm biến (vd: data/raw/pems-bay.h5).
- --edges: File CSV danh sách cạnh mạng con từ WS1 (vd: workstream01/data/pems_bay_subnetwork_edges.csv).
  Bắt buộc các cột: ['edge_id', 'sensor_u', 'sensor_v', 'distance_miles'].
- --output-dir: Thư mục xuất kết quả (mặc định: workstream03/data/pems_bay).
- Dependencies: pandas, numpy, tables (pytables), json, hashlib, argparse, pathlib.
- Assumptions:
  + Tốc độ đo bằng dặm/giờ (mph). Cự ly đo bằng dặm (miles). Thời gian di chuyển tính theo phút.
  + Tốc độ cạnh là xấp xỉ proxy: v_uv(t) = [v_u(t) + v_v(t)] / 2.
  + Không sử dụng biến mục tiêu tương lai (Zero Cross-Boundary Data Leakage).

PROCESSING:
1. Contract Validation:
   - Chuẩn hóa Sensor ID thành string.
   - Xác thực: set(sensor_u U sensor_v) <= set(hdf_sensors). Mismatch -> Ném ngoại lệ Fail Loudly!
   - Kiểm tra distance_miles > 0, không có vòng tự thân (self-loop), edge_id duy nhất.
2. Grid Alignment:
   - Dựng lưới 5 phút chuẩn: pd.date_range(start, end, freq='5min').
   - Đối chiếu số quan sát thực tế vs kỳ vọng, log số timestamp thiếu/trùng lặp.
3. Temporal Partitioning:
   - Chia 3 tập theo chuỗi thời gian nguyên ngày: Train (~70%), Validation (~10%), Test (~20%).
   - Kiểm tra nghiêm ngặt: max(Train) < min(Val) và max(Val) < min(Test).
4. Zero Leakage Cleaning & Causal Imputation:
   - Tạo mặt nạ zero mask và NaN mask.
   - Tốc độ == 0 đánh dấu là bất thường cảm biến (sensor anomaly/dropout) -> chuyển thành NaN.
   - KHÔNG mặc định clip(lower=5) làm sai lệch dữ liệu tắc nghẽn thật (1-4 mph).
   - Nội suy nhân quả (Causal Forward-Fill) RIÊNG BIỆT trong từng tập Train/Val/Test (không nội suy xuyên biên giới).
5. Edge Travel Time Calculation:
   - v_uv(t) = [v_u(t) + v_v(t)] / 2 (mph).
   - t_uv(t) = distance_miles / v_uv(t) * 60 (phút).
6. Time Slot Aggregation (5 khung giờ):
   - Slot 1: [06:00, 08:00)
   - Slot 2: [08:00, 10:00)
   - Slot 3: [11:30, 13:30)
   - Slot 4: [16:30, 18:30)
   - Slot 5: [19:30, 21:30)
   - Ranh giới nửa mở [start, end) bảo đảm một timestamp thuộc duy nhất 1 slot.
   - Chính sách gom cụm: Mean of instantaneous travel times E[t_uv(t)].
7. Feature Engineering & Scaling:
   - StandardScaler cho distance_miles: Fit duy nhất trên Train, transform Val và Test.
   - OneHotEncoder cho edge_id, time_slot, day_of_week: Fit duy nhất trên Train.
   - is_weekend: pass-through binary (0.0/1.0).

OUTPUT:
- pems_bay_cleaned_subnetwork.csv (Toàn bộ dữ liệu 5-phút sau làm sạch)
- train.csv, validation.csv, test.csv (Dữ liệu gom cụm khung giờ)
- X_train_preprocessed.csv, X_validation_preprocessed.csv, X_test_preprocessed.csv
- y_train.csv, y_validation.csv, y_test.csv
- preprocessing_pipeline.json
- data_quality_report.json
- split_manifest.json
- artifact_hashes.json

DOWNSTREAM:
- WS4 (Hà Minh): Huấn luyện Group Mean & Linear Regression trên PeMS-BAY.
- WS5 (Yến Nhi): Huấn luyện MLP với Validation Split và Early Stopping, đánh giá trên Test Set.
- WS6 (Mỹ Lộc): Định tuyến động trên mạng con California Bay Area và đối chiếu ground truth Test.
"""

from pathlib import Path
import sys
import argparse
import json
import hashlib
import numpy as np
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

TIME_SLOT_DEFINITIONS = [
    {"slot_id": 1, "name": "06:00-08:00", "start_hour": 6, "start_min": 0, "end_hour": 8, "end_min": 0},
    {"slot_id": 2, "name": "08:00-10:00", "start_hour": 8, "start_min": 0, "end_hour": 10, "end_min": 0},
    {"slot_id": 3, "name": "11:30-13:30", "start_hour": 11, "start_min": 30, "end_hour": 13, "end_min": 30},
    {"slot_id": 4, "name": "16:30-18:30", "start_hour": 16, "start_min": 30, "end_hour": 18, "end_min": 30},
    {"slot_id": 5, "name": "19:30-21:30", "start_hour": 19, "start_min": 30, "end_hour": 21, "end_min": 30},
]

def calculate_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def validate_edges_contract(edges_df, available_sensors):
    """
    Kiểm tra tính hợp lệ của hợp đồng bàn giao cạnh từ WS1.
    Fail loudly nếu vi phạm bất kỳ ràng buộc nào.
    """
    required_cols = ["edge_id", "sensor_u", "sensor_v", "distance_miles"]
    for col in required_cols:
        if col not in edges_df.columns:
            raise ValueError(f"WS1 CONTRACT VIOLATION: Thiếu cột bắt buộc '{col}' trong edges file!")

    edges_df = edges_df.copy()
    edges_df["edge_id"] = edges_df["edge_id"].astype(str)
    edges_df["sensor_u"] = edges_df["sensor_u"].astype(str).str.strip()
    edges_df["sensor_v"] = edges_df["sensor_v"].astype(str).str.strip()
    edges_df["distance_miles"] = edges_df["distance_miles"].astype(float)

    # 1. Kiểm tra tính duy nhất của edge_id
    if edges_df["edge_id"].duplicated().any():
        dups = edges_df[edges_df["edge_id"].duplicated()]["edge_id"].tolist()
        raise ValueError(f"WS1 CONTRACT VIOLATION: Tồn tại edge_id trùng lặp: {dups}")

    # 2. Kiểm tra cự ly > 0
    if (edges_df["distance_miles"] <= 0).any():
        bad_edges = edges_df[edges_df["distance_miles"] <= 0]["edge_id"].tolist()
        raise ValueError(f"WS1 CONTRACT VIOLATION: Cự ly khoảng cách <= 0 tại các cạnh: {bad_edges}")

    # 3. Kiểm tra tự thân (self-loop)
    if (edges_df["sensor_u"] == edges_df["sensor_v"]).any():
        self_loops = edges_df[edges_df["sensor_u"] == edges_df["sensor_v"]]["edge_id"].tolist()
        raise ValueError(f"WS1 CONTRACT VIOLATION: Phát hiện self-loop (sensor_u == sensor_v) tại: {self_loops}")

    # 4. Kiểm tra tập cảm biến hợp lệ với HDF5
    available_set = set(str(s).strip() for s in available_sensors)
    edge_sensors = set(edges_df["sensor_u"].unique()).union(set(edges_df["sensor_v"].unique()))
    missing_sensors = edge_sensors - available_set
    if len(missing_sensors) > 0:
        raise ValueError(
            f"WS1 CONTRACT VIOLATION: Các cảm biến sau trong edge list không tồn tại trong HDF5: {missing_sensors}"
        )

    return edges_df

def assign_time_slot(dt):
    """
    Gán time_slot cho một timestamp theo định nghĩa nửa mở [start, end).
    Trả về (slot_id, slot_name) hoặc (None, None) nếu nằm ngoài 5 khung giờ.
    """
    total_min = dt.hour * 60 + dt.minute
    for slot in TIME_SLOT_DEFINITIONS:
        s_min = slot["start_hour"] * 60 + slot["start_min"]
        e_min = slot["end_hour"] * 60 + slot["end_min"]
        if s_min <= total_min < e_min:
            return slot["slot_id"], slot["name"]
    return None, None

def read_pems_h5(h5_path):
    """
    Đọc dữ liệu chuỗi thời gian tốc độ từ file HDF5.
    Hỗ trợ cả trường hợp HDF5 lưu trữ qua Pandas (HDFStore) hoặc PyTables trực tiếp.
    """
    h5_path = Path(h5_path)
    if not h5_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file HDF5 PeMS-BAY tại: {h5_path}")

    try:
        # Cách 1: Đọc trực tiếp qua pd.read_hdf
        df = pd.read_hdf(h5_path)
    except Exception as e1:
        try:
            # Cách 2: Khám phá keys qua HDFStore
            with pd.HDFStore(str(h5_path), mode='r') as store:
                keys = store.keys()
                if not keys:
                    raise ValueError(f"File HDF5 không chứa bảng nào (empty keys)")
                df = store[keys[0]]
        except Exception as e2:
            raise RuntimeError(f"Không thể đọc file HDF5: Lỗi 1: {e1} | Lỗi 2: {e2}")

    # Chuẩn hóa cột sensor ID thành string
    df.columns = [str(c).strip() for c in df.columns]
    
    # Đảm bảo index là DateTimeIndex
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
        
    df = df.sort_index()
    return df

def clean_partition_causal(sub_df, report_log=None):
    """
    Làm sạch dữ liệu tốc độ KHÔNG rò rỉ (Causal Imputation duy nhất theo trục thời gian).
    - Tạo zero mask và nan mask.
    - Speed == 0 -> Chuyển thành NaN.
    - Causal Forward Fill (ffill).
    - Nếu còn NaN ở điểm bắt đầu chuỗi -> bfill nội bộ tập đó (không nhìn sang tập khác).
    """
    df = sub_df.copy()
    zero_mask = (df == 0)
    nan_mask = df.isna()
    
    zero_count = int(zero_mask.sum().sum())
    nan_count = int(nan_mask.sum().sum())
    
    # Đổi 0 thành NaN
    df[zero_mask] = np.nan
    
    # Causal Forward Fill
    df_imputed = df.ffill()
    
    # Bfill dự phòng cho các giá trị đầu chuỗi
    remaining_nan = int(df_imputed.isna().sum().sum())
    if remaining_nan > 0:
        df_imputed = df_imputed.bfill()
        
    final_nan = int(df_imputed.isna().sum().sum())
    
    # Kiểm tra tốc độ hợp lệ > 0
    if (df_imputed <= 0).any().any():
        raise ValueError("Làm sạch thất bại: Phát hiện tốc độ <= 0 sau khi xử lý!")

    if report_log is not None:
        report_log["zero_count"] = zero_count
        report_log["nan_count"] = nan_count
        report_log["initial_missing_total"] = zero_count + nan_count
        report_log["remaining_nan_after_ffill"] = remaining_nan
        report_log["final_nan_count"] = final_nan
        
    return df_imputed

def process_pems_bay_pipeline(h5_path, edges_csv, output_dir,
                              train_ratio=0.7, val_ratio=0.1, test_ratio=0.2,
                              grid_freq="5min"):
    """
    Thực thi toàn bộ luồng pipeline PeMS-BAY.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("KHỞI ĐỘNG PEMS-BAY DATA ENGINEERING PIPELINE (WORKSTREAM 3)")
    print("=" * 70)
    print(f"HDF5 Input: {h5_path}")
    print(f"Edges Input: {edges_csv}")
    print(f"Output Directory: {out_dir}")
    
    # 1. Đọc và kiểm tra raw HDF5
    raw_df = read_pems_h5(h5_path)
    raw_obs_count = len(raw_df)
    sensor_count = raw_df.shape[1]
    first_ts = raw_df.index[0]
    last_ts = raw_df.index[-1]
    
    print(f"\n1. Thông tin Raw PeMS-BAY:")
    print(f"- Số dòng quan sát: {raw_obs_count:,}")
    print(f"- Số cảm biến: {sensor_count}")
    print(f"- Mốc thời gian đầu: {first_ts}")
    print(f"- Mốc thời gian cuối: {last_ts}")
    
    # 2. Đọc và kiểm tra Edges Contract từ WS1
    edges_raw = pd.read_csv(edges_csv)
    edges_df = validate_edges_contract(edges_raw, raw_df.columns)
    print(f"- Hợp đồng WS1 kiểm tra thành công: {len(edges_df)} cạnh hợp lệ, cự ly > 0, không self-loop.")
    
    # 3. Lưới thời gian chuẩn 5 phút (Expected Grid)
    expected_grid = pd.date_range(first_ts, last_ts, freq=grid_freq)
    expected_count = len(expected_grid)
    duplicate_count = int(raw_df.index.duplicated().sum())
    
    if duplicate_count > 0:
        raw_df = raw_df[~raw_df.index.duplicated(keep="first")]
        
    # Reindex về lưới chuẩn 5 phút
    grid_df = raw_df.reindex(expected_grid)
    missing_ts_count = expected_count - raw_obs_count + duplicate_count
    
    print(f"\n2. Đồng bộ lưới 5 phút (5-min Grid Alignment):")
    print(f"- Số quan sát thực tế (raw observations): {raw_obs_count:,}")
    print(f"- Số mốc kỳ vọng trên lưới hoàn chỉnh (expected grid count): {expected_count:,}")
    print(f"- Số mốc bị thiếu (missing timestamps): {missing_ts_count}")
    print(f"- Số mốc bị trùng lặp (duplicate timestamps): {duplicate_count}")

    # Lấy danh sách cảm biến cần thiết cho mạng con
    needed_sensors = sorted(list(set(edges_df["sensor_u"]).union(set(edges_df["sensor_v"]))))
    sub_grid_df = grid_df[needed_sensors].copy()
    
    # 4. Phân chia Train / Val / Test theo ngày nguyên vẹn (Whole Calendar Days)
    all_dates = sorted(list(set(sub_grid_df.index.date)))
    total_days = len(all_dates)
    
    n_train_days = int(np.round(total_days * train_ratio))
    n_val_days = int(np.round(total_days * val_ratio))
    if n_train_days + n_val_days >= total_days:
        n_val_days = max(1, total_days - n_train_days - 1)
    n_test_days = total_days - n_train_days - n_val_days
    
    train_dates = set(all_dates[:n_train_days])
    val_dates = set(all_dates[n_train_days : n_train_days + n_val_days])
    test_dates = set(all_dates[n_train_days + n_val_days :])
    
    train_idx = sub_grid_df.index.map(lambda dt: dt.date() in train_dates)
    val_idx = sub_grid_df.index.map(lambda dt: dt.date() in val_dates)
    test_idx = sub_grid_df.index.map(lambda dt: dt.date() in test_dates)
    
    train_raw = sub_grid_df[train_idx].copy()
    val_raw = sub_grid_df[val_idx].copy()
    test_raw = sub_grid_df[test_idx].copy()
    
    assert train_raw.index.max() < val_raw.index.min(), "LỖI RÒ RỈ THỜI GIAN: max(Train) >= min(Val)"
    assert val_raw.index.max() < test_raw.index.min(), "LỖI RÒ RỈ THỜI GIAN: max(Val) >= min(Test)"
    
    print(f"\n3. Phân chia chuỗi thời gian (Temporal Split):")
    print(f"- Train ({len(train_dates)} ngày, {len(train_raw):,} mốc 5p): {train_raw.index.min()} -> {train_raw.index.max()}")
    print(f"- Val   ({len(val_dates)} ngày, {len(val_raw):,} mốc 5p): {val_raw.index.min()} -> {val_raw.index.max()}")
    print(f"- Test  ({len(test_dates)} ngày, {len(test_raw):,} mốc 5p): {test_raw.index.min()} -> {test_raw.index.max()}")

    # 5. Làm sạch Causal Imputation độc lập từng tập
    quality_log = {}
    train_clean = clean_partition_causal(train_raw, quality_log.setdefault("train", {}))
    val_clean = clean_partition_causal(val_raw, quality_log.setdefault("val", {}))
    test_clean = clean_partition_causal(test_raw, quality_log.setdefault("test", {}))
    
    cleaned_all = pd.concat([train_clean, val_clean, test_clean])
    cleaned_all.to_csv(out_dir / "pems_bay_cleaned_subnetwork.csv")
    print(f"\n4. Đã làm sạch và xuất pems_bay_cleaned_subnetwork.csv thành công.")
    
    # 6. Tính toán tốc độ cạnh và thời gian di chuyển 5 phút
    def build_instantaneous_edge_df(speed_df, partition_name):
        records = []
        for idx, row in speed_df.iterrows():
            ts = idx
            dt_date = ts.strftime("%Y-%m-%d")
            day_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][ts.weekday()]
            is_weekend = 1 if ts.weekday() in [5, 6] else 0
            slot_id, slot_name = assign_time_slot(ts)
            
            for _, edge in edges_df.iterrows():
                e_id = edge["edge_id"]
                u = edge["sensor_u"]
                v = edge["sensor_v"]
                dist = edge["distance_miles"]
                
                v_u = row[u]
                v_v = row[v]
                # Công thức proxy tốc độ cạnh: (v_u + v_v) / 2
                edge_speed = (v_u + v_v) / 2.0
                # Thời gian di chuyển (phút): distance / speed * 60
                travel_time = (dist / edge_speed) * 60.0
                
                records.append({
                    "timestamp": ts,
                    "date": dt_date,
                    "day_of_week": day_of_week,
                    "is_weekend": is_weekend,
                    "time_slot": slot_id,
                    "time_slot_name": slot_name,
                    "edge_id": e_id,
                    "distance_miles": dist,
                    "speed_mph": edge_speed,
                    "travel_time": travel_time,
                    "partition": partition_name
                })
        return pd.DataFrame(records)

    train_edge_inst = build_instantaneous_edge_df(train_clean, "train")
    val_edge_inst = build_instantaneous_edge_df(val_clean, "validation")
    test_edge_inst = build_instantaneous_edge_df(test_clean, "test")
    
    # 7. Gom cụm theo 5 khung giờ (Time-Slot Aggregation)
    def aggregate_by_slot(edge_inst_df):
        # Lọc các mốc thuộc 5 khung giờ hợp lệ
        valid_slots = edge_inst_df[edge_inst_df["time_slot"].notna()].copy()
        valid_slots["time_slot"] = valid_slots["time_slot"].astype(int)
        
        # Policy A: Mean of instantaneous travel times
        grouped = valid_slots.groupby(["date", "day_of_week", "is_weekend", "time_slot", "time_slot_name", "edge_id", "distance_miles"]).agg(
            travel_time=("travel_time", "mean"),
            mean_speed_mph=("speed_mph", "mean")
        ).reset_index()
        
        grouped["travel_time"] = grouped["travel_time"].round(4)
        grouped["mean_speed_mph"] = grouped["mean_speed_mph"].round(2)
        return grouped

    train_agg = aggregate_by_slot(train_edge_inst)
    val_agg = aggregate_by_slot(val_edge_inst)
    test_agg = aggregate_by_slot(test_edge_inst)
    
    print(f"\n5. Gom cụm theo khung giờ (Time-slot aggregation):")
    print(f"- Train aggregated rows: {len(train_agg):,}")
    print(f"- Val aggregated rows:   {len(val_agg):,}")
    print(f"- Test aggregated rows:  {len(test_agg):,}")
    
    # Lưu train.csv, validation.csv, test.csv
    train_agg.to_csv(out_dir / "train.csv", index=False)
    val_agg.to_csv(out_dir / "validation.csv", index=False)
    test_agg.to_csv(out_dir / "test.csv", index=False)
    
    # 8. Feature Engineering: StandardScaler & OneHotEncoder (Fit DUY NHẤT trên Train)
    dist_mean = float(train_agg["distance_miles"].mean())
    dist_std = float(train_agg["distance_miles"].std(ddof=1))
    if dist_std == 0:
        dist_std = 1.0
        
    scaler_params = {
        "distance_miles": {"mean": dist_mean, "std": dist_std, "ddof": 1}
    }
    
    categories = {
        "edge_id": sorted(train_agg["edge_id"].unique().tolist()),
        "time_slot": sorted(train_agg["time_slot"].unique().tolist()),
        "day_of_week": sorted(train_agg["day_of_week"].unique().tolist())
    }
    
    def transform_features(df):
        out_dfs = []
        # Scaled distance
        scaled_dist = (df["distance_miles"] - dist_mean) / dist_std
        out_dfs.append(pd.DataFrame({"distance_miles": scaled_dist}, index=df.index))
        # Binary is_weekend
        out_dfs.append(pd.DataFrame({"is_weekend": df["is_weekend"].astype(float)}, index=df.index))
        # One-hot edge_id
        for cat in categories["edge_id"]:
            out_dfs.append(pd.DataFrame({f"edge_id_{cat}": (df["edge_id"] == cat).astype(float)}, index=df.index))
        # One-hot time_slot
        for cat in categories["time_slot"]:
            out_dfs.append(pd.DataFrame({f"time_slot_{cat}": (df["time_slot"] == cat).astype(float)}, index=df.index))
        # One-hot day_of_week
        for cat in categories["day_of_week"]:
            out_dfs.append(pd.DataFrame({f"day_of_week_{cat}": (df["day_of_week"] == cat).astype(float)}, index=df.index))
            
        X = pd.concat(out_dfs, axis=1)
        y = pd.DataFrame({"travel_time": df["travel_time"].copy()}, index=df.index)
        return X, y

    X_train, y_train = transform_features(train_agg)
    X_val, y_val = transform_features(val_agg)
    X_test, y_test = transform_features(test_agg)
    
    # Xuất feature matrices
    X_train.to_csv(out_dir / "X_train_preprocessed.csv", index=False)
    y_train.to_csv(out_dir / "y_train.csv", index=False)
    X_val.to_csv(out_dir / "X_validation_preprocessed.csv", index=False)
    y_val.to_csv(out_dir / "y_validation.csv", index=False)
    X_test.to_csv(out_dir / "X_test_preprocessed.csv", index=False)
    y_test.to_csv(out_dir / "y_test.csv", index=False)
    
    # 9. Xuất Pipeline Metadata & Manifests
    pipeline_meta = {
        "dataset_name": "PeMS-BAY Subnetwork",
        "scaler_params": scaler_params,
        "categories": categories,
        "feature_names_out": list(X_train.columns),
        "target_col": "travel_time",
        "target_unit": "minutes",
        "aggregation_policy": "Policy A: mean(instantaneous travel_time) in minutes"
    }
    with open(out_dir / "preprocessing_pipeline.json", "w", encoding="utf-8") as f:
        json.dump(pipeline_meta, f, indent=2, ensure_ascii=False)
        
    quality_report = {
        "raw_observations": raw_obs_count,
        "sensor_count": sensor_count,
        "subnetwork_sensor_count": len(needed_sensors),
        "subnetwork_edge_count": len(edges_df),
        "expected_grid_count": expected_count,
        "missing_timestamps": missing_ts_count,
        "duplicate_timestamps": duplicate_count,
        "first_timestamp": str(first_ts),
        "last_timestamp": str(last_ts),
        "partition_quality": quality_log
    }
    with open(out_dir / "data_quality_report.json", "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2, ensure_ascii=False)
        
    split_manifest = {
        "train": {
            "start": str(train_raw.index.min()),
            "end": str(train_raw.index.max()),
            "days_count": len(train_dates),
            "rows_aggregated": len(train_agg)
        },
        "validation": {
            "start": str(val_raw.index.min()),
            "end": str(val_raw.index.max()),
            "days_count": len(val_dates),
            "rows_aggregated": len(val_agg)
        },
        "test": {
            "start": str(test_raw.index.min()),
            "end": str(test_raw.index.max()),
            "days_count": len(test_dates),
            "rows_aggregated": len(test_agg)
        }
    }
    with open(out_dir / "split_manifest.json", "w", encoding="utf-8") as f:
        json.dump(split_manifest, f, indent=2, ensure_ascii=False)
        
    # Tính SHA-256 cho toàn bộ artifacts
    hashes = {}
    for p in out_dir.glob("*.csv"):
        hashes[p.name] = calculate_sha256(p)
    for p in out_dir.glob("*.json"):
        if p.name != "artifact_hashes.json":
            hashes[p.name] = calculate_sha256(p)
            
    with open(out_dir / "artifact_hashes.json", "w", encoding="utf-8") as f:
        json.dump(hashes, f, indent=2)
        
    print(f"\nPipeline PeMS-BAY hoàn tất 100%! Đã xuất toàn bộ artifacts vào: {out_dir}")
    return hashes

def main():
    parser = argparse.ArgumentParser(description="Pipeline tiền xử lý PeMS-BAY (Workstream 3)")
    parser.add_argument("--h5", type=str, required=True, help="Đường dẫn file pems-bay.h5")
    parser.add_argument("--edges", type=str, required=True, help="Đường dẫn file pems_bay_subnetwork_edges.csv")
    parser.add_argument("--output-dir", type=str, default="workstream03/data/pems_bay", help="Thư mục xuất file")
    parser.add_argument("--train-ratio", type=float, default=0.7, help="Tỷ lệ Train (mặc định 0.7)")
    parser.add_argument("--val-ratio", type=float, default=0.1, help="Tỷ lệ Validation (mặc định 0.1)")
    parser.add_argument("--test-ratio", type=float, default=0.2, help="Tỷ lệ Test (mặc định 0.2)")
    args = parser.parse_args()

    process_pems_bay_pipeline(
        h5_path=args.h5,
        edges_csv=args.edges,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio
    )

if __name__ == "__main__":
    main()
