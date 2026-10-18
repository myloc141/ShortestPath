"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Tập lệnh: workstream03/src/eda_analysis.py
Phân tích Khám phá Dữ liệu (Exploratory Data Analysis - EDA) trên chuỗi thời gian di chuyển mạng Seervada.

INPUT:
- File dữ liệu: seervada_travel_time_SIMULATED.csv (1.800 dòng).
- Dependencies: pandas, numpy, scipy.stats, json, pathlib.
- Assumptions:
  + Dữ liệu mô phỏng không chứa giá trị khuyết (missing) và giá trị âm (negative).

PROCESSING:
- Tính toán thống kê mô tả: Mean, Std Dev, Median, IQR, Min, Max, Skewness, Kurtosis.
- Thống kê nhóm theo 5 khung giờ (Time slots) và 12 cạnh mạng (Edges).
- So sánh phân phối giữa ngày làm việc trong tuần (Weekdays) và ngày cuối tuần (Weekends).
- Xuất kết quả tổng hợp ra file JSON.

OUTPUT:
- File JSON tóm tắt thống kê: workstream03/reports/eda_summary.json.

DOWNSTREAM:
- Cung cấp số liệu thống kê mô tả thực nghiệm cho DATA_ENGINEERING_REPORT.md và Slide báo cáo nhóm.
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import scipy.stats as stats
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC_DIR = Path(__file__).resolve().parent
WS3_DIR = SRC_DIR.parent
DATA_RAW_DIR = WS3_DIR / "data" / "raw"
REPORT_DIR = WS3_DIR / "reports"

def run_eda(csv_path=None, report_dir=None):
    if csv_path is None:
        c1 = DATA_RAW_DIR / "seervada_travel_time_SIMULATED.csv"
        c2 = WS3_DIR / "seervada_travel_time_SIMULATED.csv"
        csv_path = c1 if c1.exists() else c2

    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Không tìm thấy file: {csv_path}")

    df = pd.read_csv(csv_path)
    
    print("=" * 60)
    print("BÁO CÁO PHÂN TÍCH KHÁM PHÁ DỮ LIỆU (EDA) - SEERVADA TRAVEL TIME")
    print("=" * 60)
    
    # 1. Cấu trúc và tính toàn vẹn
    missing_count = int(df.isnull().sum().sum())
    invalid_tt = int((df['travel_time'] <= 0).sum())
    print(f"\n1. Tổng quan cấu trúc:")
    print(f"- Số lượng quan sát: {len(df)} dòng")
    print(f"- Số lượng thuộc tính: {df.shape[1]} cột")
    print(f"- Giá trị thiếu (Missing values): {missing_count} ({missing_count/len(df)*100:.1f}%)")
    print(f"- Giá trị không hợp lệ (travel_time <= 0): {invalid_tt}")
    
    # 2. Thống kê mô tả
    tt = df["travel_time"]
    mean_val = float(tt.mean())
    std_val = float(tt.std())
    median_val = float(tt.median())
    q25 = float(tt.quantile(0.25))
    q75 = float(tt.quantile(0.75))
    iqr_val = q75 - q25
    skew_val = float(stats.skew(tt))
    kurt_val = float(stats.kurtosis(tt))
    
    print(f"\n2. Thống kê mô tả tổng thể travel_time (phút):")
    print(f"- Trung bình (Mean): {mean_val:.2f} phút")
    print(f"- Độ lệch chuẩn (Std Dev): {std_val:.2f} phút")
    print(f"- Trung vị (Median): {median_val:.2f} phút")
    print(f"- Khoảng tứ phân vị (IQR): {iqr_val:.2f} phút [Q1: {q25:.2f}, Q3: {q75:.2f}]")
    print(f"- Giá trị nhỏ nhất (Min): {float(tt.min()):.2f} phút")
    print(f"- Giá trị lớn nhất (Max): {float(tt.max()):.2f} phút")
    print(f"- Độ lệch (Skewness): {skew_val:.2f} (Lệch phải dương, phản ánh tắc nghẽn)")
    print(f"- Độ nhọn (Kurtosis): {kurt_val:.2f}")
    
    # 3. Khung giờ
    slot_summary = df.groupby(["time_slot", "time_slot_name"])["travel_time"].agg(
        Mean="mean", Std="std", Min="min", Median="median", Max="max"
    ).reset_index()
    print(f"\n3. Phân bố thời gian di chuyển theo 5 khung giờ:")
    print(slot_summary.to_string(index=False))
    
    # 4. Ngày thường vs cuối tuần
    day_type_summary = df.groupby("is_weekend")["travel_time"].agg(
        Mean="mean", Std="std", Median="median", Max="max"
    ).reset_index()
    day_type_summary["Loại ngày"] = day_type_summary["is_weekend"].map({0: "Ngày trong tuần (T2-T6)", 1: "Cuối tuần (T7-CN)"})
    print(f"\n4. So sánh Ngày thường vs Cuối tuần:")
    print(day_type_summary[["Loại ngày", "Mean", "Std", "Median", "Max"]].to_string(index=False))
    
    # 5. Phân tích 12 cạnh
    edge_summary = df.groupby(["edge_id", "distance"])["travel_time"].agg(
        Mean="mean", Std="std", Min="min", Max="max"
    ).reset_index()
    edge_summary["Tốc độ TB (km/h quy ước)"] = (edge_summary["distance"] / (edge_summary["Mean"] / 60)).round(2)
    print(f"\n5. Phân tích thời gian di chuyển theo 12 cạnh mạng Seervada:")
    print(edge_summary.to_string(index=False))
    
    # Lưu JSON báo cáo
    target_report_dir = Path(report_dir) if report_dir else REPORT_DIR
    target_report_dir.mkdir(parents=True, exist_ok=True)
    out_json = target_report_dir / "eda_summary.json"
    
    eda_results = {
        "dataset": csv_path.name,
        "total_rows": int(len(df)),
        "total_columns": int(df.shape[1]),
        "missing_count": missing_count,
        "invalid_travel_time_count": invalid_tt,
        "descriptive_statistics": {
            "mean": round(mean_val, 2),
            "std": round(std_val, 2),
            "median": round(median_val, 2),
            "q25": round(q25, 2),
            "q75": round(q75, 2),
            "iqr": round(iqr_val, 2),
            "min": round(float(tt.min()), 2),
            "max": round(float(tt.max()), 2),
            "skewness": round(skew_val, 2),
            "kurtosis": round(kurt_val, 2)
        },
        "time_slot_breakdown": slot_summary.to_dict(orient="records"),
        "edge_breakdown": edge_summary.to_dict(orient="records")
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(eda_results, f, ensure_ascii=False, indent=2)
    print(f"\nĐã xuất kết quả EDA vào: {out_json}")
    return eda_results

def main():
    parser = argparse.ArgumentParser(description="Chạy phân tích khám phá dữ liệu (EDA) Seervada")
    parser.add_argument("--input", type=str, default=None, help="Đường dẫn file SIMULATED csv")
    parser.add_argument("--report-dir", type=str, default=None, help="Thư mục xuất báo cáo")
    args = parser.parse_args()

    run_eda(csv_path=args.input, report_dir=args.report_dir)

if __name__ == "__main__":
    main()
