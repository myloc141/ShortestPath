import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

# ---------- PATHS ----------
THIS_DIR   = Path(__file__).resolve().parent      
ROOT_DIR   = THIS_DIR.parent
WS3_DIR    = ROOT_DIR / "workstream03"            
COMMON_DIR = ROOT_DIR / "common"                  

sys.path.append(str(COMMON_DIR))
from metrics import evaluate_all

# ---------- 1. LOAD ----------
X_train = pd.read_csv(WS3_DIR / "X_train_preprocessed.csv")
X_test  = pd.read_csv(WS3_DIR / "X_test_preprocessed.csv")
y_train = pd.read_csv(WS3_DIR / "y_train.csv").squeeze("columns")
y_test  = pd.read_csv(WS3_DIR / "y_test.csv").squeeze("columns")

print("=" * 60)
print("LINEAR REGRESSION — WS4")
print("=" * 60)
print(f"X_train : {X_train.shape}")
print(f"X_test  : {X_test.shape}")

assert X_train.shape[0] == len(y_train), "Số dòng train không khớp!"
assert X_test.shape[0]  == len(y_test),  "Số dòng test không khớp!"
assert list(X_train.columns) == list(X_test.columns), "Cột train/test không khớp!"

# ---------- 2. FIT ----------
lr = LinearRegression()
lr.fit(X_train, y_train)

print(f"\nIntercept : {lr.intercept_:.4f}")
print(f"Số hệ số  : {len(lr.coef_)}")

coef_df = pd.DataFrame({
    "feature": X_train.columns,
    "coef":    lr.coef_,
}).sort_values("coef", key=abs, ascending=False)

print("\nTop 10 hệ số |coef| lớn nhất:")
print(coef_df.head(10).to_string(index=False))

# ---------- 3. PREDICT ----------
y_pred = lr.predict(X_test)

# ---------- 4. ĐÁNH GIÁ ----------
metrics = evaluate_all(y_test.values, y_pred)
print("\n--- Metrics Linear Regression ---")
for k, v in metrics.items():
    print(f"  {k:<14}: {v}")

# ---------- 5. DECODE KEY (chỉ để xuất output) ----------
edge_cols = [c for c in X_test.columns if c.startswith("edge_id_")]
slot_cols = [c for c in X_test.columns if c.startswith("time_slot_")]
dow_cols  = [c for c in X_test.columns if c.startswith("day_of_week_")]

edge_t = X_test[edge_cols].idxmax(axis=1).str.replace("edge_id_", "", regex=False).values
slot_t = X_test[slot_cols].idxmax(axis=1).str.replace("time_slot_", "", regex=False).astype(int).values
dow_t  = X_test[dow_cols].idxmax(axis=1).str.replace("day_of_week_", "", regex=False).values

# ---------- 6. XUẤT OUTPUT ----------
pd.DataFrame({"y_pred": y_pred}).to_csv(
    THIS_DIR / "pred_linearreg_raw.csv", index=False)

pd.DataFrame({
    "edge_id": edge_t, "time_slot": slot_t, "day_of_week": dow_t,
    "y_true": y_test.values, "y_pred": y_pred,
}).to_csv(THIS_DIR / "pred_linearreg_withkey.csv", index=False)

pd.DataFrame([{"model": "LinearRegression", **metrics}]).to_csv(
    THIS_DIR / "metrics_linearreg.csv", index=False)

coef_df.to_csv(THIS_DIR / "coef_linearreg.csv", index=False)

print(f"\nĐã ghi 4 file trong: {THIS_DIR}")
print("  - pred_linearreg_raw.csv")
print("  - pred_linearreg_withkey.csv")
print("  - metrics_linearreg.csv")
print("  - coef_linearreg.csv")