# ============================================================
# TASK 1.4: TÌM ĐƯỜNG ĐI NGẮN NHẤT TỪ NGUỒN ĐẾN ĐÍCH
# ============================================================
import csv
import heapq

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

# 2. DIJKSTRA
def dijkstra(graph, start):
    distances = {node: float('inf') for node in graph}
    prev = {node: None for node in graph}
    distances[start] = 0

    heap = [(0, start)]

    while heap:
        current_dist, current_node = heapq.heappop(heap)

        # Lazy deletion
        if current_dist > distances[current_node]:
            continue

        for neighbor, weight in graph[current_node]:
            if neighbor not in distances:
                distances[neighbor] = float('inf')
                prev[neighbor] = None

            distance = current_dist + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                prev[neighbor] = current_node
                heapq.heappush(heap, (distance, neighbor))

    return distances, prev

# 3. KHÔI PHỤC ĐƯỜNG ĐI
def reconstruct_path(prev, target):
    path = []
    while target is not None:
        path.append(target)
        target = prev[target]
    return path[::-1]



if __name__ == "__main__":
    CSV_PATH = "workstream01/seervada_network.csv"

    graph = load_graph(CSV_PATH)

    source = "O"
    target = "T"

    dist, path = find_shortest_path(graph, source, target)

    print(f"Khoảng cách ngắn nhất từ {source} đến {target}: {dist}")
    print(f"Đường đi: {' -> '.join(path)}")