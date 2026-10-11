"""
WS4 - Xuất metrics của 2 baseline vào 1 file JSON trong common/.

Input:
    workstream04/metrics_groupmean.csv   (6 dòng: 1 overall + 5 per-slot)
    workstream04/metrics_linearreg.csv   (6 dòng: 1 overall + 5 per-slot)

Output:
    common/workstream04_metrics.json

Format JSON:
    List 2 object, mỗi object có:
      - workstream, model_name
      - MAE / RMSE / MSE / MAPE_percent (metric tổng thể)
      - n_obs (số quan sát tập test)
      - by_time_slot: dict metric của từng khung giờ (1-5)
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
print(f"Đọc: {gm_csv.name}  ({len(gm_df)} dòng)")
print(f"Đọc: {lr_csv.name}  ({len(lr_df)} dòng)")

# ---------- 2. HÀM CHUYỂN ĐỔI ----------
METRIC_COLS = ["MAE", "RMSE", "MSE", "MAPE_percent"]

def row_to_metrics(row):
    """Chuyển 1 dòng DataFrame thành dict metric."""
    d = {col: float(row[col]) for col in METRIC_COLS}
    if "n_obs" in row.index:
        d["n_obs"] = int(row["n_obs"])
    return d

def df_to_model_json(df, workstream, model_name):
    """Chuyển DataFrame (6 dòng) thành dict JSON cho 1 model."""
    # Dòng overall: time_slot == "all"
    overall_row = df[df["time_slot"] == "all"].iloc[0]
    json_obj = {
        "workstream": workstream,
        "model_name": model_name,
        **row_to_metrics(overall_row),   
    }

    # Per-slot: các dòng còn lại
    slot_rows = df[df["time_slot"] != "all"]
    json_obj["by_time_slot"] = {
        str(int(r["time_slot"])): row_to_metrics(r)
        for _, r in slot_rows.iterrows()
    }
    return json_obj

# ---------- 3. TẠO JSON LIST ----------
metrics_list = [
    df_to_model_json(gm_df, "workstream04", "GroupMean"),
    df_to_model_json(lr_df, "workstream04", "LinearRegression"),
]

# ---------- 4. GHI FILE JSON VÀO common/ ----------
out_file = COMMON_DIR / "workstream04_metrics.json"

with open(out_file, "w", encoding="utf-8") as f:
    json.dump(metrics_list, f, indent=4, ensure_ascii=False)

# ---------- 5. IN RA ĐỂ KIỂM TRA ----------
print(f"\nNội dung file {out_file.name}:")
print(json.dumps(metrics_list, indent=4, ensure_ascii=False))

print(f"\nĐã ghi file JSON vào: {COMMON_DIR.resolve()}")
print(f"  - {out_file.name}")