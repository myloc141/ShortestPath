import csv
from pathlib import Path

# ============================================
# TASK: TỔNG HỢP CÁC ĐƯỜNG ĐI TỐI ƯU TƯƠNG ĐƯƠNG
# ============================================

# 1. Đường dẫn file kết quả brute force
folder = Path(__file__).parent
PATH = Path(__file__).parent / "results_paths.csv"
output_path = folder / "equivalent_paths.csv"

# 2. Đọc toàn bộ kết quả
with open(PATH, "r", encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)
    paths = list(reader)

if not paths:
    raise ValueError("File kết quả không có dữ liệu.")

# 3. Tìm tổng khoảng cách nhỏ nhất
minimum_distance = min(
    float(row["total_distance"]) for row in paths
)

# 4. Lọc tất cả đường đi có cùng khoảng cách nhỏ nhất
equivalent_paths = [
    row for row in paths
    if float(row["total_distance"]) == minimum_distance
]

# 5. Sắp xếp theo số cạnh, sau đó theo đường đi
equivalent_paths.sort(
    key=lambda row: (
        int(row["num_edges"]),
        row["path"]
    )
)

# 6. Tạo bảng tổng hợp
columns = [
    "rank",
    "source",
    "target",
    "path",
    "total_distance",
    "num_nodes",
    "num_edges",
    "algorithm",
    "is_optimal"
]

with open(output_path, "w", encoding="utf-8-sig", newline="") as file:
    writer = csv.DictWriter(file, fieldnames=columns)
    writer.writeheader()

    for rank, row in enumerate(equivalent_paths, start=1):
        result = {column: row[column] for column in columns}
        result["rank"] = rank
        result["is_optimal"] = True
        writer.writerow(result)

# 7. Hiển thị kết quả
print("Minimum distance:", minimum_distance)
print("Number of equivalent shortest paths:", len(equivalent_paths))

for row in equivalent_paths:
    print(f'{row["rank"]}. {row["path"]} '
          f'| Distance: {row["total_distance"]}')

print("Saved table to:", output_path)