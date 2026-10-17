import os
import sys
import pandas as pd
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Thêm đường dẫn thư mục gốc RCSP để import thư viện chung từ 'common'
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from common.metrics import evaluate_all

Y_TEST_PATH = os.path.join(BASE_DIR, "..", "workstream03", "y_test.csv")
PRED_PATH = os.path.join(BASE_DIR, "pred_nn.csv")

def main():
    print("=== TÍNH TOÁN CÁC CHỈ SỐ ĐÁNH GIÁ VỚI COMMON/METRICS.PY ===")
    
    if not os.path.exists(PRED_PATH):
        print("Lỗi: Không tìm thấy file pred_nn.csv. Hãy chạy train_nn.py trước!")
        return

    y_test = pd.read_csv(Y_TEST_PATH).values.ravel()
    y_pred = pd.read_csv(PRED_PATH)["y_pred"].values

    # Gọi hàm evaluate_all từ common.metrics
    metrics_result = evaluate_all(y_test, y_pred)

    print("\nKết quả đánh giá Neural Network (WS5):")
    for metric_name, val in metrics_result.items():
        print(f" - {metric_name:12s}: {val}")

    # Chuẩn bị dữ liệu trong common
    output_data = {
        "workstream": "workstream05",
        "model_name": "Neural_Network_MLP",
        **metrics_result
    }

    common_dir = os.path.join(PROJECT_ROOT, "common")
    os.makedirs(common_dir, exist_ok=True)
    
    output_json = os.path.join(common_dir, "workstream05_metrics.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=4, ensure_ascii=False)
        
    print(f"\n[Output] Đã xuất kết quả chuẩn vào: common/workstream05_metrics.json")

if __name__ == "__main__":
    main()