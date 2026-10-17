# Workstream 01 - Seervada Network & Shortest Path
## 1) File dữ liệu đầu vào chính

- `seervada_network.csv`
  - Định dạng: CSV với các cột chính:
    - `node_u`
    - `node_v`
    - `distance`
    - `directed`
  - Đây là file dữ liệu gốc cho toàn bộ quá trình xử lý trong workstream01.
  - Các script chính đều đọc file này để tạo đồ thị, chạy thuật toán và tính đường đi.

## 2) Tổng hợp theo từng file

### 2.1. Đọc dữ liệu và kiểm tra tính hợp lệ của Netword (Task1.py)

#### Input
- Đọc file: `workstream01/seervada_network.csv`
- Tham số/biến bên ngoài:
  - `CSV_PATH = "workstream01/seervada_network.csv"`
  - `source = "O"`
  - `target = "T"`
  - `nodes`, `edges`, `adj` được khai báo ngoài và cập nhật trong quá trình đọc file

#### Processing
- Đọc dữ liệu CSV và lưu vào `adj` (bảng kề), `edges` (danh sách cạnh), `nodes` (tập các nút)
- Xác định loại cạnh:
  - nếu `directed == "true"` thì lưu chỉ một chiều
  - nếu `directed == "false"` thì lưu theo cả hai chiều
- Kiểm tra:
  - node nguồn và node đích có tồn tại trong mạng hay không
  - tổng số cạnh
  - mạng có liên thông hay không (`nx.is_connected`)
  - trọng số có phải là số dương không
- Tạo ra các bản in ra console để mô tả đồ thị, danh sách kề và kết luận độ hợp lệ của mạng

#### Output
- In ra console:
  - danh sách node
  - danh sách cạnh và hướng đi
  - thống kê số node, số cạnh, cạnh vô hướng, cạnh có hướng
  - danh sách kề của từng node
  - kết luận mạng hợp lệ để chạy thuật toán
- Không ghi file CSV bổ sung

#### Downstream
- Không có WS nào sử dụng kết quả này 
- File này phục vụ như một script phân tích nền cho các phần sau trong workstream01.

---

### 2.2. Thư viện Dijkstra (Dijkstra.py)

#### Input
- Đọc file: `workstream01/seervada_network.csv`
- Tham số/biến bên ngoài:
  - `graph` được xây dựng từ các hàng trong CSV
  - `start` được gán bằng `"O"` trong main
- Cấu trúc dữ liệu chính:
  - `graph[u] = [(v, w), ...]`
  - `distances`, `prev` là các dict được tạo bên trong thuật toán

#### Processing
- Triển khai thuật toán Dijkstra bằng heap queue (`heapq`)
- Tính khoảng cách ngắn nhất từ node xuất phát tới tất cả các node trong mạng
- Dùng `prev` để lưu đỉnh đứng trước trên đường đi ngắn nhất
- Hàm `reconstruct_path()` sẽ khôi phục đường đi cụ thể từ `prev`

#### Output
- Trả về:
  - `distances`: khoảng cách ngắn nhất từ nguồn tới mỗi node
  - `prev`: node trước đó trên đường đi tối ưu
- In ra console:
  - khoảng cách ngắn nhất từ `source` đến `target`
  - đường đi cụ thể theo định dạng `A -> B -> T`

#### Downstream
- Không có WS nào khác sử dụng kết quả này 

---

### 2.3. Tìm đường đi ngắn nhất từ nguồn đến đích (shortpath.py)

#### Input
- Đọc file: `workstream01/seervada_network.csv`
- Tham số/biến bên ngoài:
  - `CSV_PATH = "workstream01/seervada_network.csv"`
  - `source = "O"`
  - `target = "T"`
- Hàm `load_graph(filename)` tạo đồ thị từ file CSV

#### Processing
- Tạo `graph` theo cấu trúc `{u: [(v, w), ...]}`
- Gọi `dijkstra(graph, source)`
- Tìm đường đi ngắn nhất và trả về khoảng cách + path
- Sử dụng lazy deletion để xử lý các giá trị cũ trong heap

#### Output
- Trả về:
  - `dist` = khoảng cách ngắn nhất từ `source` đến `target`
  - `path` = danh sách node theo đường đi
- In ra console:
  - `Khoảng cách ngắn nhất từ O đến T: ...`
  - `Đường đi: ...`

#### Downstream
- Không tìm thấy output của file này được các workstream khác sử dụng trực tiếp.

---

### 2.4. Liệt kê mọi đường đi đơn từ nguồn đến đích bằng brute-force trên mạng nhỏ (shortpath2.py)

#### Input
- Đọc file: `workstream01/seervada_network.csv`
- Tham số/biến bên ngoài:
  - `CSV_PATH = "workstream01/seervada_network.csv"`
  - `source = "O"`
  - `target = "T"`
- Hàm `load_graph(filename)`, `all_simple_paths(graph, source, target)`

#### Processing
- Dùng Brute-force bằng DFS để tìm tất cả đường đi đơn giản từ `source` đến `target`
- Với mỗi đường đi, tính tổng khoảng cách bằng `path_cost(graph, path)`
- Sắp xếp các đường đi theo `total_distance`
- Tìm các đường đi tối ưu có chi phí thấp nhất
- Có thể xây dựng `results` dạng metadata + list đường đi
- Ghi CSV với các cột:
  - `rank`
  - `source`
  - `target`
  - `path`
  - `total_distance`
  - `num_nodes`
  - `num_edges`
  - `algorithm`
  - `is_optimal`

#### Output
- In ra console:
  - số lượng đường đi khả thi
  - tổng khoảng cách tối thiểu
  - số phương án tối ưu
  - từng đường đi cùng khoảng cách tối ưu
- Ghi ra file:
  - `workstream01/results_paths.csv`

#### Downstream
- Output results_paths dùng cho WS2 sử dụng kiểm chứng RCSP