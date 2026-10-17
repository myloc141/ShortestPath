# ============================================================
# WORKSTREAM 2: RCSP - RESOURCE CONSTRAINED SHORTEST PATH
# Người thực hiện: Ngọc Hân
#
# Bài toán: Tìm đường đi O -> T trên mạng Seervada sao cho
#   - Tổng khoảng cách (distance) NHỎ NHẤT
#   - Ràng buộc: tổng thời gian (time) <= Tmax
#
# MÔ HÌNH QUY HOẠCH TUYẾN TÍNH NGUYÊN 0-1 (MILP):
#   Biến quyết định:  x[i,j] ∈ {0,1} — cung (i,j) có nằm trên đường đi hay không
#                     (mỗi cạnh vô hướng được tách thành 2 cung có hướng)
#   Hàm mục tiêu:     min Σ distance[i,j] * x[i,j]
#   Ràng buộc cân bằng dòng (flow conservation), với mỗi node v:
#       Σ x[v,j] - Σ x[i,v] = +1 nếu v = O (nguồn)
#                           = -1 nếu v = T (đích)
#                           =  0 nếu v là node trung gian
#   Ràng buộc tài nguyên: Σ time[i,j] * x[i,j] <= Tmax
#
# Ghi chú: vì mọi distance > 0 và bài toán cực tiểu hóa, chu trình tách rời
# không thể xuất hiện trong nghiệm tối ưu (nó chỉ làm tăng chi phí),
# nên không cần ràng buộc khử chu trình (subtour elimination).
# Dù vậy, nghiệm vẫn được kiểm tra độc lập bằng verify_path().
#
# SOLVER: PuLP (v4.x) + CBC (COIN-OR Branch and Cut, đi kèm sẵn trong PuLP).
# KIỂM CHỨNG CHÉO (3 lớp độc lập):
#   1. MILP (PuLP + CBC)
#   2. Brute-force: liệt kê mọi simple path, lọc theo Tmax, lấy min distance
#   3. cspy (github.com/torressa/cspy) - thư viện chuyên RCSP, thuật toán
#      BiDirectional labeling (nếu import được; không bắt buộc)
# ============================================================

import csv
import sys
from pathlib import Path

import pulp

# Đảm bảo in được tiếng Việt trên console Windows (cp1252)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Đường dẫn tính từ repo root (file này nằm trong workstream02/)
REPO_ROOT = Path(__file__).resolve().parents[1]
RCSP_CSV = REPO_ROOT / "workstream03" / "seervada_rcsp_teaching.csv"
WS1_NETWORK_CSV = REPO_ROOT / "workstream03" / "seervada_network.csv"
OUT_DIR = REPO_ROOT / "workstream02"

SOURCE = "O"
TARGET = "T"


# ------------------------------------------------------------
# 1. ĐỌC DỮ LIỆU RCSP (distance + time trên từng cạnh)
# ------------------------------------------------------------
def load_rcsp_edges(csv_path=RCSP_CSV):
    """Đọc seervada_rcsp_teaching.csv.

    Trả về list các cạnh gốc: [(u, v, distance, time, directed), ...]
    """
    edges = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            edges.append((
                row["node_u"].strip(),
                row["node_v"].strip(),
                float(row["distance"]),
                float(row["time"]),
                row["directed"].strip().lower() == "true",
            ))
    return edges


def build_arcs(edges):
    """Tách cạnh vô hướng thành 2 cung có hướng.

    Trả về:
        arcs:  list [(i, j), ...]
        dist:  dict {(i, j): distance}
        time_: dict {(i, j): time}
        nodes: set các node
    """
    arcs, dist, time_, nodes = [], {}, {}, set()
    for u, v, d, t, directed in edges:
        nodes.update([u, v])
        pairs = [(u, v)] if directed else [(u, v), (v, u)]
        for i, j in pairs:
            arcs.append((i, j))
            dist[(i, j)] = d
            time_[(i, j)] = t
    return arcs, dist, time_, nodes


# ------------------------------------------------------------
# 2. ĐỐI CHIẾU NETWORK RCSP VỚI NETWORK SEERVADA CỦA WS1
# ------------------------------------------------------------
def check_network_consistency(rcsp_csv=RCSP_CSV, ws1_csv=WS1_NETWORK_CSV,
                              out_csv=OUT_DIR / "rcsp_network_consistency.csv"):
    """So khớp node, cạnh, distance và hướng đi giữa 2 file mạng.

    Xuất bảng kiểm tra ra CSV và trả về True nếu khớp 100%.
    """
    def read_net(path, has_time):
        net = {}
        with open(path, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                key = frozenset([row["node_u"].strip(), row["node_v"].strip()])
                net[key] = {
                    "distance": float(row["distance"]),
                    "directed": row["directed"].strip().lower() == "true",
                    "time": float(row["time"]) if has_time else None,
                }
        return net

    rcsp_net = read_net(rcsp_csv, has_time=True)
    ws1_net = read_net(ws1_csv, has_time=False)

    rows, all_ok = [], True
    for key in sorted(set(rcsp_net) | set(ws1_net), key=sorted):
        u, v = sorted(key)
        in_rcsp, in_ws1 = key in rcsp_net, key in ws1_net
        dist_match = (in_rcsp and in_ws1
                      and rcsp_net[key]["distance"] == ws1_net[key]["distance"])
        dir_match = (in_rcsp and in_ws1
                     and rcsp_net[key]["directed"] == ws1_net[key]["directed"])
        ok = in_rcsp and in_ws1 and dist_match and dir_match
        all_ok &= ok
        rows.append({
            "edge": f"{u}-{v}",
            "in_rcsp": in_rcsp,
            "in_ws1": in_ws1,
            "distance_rcsp": rcsp_net[key]["distance"] if in_rcsp else "",
            "distance_ws1": ws1_net[key]["distance"] if in_ws1 else "",
            "distance_match": dist_match,
            "directed_match": dir_match,
            "time_rcsp": rcsp_net[key]["time"] if in_rcsp else "",
            "consistent": ok,
        })

    rcsp_nodes = {n for key in rcsp_net for n in key}
    ws1_nodes = {n for key in ws1_net for n in key}

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    node_ok = rcsp_nodes == ws1_nodes
    print("=" * 60)
    print("ĐỐI CHIẾU NETWORK RCSP vs NETWORK SEERVADA (WS1)")
    print("=" * 60)
    print(f"- Node khớp: {node_ok} ({sorted(rcsp_nodes)})")
    print(f"- Số cạnh RCSP: {len(rcsp_net)} | Số cạnh WS1: {len(ws1_net)}")
    print(f"- Toàn bộ cạnh khớp (edge/distance/hướng): {all_ok}")
    print(f"- Đã lưu bảng kiểm tra: {out_csv.name}")
    return all_ok and node_ok


# ------------------------------------------------------------
# 3-4. MÔ HÌNH MILP 0-1 VÀ GIẢI BẰNG PuLP + CBC
# ------------------------------------------------------------
def solve_rcsp_milp(arcs, dist, time_, nodes, t_max=None,
                    source=SOURCE, target=TARGET):
    """Xây và giải mô hình RCSP bằng PuLP + CBC.

    t_max=None nghĩa là không có ràng buộc thời gian (shortest path thuần).

    Trả về dict: status, path, total_distance, total_time, arcs_selected.
    """
    model = pulp.LpProblem("RCSP_Seervada", pulp.LpMinimize)

    # Biến nhị phân trên từng cung
    x = pulp.LpVariable.dicts("x", arcs, cat=pulp.LpBinary)

    # Hàm mục tiêu: tối thiểu hóa tổng khoảng cách
    model += pulp.lpSum(dist[a] * x[a] for a in arcs), "TotalDistance"

    # Ràng buộc cân bằng dòng tại từng node
    for v in nodes:
        out_flow = pulp.lpSum(x[a] for a in arcs if a[0] == v)
        in_flow = pulp.lpSum(x[a] for a in arcs if a[1] == v)
        rhs = 1 if v == source else (-1 if v == target else 0)
        model += (out_flow - in_flow == rhs), f"flow_{v}"

    # Ràng buộc tài nguyên: tổng thời gian <= Tmax
    if t_max is not None:
        model += (pulp.lpSum(time_[a] * x[a] for a in arcs) <= t_max,
                  "TimeBudget")

    model.solve(pulp.PULP_CBC_CMD(msg=False))
    status = pulp.LpStatus[model.status]

    if status != "Optimal":
        return {"status": status, "path": None, "total_distance": None,
                "total_time": None, "arcs_selected": []}

    selected = [a for a in arcs if x[a].varValue > 0.5]
    path = reconstruct_path_from_arcs(selected, source, target)
    return {
        "status": status,
        "path": path,
        "total_distance": sum(dist[a] for a in selected),
        "total_time": sum(time_[a] for a in selected),
        "arcs_selected": selected,
    }


# ------------------------------------------------------------
# 5. KIỂM TRA NGHIỆM SOLVER CÓ TẠO THÀNH ĐƯỜNG ĐI HỢP LỆ
# ------------------------------------------------------------
def reconstruct_path_from_arcs(selected_arcs, source, target):
    """Ghép các cung được chọn thành đường đi source -> target.

    Trả về list node nếu hợp lệ, None nếu không ghép được.
    """
    succ = {}
    for i, j in selected_arcs:
        if i in succ:          # một node có 2 cung ra -> không phải đường đi đơn
            return None
        succ[i] = j

    path, current, visited = [source], source, {source}
    while current != target:
        if current not in succ:
            return None        # đứt mạch
        current = succ[current]
        if current in visited:
            return None        # lặp node -> có chu trình
        visited.add(current)
        path.append(current)

    # Toàn bộ cung được chọn phải nằm trên đường đi (không có chu trình thừa)
    if len(selected_arcs) != len(path) - 1:
        return None
    return path


def verify_solution(result, dist, time_, t_max, source=SOURCE, target=TARGET):
    """Kiểm tra độc lập nghiệm MILP: đường đi hợp lệ + đúng tổng + thỏa Tmax."""
    checks = {}
    path = result["path"]
    checks["is_valid_simple_path"] = path is not None
    if path is None:
        return checks

    checks["starts_at_source"] = path[0] == source
    checks["ends_at_target"] = path[-1] == target
    checks["no_repeated_nodes"] = len(path) == len(set(path))

    d = sum(dist[(path[k], path[k + 1])] for k in range(len(path) - 1))
    t = sum(time_[(path[k], path[k + 1])] for k in range(len(path) - 1))
    checks["distance_matches_objective"] = abs(d - result["total_distance"]) < 1e-9
    checks["time_matches"] = abs(t - result["total_time"]) < 1e-9
    checks["time_within_budget"] = True if t_max is None else t <= t_max + 1e-9
    return checks


# ------------------------------------------------------------
# 6. KIỂM CHỨNG CHÉO BẰNG BRUTE-FORCE (như cách WS1 đã làm)
# ------------------------------------------------------------
def all_simple_paths(arcs, source, target):
    """Liệt kê mọi đường đi đơn source -> target bằng DFS (mạng nhỏ, 7 node)."""
    adj = {}
    for i, j in arcs:
        adj.setdefault(i, []).append(j)

    results = []

    def dfs(current, path, visited):
        if current == target:
            results.append(path.copy())
            return
        for nxt in adj.get(current, []):
            if nxt not in visited:
                visited.add(nxt)
                path.append(nxt)
                dfs(nxt, path, visited)
                path.pop()
                visited.remove(nxt)

    dfs(source, [source], {source})
    return results


def brute_force_rcsp(arcs, dist, time_, t_max, source=SOURCE, target=TARGET):
    """Giải RCSP bằng brute-force: lọc path thỏa Tmax, lấy min distance.

    Trả về dict: status, best_distance, best_paths (mọi path đạt min),
    n_paths_total, n_paths_feasible.
    """
    paths = all_simple_paths(arcs, source, target)
    scored = []
    for p in paths:
        d = sum(dist[(p[k], p[k + 1])] for k in range(len(p) - 1))
        t = sum(time_[(p[k], p[k + 1])] for k in range(len(p) - 1))
        scored.append((p, d, t))

    feasible = [s for s in scored if t_max is None or s[2] <= t_max + 1e-9]
    if not feasible:
        return {"status": "Infeasible", "best_distance": None, "best_paths": [],
                "n_paths_total": len(scored), "n_paths_feasible": 0}

    best_d = min(s[1] for s in feasible)
    best = [s for s in feasible if abs(s[1] - best_d) < 1e-9]
    return {"status": "Optimal", "best_distance": best_d,
            "best_paths": best, "n_paths_total": len(scored),
            "n_paths_feasible": len(feasible)}


# ------------------------------------------------------------
# 6b. LỚP KIỂM CHỨNG THỨ 3: THƯ VIỆN cspy (torressa/cspy)
# Thư viện chuyên RCSP (JOSS-published), thuật toán BiDirectional labeling.
# Dữ liệu Seervada khớp đúng input cspy: DiGraph với cost (distance)
# và vector tiêu hao tài nguyên (time), giới hạn max_res = Tmax.
# ------------------------------------------------------------
def cspy_rcsp(arcs, dist, time_, t_max, source=SOURCE, target=TARGET):
    """Giải RCSP bằng cspy.BiDirectional. Trả về dict hoặc None nếu lỗi/không cài."""
    try:
        import networkx as nx
        import numpy as np
        from cspy import BiDirectional

        # cspy quy ước node nguồn tên "Source", node đích tên "Sink"
        # res_cost = [số cung đi qua (resource đơn điệu), time]
        G = nx.DiGraph(directed=True, n_res=2)
        rename = {source: "Source", target: "Sink"}
        for (i, j) in arcs:
            if j == source or i == target:
                continue  # không quay lại nguồn / không đi ra khỏi đích
            G.add_edge(rename.get(i, i), rename.get(j, j),
                       res_cost=np.array([1.0, time_[(i, j)]]),
                       weight=dist[(i, j)])

        max_res = [float(len(arcs)), float(t_max)]
        algo = BiDirectional(G, max_res=max_res, min_res=[0.0, 0.0],
                             elementary=True)
        algo.run()
        try:
            found = algo.path
        except Exception:
            found = None  # cspy 0.1.2 raise khi không tồn tại đường khả thi
        if found is None:
            return {"status": "Infeasible", "path": None,
                    "total_distance": None, "total_time": None}
        path = [source if n == "Source" else (target if n == "Sink" else n)
                for n in found]
        d = sum(dist[(path[k], path[k + 1])] for k in range(len(path) - 1))
        t = sum(time_[(path[k], path[k + 1])] for k in range(len(path) - 1))
        return {"status": "Optimal", "path": path,
                "total_distance": d, "total_time": t}
    except Exception as exc:  # cspy không bắt buộc - chỉ là lớp kiểm chứng thêm
        print(f"  [cspy] Bỏ qua lớp kiểm chứng cspy: {exc}")
        return None


# ------------------------------------------------------------
# 7. PHÂN TÍCH ĐỘ NHẠY THEO NHIỀU MỨC Tmax
# ------------------------------------------------------------
def sensitivity_analysis(arcs, dist, time_, nodes, t_max_values,
                         out_csv=OUT_DIR / "rcsp_sensitivity.csv"):
    """Chạy MILP trên dãy Tmax, ghi nhận nghiệm và các điểm route thay đổi."""
    rows, prev_path = [], None
    for t_max in t_max_values:
        res = solve_rcsp_milp(arcs, dist, time_, nodes, t_max)
        path_str = "-".join(res["path"]) if res["path"] else ""
        route_changed = (res["path"] != prev_path)
        rows.append({
            "t_max": "unconstrained" if t_max is None else t_max,
            "status": res["status"],
            "optimal_path": path_str,
            "total_distance": res["total_distance"] if res["path"] else "",
            "total_time": res["total_time"] if res["path"] else "",
            "route_changed_vs_previous": route_changed,
        })
        prev_path = res["path"]

    with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Đã lưu bảng độ nhạy: {out_csv.name}")
    return rows


# ------------------------------------------------------------
# MAIN: chạy toàn bộ quy trình WS2
# ------------------------------------------------------------
def main():
    print("#" * 60)
    print("# WORKSTREAM 2: RCSP - MILP 0-1 (PuLP + CBC)")
    print(f"# PuLP version: {pulp.__version__} | Solver: CBC (COIN-OR)")
    print("#" * 60)

    # --- Task: đọc dữ liệu RCSP ---
    edges = load_rcsp_edges()
    arcs, dist, time_, nodes = build_arcs(edges)
    print(f"\nĐọc {RCSP_CSV.name}: {len(edges)} cạnh vô hướng "
          f"-> {len(arcs)} cung có hướng, {len(nodes)} node.")

    # --- Task: đối chiếu với network WS1 ---
    print()
    consistent = check_network_consistency()
    assert consistent, "Network RCSP không khớp network Seervada WS1!"

    # --- Task: shortest path KHÔNG ràng buộc (mốc so sánh) ---
    sp = solve_rcsp_milp(arcs, dist, time_, nodes, t_max=None)
    print("\n" + "=" * 60)
    print("SHORTEST PATH KHÔNG RÀNG BUỘC (mốc so sánh)")
    print("=" * 60)
    print(f"- Đường đi: {' -> '.join(sp['path'])}")
    print(f"- Tổng distance: {sp['total_distance']:g} | "
          f"Tổng time: {sp['total_time']:g} phút")

    # --- Xác định dải Tmax cho sensitivity ---
    # Chạy thử cho thấy: min-time path = 18 phút (dưới 18 là infeasible),
    # shortest path không ràng buộc tốn 19-20 phút tùy tuyến.
    # => Quét 16..23 (bao trùm vùng infeasible -> vùng hết ràng buộc) + unconstrained.
    t_max_values = list(range(16, 24)) + [None]

    # --- Task: sensitivity analysis ---
    print("\n" + "=" * 60)
    print("PHÂN TÍCH ĐỘ NHẠY THEO Tmax")
    print("=" * 60)
    sens_rows = sensitivity_analysis(arcs, dist, time_, nodes, t_max_values)
    for r in sens_rows:
        print(f"  Tmax={r['t_max']:>13} | {r['status']:<10} | "
              f"dist={str(r['total_distance']):>5} | time={str(r['total_time']):>5} | "
              f"{r['optimal_path']}"
              + ("   <-- route đổi" if r["route_changed_vs_previous"] else ""))

    # --- Task: verify + cross-verify từng mức Tmax ---
    print("\n" + "=" * 60)
    print("KIỂM CHỨNG: MILP vs BRUTE-FORCE vs CSPY")
    print("=" * 60)
    verif_rows = []
    for t_max in t_max_values:
        milp = solve_rcsp_milp(arcs, dist, time_, nodes, t_max)
        bf = brute_force_rcsp(arcs, dist, time_, t_max)
        cspy_res = cspy_rcsp(arcs, dist, time_, t_max) if t_max is not None else None

        # Verify nghiệm MILP là đường đi hợp lệ
        checks = verify_solution(milp, dist, time_, t_max)
        path_ok = all(checks.values()) if milp["status"] == "Optimal" else None

        # So khớp giá trị tối ưu giữa các lớp
        status_match = ((milp["status"] == "Optimal") ==
                        (bf["status"] == "Optimal"))
        dist_match = (status_match and
                      (milp["status"] != "Optimal" or
                       abs(milp["total_distance"] - bf["best_distance"]) < 1e-9))
        cspy_match = (cspy_res is None or
                      (cspy_res["status"] == milp["status"] and
                       (milp["status"] != "Optimal" or
                        abs(cspy_res["total_distance"] - milp["total_distance"]) < 1e-9)))

        label = "unconstrained" if t_max is None else t_max
        verif_rows.append({
            "t_max": label,
            "milp_status": milp["status"],
            "milp_path": "-".join(milp["path"]) if milp["path"] else "",
            "milp_distance": milp["total_distance"] if milp["path"] else "",
            "milp_path_valid": path_ok if path_ok is not None else "",
            "bf_status": bf["status"],
            "bf_best_distance": bf["best_distance"] if bf["best_distance"] else "",
            "bf_n_feasible_paths": bf["n_paths_feasible"],
            "bf_optimal_paths": " | ".join("-".join(p) for p, _, _ in bf["best_paths"]),
            "cspy_status": cspy_res["status"] if cspy_res else "n/a",
            "cspy_distance": (cspy_res["total_distance"]
                              if cspy_res and cspy_res["path"] else ""),
            "milp_vs_bf_match": status_match and dist_match,
            "milp_vs_cspy_match": cspy_match,
        })
        print(f"  Tmax={str(label):>13} | MILP={milp['status']:<10} "
              f"| BF khả thi={bf['n_paths_feasible']:>2}/{bf['n_paths_total']} "
              f"| khớp BF: {status_match and dist_match} | khớp cspy: {cspy_match}")

    out_verif = OUT_DIR / "rcsp_verification.csv"
    with open(out_verif, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(verif_rows[0].keys()))
        writer.writeheader()
        writer.writerows(verif_rows)
    print(f"Đã lưu bảng kiểm chứng: {out_verif.name}")

    assert all(r["milp_vs_bf_match"] for r in verif_rows), \
        "MILP và brute-force KHÔNG khớp nhau!"
    assert all(r["milp_vs_cspy_match"] for r in verif_rows), \
        "MILP và cspy KHÔNG khớp nhau!"

    # --- Task: so sánh SP vs RCSP ---
    print("\n" + "=" * 60)
    print("SO SÁNH SHORTEST PATH vs RCSP (trade-off distance / time)")
    print("=" * 60)
    print(f"  SP không ràng buộc : dist={sp['total_distance']:g}, "
          f"time={sp['total_time']:g} ({' -> '.join(sp['path'])})")
    for r in sens_rows:
        if r["status"] == "Optimal" and r["t_max"] != "unconstrained":
            extra = float(r["total_distance"]) - sp["total_distance"]
            note = f" (+{extra:g} km so với SP)" if extra > 0 else " (bằng SP)"
            print(f"  Tmax={r['t_max']:>2}: dist={r['total_distance']}, "
                  f"time={r['total_time']}{note}")

    print("\nHOÀN THÀNH WS2. Mọi lớp kiểm chứng đều khớp.")


if __name__ == "__main__":
    main()
