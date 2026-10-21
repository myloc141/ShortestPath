# TỪ ĐIỂN DỮ LIỆU PeMS-BAY MỞ RỘNG (DATA DICTIONARY: PeMS-BAY SUBNETWORK)
**Học phần:** Vận trù học | **Chủ đề:** 5. Mối liên hệ giữa bài toán đường đi ngắn nhất và machine learning / routing hiện đại (Mức độ C)  
**Tác giả Workstream 3:** Lại Gia Huy (MSSV: K24419) – UEL / ĐHQG-HCM  
**Nguồn dữ liệu gốc:** California Department of Transportation (Caltrans) Performance Measurement System (PeMS), mạng cảm biến PeMS-Bay (Vùng Vịnh San Francisco, California).

---

## 1. TỔNG QUAN VỀ BỘ DỮ LIỆU PeMS-BAY SUBNETWORK

Để phục vụ tiêu chí **Mở rộng Mức độ C** (tự thu thập, xử lý dữ liệu thực và mô hình hóa mạng lưới quy mô lớn cho Neural Network), Workstream 3 đã trích xuất từ mạng 325 trạm cảm biến của PeMS-Bay một **mạng con liên thông mạnh (Connected Subnetwork) gồm 25 trạm cảm biến và 139 cạnh có hướng**.

* **Số nút cảm biến ($|V|$):** 25 nút (tương ứng với 25 trạm đo vòng từ trường Inductive Loop Detectors).
* **Số cạnh có hướng ($|E|$):** 139 cạnh (dựa trên ngưỡng liên thông ma trận kề $W_{ij} > 0$).
* **Nút nguồn đại diện ($O$):** Sensor ID `402365` (Bậc liên thông: 23).
* **Nút đích đại diện ($T$):** Sensor ID `403225`.
* **Khoảng cách ngắn nhất Dijkstra:** $2.199\text{ km}$.

---

## 2. BẢNG MÃ HÓA CÁC BIẾN NÚT MẠNG CẢM BIẾN (`pems_subnetwork_nodes.csv`)

| Tên trường (Column) | Kiểu dữ liệu | Đơn vị | Miền giá trị | Mô tả ý nghĩa khoa học |
| :--- | :---: | :---: | :---: | :--- |
| `node_id` | String | Mã số | 6 chữ số (VD: `402365`) | Mã định danh trạm cảm biến cao tốc Caltrans PeMS. |
| `latitude` | Float64 | Độ (Degrees) | $[37.20, 37.45]$ | Tọa độ vĩ độ địa lý (WGS84). |
| `longitude` | Float64 | Độ (Degrees) | $[-122.05, -121.80]$ | Tọa độ kinh độ địa lý (WGS84). |
| `degree_in_subnetwork`| Integer | Bậc đồ thị | $[2, 23]$ | Tổng số cung đi ra và đi vào của nút trong mạng con. |

---

## 3. BẢNG MÃ HÓA CÁC BIẾN CẠNH LIÊN KẾT (`pems_subnetwork_edges.csv`)

| Tên trường (Column) | Kiểu dữ liệu | Đơn vị | Miền giá trị | Mô tả ý nghĩa khoa học |
| :--- | :---: | :---: | :---: | :--- |
| `source` | String | Mã số | Danh sách 25 node | Mã cảm biến điểm xuất phát của cung đường ($u$). |
| `target` | String | Mã số | Danh sách 25 node | Mã cảm biến điểm kết thúc của cung đường ($v$). |
| `distance_km` | Float64 | Kilomet (km) | $[0.05, 12.85]$ | Chiều dài cung đường hình học, tính xấp xỉ bằng công thức **Haversine** từ tọa độ GPS. |
| `weight` | Float64 | Không thứ nguyên | $(0.0, 1.0]$ | Trọng số ma trận kề gốc tính theo hàm phân phối Gaussian khoảng cách $W_{ij} = \exp\left(-\left(\frac{dist_{ij}}{\sigma}\right)^2\right)$. |

---

## 4. QUY TẮC TÍNH CHIỀU DÀI HAVERSINE

Khoảng cách hình học $d$ giữa hai cảm biến $(lat_1, lon_1)$ và $(lat_2, lon_2)$ được tính theo công thức mặt cầu:
$$\Delta\phi = \text{radians}(lat_2 - lat_1), \quad \Delta\lambda = \text{radians}(lon_2 - lon_1)$$
$$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\text{radians}(lat_1))\cos(\text{radians}(lat_2))\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
$$d = 2 R \cdot \arctan2(\sqrt{a}, \sqrt{1 - a})$$
Trong đó bán kính Trái Đất quy ước $R = 6.371\text{ km}$. Nếu $d = 0$ (hai trạm cùng cột mốc), gán ngưỡng an toàn tối thiểu $d = 0.05\text{ km}$.

---

## 5. BẢNG BIẾN CHUỖI THỜI GIAN VÀ CHUYỂN ĐỔI TỐC ĐỘ SANG TRAVEL TIME

| Tên biến | Kiểu dữ liệu | Đơn vị | Quy tắc tiền xử lý |
| :--- | :---: | :---: | :--- |
| `timestamp` | String ISO-8601 | Thời gian | Định dạng `YYYY-MM-DDTHH:MM:SS`. Chu kỳ đo chuẩn hóa: 5 phút. |
| `speed_mph` | Float64 | dặm/giờ (mph) | Tốc độ dòng xe do vòng từ PeMS ghi nhận. Tốc độ bằng 0 hoặc thiếu được xử lý theo nguyên tắc nhân quả (**Causal Forward-Fill**). |
| `speed_kmh` | Float64 | km/h | Chuyển đổi vận tốc: $v_{\text{km/h}} = v_{\text{mph}} \times 1.609344$. |
| `travel_time` | Float64 | Phút (minutes) | Thời gian di chuyển ước lượng trên cạnh: $t = \frac{distance\_km}{v_{\text{km/h}}} \times 60$. |
