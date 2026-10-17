
import csv
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path

# ==================================================
# TASK: TRỰC QUAN HÓA NETWORK VÀ ĐƯỜNG ĐI NGẮN NHẤT
# ==================================================

# 1. Đọc dữ liệu từ file CSV
csv_path = Path(__file__).parent / "seervada_network.csv"

G = nx.Graph() 

with open(csv_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        u = row["node_u"].strip()
        v = row["node_v"].strip()
        distance = float(row["distance"])

        G.add_edge(u, v, weight=distance)

# 2. Xác định điểm xuất phát và điểm đích
source = "O"
target = "T"

# 3. Tìm đường đi ngắn nhất bằng Dijkstra
shortest_path = nx.dijkstra_path(
    G, source, target, weight="weight"
)

shortest_distance = nx.dijkstra_path_length(
    G, source, target, weight="weight"
)

# 4. Xác định các cạnh thuộc đường đi ngắn nhất
path_edges = list(zip(shortest_path[:-1], shortest_path[1:]))

# 5. Thiết lập vị trí cố định cho các nút
pos = {
    "O": (0, 2),
    "A": (1.5, 3.5),
    "B": (3, 2.5),
    "C": (1.5, 0.5),
    "D": (4.5, 3.5),
    "E": (4.5, 1),
    "T": (6, 2.5)
}

# 6. Vẽ network
plt.figure(figsize=(12, 7))

# Vẽ tất cả các cạnh
nx.draw_networkx_edges(
    G, pos,
    edge_color="gray",
    width=1.8
)

# Vẽ các nút
nx.draw_networkx_nodes(
    G, pos,
    node_color="lightblue",
    node_size=1100,
    edgecolors="black"
)

# Vẽ tên nút
nx.draw_networkx_labels(
    G, pos,
    font_size=12,
    font_weight="bold"
)

# 7. Tô nổi bật đường đi ngắn nhất
nx.draw_networkx_edges(
    G, pos,
    edgelist=path_edges,
    edge_color="red",
    width=3.5
)

# 8. Hiển thị khoảng cách trên từng cạnh
edge_labels = nx.get_edge_attributes(G, "weight")

nx.draw_networkx_edge_labels(
    G, pos,
    edge_labels=edge_labels,
    font_size=10,
    font_color="black"
)

# 9. Tiêu đề và kết quả
path_text = " -> ".join(shortest_path)

plt.title(
    f"Seervada Network - Shortest Path\n"
    f"Path: {path_text} | Total Distance: {shortest_distance:g}",
    fontsize=13
)

plt.axis("off")
plt.tight_layout()

# 10. Lưu biểu đồ và hiển thị
output_path = Path(__file__).parent / "seervada_network.png"

plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()

print("Shortest path:", path_text)
print("Total distance:", shortest_distance)
print("Saved visualization to:", output_path)



