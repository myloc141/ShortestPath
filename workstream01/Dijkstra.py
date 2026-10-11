# ============================================================
# TASK 1.3: CÀI ĐẶT THUẬT TOÁN DIJKSTRA
# Lựa chọn: Tự cài đặt Dijkstra bằng Python
# ============================================================
# Cài đặt thuật toán Dijkstra bằng Python
# Viết code Sử dụng thư viện heapq để triển khai Min-Heap

import heapq

def dijkstra(graph, start):
    """
    graph: dict {u: [(v, w), ...]}   (w >= 0)
    start: đỉnh xuất phát
    return: distances, prev
    """
    distances = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    distances[start] = 0

    heap = [(0, start)]

    while heap:
        current_dist, current_node = heapq.heappop(heap)

        # Lazy deletion: bỏ qua bản ghi cũ
        if current_dist > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node]:
            # Đảm bảo neighbor có trong distances (tránh KeyError)
            if neighbor not in distances:
                distances[neighbor] = float('inf')
                prev[neighbor] = None

            distance = current_dist + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                prev[neighbor] = current_node
                heapq.heappush(heap, (distance, neighbor))

    return distances, prev


def reconstruct_path(prev, target):
    path = []
    while target is not None:
        path.append(target)
        target = prev[target]
    return path[::-1]


# ============================================================
# XÁC ĐỊNH INPUT, OUTPUT VÀ QUY ƯỚC
# ============================================================

"""
1. INPUT
------------------------------------------------------------
- graph:
  Đồ thị mạng Seervada, biểu diễn dạng:

      graph[u] = [(v, weight), ...]

- start:
  Node nguồn, ví dụ:

      start = "O"

- Trọng số:
  Các cạnh phải có trọng số w >= 0.

- Đồ thị vô hướng:
  Mỗi cạnh được biểu diễn theo cả hai chiều.

2. OUTPUT
------------------------------------------------------------
- distances:
  Khoảng cách ngắn nhất từ node nguồn start đến mỗi node.

  Ví dụ:
      distances["T"] = 13

- prev:
  Node đứng trước trên đường đi ngắn nhất.

  Ví dụ:
      prev["T"] = "D"

- reconstruct_path():
  Sử dụng prev để khôi phục đường đi cụ thể
  từ node nguồn đến node đích.

3. QUY ƯỚC KHI CÓ NHIỀU ĐƯỜNG ĐI CÙNG TỔNG TRỌNG SỐ
------------------------------------------------------------

- Nếu tìm được đường đi có tổng trọng số nhỏ hơn
  khoảng cách hiện tại:

      if distance < distances[neighbor]:

  -> Cập nhật distances và prev.

- Nếu:

      distance == distances[neighbor]

  -> Không cập nhật distances.
  -> Không cập nhật prev.
  -> Giữ lại đường đi đã được phát hiện trước đó.

- Do đó, quy ước của thuật toán là: giữ lại đường đi được phát hiện đầu tiên.

- Không sử dụng tie-break lexicographic.

- Khi có nhiều đường cùng tổng trọng số, đường được giữ lại
  có thể phụ thuộc vào thứ tự duyệt cạnh và thứ tự xử lý
  các node trong Min-Heap.
"""



# ============================================================
# TASK 1.4: TÌM ĐƯỜNG ĐI NGẮN NHẤT TỪ NGUỒN ĐẾN ĐÍCH
# ============================================================
import csv

# ============================================================
# ĐỌC VÀ MÃ HÓA MẠNG SEERVADA
# ============================================================

CSV_PATH = "workstream01/seervada_network.csv"

graph = {}

with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        u = row["node_u"]
        v = row["node_v"]
        weight = float(row["distance"])
        directed = row["directed"].strip().lower() == "true"

        # Khởi tạo node nếu chưa có
        graph.setdefault(u, [])
        graph.setdefault(v, [])

        # Thêm cạnh u -> v
        graph[u].append((v, weight))

        # Nếu là đồ thị vô hướng thì thêm cạnh v -> u
        if not directed:
            graph[v].append((u, weight))
# Xác định node nguồn và node đích
start = "O"
target = "T"

# Chạy thuật toán Dijkstra từ node nguồn
distances, prev = dijkstra(graph, start)

# Khôi phục đường đi ngắn nhất đến node đích
path = reconstruct_path(prev, target)

# In kết quả
print("Node nguồn:", start)
print("Node đích:", target)
print("Đường đi ngắn nhất:", " -> ".join(path))
print("Tổng khoảng cách:", distances[target])