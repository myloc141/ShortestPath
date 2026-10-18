# BIÊN BẢN BÀN GIAO DỮ LIỆU CHUẨN (HANDOFF MANIFEST)
**Người phụ trách:** Lại Gia Huy (Workstream 3: Data Engineering)  
**Dự án:** Nghiên cứu Mối liên hệ giữa Bài toán Đường đi ngắn nhất và Định tuyến Động / Machine Learning  
**Học phần:** Vận trù học | UEL / ĐHQG-HCM  
**Phiên bản Dataset:** `v1.0-seervada-teaching`  
**Git HEAD Commit:** `9c985e1`  
**Thời điểm đóng gói:** 2026-10-12 15:47:00 (UTC+7)  

---

## 1. TỔNG QUAN TẬP DỮ LIỆU BÀN GIAO

| Thuộc tính | Chi tiết kỹ thuật |
| :--- | :--- |
| **Nguồn dữ liệu gốc** | `seervada_travel_time_SIMULATED.csv` (Mô phỏng mạng Seervada Park 12 cạnh, seed = 42). |
| **Tổng số quan sát** | 1.800 dòng (30 ngày $\times$ 5 khung giờ $\times$ 12 cạnh). |
| **Phân chia thời gian (Split)** | Time-series Block Split (Không random shuffle). |
| **Ranh giới Train Set** | Ngày 1 đến Ngày 24 (1.440 dòng, chiếm 80,0% tổng số quan sát). |
| **Ranh giới Test Set** | Ngày 25 đến Ngày 30 (360 dòng, chiếm 20,0% tổng số quan sát). |
| **Bảo toàn thời gian** | $\max(\text{train\_day}) = 24 < \min(\text{test\_day}) = 25$ $\to$ **Zero Data Leakage**. |
| **Kích thước Ma trận X** | `X_train`: $(1.440 \times 26)$ \| `X_test`: $(360 \times 26)$. |
| **Kích thước Vector Nhãn y** | `y_train`: $(1.440 \times 1)$ \| `y_test`: $(360 \times 1)$. |
| **Biến mục tiêu (Target)** | `travel_time` (Đơn vị: **phút**). |
| **Quy tắc Chuẩn hóa (Scaler)** | Z-score chuẩn hóa cự ly: $z = \frac{x - \mu}{\sigma}$ với $\mu = 3.75$, $\sigma = 1.963885...$ (mẫu $ddof=1$). Fit **DUY NHẤT** trên Train. |
| **Quy tắc Mã hóa (Encoder)** | One-Hot Encoding cho `edge_id` (12), `time_slot` (5), `day_of_week` (7). Fit **DUY NHẤT** trên Train. |
| **Số chiều đặc trưng (Features)** | **26 đặc trưng** (1 scaled distance, 1 binary is_weekend, 24 one-hot columns). |

---

## 2. DANH SÁCH 26 ĐẶC TRƯNG CHUẨN (EXACT FEATURE ORDER)

Thứ tự 26 cột bắt buộc phải được giữ nguyên vẹn trong toàn bộ các mô hình dự báo của WS4 và WS5:

1. `distance` (Numerical: Z-score scaled, $\mu=3.75, s=1.963885$)
2. `is_weekend` (Binary: 0.0 hoặc 1.0)
3. `edge_id_A-B`
4. `edge_id_A-D`
5. `edge_id_B-C`
6. `edge_id_B-D`
7. `edge_id_B-E`
8. `edge_id_C-E`
9. `edge_id_D-E`
10. `edge_id_D-T`
11. `edge_id_E-T`
12. `edge_id_O-A`
13. `edge_id_O-B`
14. `edge_id_O-C`
15. `time_slot_1` (06:00–08:00)
16. `time_slot_2` (08:00–10:00 - Cao điểm sáng)
17. `time_slot_3` (11:30–13:30 - Trưa)
18. `time_slot_4` (16:30–18:30 - Cao điểm chiều)
19. `time_slot_5` (19:30–21:30 - Tối)
20. `day_of_week_Fri`
21. `day_of_week_Mon`
22. `day_of_week_Sat`
23. `day_of_week_Sun`
24. `day_of_week_Thu`
25. `day_of_week_Tue`
26. `day_of_week_Wed`

---

## 3. BẢNG MÃ HÓA BẢO MẬT & HASH TOÀN VẸN (SHA-256 CHECKSUMS)

Tất cả các thành viên phải đối chiếu mã hash trước khi nạp dữ liệu vào mô hình:

| Tên Artifact | Vị trí phân phối | SHA-256 Checksum | Đơn vị tiếp nhận |
| :--- | :--- | :--- | :--- |
| `train.csv` | `workstream03/` & `data/processed/` | `25cbf4050e916280bdcbd298e1cb8fe81a0776991c115d485efe53b12bf5bd21` | WS4, WS5 |
| `test.csv` | `workstream03/` & `data/processed/` | `460da2f86a3e8ea0c395da2f2214e4dc3a0ee893471940754046c756658e97df` | WS4, WS5, WS6 |
| `X_train_preprocessed.csv` | `workstream03/` & `data/processed/` | `4f42865e1e8f26b991dbfd3b786a4b829adfa2cc8bf86ca93a3fb427e471b24e` | WS4, WS5 |
| `X_test_preprocessed.csv` | `workstream03/` & `data/processed/` | `181c0544eb2c0518022772de00ec79bb9368afe68b3d3e7ef6153ef11be5e5e2` | WS4, WS5 |
| `y_train.csv` | `workstream03/` & `data/processed/` | `ad8f5dc7ba16af7cac7f2c147f7dc4a3e4d9bf01eaea986b7fd8af55a971aac9` | WS4, WS5 |
| `y_test.csv` | `workstream03/` & `data/processed/` | `c3fab4791e1e7d127cc1c22bf78e9a601c8eff422c07184e8125457018e24b85` | WS4, WS5, WS6 |
| `preprocessing_pipeline.json`| `workstream03/` & `data/processed/` | `9420f3e79c3161a6424d94d193e46c5e4294b3892f9ba95d62799d85a54f9fd9` | WS4, WS5 |
| `seervada_network.csv` | `workstream03/` & `data/raw/` | `0afa87aa1a2189054848b008e7fd0b5c40e1b86b7867379afbc526ae6c3e3d17` | WS1, WS6 |
| `seervada_rcsp_teaching.csv`| `workstream03/` & `data/raw/` | `c3c864a0a1f39d7613ec34f18bcb288167622f74961e8275dc52d402e4cd6830` | WS2 |
| `seervada_travel_time_SIMULATED.csv`| `workstream03/` & `data/raw/` | `19c1391ec53141069136657597e9557bbad33c4e716c0ca6cbf91d50f936c501` | WS3 (Core) |
| `seervada_travel_time_EXTENDED_NN.csv`| `workstream03/` & `data/raw/` | `2927b836f5fd86c3127aaa4fcca422df2af2afc492f26d8a46dee1c846202e91` | WS5 (NN scale-up) |

---

## 4. HỢP ĐỒNG BÀN GIAO CHI TIẾT THEO WORKSTREAM

### 4.1. Hợp đồng bàn giao WS4 (Hà Minh - Baselines)
- **Tài nguyên tiếp nhận:**
  + Huấn luyện Group Mean: Đọc `train.csv`, tính trung bình theo `(edge_id, time_slot, is_weekend)` hoặc `(edge_id, time_slot, day_of_week)`. Dự báo trên `test.csv`.
  + Huấn luyện Linear Regression: Đọc trực tiếp `X_train_preprocessed.csv` và `y_train.csv` (1.440 dòng). Dự báo trên `X_test_preprocessed.csv` (360 dòng).
- **Quy tắc đánh giá:** Bắt buộc import hàm đánh giá từ `common/metrics.py`:
  ```python
  from common.metrics import evaluate_all
  metrics = evaluate_all(y_test, y_pred)
  ```
- **Cảnh báo Data Leakage:** WS4 tuyệt đối không tự ý fit lại scaler hoặc one-hot encoder trên tập Test. Sử dụng ma trận đã tiền xử lý từ WS3 để đảm bảo tính nhất quán 100%.

### 4.2. Hợp đồng bàn giao WS5 (Yến Nhi - Neural Network)
- **Tài nguyên tiếp nhận:**
  + Ma trận đầu vào: `X_train_preprocessed.csv` (1.440 x 26) và `y_train.csv` (1.440 x 1).
  + Tầng Input của MLP: Cố định đúng **26 neurons**.
  + Tập đánh giá cuối cùng: `X_test_preprocessed.csv` và `y_test.csv` (360 dòng).
- **Khuyến nghị về Validation Split và Early Stopping:**
  + **NGHIÊM CẤM:** Không được sử dụng Test Set làm tập Validation để kích hoạt Early Stopping (đây là lỗi rò rỉ dữ liệu học thuật nghiêm trọng - Data Leakage).
  + **KHUYẾN NGHỊ CHUẨN:** Nếu MLP cần Validation Set để theo dõi loss và dừng sớm:
    - Trích xuất Validation Set từ phần cuối của Train Set theo thời gian (ví dụ: Train = Ngày 1–20 (1.200 dòng), Validation = Ngày 21–24 (240 dòng)).
    - Hoặc sử dụng bộ dữ liệu mở rộng 5.400 dòng (`seervada_travel_time_EXTENDED_NN.csv`) do WS3 đã chuẩn bị sẵn để có dung lượng mẫu dồi dào hơn cho Deep Learning.

### 4.3. Hợp đồng bàn giao WS6 (Mỹ Lộc - Routing Experiment)
- **Quy trình định tuyến động:**
  $$\text{Predicted Edge Travel Time} \xrightarrow{\text{Routing Algorithm (Dijkstra/MILP)}} \text{Selected Route} \xrightarrow{\text{Evaluation}} \text{Actual Test Travel Time}$$
- **Quy tắc cốt lõi:**
  + Giá trị dự báo $\hat{y}$ từ WS4/WS5 chỉ dùng làm trọng số để tìm tuyến đường tốt nhất.
  + Chất lượng của tuyến đường được chọn **phải được tính bằng tổng `travel_time` thực tế trên `test.csv`** (Ground Truth). Tuyệt đối không dùng giá trị dự báo để tự đánh giá chất lượng tuyến.
- **Khóa kết nối (Join Keys):**
  + Khi ghép nối bảng trọng số dự báo với mạng: sử dụng khóa kết hợp `edge_id` và `time_slot` (hoặc `time_slot_name`).
