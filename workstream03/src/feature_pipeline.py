"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Tập lệnh: workstream03/src/feature_pipeline.py
Pipeline Tiền xử lý & Trích xuất Đặc trưng (Feature Engineering & Preprocessing Pipeline).
Đóng gói quy trình tiền xử lý thống nhất cho Workstream 4 (Baselines) và Workstream 5 (Neural Network).

INPUT:
- File tập huấn luyện: train.csv (1.440 dòng, Ngày 1–24).
- File tập kiểm thử: test.csv (360 dòng, Ngày 25–30).
- Dependencies: pandas, numpy, json, pathlib.
- Assumptions:
  + Các tham số chuẩn hóa (Mean, Std) và từ điển phân loại (Categories) chỉ được học (fit) DUY NHẤT trên Train set.
  + Test set hoàn toàn vô hình trong bước fit (Zero Leakage Principle).
  + Scaler policy: Z-score chuẩn hóa cự ly distance với mẫu độ lệch chuẩn sample std (ddof=1) nhằm đảm bảo tính tái lập 100% với artifact hiện hữu của WS4/WS5.

PROCESSING:
- 1. Numerical scaling: Cự ly 'distance' được chuẩn hóa z = (x - mean_train) / std_train.
- 2. Binary pass-through: Cờ 'is_weekend' giữ nguyên kiểu float (0.0 hoặc 1.0).
- 3. One-Hot Encoding:
  + 'edge_id': 12 categories danh mục cạnh.
  + 'time_slot': 5 categories khung giờ.
  + 'day_of_week': 7 categories thứ trong tuần.
- 4. Tổng số chiều đặc trưng: 1 (distance) + 1 (is_weekend) + 12 (edge) + 5 (slot) + 7 (day) = 26 features.
- 5. Trích xuất biến mục tiêu 'travel_time' độc lập thành y_train và y_test.

OUTPUT:
- X_train_preprocessed.csv (1.440 x 26)
- y_train.csv (1.440 x 1)
- X_test_preprocessed.csv (360 x 26)
- y_test.csv (360 x 1)
- preprocessing_pipeline.json (Metadata lưu trữ toàn bộ tham số chuẩn hóa)
- Lưu đồng thời vào workstream03/data/processed/ và workstream03/.

DOWNSTREAM:
- WS4 (Hà Minh): Dùng X_train/X_test cho mô hình hồi quy tuyến tính (Linear Regression).
- WS5 (Yến Nhi): Dùng X_train/X_test nạp trực tiếp vào tầng Input của Multi-Layer Perceptron (26 input neurons).
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np
import json
import argparse

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SRC_DIR = Path(__file__).resolve().parent
WS3_DIR = SRC_DIR.parent
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"

class SeervadaFeaturePipeline:
    def __init__(self, ddof=1):
        self.fitted = False
        self.ddof = ddof  # Mặc định ddof=1 (sample std) khớp với artifact chuẩn của nhóm
        self.numerical_cols = ["distance"]
        self.categorical_cols = ["edge_id", "time_slot", "day_of_week"]
        self.binary_cols = ["is_weekend"]
        self.target_col = "travel_time"
        
        # Tham số học từ tập Train
        self.scaler_params = {}
        self.categories_ = {}
        self.feature_names_out_ = []

    def fit(self, train_df: pd.DataFrame):
        """Học tham số chuẩn hóa (Mean/Std, Categories) DUY NHẤT trên tập Train."""
        # 1. Học tham số Numerical (Z-score scaling: mean, std)
        for col in self.numerical_cols:
            mean = float(train_df[col].mean())
            std = float(train_df[col].std(ddof=self.ddof))
            self.scaler_params[col] = {
                "mean": mean,
                "std": std if std > 0 else 1.0,
                "ddof": self.ddof
            }
            
        # 2. Học các giá trị phân loại (One-Hot Encoding categories)
        for col in self.categorical_cols:
            cats = sorted(train_df[col].unique().tolist())
            self.categories_[col] = cats
            
        # 3. Tạo danh sách tên cột sau khi encode
        out_names = []
        for col in self.numerical_cols:
            out_names.append(col)
        for col in self.binary_cols:
            out_names.append(col)
        for col in self.categorical_cols:
            for cat in self.categories_[col]:
                out_names.append(f"{col}_{cat}")
                
        self.feature_names_out_ = out_names
        self.fitted = True
        print(f"Pipeline fitted thành công với {len(self.feature_names_out_)} đặc trưng đầu ra.")
        return self

    def transform(self, df: pd.DataFrame):
        """Biến đổi dữ liệu dựa trên tham số đã học từ Train."""
        assert self.fitted, "Pipeline chưa được fit! Hãy gọi .fit(train_df) trước."
        
        encoded_dfs = []
        
        # 1. Numerical scaling: (x - mean) / std
        for col in self.numerical_cols:
            mean = self.scaler_params[col]["mean"]
            std = self.scaler_params[col]["std"]
            scaled_series = (df[col] - mean) / std
            encoded_dfs.append(pd.DataFrame({col: scaled_series}, index=df.index))
            
        # 2. Binary features
        for col in self.binary_cols:
            encoded_dfs.append(pd.DataFrame({col: df[col].astype(float)}, index=df.index))
            
        # 3. Categorical One-Hot Encoding
        for col in self.categorical_cols:
            cats = self.categories_[col]
            for cat in cats:
                col_name = f"{col}_{cat}"
                encoded_dfs.append(pd.DataFrame({col_name: (df[col] == cat).astype(float)}, index=df.index))
                
        X_out = pd.concat(encoded_dfs, axis=1)
        
        # Đảm bảo target không bị rò rỉ vào ma trận X
        assert self.target_col not in X_out.columns, "CRITICAL ERROR: Biến target nằm trong ma trận đặc trưng X!"
        
        # Trích xuất vector nhãn y nếu có
        y_out = pd.DataFrame({self.target_col: df[self.target_col].copy()}, index=df.index) if self.target_col in df.columns else None
        
        return X_out, y_out

    def save_pipeline(self, json_paths):
        """Lưu lại pipeline metadata dưới dạng JSON để tái lập 100%."""
        data = {
            "scaler_params": {
                col: {"mean": self.scaler_params[col]["mean"], "std": self.scaler_params[col]["std"]}
                for col in self.numerical_cols
            },
            "categories": self.categories_,
            "feature_names_out": self.feature_names_out_,
            "numerical_cols": self.numerical_cols,
            "categorical_cols": self.categorical_cols,
            "binary_cols": self.binary_cols,
            "target_col": self.target_col
        }
        for jp in json_paths:
            jp = Path(jp)
            jp.parent.mkdir(parents=True, exist_ok=True)
            with open(jp, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Đã lưu cấu hình pipeline vào: {jp}")

def run_pipeline(train_path=None, test_path=None, output_dir=None):
    if train_path is None:
        c1 = DATA_PROCESSED_DIR / "train.csv"
        c2 = WS3_DIR / "train.csv"
        train_path = c1 if c1.exists() else c2
    if test_path is None:
        c1 = DATA_PROCESSED_DIR / "test.csv"
        c2 = WS3_DIR / "test.csv"
        test_path = c1 if c1.exists() else c2

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)
    
    pipeline = SeervadaFeaturePipeline(ddof=1)
    pipeline.fit(train_df)
    
    DATA_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    json_targets = [
        DATA_PROCESSED_DIR / "preprocessing_pipeline.json",
        WS3_DIR / "preprocessing_pipeline.json"
    ]
    if output_dir:
        json_targets.append(Path(output_dir) / "preprocessing_pipeline.json")
    pipeline.save_pipeline(json_targets)
    
    X_train, y_train = pipeline.transform(train_df)
    X_test, y_test = pipeline.transform(test_df)
    
    # Validation
    assert len(X_train) == len(y_train) == 1440, "LỖI: Kích thước tập Train sai lệch!"
    assert len(X_test) == len(y_test) == 360, "LỖI: Kích thước tập Test sai lệch!"
    assert X_train.shape[1] == X_test.shape[1] == 26, "LỖI: Số chiều đặc trưng không bằng 26!"
    assert X_train.isna().sum().sum() == 0, "LỖI: Phát hiện NaN trong X_train!"
    assert X_test.isna().sum().sum() == 0, "LỖI: Phát hiện NaN trong X_test!"
    
    # Lưu file
    file_pairs = [
        (DATA_PROCESSED_DIR / "X_train_preprocessed.csv", X_train),
        (DATA_PROCESSED_DIR / "y_train.csv", y_train),
        (DATA_PROCESSED_DIR / "X_test_preprocessed.csv", X_test),
        (DATA_PROCESSED_DIR / "y_test.csv", y_test),
        (WS3_DIR / "X_train_preprocessed.csv", X_train),
        (WS3_DIR / "y_train.csv", y_train),
        (WS3_DIR / "X_test_preprocessed.csv", X_test),
        (WS3_DIR / "y_test.csv", y_test),
    ]
    if output_dir:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)
        file_pairs.extend([
            (out_p / "X_train_preprocessed.csv", X_train),
            (out_p / "y_train.csv", y_train),
            (out_p / "X_test_preprocessed.csv", X_test),
            (out_p / "y_test.csv", y_test)
        ])

    for p, df_to_save in file_pairs:
        p.parent.mkdir(parents=True, exist_ok=True)
        df_to_save.to_csv(p, index=False)
        print(f"Đã lưu: {p}")
        
    print("=" * 60)
    print("HOÀN THÀNH XUẤT MA TRẬN ĐẶC TRƯNG CHUẨN:")
    print(f"- X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"- X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    print("=" * 60)
    return X_train, y_train, X_test, y_test, pipeline

def main():
    parser = argparse.ArgumentParser(description="Chạy Pipeline tiền xử lý đặc trưng mạng Seervada")
    parser.add_argument("--train", type=str, default=None, help="Đường dẫn train.csv")
    parser.add_argument("--test", type=str, default=None, help="Đường dẫn test.csv")
    parser.add_argument("--output-dir", type=str, default=None, help="Thư mục xuất file tùy chọn")
    args = parser.parse_args()

    run_pipeline(train_path=args.train, test_path=args.test, output_dir=args.output_dir)

if __name__ == "__main__":
    main()
