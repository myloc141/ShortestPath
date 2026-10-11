import sys
from pathlib import Path
import numpy as np
import pandas as pd

# ---------- PATHS----------
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
print("GROUP MEAN — WS4")
print("=" * 60)
print(f"X_train : {X_train.shape}")
print(f"X_test  : {X_test.shape}")
print(f"y_train : {y_train.shape}")
print(f"y_test  : {y_test.shape}")

assert X_train.shape[0] == len(y_train), "Số dòng train không khớp!"
assert X_test.shape[0]  == len(y_test),  "Số dòng test không khớp!"
assert list(X_train.columns) == list(X_test.columns), "Cột train/test không khớp!"

# ---------- 2. LẤY CỘT ONE-HOT ----------
edge_cols = [c for c in X_train.columns if c.startswith("edge_id_")]
slot_cols = [c for c in X_train.columns if c.startswith("time_slot_")]
dow_cols  = [c for c in X_train.columns if c.startswith("day_of_week_")]

print(f"\nOne-hot — edge: {len(edge_cols)}, slot: {len(slot_cols)}, dow: {len(dow_cols)}")

for name, X in [("train", X_train), ("test", X_test)]:
    for grp, cols in [("edge", edge_cols), ("slot", slot_cols), ("dow", dow_cols)]:
        s = X[cols].sum(axis=1)
        assert (s == 1).all(), f"[{name}] {grp} one-hot hỏng ở dòng {(s != 1).idxmax()}"
print("Kiểm tra one-hot: hợp lệ.")

# ---------- 3. TẠO KEY ----------
def key_l1(X):  # (edge, slot)
    return (X[edge_cols].astype(str).agg("|".join, axis=1)
            + "||"
            + X[slot_cols].astype(str).agg("|".join, axis=1))

def key_l2(X):  # edge
    return X[edge_cols].astype(str).agg("|".join, axis=1)

tr_k1, te_k1 = key_l1(X_train), key_l1(X_test)
tr_k2, te_k2 = key_l2(X_train), key_l2(X_test)

# ---------- 4. FIT TRÊN TRAIN ----------
group_mean  = y_train.groupby(tr_k1).mean()   # mức 1
edge_mean   = y_train.groupby(tr_k2).mean()   # mức 2
global_mean = y_train.mean()                  # mức 3

print(f"\nSố nhóm (edge, slot) train: {len(group_mean)}  (kỳ vọng ≤ 60)")
print(f"Số nhóm edge train        : {len(edge_mean)}")
print(f"Global mean (train)       : {global_mean:.4f}")

# ---------- 5. PREDICT + FALLBACK 3 MỨC ----------
def predict_one(k1, k2):
    if k1 in group_mean.index: return group_mean[k1], "level1"
    if k2 in edge_mean.index:  return edge_mean[k2],  "level2"
    return global_mean, "level3"

preds = [predict_one(k1, k2) for k1, k2 in zip(te_k1, te_k2)]
y_pred        = np.array([p[0] for p in preds])
fallback_lvls = pd.Series([p[1] for p in preds], name="fallback_level")

print("\nPhân bố fallback trên test:")
print(fallback_lvls.value_counts().to_string())

# ---------- 6. ĐÁNH GIÁ ----------
metrics = evaluate_all(y_test.values, y_pred)
print("\n--- Metrics Group Mean ---")
for k, v in metrics.items():
    print(f"  {k:<14}: {v}")

# ---------- 7. DECODE KEY (chỉ để xuất output, không dùng cho model) ----------
def decode(X):
    edge = X[edge_cols].idxmax(axis=1).str.replace("edge_id_", "", regex=False)
    slot = X[slot_cols].idxmax(axis=1).str.replace("time_slot_", "", regex=False).astype(int)
    dow  = X[dow_cols].idxmax(axis=1).str.replace("day_of_week_", "", regex=False)
    return edge.values, slot.values, dow.values

edge_t, slot_t, dow_t = decode(X_test)

# ---------- 8. XUẤT OUTPUT ----------
pd.DataFrame({"y_pred": y_pred}).to_csv(
    THIS_DIR / "pred_groupmean_raw.csv", index=False)

pd.DataFrame({
    "edge_id": edge_t, "time_slot": slot_t, "day_of_week": dow_t,
    "y_true": y_test.values, "y_pred": y_pred,
    "fallback_level": fallback_lvls.values,
}).to_csv(THIS_DIR / "pred_groupmean_withkey.csv", index=False)

pd.DataFrame([{"model": "GroupMean", **metrics}]).to_csv(
    THIS_DIR / "metrics_groupmean.csv", index=False)

print(f"\nĐã ghi 3 file trong: {THIS_DIR}")
print("  - pred_groupmean_raw.csv")
print("  - pred_groupmean_withkey.csv")
print("  - metrics_groupmean.csv")