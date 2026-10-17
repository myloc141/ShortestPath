# TỪ ĐIỂN DỮ LIỆU (DATA DICTIONARY)
## Học phần: Vận trù học | Chủ đề 5: Định tuyến Động & Mạng Seervada Park
**Người phụ trách:** Lại Gia Huy (Workstream 3: Data Engineering)

---

### 1. Bảng Dữ liệu Cơ sở: Mạng Seervada Park (`seervada_network.csv`)
*Nguồn:* Giáo trình *Introduction to Operations Research* (Hillier & Lieberman), Chương Network Optimization Models.

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Business / Technical Description) | Ràng buộc / Giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `node_u` | String (Categorical) | N/A | Nút bắt đầu của cạnh trong đồ thị Seervada Park. | Tập các nút: $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút kết thúc của cạnh trong đồ thị Seervada Park. | Tập các nút: $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km (hoặc dặm) | Chiều dài vật lý cố định của cung đường nối hai nút $u$ và $v$. | Giá trị dương nguyên: $1 \le distance \le 7$ |
| `directed` | Boolean | N/A | Cờ xác định tính định hướng của cạnh. | `False` (Cạnh vô hướng, phương tiện có thể lưu thông 2 chiều) |

---

### 2. Bảng Dữ liệu Dạy học RCSP (`seervada_rcsp_teaching.csv`)
*Nguồn:* Chuẩn hóa từ bài toán Đường đi ngắn nhất có ràng buộc tài nguyên (Resource Constrained Shortest Path - RCSP).

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Business / Technical Description) | Ràng buộc / Giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `node_u` | String (Categorical) | N/A | Nút bắt đầu của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút kết thúc của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km | Trọng số mục tiêu (Hàm mục tiêu cực tiểu hóa tổng khoảng cách). | $1 \le distance \le 7$ |
| `time` | Integer (Discrete) | phút | Lượng tài nguyên tiêu hao khi đi qua cạnh (Ràng buộc $\sum time \le T_{max}$). | $2 \le time \le 8$ |
| `directed` | Boolean | N/A | Cờ tính định hướng của cạnh. | `False` |

*Ghi chú kỹ thuật về giới hạn tài nguyên ($T_{max}$):*
- $T_{max} \ge 20$: Tồn tại 2 phương án tối ưu toàn cục không ràng buộc ($O-A-B-D-T$ và $O-A-B-E-D-T$, tổng khoảng cách = 13).
- $T_{max} = 19$: Nghiệm tối ưu duy nhất là $O-A-B-E-D-T$ (khoảng cách = 13, thời gian = 19).
- $T_{max} = 18$: Đánh đổi tối ưu, tuyến đường chuyển sang $O-B-E-T$ hoặc $O-C-E-T$ (khoảng cách tăng lên 15, thời gian = 18).
- $T_{max} < 18$: Bài toán không khả thi (Infeasible).

---

### 3. Bảng Dữ liệu Mô phỏng Thời gian Di chuyển (`seervada_travel_time_SIMULATED.csv`)
*Quy mô:* 1.800 dòng (30 ngày $\times$ 5 khung giờ $\times$ 12 cạnh mạng Seervada).  
*Đặc tính:* Dữ liệu mô phỏng theo mô hình giao thông hiện đại (Congestion Multipliers & Log-Normal Delay).

| Tên biến (Field Name) | Kiểu dữ liệu (Data Type) | Đơn vị đo (Unit) | Ý nghĩa nghiệp vụ (Business / Technical Description) | Ràng buộc / Giá trị hợp lệ |
| :--- | :--- | :--- | :--- | :--- |
| `day` | Integer (Discrete) | Ngày | Thứ tự ngày quan sát trong chuỗi dữ liệu 30 ngày liên tục. | $1 \le day \le 30$ |
| `day_of_week` | String (Categorical) | N/A | Tên thứ trong tuần tương ứng với ngày quan sát. | `['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']` |
| `is_weekend` | Integer (Binary) | N/A | Cờ xác định ngày cuối tuần. | `0`: Thứ Hai - Thứ Sáu; `1`: Thứ Bảy, Chủ Nhật |
| `time_slot` | Integer (Categorical) | Mã khung giờ | Mã định danh 5 khung giờ di chuyển trong ngày. | $1 \le time\_slot \le 5$ |
| `time_slot_name` | String (Categorical) | Giờ:Phút | Chi tiết khoảng thời gian tương ứng của khung giờ. | `06:00-08:00`, `08:00-10:00`, `11:30-13:30`, `16:30-18:30`, `19:30-21:30` |
| `edge_id` | String (Categorical) | N/A | Mã định danh duy nhất của đoạn đường nối giữa hai nút. | 12 cạnh: `O-A`, `O-B`, `O-C`, `A-B`, `A-D`, `B-C`, `B-D`, `B-E`, `C-E`, `D-E`, `D-T`, `E-T` |
| `node_u` | String (Categorical) | N/A | Nút xuất phát của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `node_v` | String (Categorical) | N/A | Nút đến của cạnh. | $\{O, A, B, C, D, E, T\}$ |
| `distance` | Integer (Discrete) | km | Chiều dài vật lý của đoạn đường (tính chất mạng tĩnh). | $1 \le distance \le 7$ |
| `travel_time` | Float (Continuous) | Phút | **Biến mục tiêu (Target Variable):** Thời gian di chuyển thực tế mô phỏng trên cạnh tại ngày và khung giờ tương ứng. | $travel\_time > 0$, phân phối lệch phải (Min: 1.39, Mean: 6.50, Max: 21.67) |

---

### 4. Bảng Phân chia Tập dữ liệu (Train / Test Split Structure)
*Quy tắc phân chia:* Phân chia theo khối thời gian (Time-series Block Split) để chống rò rỉ dữ liệu (No Data Leakage).

| Tên tập dữ liệu (Dataset) | Phạm vi thời gian (Time Window) | Số dòng (Observations) | Tỷ lệ (%) | Mục đích sử dụng (Usage Purpose) |
| :--- | :--- | :--- | :--- | :--- |
| `train.csv` | Ngày 1 đến Ngày 24 (Day 1 - 24) | 1.440 | 80,0% | Huấn luyện mô hình cơ sở (Group Mean, Linear Regression - WS4) và Neural Network (MLP - WS5). |
| `test.csv` | Ngày 25 đến Ngày 30 (Day 25 - 30) | 360 | 20,0% | Đánh giá độc lập chất lượng dự báo (MAE, RMSE) và chạy thí nghiệm định tuyến thực tế (Actual Travel Time - WS6). |

---

### 5. Ma trận Đặc trưng Đã Chuẩn hóa (`X_train_preprocessed.csv`, `X_test_preprocessed.csv`)
*Quy chuẩn tiền xử lý:* Fit tham số (Mean, Std, One-hot categories) duy nhất trên tập Train, sau đó Transform trên Test.

| Nhóm đặc trưng (Feature Group) | Phương pháp xử lý (Preprocessing Method) | Danh sách cột sinh ra (Output Columns) | Số chiều (Dimension) |
| :--- | :--- | :--- | :--- |
| **Numerical** | StandardScaler: $(x - \mu)/\sigma$ | `distance` | 1 |
| **Binary** | Giữ nguyên định dạng float | `is_weekend` | 1 |
| **Edge Identity** | One-Hot Encoding | `edge_id_A-B`, `edge_id_A-D`, `edge_id_B-C`, `edge_id_B-D`, `edge_id_B-E`, `edge_id_C-E`, `edge_id_D-E`, `edge_id_D-T`, `edge_id_E-T`, `edge_id_O-A`, `edge_id_O-B`, `edge_id_O-C` | 12 |
| **Time Slot** | One-Hot Encoding | `time_slot_1`, `time_slot_2`, `time_slot_3`, `time_slot_4`, `time_slot_5` | 5 |
| **Day of Week** | One-Hot Encoding | `day_of_week_Fri`, `day_of_week_Mon`, `day_of_week_Sat`, `day_of_week_Sun`, `day_of_week_Thu`, `day_of_week_Tue`, `day_of_week_Wed` | 7 |
| **TỔNG CỘNG** | | | **26 đặc trưng (Input Features)** |

### 6. The traffic data files for the Bay Area (PEMS-BAY)
https://pmc.ncbi.nlm.nih.gov/articles/PMC9861593/
https://github.com/liyaguang/DCRNN/tree/master
https://drive.google.com/drive/folders/10FOTa6HXPqX8Pf5WRoRwcFnW9BrNZEIX
@inproceedings{li2018dcrnn_traffic,
  title={Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting},
  author={Li, Yaguang and Yu, Rose and Shahabi, Cyrus and Liu, Yan},
  booktitle={International Conference on Learning Representations (ICLR '18)},
  year={2018}
}

`pems-bay.h5`: Chứa dữ liệu đầu vào theo thời gian (tốc độ xe tại các trạm qua từng khoảng thời gian 5 phút). Đây là nhãn/giá trị cần dự báo (ground truth).

`adj_mx_bay.pkl`: Chứa thông tin về ma trận kề (adjacency matrix) và danh sách các ID cảm biến (sensor IDs). File này dùng để xây dựng đồ thị mạng lưới giao thông (khoảng cách hoặc kết nối giữa các trạm đo).

`graph_sensor_locations_bay.csv`: Chứa tọa độ địa lý (vĩ độ, kinh độ) của các trạm cảm biến tương ứng với các ID trong mạng lưới giao thông, giúp ích cho việc trực quan hóa bản đồ hoặc tính toán khoảng cách không gian.