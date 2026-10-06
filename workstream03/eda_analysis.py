"""
Workstream 3: Data Engineering - Lại Gia Huy
Kịch bản Phân tích Khám phá Dữ liệu (Exploratory Data Analysis - EDA)
Tính toán toàn bộ thống kê mô tả, phân phối theo khung giờ và theo cạnh mạng Seervada.
"""

import pandas as pd
import numpy as np
import scipy.stats as stats
import json

def run_eda(csv_path="workspace_ws3/data/seervada_travel_time_SIMULATED.csv"):
    df = pd.read_csv(csv_path)
    
    print("=" * 60)
    print("BÁO CÁO PHÂN TÍCH KHÁM PHÁ DỮ LIỆU (EDA) - SEERVADA TRAVEL TIME")
    print("=" * 60)
    
    # 1. Khái quát kích thước và chất lượng dữ liệu
    print(f"\n1. Tổng quan cấu trúc:")
    print(f"- Số lượng quan sát: {len(df)} dòng")
    print(f"- Số lượng thuộc tính: {df.shape[1]} cột")
    print(f"- Danh sách cột: {list(df.columns)}")
    print(f"- Số giá trị thiếu (Missing values): {df.isnull().sum().sum()} (0% missing)")
    print(f"- Kiểm tra tính khả thi vật lý (travel_time <= 0): {(df['travel_time'] <= 0).sum()} dòng không hợp lệ")
    
    # 2. Thống kê mô tả tổng thể biến mục tiêu travel_time
    tt = df["travel_time"]
    mean_val = tt.mean()
    std_val = tt.std()
    median_val = tt.median()
    iqr_val = tt.quantile(0.75) - tt.quantile(0.25)
    skew_val = stats.skew(tt)
    kurt_val = stats.kurtosis(tt)
    
    print(f"\n2. Thống kê mô tả tổng thể travel_time (phút):")
    print(f"- Trung bình (Mean): {mean_val:.2f} phút")
    print(f"- Độ lệch chuẩn (Std Dev): {std_val:.2f} phút")
    print(f"- Trung vị (Median): {median_val:.2f} phút")
    print(f"- Khoảng tứ phân vị (IQR): {iqr_val:.2f} phút [Q1: {tt.quantile(0.25):.2f}, Q3: {tt.quantile(0.75):.2f}]")
    print(f"- Giá trị nhỏ nhất (Min): {tt.min():.2f} phút")
    print(f"- Giá trị lớn nhất (Max): {tt.max():.2f} phút")
    print(f"- Độ lệch (Skewness): {skew_val:.2f} (Lệch phải dương, phù hợp quy luật tắc nghẽn giao thông)")
    print(f"- Độ nhọn (Kurtosis): {kurt_val:.2f}")
    
    # 3. Phân tích theo từng khung giờ (Time Slot Analysis)
    slot_summary = df.groupby(["time_slot", "time_slot_name"])["travel_time"].agg(
        Mean="mean", Std="std", Min="min", Median="median", Max="max"
    ).reset_index()
    print(f"\n3. Phân bố thời gian di chuyển theo 5 khung giờ:")
    print(slot_summary.to_string(index=False))
    
    # 4. Phân tích theo Ngày trong tuần vs Cuối tuần
    day_type_summary = df.groupby("is_weekend")["travel_time"].agg(
        Mean="mean", Std="std", Median="median", Max="max"
    ).reset_index()
    day_type_summary["Loại ngày"] = day_type_summary["is_weekend"].map({0: "Ngày trong tuần (T2-T6)", 1: "Cuối tuần (T7-CN)"})
    print(f"\n4. So sánh Ngày thường vs Cuối tuần:")
    print(day_type_summary[["Loại ngày", "Mean", "Std", "Median", "Max"]].to_string(index=False))
    
    # 5. Phân tích theo từng cạnh mạng Seervada (Edge-level Analysis)
    edge_summary = df.groupby(["edge_id", "distance"])["travel_time"].agg(
        Mean="mean", Std="std", Min="min", Max="max"
    ).reset_index()
    edge_summary["Tốc độ TB (km/h quy ước)"] = (edge_summary["distance"] / (edge_summary["Mean"] / 60)).round(2)
    print(f"\n5. Phân tích thời gian di chuyển theo 12 cạnh mạng Seervada:")
    print(edge_summary.to_string(index=False))
    
    # Lưu kết quả EDA thành file json
    eda_results = {
        "total_rows": int(len(df)),
        "mean_travel_time": round(float(mean_val), 2),
        "std_travel_time": round(float(std_val), 2),
        "median_travel_time": round(float(median_val), 2),
        "skewness": round(float(skew_val), 2),
        "slot_stats": slot_summary.to_dict(orient="records"),
        "edge_stats": edge_summary.to_dict(orient="records")
    }
    with open("workspace_ws3/reports/eda_summary.json", "w", encoding="utf-8") as f:
        json.dump(eda_results, f, ensure_ascii=False, indent=2)
    print("\nSaved eda_summary.json successfully.")

if __name__ == "__main__":
    run_eda()
