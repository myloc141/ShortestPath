# Workstream 4: Prediction Baselines

Xây dựng hai mô hình dự báo thời gian di chuyển (travel_time) trên mạng Seervada
Park để làm baseline cho Workstream 6 (Routing).

---

# PHẦN 1: CHI TIẾT TỪNG SCRIPT (THEO YÊU CẦU CHUNG)

## 1.1. `group_mean.py` — Baseline Group Mean

**Input:**
- File đọc: `workstream03/X_train_preprocessed.csv`, `X_test_preprocessed.csv`, `y_train.csv`, `y_test.csv`
- Tham số: không có
- Biến ngoài: import `evaluate_all` từ `common/metrics.py`

**Processing:**
- Tạo key mức 1 = `(edge_id, time_slot, day_of_week)`, mức 2 = `(edge_id, time_slot)`, mức 3 = `edge_id`
- Tính trung bình travel_time trên train cho mỗi mức
- Dự báo trên test bằng fallback 4 mức: level1 → level2 → level3 → level4 (global mean)
- Đánh giá MAE / RMSE / MSE / MAPE tổng thể + theo từng khung giờ

**Output:**
- `pred_groupmean_raw.csv` — 360 dòng, chỉ có cột `y_pred`
- `pred_groupmean_withkey.csv` — 360 dòng, có `edge_id, time_slot, day_of_week, y_true, y_pred, fallback_level`
- `metrics_groupmean.csv` — 6 dòng (1 overall + 5 per-slot)
- In ra màn hình phân bố fallback + bảng metric

**Downstream:**
- `pred_groupmean_withkey.csv` → **WS6** dùng làm baseline chính cho routing
- `metrics_groupmean.csv` → `export_metrics_json.py` + `baseline_comparison_ws04.txt`

---

## 1.2. `linear_regression.py` — Baseline Linear Regression

**Input:**
- File đọc: 4 file từ `workstream03/` (giống trên)
- Tham số: không có
- Biến ngoài: `evaluate_all` từ `common/metrics.py`, `LinearRegression` từ `sklearn.linear_model`

**Processing:**
- Drop 4 cột tham chiếu `edge_id_A-B`, `time_slot_1`, `day_of_week_Fri`, `is_weekend` để khử đa cộng tuyến hoàn hảo
- Fit OLS trên 22 đặc trưng còn lại
- Kiểm tra rank ma trận để xác nhận full rank
- Dự báo trên test
- Đánh giá MAE / RMSE / MSE / MAPE tổng thể + theo từng khung giờ

**Output:**
- `pred_linearreg_raw.csv` — 360 dòng, chỉ có `y_pred`
- `pred_linearreg_withkey.csv` — 360 dòng, có `edge_id, time_slot, day_of_week, y_true, y_pred`
- `metrics_linearreg.csv` — 6 dòng (1 overall + 5 per-slot)
- `coef_linearreg.csv` — 22 dòng hệ số + cột `note`
- In ra màn hình intercept, top 10 hệ số, rank

**Downstream:**
- `pred_linearreg_withkey.csv` → **WS6** dùng làm baseline phụ (đối chiếu nếu cần)

---

## 1.3. `export_metrics_json.py` — Xuất metrics ra common/

**Input:**
- File đọc: `workstream04/metrics_groupmean.csv`, `workstream04/metrics_linearreg.csv`
- Tham số: không có
- Biến ngoài: không

**Processing:**
- Chuyển format CSV → JSON
- Metric overall đặt ở top level
- Metric từng khung giờ đặt trong dict `by_time_slot`

**Output:**
- `common/workstream04_metrics.json` — list 2 object (GroupMean, LinearRegression), mỗi object có MAE/RMSE/MSE/MAPE top level + `n_obs` + `by_time_slot`

**Downstream:**
- **WS5**, **WS6** và các thành viên nhóm đọc số liệu trực tiếp

---

# PHẦN 2: THÔNG TIN BỔ SUNG

## 2.1. Hai mô hình baseline

| # | Mô hình | Mô tả ngắn | Vai trò |
|---|---------|------------|---------|
| 1 | **Group Mean** | Trung bình travel_time theo bộ ba `(edge_id, time_slot, day_of_week)`. Fallback 4 mức. | **Baseline chính** cho routing |
| 2 | **Linear Regression** | Hồi quy OLS trên 22 đặc trưng sau khi drop 4 cột tham chiếu. | Baseline đối chiếu |

Chi tiết lý thuyết, công thức, quy tắc dự báo: xem `baseline_theory.txt`.
Lý do chọn baseline chính: xem `baseline_comparison_ws04.txt`.

---

## 2.2. Danh sách file trong `workstream04/`

### Code

| File | Mục đích |
|------|----------|
| `group_mean.py` | Huấn luyện + dự báo Group Mean (3 features, fallback 4 mức) |
| `linear_regression.py` | Huấn luyện + dự báo Linear Regression (22 features sau drop-first) |
| `export_metrics_json.py` | Chuyển metrics CSV → JSON trong `common/` |

### Predictions

| File | Mục đích | Ai dùng |
|------|----------|---------|
| `pred_groupmean_withkey.csv` | Dự báo Group Mean có key | **WS6** (baseline chính) |
| `pred_linearreg_withkey.csv` | Dự báo Linear Regression có key | WS6 (đối chiếu nếu cần) |
| `pred_groupmean_raw.csv` | Chỉ có `y_pred`, không key | Backup |
| `pred_linearreg_raw.csv` | Chỉ có `y_pred`, không key | Backup |

### Metrics & phân tích

| File | Mục đích |
|------|----------|
| `metrics_groupmean.csv` | Metric Group Mean: 1 overall + 5 per-slot |
| `metrics_linearreg.csv` | Metric Linear Regression: 1 overall + 5 per-slot |
| `coef_linearreg.csv` | 22 hệ số hồi quy sau drop-first |
| `baseline_comparison_ws04.txt` | So sánh 2 baseline + quyết định chọn baseline chính |
| `baseline_theory.txt` | Lý thuyết 2 mô hình: công thức, quy tắc, ưu nhược điểm |

---

## 2.3. Ý nghĩa cột trong các file CSV

### a) `metrics_groupmean.csv` và `metrics_linearreg.csv`

Mỗi file có **6 dòng**: 1 dòng overall (`time_slot = "all"`) + 5 dòng per-slot.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `time_slot` | String/Int | `"all"` cho dòng tổng thể; `1`–`5` cho từng khung giờ |
| `model` | String | `GroupMean` hoặc `LinearRegression` |
| `MAE` | Float | Sai số tuyệt đối trung bình |
| `RMSE` | Float | Căn bậc 2 sai số bình phương trung bình |
| `MSE` | Float | Sai số bình phương trung bình |
| `MAPE_percent` | Float | Sai số phần trăm tuyệt đối trung bình (đơn vị %) |
| `n_obs` | Integer | Số quan sát trong nhóm (72 mỗi slot, 360 overall) |

### b) `coef_linearreg.csv`

22 dòng — mỗi dòng ứng với 1 đặc trưng của Linear Regression sau drop-first.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `feature` | String | Tên đặc trưng (`distance`, `edge_id_*`, `time_slot_*`, `day_of_week_*`) |
| `coef` | Float | Hệ số hồi quy — chênh lệch travel_time so với nhóm tham chiếu |
| `note` | String | Luôn là `coef_vs_reference` |

**Nhóm tham chiếu (đã bị drop):** `edge_id_A-B`, `time_slot_1`, `day_of_week_Fri`, `is_weekend`.

### c) `pred_groupmean_withkey.csv` và `pred_linearreg_withkey.csv`

360 dòng — mỗi dòng ứng với 1 quan sát trong tập test (6 ngày cuối).

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `edge_id` | String | Cạnh (ví dụ `O-A`, `B-D`, ...). 12 giá trị. |
| `time_slot` | Integer | Mã khung giờ (1–5) |
| `day_of_week` | String | Thứ trong tuần (`Mon`, `Tue`, ...) |
| `y_true` | Float | Travel_time thực tế (phút) |
| `y_pred` | Float | Travel_time dự báo (phút) |
| `fallback_level` | String | **Chỉ có trong file Group Mean.** Mức đã dùng: `level1` / `level2` / `level3` / `level4` |

### d) `pred_groupmean_raw.csv` và `pred_linearreg_raw.csv`

360 dòng, 1 cột `y_pred` — đúng thứ tự của `X_test_preprocessed.csv`.
Dùng để backup và đối chiếu.


