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
print("LINEAR REGRESSION — WS4 (drop-first, no multicollinearity)")
print("=" * 60)
print(f"X_train (raw) : {X_train.shape}")
print(f"X_test  (raw) : {X_test.shape}")

assert X_train.shape[0] == len(y_train), "Số dòng train không khớp!"
assert X_test.shape[0]  == len(y_test),  "Số dòng test không khớp!"
assert list(X_train.columns) == list(X_test.columns), "Cột train/test không khớp!"

# ---------- 2. DROP-FIRST (khử đa cộng tuyến hoàn hảo) ----------
# Mỗi nhóm one-hot có tổng = 1 với mọi dòng -> cộng tuyến với intercept.
# Bỏ 1 cột mỗi nhóm -> nhóm đó trở thành nhóm tham chiếu.
DROP_COLS = [
    "edge_id_A-B",       # tham chiếu cho 12 cạnh
    "time_slot_1",       # tham chiếu cho 5 khung giờ
    "day_of_week_Fri",   # tham chiếu cho 7 thứ
    "is_weekend",        # DƯ THỪA: = Sat + Sun
]

X_train_lr = X_train.drop(columns=DROP_COLS)
X_test_lr  = X_test.drop(columns=DROP_COLS)

print(f"\nĐã drop {len(DROP_COLS)} cột tham chiếu: {DROP_COLS}")
print(f"X_train (LR)  : {X_train_lr.shape}")
print(f"X_test  (LR)  : {X_test_lr.shape}")

# ---------- 3. FIT ----------
lr = LinearRegression()
lr.fit(X_train_lr, y_train)

print(f"\nIntercept : {lr.intercept_:.4f}")
print(f"Số hệ số  : {len(lr.coef_)}")

coef_df = pd.DataFrame({
    "feature": X_train_lr.columns,
    "coef":    lr.coef_,
}).sort_values("coef", key=abs, ascending=False)

print("\nTop 10 hệ số |coef| lớn nhất:")
print(coef_df.head(10).to_string(index=False))

# --- Kiểm tra đa cộng tuyến ---
import numpy as np
rank = np.linalg.matrix_rank(X_train_lr.values)
n_features = X_train_lr.shape[1]
print(f"\nRank của X_train_lr   : {rank}")
print(f"Số cột X_train_lr     : {n_features}")
print(f"Full rank?            : {rank == n_features}  (True = hết đa cộng tuyến)")

# ---------- 4. PREDICT ----------
y_pred = lr.predict(X_test_lr)

# ---------- 5. ĐÁNH GIÁ ----------
metrics = evaluate_all(y_test.values, y_pred)
print("\n--- Metrics Linear Regression ---")
for k, v in metrics.items():
    print(f"  {k:<14}: {v}")

# ---------- 6. DECODE KEY (chỉ để xuất output) ----------
edge_cols = [c for c in X_test.columns if c.startswith("edge_id_")]
slot_cols = [c for c in X_test.columns if c.startswith("time_slot_")]
dow_cols  = [c for c in X_test.columns if c.startswith("day_of_week_")]

edge_t = X_test[edge_cols].idxmax(axis=1).str.replace("edge_id_", "", regex=False).values
slot_t = X_test[slot_cols].idxmax(axis=1).str.replace("time_slot_", "", regex=False).astype(int).values
dow_t  = X_test[dow_cols].idxmax(axis=1).str.replace("day_of_week_", "", regex=False).values

# ---------- 7. XUẤT OUTPUT ----------
pd.DataFrame({"y_pred": y_pred}).to_csv(
    THIS_DIR / "pred_linearreg_raw.csv", index=False)

pd.DataFrame({
    "edge_id": edge_t, "time_slot": slot_t, "day_of_week": dow_t,
    "y_true": y_test.values, "y_pred": y_pred,
}).to_csv(THIS_DIR / "pred_linearreg_withkey.csv", index=False)

pd.DataFrame([{"model": "LinearRegression", **metrics}]).to_csv(
    THIS_DIR / "metrics_linearreg.csv", index=False)

# Thêm 1 cột "reference" đánh dấu nhóm tham chiếu (tiện cho báo cáo)
coef_df["note"] = coef_df["feature"].apply(
    lambda x: "reference" if x in DROP_COLS else "coef_vs_reference"
)
coef_df.to_csv(THIS_DIR / "coef_linearreg.csv", index=False)

print(f"\nĐã ghi 4 file trong: {THIS_DIR}")
print("  - pred_linearreg_raw.csv")
print("  - pred_linearreg_withkey.csv")
print("  - metrics_linearreg.csv")
print("  - coef_linearreg.csv")