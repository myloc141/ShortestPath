"""
Workstream 3: Data Engineering - Lại Gia Huy
Pipeline Tiền xử lý & Trích xuất Đặc trưng (Feature Engineering & Preprocessing Pipeline)
Chuẩn hóa dữ liệu dùng chung thống nhất cho Workstream 4 (Baselines) và Workstream 5 (Neural Network).
Không sử dụng thư viện phụ thuộc ngoài (chạy thuần túy trên Pandas & NumPy).
"""

import pandas as pd
import numpy as np
import json

class SeervadaFeaturePipeline:
    def __init__(self):
        self.fitted = False
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
        # 1. Học tham số Numerical (StandardScaler: mean, std)
        for col in self.numerical_cols:
            mean = float(train_df[col].mean())
            std = float(train_df[col].std())
            self.scaler_params[col] = {"mean": mean, "std": std if std > 0 else 1.0}
            
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
        """Biến đổi dữ liệu dựa trên tham số đã học."""
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
                # So sánh giá trị chính xác
                encoded_dfs.append(pd.DataFrame({col_name: (df[col] == cat).astype(float)}, index=df.index))
                
        X_out = pd.concat(encoded_dfs, axis=1)
        
        # Nếu có cột target trong df thì trích xuất y
        y_out = df[self.target_col].copy() if self.target_col in df.columns else None
        
        return X_out, y_out

    def save_pipeline(self, json_path="workspace_ws3/data/preprocessing_pipeline.json"):
        """Lưu lại pipeline metadata dưới dạng JSON để tái lập 100%."""
        data = {
            "scaler_params": self.scaler_params,
            "categories": self.categories_,
            "feature_names_out": self.feature_names_out_,
            "numerical_cols": self.numerical_cols,
            "categorical_cols": self.categorical_cols,
            "binary_cols": self.binary_cols,
            "target_col": self.target_col
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu cấu hình pipeline vào {json_path}")

def run_pipeline():
    train_df = pd.read_csv("workspace_ws3/data/train.csv")
    test_df = pd.read_csv("workspace_ws3/data/test.csv")
    
    pipeline = SeervadaFeaturePipeline()
    pipeline.fit(train_df)
    pipeline.save_pipeline("workspace_ws3/data/preprocessing_pipeline.json")
    
    X_train, y_train = pipeline.transform(train_df)
    X_test, y_test = pipeline.transform(test_df)
    
    # Lưu các file ma trận đặc trưng
    X_train.to_csv("workspace_ws3/data/X_train_preprocessed.csv", index=False)
    y_train.to_csv("workspace_ws3/data/y_train.csv", index=False)
    X_test.to_csv("workspace_ws3/data/X_test_preprocessed.csv", index=False)
    y_test.to_csv("workspace_ws3/data/y_test.csv", index=False)
    
    print("=" * 60)
    print("HOÀN THÀNH XUẤT MA TRẬN ĐẶC TRƯNG CHUẨN:")
    print(f"- X_train shape: {X_train.shape}, y_train shape: {y_train.shape}")
    print(f"- X_test shape: {X_test.shape}, y_test shape: {y_test.shape}")
    print("=" * 60)

if __name__ == "__main__":
    run_pipeline()
