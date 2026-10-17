# ============================================================
# TASK 1.5: LIỆT KÊ MỌI ĐƯỜNG ĐI ĐƠN TỪ NGUỒN ĐẾN ĐÍCH
# Phương pháp: Brute-force bằng DFS
import csv
def load_graph(filename):
    graph = {}
    with open(filename, "r", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            u = row["node_u"].strip()
            v = row["node_v"].strip()
            w = int(row["distance"])
            directed = row["directed"].strip().lower() == "true"

            graph.setdefault(u, [])
            graph.setdefault(v, [])

            graph[u].append((v, w))
            if not directed:
                graph[v].append((u, w))
    return graph

# 2. BRUTE-FORCE: LIỆT KÊ MỌI ĐƯỜNG ĐI ĐƠN
def all_simple_paths(graph, source, target):
    """
    Trả về list các đường đi đơn từ source -> target.
    Mỗi đường là list các node: [source, ..., target]
    """
    results = []

    def dfs(current, path, visited):
        if current == target:
            results.append(path.copy())
            return

        for neighbor, _ in graph[current]:
            if neighbor not in visited:
                visited.add(neighbor)
                path.append(neighbor)
                dfs(neighbor, path, visited)
                path.pop()
                visited.remove(neighbor)

    dfs(source, [source], {source})
    return results

# 3. TÍNH TỔNG KHOẢNG CÁCH CỦA TỪNG ĐƯỜNG
def path_cost(graph, path):
    """Tính tổng trọng số của 1 đường đi."""
    total = 0
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        for neighbor, w in graph[u]:
            if neighbor == v:
                total += w
                break
    return total

if __name__ == "__main__":
    CSV_PATH = "workstream01/seervada_network.csv"

    graph = load_graph(CSV_PATH)
    source = "O"
    target = "T"

    # Liệt kê mọi đường đi đơn
    paths = all_simple_paths(graph, source, target)

    print(f"Số lượng đường đi khả thi từ {source} đến {target}: {len(paths)}")
    print("=" * 60)

    # Tính khoảng cách từng đường
    results = []
    for p in paths:
        cost = path_cost(graph, p)
        results.append((cost, p))

    # Sắp xếp theo tổng khoảng cách tăng dần
    results.sort(key=lambda x: x[0])

    # In tất cả đường đi + khoảng cách
    for cost, p in results:
        print(f"{cost:>4}  |  {' -> '.join(p)}")

    # Tìm khoảng cách tối thiểu
    min_cost = results[0][0]
    optimal_paths = [p for cost, p in results if cost == min_cost]

    print("=" * 60)
    print(f"Tổng khoảng cách tối thiểu: {min_cost}")
    print(f"Số phương án tối ưu: {len(optimal_paths)}")
    print("Các phương án tối ưu:")
    for p in optimal_paths:
        print(f"  {' -> '.join(p)}")




def build_results(graph, source, target, algorithm="brute_force"):
    paths = all_simple_paths(graph, source, target)

    # Tính cost từng đường
    scored = [(path_cost(graph, p), p) for p in paths]

    # Sắp xếp theo cost tăng dần
    scored.sort(key=lambda x: x[0])

    if not scored:
        return {"metadata": {...}, "paths": []}

    min_cost = scored[0][0]

    results = []
    rank = 1
    for cost, p in scored:
        results.append({
            "rank": rank,
            "path": p,
            "total_distance": cost,
            "num_nodes": len(p),
            "num_edges": len(p) - 1,
            "is_optimal": (cost == min_cost),
        })
        rank += 1

    return {
        "metadata": {
            "source": source,
            "target": target,
            "algorithm": algorithm,
            "total_paths": len(results),
            "min_distance": min_cost,
            "num_optimal": sum(1 for r in results if r["is_optimal"]),
        },
        "paths": results,
    }

# ------------------------------------------------------------
# 5. GHI FILE CSV
# ------------------------------------------------------------
def save_csv(results, filename):
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "source", "target", "path",
            "total_distance", "num_nodes", "num_edges",
            "algorithm", "is_optimal"
        ])
        src = results["metadata"]["source"]
        tgt = results["metadata"]["target"]
        alg = results["metadata"]["algorithm"]
        for r in results["paths"]:
            writer.writerow([
                r["rank"], src, tgt,
                "-".join(r["path"]),
                r["total_distance"],
                r["num_nodes"], r["num_edges"],
                alg, r["is_optimal"]
            ])
    print(f"Đã lưu CSV: {filename}")


# ------------------------------------------------------------
# 6. MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    CSV_PATH = "workstream01/seervada_network.csv"
    OUT_JSON = "workstream01/results_paths.json"
    OUT_CSV = "workstream01/results_paths.csv"

    graph = load_graph(CSV_PATH)
    source = "O"
    target = "T"

    results = build_results(graph, source, target, algorithm="brute_force")

    save_csv(results, OUT_CSV)

    print(f"\nTổng số đường: {results['metadata']['total_paths']}")
    print(f"Khoảng cách tối thiểu: {results['metadata']['min_distance']}")
    print(f"Số phương án tối ưu: {results['metadata']['num_optimal']}")