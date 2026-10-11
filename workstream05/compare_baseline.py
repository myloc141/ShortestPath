import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
COMMON_DIR = os.path.join(PROJECT_ROOT, "common")

def extract_metric_value(item, keys):
    """Hàm hỗ trợ lấy giá trị bất kể hoa hay thường"""
    for k in keys:
        if k in item:
            return item[k]
    return "N/A"

def main():
    print("=== BẢNG SO SÁNH CÁC MÔ HÌNH BASELINE VÀ NEURAL NETWORK ===")

    all_models = []

    if os.path.exists(COMMON_DIR):
        for file in os.listdir(COMMON_DIR):
            if file.endswith("_metrics.json"):
                file_path = os.path.join(COMMON_DIR, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                        # Nếu file chứa một danh sách nhiều mô hình (như WS4)
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    all_models.append(item)
                        # Nếu file chứa một mô hình duy nhất (như WS5)
                        elif isinstance(data, dict):
                            all_models.append(data)
                except Exception as e:
                    print(f"Không thể đọc file {file}: {e}")

    if not all_models:
        print("Chưa tìm thấy dữ liệu metrics trong folder common!")
        return

    # Trích xuất dữ liệu ra bảng
    rows = []
    for m in all_models:
        ws = extract_metric_value(m, ["workstream", "ws", "Workstream"])
        model_name = extract_metric_value(m, ["model_name", "model", "Model"])
        mae = extract_metric_value(m, ["MAE", "mae"])
        rmse = extract_metric_value(m, ["RMSE", "rmse"])
        mse = extract_metric_value(m, ["MSE", "mse"])
        mape = extract_metric_value(m, ["MAPE_percent", "MAPE", "mape", "mape_percent"])

        rows.append({
            "Workstream": ws,
            "Model Name": model_name,
            "MAE": mae,
            "RMSE": rmse,
            "MSE": mse,
            "MAPE (%)": mape
        })

    df_compare = pd.DataFrame(rows)
    print("\n" + "="*70)
    print(df_compare.to_string(index=False))
    print("="*70)

    # Xuất file CSV
    out_csv = os.path.join(BASE_DIR, "baseline_comparison.csv")
    df_compare.to_csv(out_csv, index=False)
    print(f"\n[Output] Đã xuất thành công bảng so sánh tại: {out_csv}")

if __name__ == "__main__":
    main()