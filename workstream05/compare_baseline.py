#Cập nhật đọc đầy đủ thông số
import os
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMMON_DIR = os.path.join(BASE_DIR, "..", "common")

def main():
    print("=== SO SÁNH NEURAL NETWORK VỚI BASELINE (WORKSTREAM 4) ===")

    nn_json_path = os.path.join(COMMON_DIR, "workstream05_metrics.json")
    
    if not os.path.exists(nn_json_path):
        print("Vui lòng chạy evaluate_nn.py trước!")
        return

    with open(nn_json_path, "r", encoding="utf-8") as f:
        nn_metrics = json.load(f)

    # Đọc tất cả các file metrics của các workstream khác trong folder common
    all_metrics = [nn_metrics]
    
    if os.path.exists(COMMON_DIR):
        for file in os.listdir(COMMON_DIR):
            if file.endswith("_metrics.json") and file != "workstream05_metrics.json":
                try:
                    with open(os.path.join(COMMON_DIR, file), "r", encoding="utf-8") as f:
                        all_metrics.append(json.load(f))
                except Exception as e:
                    pass

    # Tạo bảng so sánh
    rows = []
    for m in all_metrics:
        rows.append({
            "Workstream": m.get("workstream", "N/A"),
            "Model": m.get("model_name", "N/A"),
            "MAE": m.get("MAE", "N/A"),
            "RMSE": m.get("RMSE", "N/A"),
            "MSE": m.get("MSE", "N/A"),
            "MAPE (%)": m.get("MAPE_percent", "N/A")
        })

    df_compare = pd.DataFrame(rows)
    print("\n--- BẢNG SO SÁNH KẾT QUẢ CÁC MÔ HÌNH ---")
    print(df_compare.to_string(index=False))
    
    # Export file CSV so sánh
    csv_out = os.path.join(BASE_DIR, "baseline_comparison.csv")
    df_compare.to_csv(csv_out, index=False)
    print(f"\n[Output] Đã lưu bảng so sánh tại: baseline_comparison.csv")

if __name__ == "__main__":
    main()