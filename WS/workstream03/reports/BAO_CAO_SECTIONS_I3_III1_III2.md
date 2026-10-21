# NỘI DUNG CHÍNH THỨC 3 MỤC BÁO CÁO CỦA LẠI GIA HUY (WORKSTREAM 3)
## ĐỂ DÁN VÀO THẺ "Tiểu luận" TRÊN GOOGLE DOCS CHUNG CỦA NHÓM
**Học phần:** Vận trù học | **Chủ đề:** 5. Mối liên hệ giữa bài toán đường đi ngắn nhất và machine learning / routing hiện đại (Mức độ C)  
**Tác giả:** Lại Gia Huy (MSSV: K24419) – UEL / ĐHQG-HCM

---

### I.3. Phạm vi nghiên cứu

Bài tiểu luận tập trung nghiên cứu bài toán đường đi ngắn nhất tĩnh và động trong môi trường mạng giao thông, kết nối lý thuyết tối ưu hóa tổ hợp với các mô hình dự báo học máy. Phạm vi nghiên cứu được xác định rõ trên hai không gian mạng lưới:

1. **Không gian mạng cốt lõi (Core Seervada Network):**
   * **Cấu trúc mạng:** Sử dụng đồ thị vô hướng mạng công viên Seervada (Hillier & Lieberman, 2015), bao gồm 7 đỉnh ($O, A, B, C, D, E, T$) và 12 cạnh kết nối trực tiếp. Nút nguồn được quy ước là $O$ và nút đích là $T$. Mỗi cạnh vô hướng được mở rộng thành hai cung có hướng đối xứng để phục vụ mô hình hóa luồng.
   * **Khung thời gian nghiên cứu:** Dữ liệu thời gian di chuyển được khảo sát trong chu kỳ 30 ngày liên tục, mỗi ngày phân chia thành 5 khung giờ tác nghiệp cố định ($S_1: \text{06:00–08:00}$, $S_2: \text{08:00–10:00}$, $S_3: \text{10:00–12:00}$, $S_4: \text{12:00–14:00}$, $S_5: \text{14:00–16:00}$). Tổng quy mô quan sát là $1.800$ điểm dữ liệu ($30\text{ ngày} \times 5\text{ khung giờ} \times 12\text{ cạnh}$).
   * **Mục tiêu trong không gian cốt lõi:** Xác định đường đi ngắn nhất không ràng buộc bằng thuật toán Dijkstra; kiểm chứng mô hình quy hoạch tuyến tính nguyên 0-1 cho bài toán đường đi ngắn nhất có ràng buộc thời gian (RCSP với $T_{max} = 18\text{ phút}$); huấn luyện các mô hình dự báo thời gian di chuyển baseline (Group Mean, Linear Regression) và so sánh quyết định định tuyến giữa trọng số cố định với trọng số dự báo theo khung giờ.

2. **Không gian mở rộng thực tế (Real-world Expansion - PeMS-Bay Subnetwork):**
   * **Động lực mở rộng:** Theo yêu cầu đánh giá Chủ đề 5 ở **Mức độ C** (yêu cầu tự thu thập, xử lý dữ liệu thực tế và mô hình hóa mở), tập dữ liệu mô phỏng Seervada tuy chuẩn mực về mặt lý thuyết nhưng có quy mô hữu hạn, các biến thiên mang tính giả lập nên chưa đủ độ phức tạp để khai thác trọn vẹn ưu thế của các mô hình học sâu (Deep Neural Networks/MLP).
   * **Mạng lưới cảm biến thực tế:** Nhóm mở rộng nghiên cứu sang hệ thống cảm biến giao thông cao tốc PeMS-Bay do Sở Giao thông Vận tải California (Caltrans) vận hành tại Vùng Vịnh San Francisco. Từ mạng lưới tổng thể 325 trạm cảm biến vòng từ, Workstream 3 trích xuất một **mạng con liên thông mạnh gồm 25 trạm cảm biến và 139 cạnh có hướng**, chiều dài các cung được tính toán chính xác bằng công thức Haversine từ tọa độ GPS thực tế. Mạng con này đóng vai trò làm môi trường kiểm thử mở rộng cho pipeline tiền xử lý dữ liệu nhân quả và đánh giá khả năng tổng quát hóa của bài toán định tuyến động trên dữ liệu thực.

---

### III.1. Dữ liệu

Nghiên cứu sử dụng hệ thống dữ liệu đa tầng, bao gồm cả dữ liệu kinh điển trong vận trù học, dữ liệu chuỗi thời gian mô phỏng và dữ liệu giao thông thực tế:

1. **Mạng Seervada cơ sở (`seervada_network.csv`):**
   * Thể hiện cấu trúc liên kết hình học giữa 7 nút và 12 cạnh của công viên Seervada.
   * Thuộc tính cạnh: Chiều dài khoảng cách cố định ($distance$, đơn vị km), dao động từ $1\text{ km}$ (cạnh $B-E$) đến $7\text{ km}$ (cạnh $D-T$). Đây là trọng số cơ sở cho bài toán tìm đường ngắn nhất truyền thống.

2. **Dữ liệu RCSP dạy học (`seervada_rcsp_teaching.csv`):**
   * Kế thừa cấu trúc mạng Seervada, mỗi cạnh được bổ sung một thuộc tính chi phí tài nguyên cố định: thời gian di chuyển chuẩn hóa ($travel\_time$, đơn vị phút), dao động từ $1\text{ phút}$ đến $6\text{ phút}$.
   * Tệp dữ liệu này được sử dụng làm tham chiếu cho bài toán RCSP với giới hạn thời gian $T_{max} = 18\text{ phút}$, phục vụ việc đối chiếu chéo giữa solver quy hoạch nguyên (PuLP/CBC) và thuật toán duyệt cạn vét cạn 28 đường đi đơn.

3. **Dữ liệu mô phỏng thời gian di chuyển 30 ngày (`seervada_travel_time_SIMULATED.csv`):**
   * Cấu trúc bảng gồm 1.800 dòng và 10 cột: `day` ($1 \rightarrow 30$), `day_of_week` (Mon $\rightarrow$ Sun), `is_weekend` ($0/1$), `time_slot` ($1 \rightarrow 5$), `time_slot_name`, `edge_id` ($u-v$), `node_u`, `node_v`, `distance`, và biến mục tiêu `travel_time`.
   * **Bản chất dữ liệu:** Đây là dữ liệu được mô phỏng có định hướng phục vụ kiểm chứng phương pháp (không phải dữ liệu đo đạc thực địa). Giá trị thời gian di chuyển được sinh ra dựa trên chiều dài cạnh, vận tốc cơ sở, cộng thêm hệ số tắc nghẽn đặc trưng cho từng khung giờ cao điểm (Slot 2 và Slot 5) và thành phần nhiễu ngẫu nhiên tuân theo phân phối chuẩn.
   * **Kết quả phân tích khám phá (EDA):**
     * Biến mục tiêu `travel_time` (phút) có giá trị nhỏ nhất $\min = 1.17$, lớn nhất $\max = 20.00$, trung bình $\mu = 6.33$, trung vị $\text{median} = 5.86$, độ lệch chuẩn $\sigma = 2.76$.
     * Hệ số bất đối xứng $\text{skewness} = 0.98$ (phân phối lệch phải nhẹ), phản ánh chính xác quy luật giao thông: thời gian di chuyển tập trung ở mức thông thoáng và kéo dài khi xảy ra ùn ứ vào các khung giờ cao điểm.
     * Tập dữ liệu đạt độ tin cậy tuyệt đối: **0 giá trị khuyết thiếu (missing = 0)**, **0 bản ghi trùng lặp (duplicate = 0)**, và mọi giá trị $travel\_time > 0$.

4. **Dữ liệu mở rộng huấn luyện Neural Network (`seervada_travel_time_EXTENDED_NN.csv`):**
   * Nhóm xây dựng thêm phiên bản mở rộng 90 ngày quan sát ($90 \times 5 \times 12 = 5.400\text{ dòng}$) với các quy luật biến thiên phi tuyến và tương tác đa biến phức tạp hơn, bảo đảm cỡ mẫu đủ lớn cho mô hình mạng nơ-ron (MLP) hội tụ ổn định và tránh hiện tượng ghi nhớ dữ liệu (memorization/overfitting).

5. **Dữ liệu thực tế PeMS-Bay Subnetwork (`pems_subnetwork_nodes.csv` và `edges.csv`):**
   * Trích xuất từ kho dữ liệu Caltrans PeMS tại Vùng Vịnh California, gồm 25 trạm quan sát và 139 cạnh liên thông. Tọa độ địa lý WGS84 được chuẩn hóa, khoảng cách các cạnh được tính bằng công thức Haversine với giá trị trung bình $2.45\text{ km}$, cung cấp nền tảng mạng lưới thực tế cho các thử nghiệm mở rộng.

---

### III.2. Tiền xử lý và xây dựng dữ liệu dự báo

Để bảo đảm tính khách quan khoa học và ngăn chặn triệt để hiện tượng sai lệch dự báo, toàn bộ quy trình tiền xử lý được thiết kế tuân thủ nghiêm ngặt nguyên tắc nhân quả trong kỹ thuật dữ liệu:

#### 1. Cơ chế phân chia dữ liệu tuần tự theo thời gian (Temporal Split - Zero Data Leakage)
* **Nguyên tắc cốt lõi:** Tuyệt đối không áp dụng kỹ thuật xáo trộn ngẫu nhiên (random shuffle) hay phân chia chéo ngẫu nhiên ($K$-Fold Cross Validation). Trong bài toán chuỗi thời gian giao thông, xáo trộn ngẫu nhiên sẽ khiến thông tin của các thời điểm tương lai bị rò rỉ vào quá trình học của quá khứ (Data Leakage), dẫn đến các chỉ số đánh giá ảo.
* **Quy hoạch phân chia:** Tập dữ liệu 30 ngày được phân chia tuần tự dọc theo trục thời gian tuyệt đối theo tỷ lệ chuẩn $80/20$:
  * **Tập Huấn luyện (Train set):** Gồm toàn bộ dữ liệu từ **Ngày 1 đến Ngày 24** ($24\text{ ngày} \times 5\text{ slot} \times 12\text{ cạnh} = 1.440\text{ quan sát}$, chiếm $80\%$).
  * **Tập Kiểm tra (Test set):** Gồm toàn bộ dữ liệu từ **Ngày 25 đến Ngày 30** ($6\text{ ngày} \times 5\text{ slot} \times 12\text{ cạnh} = 360\text{ quan sát}$, chiếm $20\%$).
* **Cam kết toàn vẹn:** Mọi giá trị thời gian của tập Test đều thỏa mãn điều kiện $T_{test} \ge 25 > T_{train} \le 24$. Không tồn tại sự giao thoa thời gian giữa hai tập.

#### 2. Kỹ thuật thiết kế đặc trưng (Feature Engineering - Không gian 26 chiều)
Từ các biến ban đầu, hệ thống kiến tạo một không gian đặc trưng toàn diện gồm 26 biến số phục vụ huấn luyện:
* **Chuẩn hóa khoảng cách (Distance Standardization):** Khoảng cách $distance$ được chuẩn hóa theo phương pháp Z-score:
  $$z = \frac{x - \mu_{\text{train}}}{\sigma_{\text{train}}}$$
  Trong đó, giá trị trung bình $\mu_{\text{train}} = 6.357$ và độ lệch chuẩn $\sigma_{\text{train}} = 2.766$ ($\text{ddof} = 0$) **chỉ được tính toán duy nhất trên tập Train**, sau đó đóng băng và áp dụng để biến đổi (transform) cho tập Test. Tuyệt đối không cập nhật lại scaler trên tập Test.
* **Mã hóa không gian (Spatial Encoding):** Áp dụng One-hot encoding cho 12 liên kết cạnh mạng (`edge_id_O-A`, `edge_id_O-B`, ..., `edge_id_E-T`), giúp mô hình nắm bắt được độ cản trở cơ sở riêng biệt của từng cung đường.
* **Mã hóa thời gian phân loại (Temporal One-Hot):** Mã hóa 5 khung giờ (`time_slot_1` đến `time_slot_5`) và 7 ngày trong tuần (`day_of_week_Mon` đến `Sun`), nắm bắt sự khác biệt giữa giờ cao điểm/thấp điểm và ngày làm việc/ngày nghỉ.
* **Mã hóa chu kỳ liên tục (Cyclical Trigonometric Features):** Nhằm bảo toàn tính chất tuần hoàn liên tục của thời gian (ví dụ: khung giờ cuối ngày tiếp nối với đầu ngày hôm sau, Chủ nhật tiếp nối với Thứ hai), nhóm biến đổi thời gian sang tọa độ góc hai chiều:
  $$\text{sin\_slot} = \sin\left(\frac{2\pi \cdot slot}{5}\right), \quad \text{cos\_slot} = \cos\left(\frac{2\pi \cdot slot}{5}\right)$$
  $$\text{sin\_dow} = \sin\left(\frac{2\pi \cdot dow}{7}\right), \quad \text{cos\_dow} = \cos\left(\frac{2\pi \cdot dow}{7}\right)$$
* **Đặc trưng bổ trợ:** Cột nhị phân `is_weekend` nhận giá trị 1 cho Thứ bảy và Chủ nhật, 0 cho các ngày còn lại.

#### 3. Xử lý triệt để hiện tượng Đa cộng tuyến hoàn hảo (Multicollinearity & Drop-first)
* Khi biểu diễn đầy đủ biến One-hot cho cả 3 nhóm phân loại (12 cạnh, 5 slot, 7 thứ), tổng các cột trong mỗi nhóm luôn bằng 1 ở mọi hàng quan sát. Đồng thời, cột `is_weekend` bằng tổng của `day_of_week_Sat` và `day_of_week_Sun`. Hiện tượng này làm ma trận hiệp phương sai không khả nghịch, khiến các hệ số hồi quy của mô hình Linear Regression (WS4) không thể xác định duy nhất.
* Để khắc phục, pipeline cung cấp chế độ **Drop-first**: Loại bỏ 4 cột cơ sở gồm `edge_id_A-B` (cạnh tham chiếu), `time_slot_1` (khung giờ tham chiếu), `day_of_week_Fri` (ngày tham chiếu) và `is_weekend` (cột dư thừa). Ma trận thu gọn đạt đúng **hạng đầy đủ 22** ($\text{rank}(X) = 22$), bảo đảm nghiệm OLS của Linear Regression xác định duy nhất và diễn giải được hệ số góc một cách tường minh.

#### 4. Đóng gói sản phẩm bàn giao (Artifacts Contract)
Toàn bộ dữ liệu tiền xử lý được cố định thành các tệp chuẩn hóa bàn giao cho các Workstream phía sau:
* `train.csv` ($1.440\text{ dòng}$) và `test.csv` ($360\text{ dòng}$): Dữ liệu quan sát dạng bảng đầy đủ dùng cho Group Mean (WS4).
* `X_train_preprocessed.csv` ($1.440 \times 26$) và `X_test_preprocessed.csv` ($360 \times 26$): Ma trận đặc trưng số thực chuẩn hóa dùng cho Linear Regression (WS4) và Neural Network (WS5).
* `y_train.csv` ($1.440 \times 1$) và `y_test.csv` ($360 \times 1$): Vector nhãn biến mục tiêu `travel_time`.
* `preprocessing_pipeline.json`: Siêu dữ liệu lưu giữ toàn bộ tham số scaler, thứ tự cột và ánh xạ danh mục, bảo đảm mọi bên thứ ba đều có thể tái lập kết quả một cách độc lập.
* **Kiểm định chất lượng tự động:** Bộ kiểm thử gồm **41 unit tests (Pytest)** kiểm tra độc lập tính toàn vẹn ma trận, kích thước $X/y$, không rò rỉ target và tính khớp nối giao diện với downstream, đạt tỷ lệ vượt qua **$100\%$ ($41/41\text{ PASS}$)**.
