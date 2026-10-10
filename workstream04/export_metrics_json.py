"""
WS4 - Xuất metrics của 2 baseline vào 1 file JSON trong common/.

Input:
    workstream04/metrics_groupmean.csv
    workstream04/metrics_linearreg.csv

Output:
    common/workstream04_metrics.json    

"""

import json
from pathlib import Path
import pandas as pd

# ---------- PATHS ----------
THIS_DIR   = Path(__file__).resolve().parent     
ROOT_DIR   = THIS_DIR.parent                      
COMMON_DIR = ROOT_DIR / "common"                  

# ---------- 1. ĐỌC CSV METRICS ----------
gm_csv = THIS_DIR / "metrics_groupmean.csv"
lr_csv = THIS_DIR / "metrics_linearreg.csv"

assert gm_csv.exists(), f"Không thấy file: {gm_csv}"
assert lr_csv.exists(), f"Không thấy file: {lr_csv}"

gm_df = pd.read_csv(gm_csv)
lr_df = pd.read_csv(lr_csv)

print("=" * 60)
print("EXPORT METRICS JSON - WS4")
print("=" * 60)
print(f"Đọc: {gm_csv.name}")
print(f"Đọc: {lr_csv.name}")

# ---------- 2. HÀM CHUYỂN ĐỔI ----------
def to_json_dict(row, workstream, model_name):
    """Chuyển 1 dòng DataFrame metric thành dict JSON theo format WS5."""
    return {
        "workstream":   workstream,
        "model_name":   model_name,
        "MAE":          float(row["MAE"]),
        "RMSE":         float(row["RMSE"]),
        "MSE":          float(row["MSE"]),
        "MAPE_percent": float(row["MAPE_percent"]),
    }


metrics_list = [
    to_json_dict(gm_df.iloc[0], "workstream04", "GroupMean"),
    to_json_dict(lr_df.iloc[0], "workstream04", "LinearRegression"),
]

# ---------- 3. GHI FILE JSON VÀO common/ ----------
out_file = COMMON_DIR / "workstream04_metrics.json"

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(metrics_list, f, indent=4, ensure_ascii=False)

# ---------- 4. IN RA ĐỂ KIỂM TRA ----------
print(f"\nNội dung file {out_file.name}:")
print(json.dumps(metrics_list, indent=4, ensure_ascii=False))

print(f"\nĐã ghi file JSON vào: {COMMON_DIR.resolve()}")
print(f"  - {out_file.name}")