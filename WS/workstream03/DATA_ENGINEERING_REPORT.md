# BÁO CÁO KỸ THUẬT TIỀN XỬ LÝ DỮ LIỆU & ĐẶC TẢ HỆ THỐNG
## WORKSTREAM 3: DATA ENGINEERING & PIPELINE ARCHITECTURE
**Sinh viên phụ trách:** Lại Gia Huy (MSSV: K24419)  
**Học phần:** Vận trù học | **Đề tài:** Mối liên hệ giữa bài toán đường đi ngắn nhất và học máy / định tuyến hiện đại (Chủ đề 5 - Mức độ C)  
**Ngày hoàn thành:** 05/10/2026  

---

### 1. ĐẶT VẤN ĐỀ VÀ MỤC TIÊU CỦA KHÂU KỸ THUẬT DỮ LIỆU

Trong các bài toán tối ưu hóa mạng lưới cổ điển, trọng số trên mỗi cung thường được giả định là hằng số cố định bất biến theo thời gian. Giả định này triệt tiêu hoàn toàn tính ngẫu nhiên và biến động thực tế của hệ thống giao thông đô thị – nơi mà vận tốc lưu thông và thời gian di chuyển chịu chi phối sâu sắc bởi quy luật giờ cao điểm, hành vi di chuyển theo ngày làm việc/cuối tuần và các điểm nghẽn cục bộ.

Khi bước sang giai đoạn định tuyến động (Dynamic Routing), chất lượng của đường đi tối ưu phụ thuộc trực tiếp vào độ tin cậy của mô hình dự báo thời gian di chuyển. Nếu dữ liệu đầu vào bị rò rỉ (data leakage), phân phối bị bóp méo hoặc việc phân chia tập huấn luyện/kiểm thử không nhất quán, toàn bộ các kết luận thực nghiệm ở khâu sau (Workstream 4: Mô hình cơ sở, Workstream 5: Mạng nơ-ron và Workstream 6: So sánh định tuyến) đều sẽ mất đi giá trị khoa học.

Với vai trò là mắt xích huyết mạch ở giai đoạn đầu, Workstream 3 giải quyết 4 bài toán kỹ thuật cốt lõi:
1. **Chuẩn hóa cấu trúc đồ thị cơ sở:** Đồng bộ hóa mạng Seervada Park từ giáo trình Hillier & Lieberman và thiết lập bộ dữ liệu dạy học RCSP có thuộc tính thời gian phục vụ Workstream 2.
2. **Xây dựng bộ dữ liệu mô phỏng chuẩn xác:** Khởi tạo dữ liệu thời gian di chuyển 30 ngày $\times$ 5 khung giờ tuân thủ nghiêm ngặt quy luật phân phối lệch phải (right-skewed distribution) của độ trễ giao thông.
3. **Chiến lược phân chia chống rò rỉ dữ liệu (No-Leakage Time-series Split):** Thiết lập ranh giới phân tách Train/Test nghiêm ngặt theo trục thời gian, đảm bảo mô hình chỉ học từ quá khứ để dự báo tương lai.
4. **Đóng gói Pipeline tiền xử lý hợp nhất:** Thiết kế quy trình trích xuất đặc trưng và chuẩn hóa tham số (fit duy nhất trên tập Train) nhằm tạo ra đầu vào chuẩn hóa đồng bộ cho cả mô hình thống kê truyền thống lẫn mạng học sâu.

---

### 2. CẤU TRÚC ĐỒ THỊ VÀ BỘ DỮ LIỆU RCSP DẠY HỌC

#### 2.1. Đồ thị Seervada Park chuẩn
Mạng lưới Seervada Park gồm tập hợp đỉnh $V = \{O, A, B, C, D, E, T\}$ với đỉnh nguồn là $O$ (Origin) và đích đến là $T$ (Terminal). Tập cạnh $E$ gồm 12 liên kết vô hướng (tương đương 24 cung có hướng). Khoảng cách vật lý cố định $d_{uv}$ dao động từ 1 đến 7 đơn vị. Đường đi ngắn nhất không ràng buộc từ $O$ đến $T$ đạt giá trị tối ưu bằng **13 đơn vị khoảng cách**, với hai nghiệm tối ưu tương đương:
- Tuyến 1: $O \to A \to B \to D \to T$ ($2 + 2 + 4 + 5 = 13$)
- Tuyến 2: $O \to A \to B \to E \to D \to T$ ($2 + 2 + 3 + 1 + 5 = 13$)

#### 2.2. Thiết kế dữ liệu có ràng buộc tài nguyên (`seervada_rcsp_teaching.csv`)
Để tạo điều kiện cho Workstream 2 (Ngọc Hân) triển khai mô hình Quy hoạch tuyến tính nguyên 0–1 (MILP) và phân tích độ nhạy (sensitivity analysis), mỗi cạnh được gán thêm trọng số thời gian tiêu hao $t_{uv}$ dựa trên đặc tính cung đường:
- Cung $B-D$ có cự ly ngắn (4 km) nhưng thời gian di chuyển cao (7 phút) do mô phỏng địa hình đèo dốc hoặc mật độ giao cắt lớn.
- Cung $D-E$ ngắn (1 km) và thông thoáng (2 phút).
- Tuyến đường vòng qua $E$ ($B-E-D$) dài hơn về mặt hình học nhưng thời gian qua $B-E$ chỉ mất 4 phút.

**Ý nghĩa toán học trong phân tích độ nhạy:**
- Khi giới hạn thời gian $T_{max} \ge 20$ phút: Cả hai tuyến tối ưu cự ly (Tuyến 1 và Tuyến 2) đều khả thi.
- Khi siết chặt $T_{max} = 19$ phút: Tuyến 1 ($O-A-B-D-T$, tiêu tốn 20 phút) bị loại; Tuyến 2 ($O-A-B-E-D-T$, tiêu tốn 19 phút) trở thành phương án tối ưu duy nhất mà không làm tăng tổng khoảng cách (vẫn giữ nguyên $d = 13$).
- Khi siết chặt $T_{max} = 18$ phút: Cả hai tuyến ngắn nhất đều vi phạm ràng buộc. Người ra quyết định buộc phải đánh đổi (trade-off), chuyển sang tuyến $O-B-E-T$ hoặc $O-C-E-T$ với tổng cự ly tăng lên 15 km để thỏa mãn trần thời gian 18 phút.
- Khi $T_{max} < 18$ phút: Bài toán rơi vào trạng thái vô nghiệm (Infeasible).

Cơ chế này tạo ra bài toán kiểm thử mẫu mực, giúp nhóm phân tích rõ nét sự đánh đổi giữa hiệu quả chi phí (khoảng cách) và tính khả thi tài nguyên (thời gian).

---

### 3. QUY TRÌNH MÔ PHỎNG VÀ KHÁM PHÁ DỮ LIỆU (EDA)

#### 3.1. Phương pháp luận mô phỏng thời gian di chuyển
Bộ dữ liệu `seervada_travel_time_SIMULATED.csv` được xây dựng cho chuỗi 30 ngày quan sát liên tục, mỗi ngày khảo sát tại 5 khung giờ đại diện:
- **Khung 1 (06:00 – 08:00):** Giai đoạn sáng sớm, đường thông thoáng (Free-flow speed).
- **Khung 2 (08:00 – 10:00):** Giờ cao điểm sáng, áp lực giao thông dồn vào các tuyến trục chính ($O-A, A-B, B-D, D-T$).
- **Khung 3 (11:30 – 13:30):** Giờ trưa, mật độ lưu thông ổn định.
- **Khung 4 (16:30 – 18:30):** Cao điểm chiều tối, mức độ ùn ứ đạt đỉnh điểm toàn mạng lưới.
- **Khung 5 (19:30 – 21:30):** Buổi tối, lưu lượng giảm dần trên trục chính nhưng gia tăng nhẹ tại các cung đường nhánh phục vụ giải trí vào cuối tuần.

Mô hình sinh dữ liệu kết hợp hiệu ứng nhân tử tắc nghẽn (congestion multipliers) và thành phần nhiễu ngẫu nhiên tuân theo phân phối Log-Normal:
$$t_{uv}(d, s) = t_{base}(uv) \times \alpha(s, uv) \times \beta(day\_type, uv) \times \exp(\epsilon), \quad \epsilon \sim \mathcal{N}(0, \sigma^2)$$
Việc sử dụng phân phối Log-Normal thay vì phân phối chuẩn Gauss thông thường đảm bảo hai điều kiện tiên quyết: (1) Thời gian di chuyển luôn mang giá trị dương nghiêm ngặt ($t > 0$); (2) Tái hiện đúng hiện tượng lệch phải trong giao thông: vận tốc hiếm khi tăng đột biến nhưng độ trễ do ùn tắc có thể kéo dài thành đuôi dày về phía giá trị lớn. Quá trình sinh dữ liệu được cố định `seed = 42` để đảm bảo khả năng tái lập 100%.

#### 3.2. Kết quả phân tích thống kê mô tả (Descriptive Statistics)
Trên tổng số 1.800 quan sát (không có bất kỳ ô giá trị khuyết nào), các chỉ số thống kê phản ánh rõ nét tính logic:
- **Biến mục tiêu `travel_time`:**
  - Trung bình (Mean): $6.50$ phút.
  - Độ lệch chuẩn (Std Dev): $3.38$ phút.
  - Trung vị (Median): $5.93$ phút.
  - Khoảng tứ phân vị (IQR): $4.33$ phút ($Q_1 = 3.94$, $Q_3 = 8.27$).
  - Giá trị nhỏ nhất: $1.39$ phút; Giá trị lớn nhất: $21.67$ phút.
  - Hệ số bất đối xứng (Skewness): $+0.94$. Hệ số dương khẳng định phân phối lệch phải rõ nét, phù hợp hoàn hảo với thực nghiệm vận tải.
  - Hệ số nhọn (Kurtosis): $+0.87$.

- **Biến thiên theo khung giờ:**
  - Khung 1 (06:00 – 08:00): Thời gian trung bình toàn mạng là $4.47$ phút.
  - Khung 2 (08:00 – 10:00): Thời gian trung bình tăng vọt lên $7.66$ phút (tăng $71.4\%$ so với giờ thấp điểm).
  - Khung 4 (16:30 – 18:30): Mức độ ùn tắc cao nhất với thời gian trung bình đạt $8.36$ phút (tăng $87.0\%$ so với khung 1, cực đại đơn lẻ lên tới $21.67$ phút trên đoạn $A-D$).

- **Đặc trưng các cung đường nghẽn (Bottlenecks):**
  - Cung $A-D$ (cự ly 7 km): Thời gian trung bình $10.84 \pm 3.63$ phút.
  - Cung $B-D$ (cự ly 4 km): Thời gian trung bình $9.74 \pm 3.13$ phút (vận tốc trung bình chỉ đạt xấp xỉ 24.6 km/h do độ trễ lớn).
  - Cung $E-T$ (cự ly 7 km): Thời gian trung bình $9.96 \pm 2.49$ phút.

---

### 4. CHIẾN LƯỢC PHÂN CHIA TRAIN/TEST CHỐNG RÒ RỈ THỜI GIAN

Một trong những sai lầm phổ biến khi áp dụng học máy vào dữ liệu vận trù là sử dụng phương pháp xáo trộn ngẫu nhiên (`random shuffle`) để chia tập Train/Test. Trong bài toán chuỗi thời gian, việc chia ngẫu nhiên sẽ dẫn tới hiện tượng rò rỉ dữ liệu (Look-ahead Bias / Data Leakage): mô hình lấy thông tin tắc nghẽn của tương lai để học và dự báo cho quá khứ. Điều này làm cho chỉ số đánh giá trên tập test đẹp một cách giả tạo nhưng hoàn toàn thất bại khi triển khai thực tế.

Workstream 3 áp dụng phương pháp **Phân chia khối theo chuỗi thời gian (Time-series Block Split)**:
- **Tập huấn luyện (`train.csv`):** Gồm 24 ngày đầu tiên (Day 1 đến Day 24), tương đương 1.440 quan sát ($80.0\%$). Tập này bao gồm cả ngày làm việc thường nhật (1.080 dòng) lẫn các ngày cuối tuần (360 dòng), phản ánh đầy đủ chu kỳ dao động theo tuần.
- **Tập kiểm thử (`test.csv`):** Gồm 6 ngày cuối cùng (Day 25 đến Day 30), tương đương 360 quan sát ($20.0\%$).
- **Kiểm định tính cân bằng danh mục:** Cả hai tập đều chứa trọn vẹn 100% danh mục 12 cạnh mạng Seervada và đầy đủ 5 khung giờ. Do đó, tập test hoàn toàn độc lập về mặt thời gian nhưng không bị thiếu hụt bất kỳ thực thể không gian nào.

Tập `train.csv` và `test.csv` này được cố định thành chuẩn duy nhất dùng chung cho cả Workstream 4 và Workstream 5.

---

### 5. THIẾT KẾ ĐẶC TRƯNG & PIPELINE TIỀN XỬ LÝ (PREPROCESSING PIPELINE)

Để đảm bảo tính công bằng khi so sánh giữa các mô hình thống kê cơ sở (Linear Regression) và mạng nơ-ron sâu (MLP), pipeline tiền xử lý `SeervadaFeaturePipeline` được thiết kế khép kín:

1. **Chuẩn hóa biến số (Numerical Scaling):**
   - Biến `distance` được chuẩn hóa theo phương pháp Z-score ($z = \frac{x - \mu}{\sigma}$). Giá trị trung bình $\mu$ và độ lệch chuẩn $\sigma$ được tính toán nghiêm ngặt **duy nhất trên 1.440 dòng của tập Train**, sau đó áp dụng cố định để biến đổi cho tập Test.
2. **Mã hóa biến phân loại (Categorical One-Hot Encoding):**
   - `edge_id` (12 cạnh) $\to$ 12 biến nhị phân (`edge_id_A-B`, `edge_id_A-D`,...).
   - `time_slot` (5 khung giờ) $\to$ 5 biến nhị phân (`time_slot_1` đến `time_slot_5`).
   - `day_of_week` (7 ngày) $\to$ 7 biến nhị phân (`day_of_week_Mon`,...).
3. **Biến nhị phân:**
   - `is_weekend` (0 hoặc 1) được giữ nguyên định dạng nhị phân.

**Kết quả đầu ra:** Ma trận đặc trưng $X$ có tổng cộng **26 chiều (26 features)**. Toàn bộ tham số mã hóa và chuẩn hóa được lưu trữ độc lập tại tệp `preprocessing_pipeline.json`. Điều này giúp các thành viên phụ trách mô hình hóa có thể:
- Hoặc sử dụng trực tiếp các file ma trận đã chuẩn hóa sẵn (`X_train_preprocessed.csv`, `y_train.csv`, `X_test_preprocessed.csv`, `y_test.csv`).
- Hoặc đọc `preprocessing_pipeline.json` để tích hợp vào luồng xử lý riêng mà không sợ sai lệch kết quả.

---

### 6. MỞ RỘNG DỮ LIỆU CHO MẠNG NƠ-RON (EXTENDED DATASET)

Theo lý thuyết học máy, các mô hình hồi quy tuyến tính cổ điển có thể đạt điểm bão hòa rất nhanh trên các bộ dữ liệu nhỏ (dưới 2.000 mẫu), trong khi mạng nơ-ron sâu (Neural Network / MLP) đòi hỏi không gian mẫu lớn hơn để tối ưu hóa hàng nghìn trọng số liên kết ($weights$) mà không rơi vào bẫy quá khớp (overfitting).

Nhằm hỗ trợ tốt nhất cho Workstream 5 (Yến Nhi) tạo ra sự đột phá trong tiêu chí "Mở rộng (15%)" của mức độ C, Workstream 3 đã xây dựng thêm tệp dữ liệu mở rộng:
- **Tệp dữ liệu:** `seervada_travel_time_EXTENDED_NN.csv`.
- **Quy mô:** 90 ngày quan sát liên tục $\times$ 5 khung giờ $\times$ 12 cạnh = **5.400 dòng quan sát**.
- **Giá trị học thuật:** Cho phép Yến Nhi thực hiện thí nghiệm so sánh đường cong học tập (Learning Curve) giữa 1.440 mẫu và 5.400 mẫu, từ đó chứng minh luận điểm kinh tế - kỹ thuật: *"Mạng nơ-ron chỉ phát huy ưu thế vượt trội so với mô hình hồi quy tuyến tính khi quy mô dữ liệu giao thông được thu thập đủ dày và kéo dài qua nhiều chu kỳ biến động."*

---

### 7. TỔNG KẾT BÀN GIAO CHO CÁC WORKSTREAM

Toàn bộ gói sản phẩm của Workstream 3 đã được đóng gói hoàn tất và đặt tại thư mục làm việc, bao gồm:
1. `seervada_network.csv`: Mạng Seervada gốc 12 cạnh, cự ly tĩnh.
2. `seervada_rcsp_teaching.csv`: Mạng có thêm thuộc tính thời gian $t_{uv}$ bàn giao cho **Workstream 2 (Ngọc Hân)**.
3. `seervada_travel_time_SIMULATED.csv`: Dữ liệu mô phỏng 30 ngày chuẩn mực.
4. `train.csv` và `test.csv`: Dữ liệu phân chia chuẩn chống rò rỉ thời gian bàn giao cho **Workstream 4 (Hà Minh)** và **Workstream 5 (Yến Nhi)**.
5. `X_train_preprocessed.csv`, `y_train.csv`, `X_test_preprocessed.csv`, `y_test.csv`: Ma trận 26 đặc trưng đã xử lý sẵn.
6. `preprocessing_pipeline.json`: Cấu hình tái lập pipeline 100%.
7. `seervada_travel_time_EXTENDED_NN.csv`: Dữ liệu quy mô lớn 5.400 dòng phục vụ phân tích mở rộng chuyên sâu cho mạng nơ-ron.
8. `DATA_DICTIONARY.md`: Từ điển dữ liệu toàn diện.
