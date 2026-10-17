"""
Workstream 3: Data Engineering - Lại Gia Huy
Kịch bản Phân chia Train/Test theo Chuỗi Thời gian (Time-series Block Split)
Đảm bảo 100% không rò rỉ dữ liệu (No Data Leakage).
Xuất ra train.csv và test.csv chuẩn dùng chung cho WS4, WS5, WS6.
"""

import pandas as pd
import numpy as np

def split_time_series_data(input_csv="workspace_ws3/data/seervada_travel_time_SIMULATED.csv",
                           train_days=24,
                           train_out="workspace_ws3/data/train.csv",
                           test_out="workspace_ws3/data/test.csv"):
    df = pd.read_csv(input_csv)
    
    # Phân chia dựa trên trục thời gian (day <= train_days: Train, day > train_days: Test)
    train_mask = df["day"] <= train_days
    test_mask = df["day"] > train_days
    
    train_df = df[train_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)
    
    print("=" * 60)
    print("BÁO CÁO PHÂN CHIA TẬP DỮ LIỆU TRAIN / TEST")
    print("=" * 60)
    print(f"- Tổng số quan sát gốc: {len(df)} dòng")
    print(f"- Tập huấn luyện (Train Set - Ngày 1 đến {train_days}): {len(train_df)} dòng ({len(train_df)/len(df)*100:.1f}%)")
    print(f"- Tập kiểm thử (Test Set - Ngày {train_days+1} đến 30): {len(test_df)} dòng ({len(test_df)/len(df)*100:.1f}%)")
    
    # Kiểm tra tính toàn vẹn (Completeness & Balance)
    train_edges = set(train_df["edge_id"].unique())
    test_edges = set(test_df["edge_id"].unique())
    assert train_edges == test_edges, "LỖI: Tập test thiếu cạnh so với tập train!"
    print(f"- Kiểm tra danh mục cạnh (12 edges): Khớp 100% giữa Train và Test.")
    
    train_slots = set(train_df["time_slot"].unique())
    test_slots = set(test_df["time_slot"].unique())
    assert train_slots == test_slots, "LỖI: Tập test thiếu khung giờ so với tập train!"
    print(f"- Kiểm tra danh mục khung giờ (5 slots): Khớp 100% giữa Train và Test.")
    
    print(f"- Phân bố ngày cuối tuần trong Train: {train_df['is_weekend'].value_counts().to_dict()}")
    print(f"- Phân bố ngày cuối tuần trong Test: {test_df['is_weekend'].value_counts().to_dict()}")
    
    # Xuất file chuẩn
    train_df.to_csv(train_out, index=False)
    test_df.to_csv(test_out, index=False)
    print(f"\nĐã lưu thành công:")
    print(f"1. {train_out}")
    print(f"2. {test_out}")
    
    return train_df, test_df

if __name__ == "__main__":
    split_time_series_data()
