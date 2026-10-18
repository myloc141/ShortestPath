"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Tập lệnh: workstream03/src/split_dataset.py
Phân chia Train/Test theo Chuỗi Thời gian (Time-series Block Split) không rò rỉ dữ liệu (Zero Data Leakage).

INPUT:
- File dữ liệu mô phỏng: seervada_travel_time_SIMULATED.csv (1.800 dòng, 30 ngày).
- Tham số:
  + train_days: Số ngày phân bổ cho tập Train (mặc định: 24 ngày, tương ứng 80% dữ liệu).
- Dependencies: pandas, numpy, pathlib.
- Assumptions:
  + Dữ liệu thời gian có thứ tự nhân quả nghiêm ngặt: Quá khứ (ngày 1-24) không được biết tương lai (ngày 25-30).
  + Không sử dụng Random Shuffle để loại trừ triệt để Temporal Data Leakage.

PROCESSING:
- Tách mặt nạ thời gian: train_mask = (day <= train_days), test_mask = (day > train_days).
- Kiểm tra tính liên tục thời gian: assert max(train_day) < min(test_day).
- Kiểm tra toàn vẹn danh mục: 12/12 cạnh và 5/5 khung giờ phải xuất hiện đầy đủ ở cả hai tập.
- Kiểm tra bảo toàn dòng: len(train_df) + len(test_df) == len(df).

OUTPUT:
- train.csv: 1.440 dòng (Ngày 1–24).
- test.csv: 360 dòng (Ngày 25–30).
- Lưu đồng thời vào workstream03/data/processed/ và workstream03/.

DOWNSTREAM:
- train.csv:
  + WS4 (Hà Minh) huấn luyện mô hình Group Mean và Linear Regression.
  + WS5 (Yến Nhi) huấn luyện Neural Network (MLP).
- test.csv:
  + WS4 & WS5 đánh giá sai số dự báo MAE, RMSE, MSE, MAPE.
  + WS6 (Mỹ Lộc) lấy ground truth travel_time để đánh giá chất lượng tuyến đường định tuyến động.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC_DIR = Path(__file__).resolve().parent
WS3_DIR = SRC_DIR.parent
DATA_RAW_DIR = WS3_DIR / "data" / "raw"
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"

def split_time_series_data(input_csv=None,
                           train_days=24,
                           output_dir=None):
    if input_csv is None:
        # Ưu tiên tìm trong data/raw, nếu không có tìm ở workstream03 root
        candidate_1 = DATA_RAW_DIR / "seervada_travel_time_SIMULATED.csv"
        candidate_2 = WS3_DIR / "seervada_travel_time_SIMULATED.csv"
        input_csv = candidate_1 if candidate_1.exists() else candidate_2

    input_csv = Path(input_csv)
    if not input_csv.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu đầu vào: {input_csv}")

    df = pd.read_csv(input_csv)
    
    # Phân chia dựa trên trục thời gian
    train_mask = df["day"] <= train_days
    test_mask = df["day"] > train_days
    
    train_df = df[train_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)
    
    # Validation kiểm soát rò rỉ và toàn vẹn
    max_train_day = int(train_df["day"].max())
    min_test_day = int(test_df["day"].min())
    assert max_train_day < min_test_day, (
        f"DATA LEAKAGE ERROR: max(train_day)={max_train_day} >= min(test_day)={min_test_day}"
    )
    
    assert len(train_df) + len(test_df) == len(df), "LỖI: Tổng số dòng train và test không bằng tập gốc!"
    
    train_edges = set(train_df["edge_id"].unique())
    test_edges = set(test_df["edge_id"].unique())
    assert train_edges == test_edges, "LỖI: Tập test thiếu cạnh so với tập train!"
    
    train_slots = set(train_df["time_slot"].unique())
    test_slots = set(test_df["time_slot"].unique())
    assert train_slots == test_slots, "LỖI: Tập test thiếu khung giờ so với tập train!"
    
    print("=" * 60)
    print("BÁO CÁO PHÂN CHIA TẬP DỮ LIỆU TRAIN / TEST")
    print("=" * 60)
    print(f"- Tổng số quan sát gốc: {len(df)} dòng")
    print(f"- Tập huấn luyện (Train Set - Ngày 1 đến {train_days}): {len(train_df)} dòng ({len(train_df)/len(df)*100:.1f}%)")
    print(f"- Tập kiểm thử (Test Set - Ngày {train_days+1} đến 30): {len(test_df)} dòng ({len(test_df)/len(df)*100:.1f}%)")
    print(f"- Kiểm tra ranh giới thời gian: max(Train Day)={max_train_day} < min(Test Day)={min_test_day} -> ZERO LEAKAGE PASS.")
    print(f"- Kiểm tra danh mục cạnh (12 edges): Khớp 100% giữa Train và Test.")
    print(f"- Kiểm tra danh mục khung giờ (5 slots): Khớp 100% giữa Train và Test.")
    
    # Lưu file đồng thời vào data/processed và root để chống breaking change
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    targets = [
        (DATA_PROCESSED_DIR / "train.csv", DATA_PROCESSED_DIR / "test.csv"),
        (WS3_DIR / "train.csv", WS3_DIR / "test.csv")
    ]
    
    if output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        targets.append((out_p / "train.csv", out_p / "test.csv"))
        
    for tr_p, te_p in targets:
        train_df.to_csv(tr_p, index=False)
        test_df.to_csv(te_p, index=False)
        print(f"Đã lưu: {tr_p} và {te_p}")
        
    return train_df, test_df

def main():
    parser = argparse.ArgumentParser(description="Chia tập dữ liệu Seervada theo chuỗi thời gian")
    parser.add_argument("--input", type=str, default=None, help="Đường dẫn file SIMULATED csv")
    parser.add_argument("--train-days", type=int, default=24, help="Số ngày tập Train (mặc định: 24)")
    parser.add_argument("--output-dir", type=str, default=None, help="Thư mục xuất file tùy chọn")
    args = parser.parse_args()

    split_time_series_data(input_csv=args.input, train_days=args.train_days, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
