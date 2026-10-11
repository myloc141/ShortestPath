import csv
from collections import defaultdict


# ============================================================
# TASK 1.1: ĐỌC VÀ MÃ HÓA MẠNG SEERVADA
# ============================================================

CSV_PATH = "workstream01/seervada_network.csv"

# Các cấu trúc dữ liệu
adj = defaultdict(dict)   # Danh sách kề
edges = []                # Danh sách cạnh
nodes = set()             # Tập node

# 1. ĐỌC DỮ LIỆU TỪ CSV

with open(CSV_PATH, "r", encoding="utf-8-sig") as f:

    reader = csv.DictReader(f)

    for row in reader:

        u = row["node_u"].strip()
        v = row["node_v"].strip()
        w = float(row["distance"])
        directed = row["directed"].strip().lower() == "true"

        # Lưu node
        nodes.add(u)
        nodes.add(v)

        # Lưu cạnh gốc
        edges.append((u, v, w, directed))

        # Mã hóa network
        # Cạnh vô hướng → đi được hai chiều
        if not directed:
            adj[u][v] = w
            adj[v][u] = w

        # Trường hợp có cạnh có hướng
        else:
            adj[u][v] = w

# 2. HIỂN THỊ DỮ LIỆU GỐC

print("=" * 50)
print("DỮ LIỆU SEERVADA NETWORK")
print("=" * 50)

print(f"{'node_u':<8}{'node_v':<8}{'distance':<11}{'directed'}")

for u, v, w, directed in edges:
    print(f"{u:<8}{v:<8}{w:<11g}{directed}")

# 3. NETWORK ĐÃ ĐƯỢC MÃ HÓA

print("\n" + "=" * 50)
print("NETWORK ĐÃ ĐƯỢC MÃ HÓA")
print("=" * 50)


# ----- Các node -----

print("Các node:")
print(sorted(nodes))


# ----- Các cạnh -----

print("\nCác cạnh:")

for u, v, w, directed in edges:

    if directed:
        print(f"{u} --> {v} | distance = {w:g}")
    else:
        print(f"{u} <--> {v} | distance = {w:g}")


# ----- Thống kê -----

undirected = sum(1 for _, _, _, d in edges if not d)
directed_count = sum(1 for _, _, _, d in edges if d)

print(f"\nSố node: {len(nodes)}")
print(f"Số cạnh: {len(edges)}")
print(f"Cạnh vô hướng: {undirected}")
print(f"Cạnh có hướng: {directed_count}")


# ----- Danh sách kề -----

print("\n" + "=" * 50)
print("DANH SÁCH KỀ")
print("=" * 50)

for u in sorted(nodes):

    print(f"{u} -> ", end="")

    for v, w in sorted(adj[u].items()):
        print(f"{v}({w:g})", end=" ")

    print()



# ============================================================
# TASK 1.2: KIỂM TRA TÍNH HỢP LỆ CỦA NETWORK
# ============================================================

import networkx as nx

# Khai báo node nguồn và node đích
source = "O"
target = "T"
# 1. KIỂM TRA NODE NGUỒN / ĐÍCH

print("=" * 50)
print("1. KIỂM TRA NODE NGUỒN / ĐÍCH")
print("=" * 50)

# Kiểm tra node nguồn có tồn tại trong network hay không
if source in nodes:
    print(f"Node nguồn {source}: HỢP LỆ")
else:
    print(f"Node nguồn {source}: KHÔNG TỒN TẠI")

# Kiểm tra node đích có tồn tại trong network hay không
if target in nodes:
    print(f"Node đích {target}: HỢP LỆ")
else:
    print(f"Node đích {target}: KHÔNG TỒN TẠI")

# 2. KIỂM TRA SỐ CẠNH
print("\n" + "=" * 50)
print("2. KIỂM TRA SỐ CẠNH")
print("=" * 50)

# Đếm tổng số cạnh được đọc từ file CSV
print(f"Tổng số cạnh: {len(edges)}")

# 3. KIỂM TRA KHẢ NĂNG LIÊN THÔNG

print("\n" + "=" * 50)
print("3. KIỂM TRA KHẢ NĂNG LIÊN THÔNG")
print("=" * 50)

# Tạo một đồ thị vô hướng
G = nx.Graph()

# Thêm các cạnh và trọng số vào đồ thị
for u in adj:
    for v, w in adj[u].items():
        G.add_edge(u, v, weight=w)

# Kiểm tra network có liên thông hay không
connected = nx.is_connected(G)

if connected:
    print("Network LIÊN THÔNG.")
else:
    print("Network KHÔNG LIÊN THÔNG.")

# 4. KIỂM TRA TRỌNG SỐ VÀ ĐƠN VỊ

print("\n" + "=" * 50)
print("4. KIỂM TRA TRỌNG SỐ VÀ ĐƠN VỊ")
print("=" * 50)

# Lấy trọng số (distance) của tất cả các cạnh
# edge[2] là vị trí chứa giá trị distance
weights = [edge[2] for edge in edges]

# Kiểm tra tất cả trọng số có phải là số dương hay không
valid_weights = (
    len(weights) > 0
    and all(isinstance(w, (int, float)) and w > 0 for w in weights)
)

if valid_weights:
    print("Tất cả trọng số đều là số dương. HỢP LỆ.")
else:
    print("Có trọng số không hợp lệ.")

# Đơn vị khoảng cách được sử dụng trong network
print("Đơn vị trọng số: km.")

print("\n" + "=" * 50)
print("KẾT LUẬN")
print("=" * 50)

# Network hợp lệ khi:
# - Node nguồn tồn tại
# - Node đích tồn tại
# - Có cạnh trong network
# - Tất cả trọng số hợp lệ
# - Network liên thông
if (
    source in nodes
    and target in nodes
    and len(edges) > 0
    and valid_weights
    and connected
):
    print("Network hợp lệ để thực hiện bài toán tìm đường đi.")
else:
    print("Network chưa hợp lệ, cần kiểm tra lại dữ liệu.")
