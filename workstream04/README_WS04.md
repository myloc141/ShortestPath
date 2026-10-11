# Workstream 4: Prediction Baselines

Xây dựng hai mô hình dự báo thời gian di chuyển (travel_time) trên mạng Seervada
Park để làm baseline cho Workstream 6 (Routing).

- **Dữ liệu đầu vào**: `workstream03/X_train_preprocessed.csv`, `X_test_preprocessed.csv`, `y_train.csv`, `y_test.csv` (chỉ đọc, không sửa)

---

## 1. Hai mô hình baseline

| # | Mô hình | Mô tả ngắn | Vai trò |
|---|---------|------------|---------|
| 1 | **Group Mean** | Trung bình travel_time theo cặp (edge_id, time_slot). Có fallback 3 mức khi gặp cặp chưa từng thấy. | **Baseline chính** cho routing |
| 2 | **Linear Regression** | Hồi quy tuyến tính OLS trên 22 đặc trưng sau khi drop 4 cột tham chiếu (khử đa cộng tuyến hoàn hảo). | Baseline phụ để đối chiếu |

Chi tiết lý thuyết, công thức, quy tắc dự báo: xem `baseline_theory.txt`.
Lý do chọn baseline chính: xem `baseline_comparison_ws04.txt`.

---

## 2. Danh sách file

### Code 

| File | Mục đích |
|------|----------|
| `group_mean.py` | Huấn luyện + dự báo Group Mean. Xuất 3 file: 2 predictions + 1 metric. |
| `linear_regression.py` | Huấn luyện + dự báo Linear Regression (drop-first). Xuất 4 file: 2 predictions + 1 metric + 1 bảng hệ số. |
| `export_metrics_json.py` | Đọc 2 file metric CSV → ghi `common/workstream04_metrics.json`. |

### Predictions

| File | Mục đích |
|------|----------|
| `pred_groupmean_withkey.csv` | Dự báo Group Mean có key (edge_id, time_slot) |
| `pred_linearreg_withkey.csv` | Dự báo Linear Regression có key |
| `pred_groupmean_raw.csv` | Chỉ có cột `y_pred`, không có key |
| `pred_linearreg_raw.csv` | Chỉ có cột `y_pred`, không có key |

### Dữ liệu — Metrics & phân tích

| File | Mục đích |
|------|----------|
| `metrics_groupmean.csv` | 4 chỉ số đánh giá của Group Mean |
| `metrics_linearreg.csv` | 4 chỉ số đánh giá của Linear Regression |
| `coef_linearreg.csv` | 22 hệ số hồi quy sau drop-first, sắp xếp theo coef giảm dần |
| `baseline_comparison_ws04.txt` | Bảng so sánh, quyết định chọn baseline chính|
| `baseline_theory.txt` | Lý thuyết 2 mô hình: công thức, quy tắc, ưu nhược điểm |

---

## 3. Ý nghĩa cột trong các file CSV

### a/ `metrics_groupmean.csv` và `metrics_linearreg.csv`

Mỗi file có 1 dòng dữ liệu — 4 chỉ số đánh giá trên tập test (360 dòng).

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `model` | String | Tên mô hình (`GroupMean` hoặc `LinearRegression`) |
| `MAE` | Float | Sai số tuyệt đối trung bình (Mean Absolute Error) |
| `RMSE` | Float | Căn bậc hai sai số bình phương trung bình (Root Mean Squared Error) |
| `MSE` | Float | Sai số bình phương trung bình (Mean Squared Error) |
| `MAPE_percent` | Float | Sai số phần trăm tuyệt đối trung bình (đơn vị %) |

### b/ `coef_linearreg.csv`

22 dòng — mỗi dòng ứng với 1 đặc trưng của Linear Regression sau drop-first.

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `feature` | String | Tên đặc trưng (`distance`, `edge_id_*`, `time_slot_*`, `day_of_week_*`) |
| `coef` | Float | Hệ số hồi quy — chênh lệch travel_time so với nhóm tham chiếu |
| `note` | String | Luôn là `coef_vs_reference` — nhắc rằng hệ số đọc theo nghĩa "so với reference" |

**Nhóm tham chiếu** (đã bị drop khỏi mô hình): `edge_id_A-B`, `time_slot_1`, `day_of_week_Fri`, `is_weekend`.

### c/ `pred_groupmean_withkey.csv` và `pred_linearreg_withkey.csv`

360 dòng — mỗi dòng ứng với 1 quan sát trong tập test (6 ngày cuối).

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| `edge_id` | String | Cạnh (ví dụ `O-A`, `B-D`, ...). 12 giá trị. |
| `time_slot` | Integer | Mã khung giờ (1–5). |
| `day_of_week` | String | Thứ trong tuần (`Mon`, `Tue`, ...). |
| `y_true` | Float | Travel_time thực tế (phút) |
| `y_pred` | Float | Travel_time dự báo (phút)  |
| `fallback_level` | String | **Chỉ có trong file Group Mean.** Mức fallback đã dùng: `level1` / `level2` / `level3`. |

### d/ `pred_groupmean_raw.csv` và `pred_linearreg_raw.csv`

360 dòng, 1 cột duy nhất `y_pred` (Travel_time dự báo) — đúng thứ tự của `X_test_preprocessed.csv`.
Dùng để backup và đối chiếu, thiếu key.

