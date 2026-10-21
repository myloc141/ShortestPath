# BÁO CÁO KỸ THUẬT TIỀN XỬ LÝ DỮ LIỆU & ĐẶC TẢ HỆ THỐNG
## WORKSTREAM 3: DATA ENGINEERING & REPRODUCIBILITY AUDIT
**Sinh viên phụ trách:** Lại Gia Huy (MSSV: K24419)  
**Học phần:** Vận trù học | Đại học Kinh tế – Luật (UEL) / ĐHQG-HCM  
**Đề tài:** Mối liên hệ giữa bài toán đường đi ngắn nhất và học máy / định tuyến hiện đại (Chủ đề 5 - Mức độ C)  
**Thời điểm cập nhật hoàn thiện:** 12/10/2026  

---

## 1. ĐẶT VẤN ĐỀ VÀ MỤC TIÊU CỦA KHÂU KỸ THUẬT DỮ LIỆU

Trong các bài toán tối ưu hóa mạng lưới cổ điển, trọng số trên mỗi cung thường được giả định là hằng số cố định bất biến theo thời gian. Giả định này triệt tiêu hoàn toàn tính ngẫu nhiên và biến động thực tế của hệ thống giao thông đô thị – nơi mà vận tốc lưu thông và thời gian di chuyển chịu chi phối sâu sắc bởi quy luật giờ cao điểm, hành vi di chuyển theo ngày làm việc/cuối tuần và các điểm nghẽn cục bộ.

Khi bước sang giai đoạn định tuyến động (Dynamic Routing), chất lượng của đường đi tối ưu phụ thuộc trực tiếp vào độ tin cậy của mô hình dự báo thời gian di chuyển. Nếu dữ liệu đầu vào bị rò rỉ (data leakage), phân phối bị bóp méo hoặc việc phân chia tập huấn luyện/kiểm thử không nhất quán, toàn bộ các kết luận thực nghiệm ở khâu sau (Workstream 4: Mô hình cơ sở, Workstream 5: Mạng nơ-ron và Workstream 6: So sánh định tuyến) đều sẽ mất đi giá trị khoa học.

Với vai trò là mắt xích kỹ thuật nền tảng, Workstream 3 giải quyết 5 bài toán kỹ thuật cốt lõi:
1. **Chuẩn hóa cấu trúc đồ thị cơ sở:** Đồng bộ hóa mạng Seervada Park từ giáo trình Hillier & Lieberman và thiết lập bộ dữ liệu dạy học RCSP có thuộc tính thời gian phục vụ Workstream 2 (Ngọc Hân).
2. **Xây dựng bộ dữ liệu mô phỏng chuẩn xác:** Khởi tạo dữ liệu thời gian di chuyển 30 ngày $\times$ 5 khung giờ tuân thủ nghiêm ngặt quy luật phân phối lệch phải (right-skewed distribution) của độ trễ giao thông.
3. **Chiến lược phân chia chống rò rỉ dữ liệu (Zero Data Leakage Time-series Split):** Thiết lập ranh giới phân tách Train/Test nghiêm ngặt theo trục thời gian, đảm bảo mô hình chỉ học từ quá khứ để dự báo tương lai.
4. **Đóng gói Pipeline tiền xử lý hợp nhất:** Thiết kế quy trình trích xuất đặc trưng và chuẩn hóa tham số (fit duy nhất trên tập Train) nhằm tạo ra đầu vào chuẩn hóa đồng bộ 26 chiều cho cả mô hình thống kê truyền thống lẫn mạng học sâu.
5. **Kiến trúc Pipeline cho dữ liệu thực tế PeMS-BAY:** Xây dựng pipeline chuẩn công nghiệp sẵn sàng xử lý chuỗi thời gian cảm biến thực tế khu vực Vịnh California khi tiếp nhận bàn giao từ WS1.

---

## 2. PHÂN ĐỊNH PHƯƠNG PHÁP LUẬN HỌC THUẬT (SCIENTIFIC TAXONOMY)

Để đảm bảo tính trung thực học thuật và đáp ứng nghiêm ngặt Rubric giảng viên:
- **[FACT]:** Các số liệu, kích thước dòng/cột, tham số thống kê và kết quả đã được mã nguồn Python kiểm chứng và tái lập 100% từ dữ liệu thực tế trong repository.
- **[METHOD]:** Quy trình, thuật toán và giải pháp biến đổi dữ liệu được thiết kế minh bạch.
- **[ASSUMPTION]:** Các giả định kỹ thuật được đặt ra cho mô hình (ví dụ: vận tốc trung bình giữa hai đầu cảm biến làm proxy cho vận tốc cạnh).
- **[LIMITATION]:** Giới hạn phạm vi của mô hình và ranh giới áp dụng trong thực tế.

---

## 3. CẤU TRÚC ĐỒ THỊ VÀ BỘ DỮ LIỆU RCSP DẠY HỌC

### 3.1. Đồ thị Seervada Park chuẩn [FACT]
Mạng lưới Seervada Park gồm tập hợp đỉnh $V = \{O, A, B, C, D, E, T\}$ với đỉnh nguồn là $O$ (Origin) và đích đến là $T$ (Terminal). Tập cạnh $E$ gồm 12 liên kết vô hướng (tương đương 24 cung có hướng). Khoảng cách vật lý cố định $d_{uv}$ dao động từ 1 đến 7 đơn vị. Đường đi ngắn nhất không ràng buộc từ $O$ đến $T$ đạt giá trị tối ưu bằng **13 đơn vị khoảng cách**, với hai nghiệm tối ưu tương đương:
- Tuyến 1: $O \to A \to B \to D \to T$ ($2 + 2 + 4 + 5 = 13$)
- Tuyến 2: $O \to A \to B \to E \to D \to T$ ($2 + 2 + 3 + 1 + 5 = 13$)

### 3.2. Thiết kế dữ liệu có ràng buộc tài nguyên (`seervada_rcsp_teaching.csv`) [METHOD & FACT]
Để tạo điều kiện cho Workstream 2 (Ngọc Hân) triển khai mô hình Quy hoạch tuyến tính nguyên 0–1 (MILP) và phân tích độ nhạy (sensitivity analysis), mỗi cạnh được gán thêm trọng số thời gian tiêu hao $t_{uv}$ dựa trên đặc tính cung đường:
- Cung $B-D$ có cự ly ngắn (4 km) nhưng thời gian di chuyển cao (7 phút) do mô phỏng địa hình đèo dốc hoặc mật độ giao cắt lớn.
- Cung $D-E$ ngắn (1 km) và thông thoáng (2 phút).
- Tuyến đường vòng qua $E$ ($B-E-D$) dài hơn về mặt hình học nhưng thời gian qua $B-E$ chỉ mất 4 phút.

**Hiệu đính toán học chính xác về độ nhạy tài nguyên ($T_{max}$):**
- Khi giới hạn thời gian $T_{max} \ge 20$ phút: Cả hai tuyến tối ưu cự ly (Tuyến 1 và Tuyến 2) đều khả thi ($d=13$).
- Khi siết chặt $T_{max} = 19$ phút: Tuyến 1 ($O-A-B-D-T$, tiêu tốn 20 phút) bị loại; Tuyến 2 ($O-A-B-E-D-T$, tiêu tốn 19 phút) trở thành phương án tối ưu duy nhất mà không làm tăng tổng khoảng cách (vẫn giữ nguyên $d = 13$).
- Khi siết chặt $T_{max} = 18$ phút: Cả hai tuyến ngắn nhất cự ly 13 km đều vi phạm ràng buộc. Người ra quyết định buộc phải đánh đổi (trade-off). Xác minh độc lập bằng Python (duyệt toàn bộ 28 simple paths) chứng minh tồn tại **3 phương án cùng đạt cự ly tối thiểu bằng 14 km** (không phải 15 km):
  1. $O \to A \to D \to T$ (Cự ly: 14 km, Thời gian: 18 phút)
  2. $O \to B \to E \to D \to T$ (Cự ly: 14 km, Thời gian: 18 phút)
  3. $O \to C \to E \to D \to T$ (Cự ly: 14 km, Thời gian: 18 phút)
  *(Ghi chú: Tuyến $O-B-E-T$ và $O-C-E-T$ có cự ly 15 km và thời gian 18 phút, do đó bị thống trị - dominated - bởi 3 nghiệm 14 km nói trên).*
- Khi $T_{max} < 18$ phút: Bài toán rơi vào trạng thái vô nghiệm (Infeasible).

---

## 4. QUY TRÌNH MÔ PHỎNG VÀ KHÁM PHÁ DỮ LIỆU (EDA)

### 4.1. Phương pháp luận mô phỏng thời gian di chuyển [METHOD & ASSUMPTION]
Bộ dữ liệu `seervada_travel_time_SIMULATED.csv` được xây dựng cho chuỗi 30 ngày quan sát liên tục, mỗi ngày khảo sát tại 5 khung giờ đại diện:
- **Khung 1 (06:00 – 08:00):** Sáng sớm, đường thông thoáng (Free-flow speed).
- **Khung 2 (08:00 – 10:00):** Giờ cao điểm sáng, áp lực giao thông dồn vào các tuyến trục chính ($O-A, A-B, B-D, D-T$).
- **Khung 3 (11:30 – 13:30):** Buổi trưa, mật độ lưu thông ổn định.
- **Khung 4 (16:30 – 18:30):** Cao điểm chiều, mức độ ùn ứ đạt đỉnh điểm toàn mạng lưới.
- **Khung 5 (19:30 – 21:30):** Buổi tối, lưu lượng giảm dần trên trục chính nhưng gia tăng nhẹ tại các cung đường nhánh phục vụ giải trí cuối tuần.

Mô hình sinh dữ liệu kết hợp hiệu ứng nhân tử tắc nghẽn (congestion multipliers) và thành phần nhiễu ngẫu nhiên tuân theo phân phối Log-Normal:
$$t_{uv}(d, s) = t_{base}(uv) \times \alpha(s, uv) \times \beta(day\_type, uv) \times \exp(\epsilon), \quad \epsilon \sim \mathcal{N}(0, \sigma^2)$$
[ASSUMPTION]: Phân phối Log-Normal được chọn vì đảm bảo tính dương vật lý ($t > 0$) và tái hiện đặc trưng đuôi dày lệch phải của độ trễ giao thông. Quá trình sinh cố định `seed = 42` (tập 30 ngày) và `seed = 101` (tập 90 ngày) đảm bảo khả năng tái lập 100%.

### 4.2. Kết quả phân tích thống kê mô tả EDA [FACT]
Trên tổng số 1.800 quan sát (không có giá trị khuyết missing):
- **Biến mục tiêu `travel_time`:**
  - Trung bình (Mean): $6.50$ phút.
  - Độ lệch chuẩn (Std Dev): $3.38$ phút.
  - Trung vị (Median): $5.93$ phút.
  - Khoảng tứ phân vị (IQR): $4.33$ phút ($Q_1 = 3.94$, $Q_3 = 8.27$).
  - Giá trị nhỏ nhất: $1.39$ phút; Giá trị lớn nhất: $21.67$ phút.
  - Hệ số bất đối xứng (Skewness): $+0.94$ (lệch phải dương rõ nét).
  - Hệ số nhọn (Kurtosis): $+0.87$.

- **Biến thiên theo khung giờ [FACT]:**
  - Khung 1 (06:00 – 08:00): Thời gian trung bình $4.47$ phút.
  - Khung 2 (08:00 – 10:00): Thời gian trung bình tăng vọt lên $7.66$ phút (tăng $71.4\%$).
  - Khung 4 (16:30 – 18:30): Mức độ ùn tắc cao nhất với thời gian trung bình đạt $8.36$ phút (cực đại đơn lẻ $21.67$ phút trên đoạn $A-D$).

---

## 5. CHIẾN LƯỢC PHÂN CHIA TRAIN/TEST CHỐNG RÒ RỈ THỜI GIAN [METHOD & FACT]

Workstream 3 áp dụng phương pháp **Phân chia khối theo chuỗi thời gian (Time-series Block Split)**:
- **Tập huấn luyện (`train.csv`):** Gồm 24 ngày đầu tiên (Day 1 đến Day 24), tương đương 1.440 quan sát ($80.0\%$).
- **Tập kiểm thử (`test.csv`):** Gồm 6 ngày cuối cùng (Day 25 đến Day 30), tương đương 360 quan sát ($20.0\%$).
- **Kiểm định ranh giới thời gian [FACT]:** $\max(\text{train\_day}) = 24 < \min(\text{test\_day}) = 25$. Tập Train và Test không có bất kỳ mốc thời gian nào bị chồng lấn.
- **Kiểm định tính cân bằng danh mục [FACT]:** Cả hai tập đều chứa trọn vẹn 100% danh mục 12 cạnh mạng Seervada và đầy đủ 5 khung giờ.

---

## 6. THIẾT KẾ ĐẶC TRƯNG & PIPELINE TIỀN XỬ LÝ [METHOD]

Pipeline tiền xử lý `SeervadaFeaturePipeline` được thiết kế khép kín:
1. **Chuẩn hóa biến số (Numerical Scaling):**
   - Biến `distance` được chuẩn hóa theo phương pháp Z-score ($z = \frac{x - \mu}{s}$).
   - Tham số: $\mu = 3.75$, $s = 1.963885...$ (mẫu $ddof=1$). Được tính toán **DUY NHẤT trên 1.440 dòng của tập Train**.
2. **Mã hóa biến phân loại (Categorical One-Hot Encoding):**
   - `edge_id` (12 cạnh) $\to$ 12 biến nhị phân (`edge_id_A-B`, `edge_id_A-D`,...).
   - `time_slot` (5 khung giờ) $\to$ 5 biến nhị phân (`time_slot_1` đến `time_slot_5`).
   - `day_of_week` (7 ngày) $\to$ 7 biến nhị phân (`day_of_week_Mon`,...).
3. **Biến nhị phân:**
   - `is_weekend` (0 hoặc 1) được giữ nguyên định dạng nhị phân.
4. **Kết quả đầu ra:** Ma trận đặc trưng $X$ có tổng cộng **26 chiều (26 features)**, không chứa biến mục tiêu `travel_time`.

---

## 7. MỞ RỘNG DỮ LIỆU CHO MẠNG NƠ-RON (EXTENDED DATASET) [FACT]

- **Tệp dữ liệu:** `seervada_travel_time_EXTENDED_NN.csv`.
- **Quy mô:** 90 ngày quan sát liên tục $\times$ 5 khung giờ $\times$ 12 cạnh = **5.400 dòng quan sát**.
- **Ý nghĩa:** Cung cấp mẫu lớn phục vụ Workstream 5 (Yến Nhi) thử nghiệm MLP, tránh hiện tượng quá khớp do tập dữ liệu nhỏ 1.440 dòng.

---

## 8. THIẾT KẾ PIPELINE DỮ LIỆU THỰC TẾ PEMS-BAY [METHOD, ASSUMPTION & LIMITATION]

Để phục vụ tiêu chí mở rộng 15% và Mức độ C, WS3 đã xây dựng hoàn chỉnh kiến trúc pipeline PeMS-BAY tại `workstream03/src/pems_bay_pipeline.py`.

### 8.1. Hợp đồng cảm biến với Workstream 1 [METHOD]
- Tiếp nhận danh sách cạnh `pems_bay_subnetwork_edges.csv` từ WS1.
- Kiểm tra tính hợp lệ: $\text{set}(sensor_u \cup sensor_v) \subseteq \text{set}(HDF\_sensors)$, $distance > 0$, không self-loop, không trùng lặp. Bất kỳ vi phạm nào đều ném ngoại lệ rõ ràng (`Fail Loudly`).

### 8.2. Giả định mô hình hóa tốc độ cạnh [ASSUMPTION & LIMITATION]
- **[ASSUMPTION]:** Vận tốc trên cạnh được tính bằng proxy trung bình cộng giữa 2 trạm cảm biến đầu và cuối:
  $$v_{uv}(t) = \frac{v_u(t) + v_v(t)}{2}$$
- **[LIMITATION]:** Đây là đại diện ước lượng (modeling proxy), không phải phép đo vật lý trực tiếp liên tục trên toàn bộ chiều dài đoạn đường. Khi khoảng cách giữa 2 trạm cảm biến lớn, sai số ước lượng có thể gia tăng.

### 8.3. Thời gian di chuyển và Gom cụm khung giờ [METHOD]
- Thời gian di chuyển tức thời: $t_{uv}(t) = \frac{d_{uv}}{v_{uv}(t)} \times 60$ (phút).
- Gom cụm theo 5 khung giờ nửa mở $[start, end)$: Áp dụng Policy A - Giá trị kỳ vọng thời gian di chuyển tức thời $E[t_{uv}(t)]$.

### 8.4. Trạng thái thực tế của PeMS-BAY Pipeline [FACT]
- **Pipeline Code:** READY (Hoàn thành 100%, hỗ trợ giao diện dòng lệnh CLI).
- **Mock Unit Tests:** READY (38/38 bài test `pytest` thành công trên synthetic fixture).
- **Raw Data Availability:** File thật `pems-bay.h5` và `pems_bay_subnetwork_edges.csv` hiện **chưa có sẵn trong repository**. WS3 sẵn sàng chạy lệnh thực thi ngay khi nhận file từ WS1.
