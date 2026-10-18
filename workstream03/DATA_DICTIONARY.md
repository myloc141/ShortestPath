# TỪ ĐIỂN DỮ LIỆU TOÀN DIỆN (DATA DICTIONARY)
## Học phần: Vận trù học | Chủ đề 5: Định tuyến Động & Mạng Giao thông
**Sinh viên phụ trách:** Lại Gia Huy (Workstream 3: Data Engineering)  
**Thời điểm cập nhật:** 2026-10-12  

---

## PHẦN A. MẠNG MÔ PHỎNG DẠY HỌC SEERVADA PARK (SIMULATED TEACHING DATASET)

> **Lưu ý phương pháp luận:** Toàn bộ dữ liệu trong Phần A dựa trên mạng đồ thị Seervada Park (Hillier & Lieberman) và chuỗi mô phỏng ngẫu nhiên (chứa định danh `SIMULATED` theo quy chuẩn hướng dẫn của giảng viên tại trang 13, `Topics.pdf`). Đây là dữ liệu dạy học và mô phỏng học thuật, không phải số liệu giao thông thực tế.

---

### 1. Bảng Cấu trúc Mạng Cơ sở (`seervada_network.csv`)
*Nguồn:* Giáo trình *Introduction to Operations Research* (Hillier & Lieberman), Chương Network Optimization Models.

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Description) | Ràng buộc / Miền giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `node_u` | String (Categorical) | N/A | Nút xuất phát của cạnh trong đồ thị Seervada Park. | Tập các nút: $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút kết thúc của cạnh trong đồ thị Seervada Park. | Tập các nút: $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km | Chiều dài vật lý cố định của cung đường nối hai nút $u$ và $v$. | Giá trị nguyên dương: $1 \le distance \le 7$ |
| `directed` | Boolean | N/A | Cờ xác định tính định hướng của cạnh. | `False` (Cạnh vô hướng, lưu thông 2 chiều) |

---

### 2. Bảng Dữ liệu Dạy học RCSP (`seervada_rcsp_teaching.csv`)
*Nguồn:* Chuẩn hóa từ bài toán Đường đi ngắn nhất có ràng buộc tài nguyên (Resource Constrained Shortest Path - RCSP).

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Description) | Ràng buộc / Miền giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `node_u` | String (Categorical) | N/A | Nút xuất phát của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút kết thúc của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km | Trọng số mục tiêu (Hàm mục tiêu: $\min \sum distance$). | $1 \le distance \le 7$ |
| `time` | Integer (Discrete) | phút | Tài nguyên tiêu hao khi đi qua cạnh (Ràng buộc: $\sum time \le T_{max}$). | $2 \le time \le 8$ |
| `directed` | Boolean | N/A | Cờ tính định hướng của cạnh. | `False` |

*Ghi chú kỹ thuật về giới hạn tài nguyên ($T_{max}$):*
- $T_{max} \ge 20$: Tồn tại 2 phương án tối ưu toàn cục không ràng buộc ($O-A-B-D-T$ và $O-A-B-E-D-T$, tổng cự ly = 13 km).
- $T_{max} = 19$: Nghiệm tối ưu duy nhất là $O-A-B-E-D-T$ (cự ly = 13 km, thời gian = 19 phút).
- $T_{max} = 18$: Xuất hiện đánh đổi tối ưu. Tồn tại **3 nghiệm tối ưu cùng đạt cự ly tối thiểu bằng 14 km** (không phải 15 km):
  1. $O \to A \to D \to T$ (Khoảng cách = 14 km, Thời gian = 18 phút)
  2. $O \to B \to E \to D \to T$ (Khoảng cách = 14 km, Thời gian = 18 phút)
  3. $O \to C \to E \to D \to T$ (Khoảng cách = 14 km, Thời gian = 18 phút)
  *(Lưu ý: Tuyến $O-B-E-T$ và $O-C-E-T$ có cự ly 15 km, thời gian 18 phút nên bị thống trị bởi 3 nghiệm 14 km trên).*
- $T_{max} < 18$: Bài toán không khả thi (Infeasible - không tồn tại đường đi đơn nào từ O đến T có tổng thời gian $< 18$ phút).

---

### 3. Bảng Dữ liệu Chuỗi Thời gian Mô phỏng (`seervada_travel_time_SIMULATED.csv`)
*Quy mô:* 1.800 dòng (30 ngày $\times$ 5 khung giờ $\times$ 12 cạnh mạng Seervada).  
*Cơ chế sinh:* Log-Normal multiplicative delay kèm hệ số cao điểm / thấp điểm theo ngày trong tuần và cuối tuần (seed = 42).

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Description) | Ràng buộc / Miền giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `day` | Integer (Discrete) | Ngày | Thứ tự ngày quan sát trong chuỗi dữ liệu liên tục 30 ngày. | $1 \le day \le 30$ |
| `day_of_week` | String (Categorical) | N/A | Tên thứ trong tuần tương ứng với ngày quan sát. | `['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']` |
| `is_weekend` | Integer (Binary) | N/A | Cờ xác định ngày cuối tuần. | `0`: Thứ Hai - Thứ Sáu; `1`: Thứ Bảy, Chủ Nhật |
| `time_slot` | Integer (Categorical) | Mã số | Mã định danh 5 khung giờ di chuyển trong ngày. | $1 \le time\_slot \le 5$ |
| `time_slot_name` | String (Categorical) | Giờ | Chi tiết khoảng thời gian tương ứng của khung giờ. | `06:00-08:00`, `08:00-10:00`, `11:30-13:30`, `16:30-18:30`, `19:30-21:30` |
| `edge_id` | String (Categorical) | N/A | Mã định danh duy nhất của đoạn đường nối giữa hai nút. | 12 cạnh: `O-A`, `O-B`, `O-C`, `A-B`, `A-D`, `B-C`, `B-D`, `B-E`, `C-E`, `D-E`, `D-T`, `E-T` |
| `node_u` | String (Categorical) | N/A | Nút xuất phát của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút đến của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km | Chiều dài vật lý của đoạn đường (tính chất mạng tĩnh). | $1 \le distance \le 7$ |
| `travel_time` | Float (Continuous) | Phút | **Biến mục tiêu (Target Variable):** Thời gian di chuyển thực tế trên cạnh tại ngày và khung giờ tương ứng. | $travel\_time > 0$, phân phối lệch phải (Min: 1.39, Mean: 6.50, Max: 21.67) |

---

### 4. Bảng Phân chia Tập dữ liệu Seervada (Train / Test Split)

| Tập dữ liệu | Phạm vi thời gian | Số quan sát | Tỷ lệ | Mục đích sử dụng |
| :--- | :--- | :--- | :--- | :--- |
| `train.csv` | Ngày 1 đến Ngày 24 | 1.440 dòng | 80,0% | Huấn luyện mô hình Group Mean, Linear Regression (WS4) và MLP (WS5). |
| `test.csv` | Ngày 25 đến Ngày 30 | 360 dòng | 20,0% | Đánh giá sai số dự báo (WS4/WS5) và cung cấp ground truth cho định tuyến động (WS6). |

---

### 5. Ma trận Đặc trưng Tiền xử lý (26 Features)

| Nhóm đặc trưng | Tên cột trong ma trận X | Kiểu dữ liệu | Quy tắc tiền xử lý (Preprocessing Policy) |
| :--- | :--- | :--- | :--- |
| **Cự ly vật lý** | `distance` | Float | Z-score chuẩn hóa: $z = \frac{x - 3.75}{1.963885...}$ (Fit duy nhất trên Train). |
| **Cuối tuần** | `is_weekend` | Float | Giữ nguyên cờ nhị phân (0.0 hoặc 1.0). |
| **Đoạn đường** | `edge_id_A-B` ... `edge_id_O-C` (12 cột) | Float | One-Hot Encoding 12 cạnh. Fit duy nhất trên Train. Tổng mỗi hàng = 1.0. |
| **Khung giờ** | `time_slot_1` ... `time_slot_5` (5 cột) | Float | One-Hot Encoding 5 khung giờ. Fit duy nhất trên Train. Tổng mỗi hàng = 1.0. |
| **Thứ trong tuần** | `day_of_week_Fri` ... `day_of_week_Wed` (7 cột) | Float | One-Hot Encoding 7 thứ. Fit duy nhất trên Train. Tổng mỗi hàng = 1.0. |

---

## PHẦN B. BỘ DỮ LIỆU THỰC TẾ PEMS-BAY (REAL-WORLD TRAFFIC DATASET)

> **Mô tả nguồn gốc:** Bộ dữ liệu PeMS-BAY thu thập từ Hệ thống Đo lường Hiệu năng Giao thông California (Caltrans Performance Measurement System - PeMS) tại khu vực Vịnh San Francisco (Bay Area). Đây là dữ liệu đo lường thực tế từ các trạm cảm biến vòng từ (loop detectors). Dữ liệu phản ánh tình trạng tắc nghẽn thật của hệ thống xa lộ California.

---

### 1. Bảng Dữ liệu Chuỗi Thời gian Tốc độ Gốc (`pems-bay.h5`)
*Nguồn gốc:* Caltrans PeMS, được đóng gói chuẩn bởi Li et al. (DCRNN, ICLR 2018).

| Tên trường (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Nguồn thu thập (Source) | Quy trình chuyển đổi (Transformation) | Miền giá trị hợp lệ (Valid Range) | Chính sách xử lý dữ liệu khuyết (Missing Policy) | Vai trò trong mô hình hóa (Modeling Role) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `timestamp` | Datetime (Index) | YYYY-MM-DD HH:MM:SS | Bản ghi thời gian PeMS | Đồng bộ lưới 5 phút chuẩn bằng `pd.date_range` | Chuỗi thời gian liên tục | Giữ nguyên mốc thời gian, tạo bản ghi NaN để nội suy | Trục tọa độ thời gian (Temporal Coordinate) |
| `sensor_<id>` (Cột cảm biến) | Float | dặm/giờ (mph) | Trạm cảm biến vòng từ PeMS | Giữ nguyên gốc, kiểm tra âm và bằng 0 | $0 < v \le 100$ mph | Giá trị 0 hoặc NaN được nội suy nhân quả (Forward-Fill nội bộ từng tập) | Dữ liệu đo tốc độ điểm (Point Speed Measurement) |

---

### 2. Bảng Danh sách Cạnh Mạng con Bàn giao từ WS1 (`pems_bay_subnetwork_edges.csv`)
*Nguồn gốc:* Workstream 1 (Kiều Ny) trích xuất từ mạng kề và tọa độ trạm cảm biến (`adj_mx_bay.pkl`, `graph_sensor_locations_bay.csv`).

| Tên trường (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Nguồn thu thập (Source) | Quy trình chuyển đổi (Transformation) | Miền giá trị hợp lệ (Valid Range) | Chính sách xử lý dữ liệu khuyết (Missing Policy) | Vai trò trong mô hình hóa (Modeling Role) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `edge_id` | String | Định danh | WS1 sinh | Chuẩn hóa string, định danh duy nhất cho từng cung | Chuỗi không trùng lặp | Bắt buộc phải có, không được thiếu | Khóa định danh cạnh (Edge Primary Key) |
| `sensor_u` | String | Mã trạm | WS1 trích xuất | Chuẩn hóa chuỗi số | Phải thuộc tập cảm biến trong HDF5 | Không được khuyết; ném lỗi nếu thiếu | Nút đầu của cung đường (Head Node) |
| `sensor_v` | String | Mã trạm | WS1 trích xuất | Chuẩn hóa chuỗi số | Phải thuộc tập cảm biến trong HDF5 | Không được khuyết; ném lỗi nếu thiếu | Nút cuối của cung đường (Tail Node) |
| `distance_miles` | Float | dặm (miles) | Tính từ tọa độ Haversine | $d > 0$ | $d > 0$ | Bắt buộc $>0$; ném lỗi nếu $\le 0$ | Cự ly vật lý của đoạn đường (Physical Distance) |

---

### 3. Bảng Dữ liệu Gom cụm Khung giờ PeMS-BAY (`train.csv`, `validation.csv`, `test.csv`)
*Cấu trúc:* Bàn giao cho WS4, WS5, WS6 để huấn luyện và định tuyến động.

| Tên trường (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Nguồn thu thập (Source) | Quy trình chuyển đổi (Transformation) | Miền giá trị hợp lệ (Valid Range) | Chính sách xử lý dữ liệu khuyết (Missing Policy) | Vai trò trong mô hình hóa (Modeling Role) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `date` | String | YYYY-MM-DD | Lấy từ timestamp | Tách phần ngày | Ngày lịch hợp lệ | Không khuyết | Khóa định danh ngày (Date Key) |
| `day_of_week` | String | Tên thứ | Lấy từ timestamp | Thứ trong tuần `['Mon', ..., 'Sun']` | 7 giá trị thứ | Không khuyết | Biến phân loại chu kỳ tuần (Weekly Feature) |
| `is_weekend` | Integer | Nhị phân | Tính từ thứ | 1 nếu T7, CN; 0 nếu T2–T6 | $\{0, 1\}$ | Không khuyết | Cờ cuối tuần (Weekend Binary Flag) |
| `time_slot` | Integer | Mã số | Thuật toán gom cụm | 5 khung giờ nửa mở $[start, end)$ | $\{1, 2, 3, 4, 5\}$ | Loại bỏ các mốc ngoài 5 khung giờ | Phân loại khung giờ (Time-Slot Feature) |
| `time_slot_name`| String | Khoảng giờ | Thuật toán gom cụm | Tên khung giờ (vd: `08:00-10:00`) | 5 tên khung giờ | Khớp với `time_slot` | Trực quan hóa và báo cáo |
| `edge_id` | String | Định danh | WS1 Edge List | Giữ nguyên mã cạnh | Danh mục cạnh hợp lệ | Không khuyết | Phân loại đoạn đường (Edge Identifier) |
| `distance_miles`| Float | dặm | WS1 Edge List | Giữ nguyên cự ly | $d > 0$ | Không khuyết | Thuộc tính tĩnh của cạnh |
| `mean_speed_mph`| Float | mph | Tính từ cảm biến | $\frac{1}{K}\sum v_{uv}(t)$ | $v > 0$ | Đã được làm sạch | Thuộc tính tham khảo tốc độ |
| `travel_time` | Float | Phút | Tính từ cự ly & tốc độ | $E[t_{uv}(t)] = \frac{1}{K}\sum \frac{d_{uv}}{v_{uv}(t)} \times 60$ | $t > 0$ | Đã qua causal imputation | **Biến mục tiêu (Target Variable)** |

---

## 4. TÓM TẮT QUY TẮC BẢO TOÀN DỮ LIỆU
1. **Zero Data Leakage:** Biên giới thời gian Train, Validation và Test được phân định trước mọi phép biến đổi.
2. **Causal Imputation:** Chỉ sử dụng giá trị quá khứ (`ffill`) để bù đắp giá trị thiếu, tuyệt đối không dùng giá trị tương lai (`bfill` xuyên biên giới).
3. **Scaler & Encoder Isolation:** Toàn bộ tham số Z-score và One-Hot Encoder được học duy nhất trên tập Train; Validation và Test chỉ áp dụng phép biến đổi (`transform`).
