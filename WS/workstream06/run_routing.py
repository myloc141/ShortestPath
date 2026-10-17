"""
WS6 - Routing Experiment & Analysis (Seervada Park)
====================================================
Pipeline:
  trọng số (cố định / dự báo) -> route -> so sánh -> đánh giá bằng ACTUAL travel time trên test set.

Cách chạy (từ thư mục gốc repo RCSP):
    python workstream06/run_routing.py

Đầu vào (đường dẫn sửa ở khối CẤU HÌNH):
    data/seervada_network.csv          node_u, node_v, distance, directed
    workstream03/train.csv, test.csv   day, day_of_week, is_weekend, time_slot, time_slot_name,
                                       edge_id, node_u, node_v, distance, travel_time
    workstream04/pred_groupmean_raw.csv, pred_linearreg_raw.csv   cột y_pred (cùng thứ tự dòng test.csv)
    workstream05/pred_nn.csv                                      cột y_pred (cùng thứ tự dòng test.csv)

Đầu ra (workstream06/outputs/):
    precommitted_rules.md          quy tắc chọn mô hình/khung giờ, ghi TRƯỚC khi chạy routing
    selection.json                 kết quả áp dụng quy tắc (chỉ dựa trên train + metric dự báo)
    routing_results_all.csv        mỗi dòng = (khung giờ, ngày test, phương pháp)
    summary_by_slot_method.csv     tổng hợp theo (khung giờ, phương pháp)
    route_by_slot.csv              route phổ biến nhất theo (phương pháp, khung giờ)
    model_comparison.csv           so sánh từng cặp phương pháp
    results_summary.md             bảng tóm tắt dạng văn bản
    fig_actual_time_main_slots.png, fig_regret_all_slots.png, fig_route_map.png
"""
import argparse
import heapq
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# =============================================================================
# CẤU HÌNH
# =============================================================================
SOURCE, TARGET = "O", "T"

NETWORK_FILE = "data/seervada_network.csv"
TRAIN_FILE = "workstream03/train.csv"
TEST_FILE = "workstream03/test.csv"

# Tên mô hình -> file prediction. Thứ tự dòng PHẢI trùng thứ tự dòng của test.csv.
PRED_FILES = {
    "GroupMean": "workstream04/pred_groupmean_raw.csv",
    "LinearRegression": "workstream04/pred_linearreg_raw.csv",
    "NeuralNet": "workstream05/pred_nn.csv",
}
# File có kèm khóa (edge_id, time_slot, y_true) dùng để kiểm tra thứ tự dòng. NN không có.
KEYED_FILES = {
    "GroupMean": "workstream04/pred_groupmean_withkey.csv",
    "LinearRegression": "workstream04/pred_linearreg_withkey.csv",
}
# (MAE, RMSE) mà WS4/WS5 đã báo cáo, dùng để kiểm tra đã ghép đúng prediction với test set.
# LinearRegression: chưa có số trong tài liệu nhóm gửi -> điền (MAE, RMSE) nếu muốn kiểm tra.
REPORTED_METRICS = {
    "GroupMean": (0.9841, 1.4110),
    "LinearRegression": None,
    "NeuralNet": (0.7038, 0.9777),
}

# Nghiệm RCSP của WS2 (distance km, time phút). Dùng làm route tham chiếu, đánh giá bằng actual time.
# Nếu WS2 đổi nghiệm, sửa danh sách này (nhãn, route).
RCSP_REFERENCE = [
    ("RCSP_T18_a", "O-A-D-T"),        # T=18: 14 km, 18 phút (3 nghiệm đồng tối ưu)
    ("RCSP_T18_b", "O-B-E-D-T"),
    ("RCSP_T18_c", "O-C-E-D-T"),
    ("RCSP_T19", "O-A-B-E-D-T"),      # T=19: 13 km, 19 phút
    ("RCSP_T20plus", "O-A-B-D-T"),    # T>=20: 13 km, 20 phút
]

FIXED_DIST = "Fixed_distance"      # trọng số cố định = distance trong seervada_network.csv
FIXED_MEAN = "Fixed_trainmean"     # trọng số cố định = travel_time trung bình toàn bộ train (mỗi cạnh)
ORACLE = "Oracle"                  # route tối ưu theo actual travel time của đúng ngày đó (chỉ để tham chiếu)
TOL = 1e-9


# =============================================================================
# Network & thuật toán
# =============================================================================
def edge_key(u, v):
    """Khóa cạnh vô hướng: (nút nhỏ, nút lớn)."""
    return tuple(sorted((str(u), str(v))))


def load_network(path):
    net = pd.read_csv(path)
    if "directed" in net.columns and net["directed"].astype(str).str.lower().isin(["true", "1"]).any():
        raise NotImplementedError("Script giả định mọi cạnh vô hướng (directed=False) theo quy ước đề bài.")
    dist = {}
    adj = {}
    for r in net.itertuples(index=False):
        k = edge_key(r.node_u, r.node_v)
        if k in dist:
            raise ValueError(f"Cạnh trùng trong network: {k}")
        dist[k] = float(r.distance)
        adj.setdefault(str(r.node_u), []).append(str(r.node_v))
        adj.setdefault(str(r.node_v), []).append(str(r.node_u))
    for n in adj:
        adj[n] = sorted(adj[n])
    return dist, adj


def simple_paths(adj, s, t):
    """Mọi đường đi đơn (không lặp nút) từ s đến t - brute force, đủ dùng cho mạng 7 nút."""
    out = []

    def dfs(node, path):
        if node == t:
            out.append(tuple(path))
            return
        for nb in adj[node]:
            if nb not in path:
                path.append(nb)
                dfs(nb, path)
                path.pop()

    dfs(s, [s])
    return out


def path_cost(path, w):
    try:
        return sum(w[edge_key(a, b)] for a, b in zip(path, path[1:]))
    except KeyError as e:
        raise ValueError(f"Route {'-'.join(path)} dùng cạnh {e} không có trong bảng trọng số") from None


def dijkstra_cost(adj, w, s, t):
    """Dijkstra chỉ trả về chi phí tối thiểu - dùng để kiểm chứng chéo với brute force."""
    best = {s: 0.0}
    heap = [(0.0, s)]
    done = set()
    while heap:
        c, u = heapq.heappop(heap)
        if u in done:
            continue
        done.add(u)
        if u == t:
            return c
        for v in adj[u]:
            nc = c + w[edge_key(u, v)]
            if nc < best.get(v, float("inf")) - 1e-15:
                best[v] = nc
                heapq.heappush(heap, (nc, v))
    return float("inf")


def best_route(paths, w):
    """Route tối ưu theo w. Quy ước hòa: ít cạnh hơn trước, sau đó theo thứ tự chữ cái của route.
    Trả về (route, chi phí, số route đồng tối ưu)."""
    scored = [(round(path_cost(p, w), 9), len(p), p) for p in paths]
    scored.sort()
    best_c = scored[0][0]
    n_ties = sum(1 for c, _, _ in scored if abs(c - best_c) <= 1e-8)
    return scored[0][2], scored[0][0], n_ties


def rstr(path):
    return "-".join(path)


# =============================================================================
# Nạp dữ liệu & kiểm tra
# =============================================================================
def load_inputs(root):
    dist, adj = load_network(root / NETWORK_FILE)
    train = pd.read_csv(root / TRAIN_FILE).reset_index(drop=True)
    test = pd.read_csv(root / TEST_FILE).reset_index(drop=True)
    for df in (train, test):
        df["ekey"] = [edge_key(u, v) for u, v in zip(df["node_u"], df["node_v"])]
    net_edges = set(dist)
    for name, df in (("train", train), ("test", test)):
        if set(df["ekey"]) != net_edges:
            raise ValueError(f"Tập cạnh của {name} không khớp network: {set(df['ekey']) ^ net_edges}")
    return dist, adj, train, test


def load_predictions(root, test):
    preds = {}
    for name, rel in PRED_FILES.items():
        p = pd.read_csv(root / rel)
        if "y_pred" in p.columns:
            col = "y_pred"
        elif p.shape[1] == 1:
            col = p.columns[0]
        else:
            raise ValueError(f"{rel}: không tìm thấy cột y_pred (các cột: {list(p.columns)})")
        if len(p) != len(test):
            raise ValueError(f"{rel}: {len(p)} dòng, test.csv có {len(test)} dòng")
        preds[name] = p[col].to_numpy(float)
    return preds


def metrics(y, p):
    e = p - y
    return float(np.mean(np.abs(e))), float(np.sqrt(np.mean(e ** 2)))


def check_alignment(root, test, preds):
    """Bảo đảm prediction được ghép đúng dòng với test.csv. Trả về danh sách thông báo."""
    msgs = []
    y = test["travel_time"].to_numpy(float)
    for name, rel in KEYED_FILES.items():
        path = root / rel
        if not path.exists():
            msgs.append(f"[bỏ qua] không thấy {rel}")
            continue
        k = pd.read_csv(path)
        if len(k) != len(test):
            raise ValueError(f"{rel}: số dòng khác test.csv")
        ok = np.array_equal(k["time_slot"].to_numpy(), test["time_slot"].to_numpy())
        if "edge_id" in k.columns and "edge_id" in test.columns:
            ok &= np.array_equal(k["edge_id"].astype(str).to_numpy(), test["edge_id"].astype(str).to_numpy())
        ok &= np.allclose(k["y_true"].to_numpy(float), y, atol=1e-6)
        ok &= np.allclose(k["y_pred"].to_numpy(float), preds[name], atol=1e-6)
        if not ok:
            raise ValueError(f"{rel}: khóa/y_true/y_pred không khớp test.csv hoặc file raw -> sai thứ tự dòng")
        msgs.append(f"[ok] {name}: file withkey khớp test.csv và file raw")
    for name, p in preds.items():
        mae, rmse = metrics(y, p)
        rep = REPORTED_METRICS.get(name)
        if rep is None:
            msgs.append(f"[info] {name}: MAE={mae:.4f}, RMSE={rmse:.4f} (chưa có số báo cáo để đối chiếu)")
        elif abs(mae - rep[0]) > 5e-4 or abs(rmse - rep[1]) > 5e-4:
            msgs.append(f"[CẢNH BÁO] {name}: tính lại MAE={mae:.4f}, RMSE={rmse:.4f} "
                        f"khác số WS đã báo cáo {rep} -> kiểm tra thứ tự dòng/phiên bản file prediction")
        else:
            msgs.append(f"[ok] {name}: MAE={mae:.4f}, RMSE={rmse:.4f} khớp số WS đã báo cáo")
    return msgs


# =============================================================================
# Quy tắc chốt TRƯỚC khi nhìn kết quả routing
# =============================================================================
def apply_rules(train, test, preds):
    y = test["travel_time"].to_numpy(float)
    m = {n: dict(zip(("MAE", "RMSE"), metrics(y, p))) for n, p in preds.items()}

    gm, lr = m["GroupMean"], m["LinearRegression"]
    if gm["MAE"] <= lr["MAE"] and gm["RMSE"] <= lr["RMSE"]:
        base, note = "GroupMean", "GroupMean tốt hơn hoặc bằng LinearRegression ở cả MAE và RMSE"
    elif lr["MAE"] <= gm["MAE"] and lr["RMSE"] <= gm["RMSE"]:
        base, note = "LinearRegression", "LinearRegression tốt hơn hoặc bằng GroupMean ở cả MAE và RMSE"
    else:
        base, note = "GroupMean", "MAE và RMSE mâu thuẫn -> mặc định GroupMean (đơn giản hơn); cần ghi rõ khi báo cáo"

    nn = m["NeuralNet"]
    nn_in = nn["MAE"] < m[base]["MAE"] and nn["RMSE"] < m[base]["RMSE"]

    slot_mean = train.groupby("time_slot")["travel_time"].mean()
    peak, off = int(slot_mean.idxmax()), int(slot_mean.idxmin())
    return {
        "metrics_on_test": m,
        "primary_baseline": base,
        "primary_baseline_note": note,
        "nn_included_in_main_comparison": bool(nn_in),
        "train_mean_travel_time_by_slot": {int(k): float(v) for k, v in slot_mean.items()},
        "main_slots": {"peak": peak, "offpeak": off},
    }


def write_rules(out, sel):
    txt = f"""# Quy tắc chốt trước khi chạy routing (WS6)
Ghi lúc: {datetime.now().isoformat(timespec='seconds')}

Các quy tắc dưới đây chỉ dùng train set và metric dự báo (MAE/RMSE trên test). Chúng được tính và ghi
TRƯỚC khi chạy routing, nên kết quả routing không ảnh hưởng đến việc chọn mô hình hay khung giờ.

1. **Baseline chính của routing**: trong GroupMean và LinearRegression, chọn mô hình có MAE và RMSE đều thấp hơn.
   Nếu hai chỉ số mâu thuẫn, mặc định GroupMean và ghi rõ trong báo cáo.
   -> Kết quả: **{sel['primary_baseline']}** ({sel['primary_baseline_note']}).
2. **NN trong so sánh chính**: NN được xem là phương pháp chính nếu MAE và RMSE đều thấp hơn baseline chính.
   Nếu không, NN vẫn được chạy nhưng chỉ là tham chiếu.
   -> Kết quả: NN {'**vào so sánh chính**' if sel['nn_included_in_main_comparison'] else '**chỉ tham chiếu**'}.
3. **Hai khung giờ chính**: khung có travel time trung bình trên train cao nhất (peak) và thấp nhất (off-peak).
   -> Kết quả: peak = khung {sel['main_slots']['peak']}, off-peak = khung {sel['main_slots']['offpeak']}.
   Cả 5 khung giờ vẫn được chạy và báo cáo ở phần bổ sung.
4. **Trọng số cố định**: chạy cả hai phiên bản - `{FIXED_DIST}` (distance trong network) và `{FIXED_MEAN}`
   (travel time trung bình của từng cạnh trên toàn bộ train).
5. **Đánh giá**: với mỗi (khung giờ, ngày test), route được đánh giá bằng tổng actual travel time của các cạnh
   trong đúng ngày đó. Predicted travel time không dùng để chấm điểm. Báo cáo trung bình và độ lệch chuẩn qua các ngày test,
   cùng "regret" = actual time của route - actual time của route tối ưu trong ngày đó (Oracle).
6. **Quy ước hòa**: khi nhiều route cùng tổng trọng số, chọn route ít cạnh hơn, rồi theo thứ tự chữ cái.
"""
    (out / "precommitted_rules.md").write_text(txt, encoding="utf-8")


# =============================================================================
# Thí nghiệm routing
# =============================================================================
def run_experiment(dist, adj, train, test, preds):
    paths = simple_paths(adj, SOURCE, TARGET)
    fixed_mean = train.groupby("ekey")["travel_time"].mean().to_dict()
    n_edges = len(dist)
    slot_name = (test.drop_duplicates("time_slot").set_index("time_slot")["time_slot_name"].to_dict()
                 if "time_slot_name" in test.columns else {})
    ref_paths = [(lab, tuple(r.split("-"))) for lab, r in RCSP_REFERENCE]

    rows = []
    for slot in sorted(test["time_slot"].unique()):
        for day in sorted(test["day"].unique()):
            sub = test[(test["time_slot"] == slot) & (test["day"] == day)]
            if len(sub) != n_edges:
                raise ValueError(f"Khung {slot}, ngày {day}: {len(sub)} dòng, cần {n_edges} (mỗi cạnh một dòng)")
            actual = dict(zip(sub["ekey"], sub["travel_time"].astype(float)))
            dow = str(sub["day_of_week"].iloc[0]) if "day_of_week" in sub.columns else np.nan

            weights = {FIXED_DIST: dist, FIXED_MEAN: fixed_mean}
            for name, arr in preds.items():
                weights["Pred_" + name] = dict(zip(sub["ekey"], arr[sub.index]))
            weights[ORACLE] = actual

            o_path, o_time, _ = best_route(paths, actual)

            def add(method, path, objective, predicted, n_ties):
                at = path_cost(path, actual)
                rows.append(dict(
                    time_slot=int(slot), slot_name=slot_name.get(slot, str(slot)), day=int(day), day_of_week=dow,
                    method=method, route=rstr(path), distance_km=path_cost(path, dist),
                    objective=objective, predicted_time=predicted, actual_time=at,
                    oracle_route=rstr(o_path), oracle_time=o_time, regret=at - o_time,
                    matches_oracle=bool(abs(at - o_time) < 1e-9), n_ties=n_ties))

            for method, w in weights.items():
                path, cost, n_ties = best_route(paths, w)
                if abs(dijkstra_cost(adj, w, SOURCE, TARGET) - cost) > 1e-7:
                    raise AssertionError(f"Dijkstra và brute force lệch nhau ({method}, khung {slot}, ngày {day})")
                if method == FIXED_DIST:
                    predicted = np.nan
                elif method == ORACLE:
                    predicted = np.nan
                else:
                    predicted = cost  # tổng thời gian mà chính mô hình/trọng số đó dự kiến cho route
                add(method, path, cost, predicted, n_ties)

            for lab, p in ref_paths:
                add(lab, p, np.nan, np.nan, 1)

    res = pd.DataFrame(rows)
    res["abs_pred_err"] = (res["predicted_time"] - res["actual_time"]).abs()
    return res, len(paths)


# =============================================================================
# Tổng hợp
# =============================================================================
def summarize(res):
    rows = []
    for (slot, method), df in res.groupby(["time_slot", "method"], sort=False):
        c = Counter(df["route"])
        modal, modal_n = c.most_common(1)[0]
        rows.append(dict(
            time_slot=slot, slot_name=df["slot_name"].iloc[0], method=method,
            modal_route=modal, modal_route_days=modal_n, n_distinct_routes=len(c),
            mean_distance_km=df["distance_km"].mean(),
            mean_predicted_time=df["predicted_time"].mean(),
            mean_actual_time=df["actual_time"].mean(),
            std_actual_time=df["actual_time"].std(),
            mean_regret=df["regret"].mean(),
            days_equal_oracle=int(df["matches_oracle"].sum()), n_days=len(df),
            mean_abs_pred_err=df["abs_pred_err"].mean()))
    return pd.DataFrame(rows)


def compare_pairs(res, pairs):
    idx = ["time_slot", "day"]
    rt = res.set_index(idx + ["method"])["route"].unstack("method")
    pt = res.set_index(idx + ["method"])["predicted_time"].unstack("method")
    at = res.set_index(idx + ["method"])["actual_time"].unstack("method")
    rows = []
    for a, b in pairs:
        for slot in sorted(rt.index.get_level_values(0).unique()):
            r, p, t = rt.xs(slot, level=0), pt.xs(slot, level=0), at.xs(slot, level=0)
            differs = r[a] != r[b]
            pred_diff = (p[a] - p[b]).abs() > 1e-6   # NaN -> False
            rows.append(dict(
                method_A=a, method_B=b, time_slot=slot, n_days=len(r),
                days_route_differs=int(differs.sum()),
                days_same_route_but_different_predicted_time=int(((~differs) & pred_diff).sum()),
                mean_actual_A_minus_B=float((t[a] - t[b]).mean())))
    return pd.DataFrame(rows)


# =============================================================================
# Biểu đồ
# =============================================================================
def fig_main_slots(summ, main_slots, methods, slot_names, out):
    fig, axes = plt.subplots(1, len(main_slots), figsize=(6.2 * len(main_slots), 4.8), sharey=True)
    for ax, (label, slot) in zip(np.atleast_1d(axes), main_slots.items()):
        d = summ[summ["time_slot"] == slot].set_index("method").loc[methods]
        x = np.arange(len(methods))
        ax.bar(x, d["mean_actual_time"], yerr=d["std_actual_time"].fillna(0), capsize=3, color="#4C78A8")
        ax.set_xticks(x)
        ax.set_xticklabels([m.replace("_", "\n") for m in methods], fontsize=8)
        ax.set_title(f"Khung {slot} ({slot_names.get(slot, slot)}) - {label}")
        ax.grid(axis="y", alpha=0.3)
    np.atleast_1d(axes)[0].set_ylabel("Actual travel time của route (phút), TB ± độ lệch chuẩn qua các ngày test")
    fig.tight_layout()
    fig.savefig(out / "fig_actual_time_main_slots.png", dpi=150)
    plt.close(fig)


def fig_regret(summ, methods, slots, out):
    methods = [m for m in methods if m != ORACLE]
    fig, ax = plt.subplots(figsize=(9, 4.8))
    width = 0.8 / len(methods)
    for i, m in enumerate(methods):
        d = summ[summ["method"] == m].set_index("time_slot").loc[slots]
        ax.bar(np.arange(len(slots)) + i * width, d["mean_regret"], width, label=m)
    ax.set_xticks(np.arange(len(slots)) + 0.4 - width / 2)
    ax.set_xticklabels([f"Khung {s}" for s in slots])
    ax.set_ylabel("Regret TB (phút) so với route tối ưu trong ngày")
    ax.set_title("Regret của từng phương pháp theo khung giờ (thấp hơn = tốt hơn)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out / "fig_regret_all_slots.png", dpi=150)
    plt.close(fig)


def fig_route_map(summ, methods, slots, out):
    d = summ[summ["method"].isin(methods)]
    routes = sorted(d["modal_route"].unique())
    rid = {r: i for i, r in enumerate(routes)}
    mat = np.array([[rid[d[(d["method"] == m) & (d["time_slot"] == s)]["modal_route"].iloc[0]] for s in slots]
                    for m in methods])
    cmap = plt.get_cmap("tab20", max(len(routes), 1))
    fig, ax = plt.subplots(figsize=(1.5 * len(slots) + 5, 0.6 * len(methods) + 2))
    ax.imshow(mat, cmap=cmap, vmin=-0.5, vmax=len(routes) - 0.5, aspect="auto")
    for i in range(len(methods)):
        for j in range(len(slots)):
            ax.text(j, i, f"R{mat[i, j] + 1}", ha="center", va="center", fontsize=10, fontweight="bold")
    ax.set_xticks(range(len(slots)))
    ax.set_xticklabels([f"Khung {s}" for s in slots])
    ax.set_yticks(range(len(methods)))
    ax.set_yticklabels(methods)
    ax.text(1.02, 0.5, "\n".join(f"R{i + 1} = {r}" for r, i in rid.items()),
            transform=ax.transAxes, va="center", fontsize=9)
    ax.set_title("Route phổ biến nhất (qua các ngày test) theo phương pháp và khung giờ")
    fig.tight_layout()
    fig.savefig(out / "fig_route_map.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


# =============================================================================
# Báo cáo văn bản
# =============================================================================
def md_table(df, digits=3):
    def f(x):
        if isinstance(x, (float, np.floating)):
            return "" if np.isnan(x) else f"{x:.{digits}f}"
        return str(x)
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for r in df.itertuples(index=False):
        lines.append("| " + " | ".join(f(x) for x in r) + " |")
    return "\n".join(lines)


def write_summary(out, sel, summ, comp, n_paths, align_msgs, methods, n_days):
    main = sel["main_slots"]
    cols = ["time_slot", "method", "modal_route", "n_distinct_routes", "mean_distance_km",
            "mean_predicted_time", "mean_actual_time", "std_actual_time", "mean_regret", "days_equal_oracle"]
    parts = ["# Kết quả WS6 - Routing Experiment\n",
             f"- Số đường đi đơn từ {SOURCE} đến {TARGET}: **{n_paths}**; số ngày test: **{n_days}** "
             f"(mẫu nhỏ nên kết quả mang tính mô tả).",
             f"- Baseline chính: **{sel['primary_baseline']}**; NN: "
             f"{'trong so sánh chính' if sel['nn_included_in_main_comparison'] else 'chỉ tham chiếu'}.",
             f"- Khung peak = {main['peak']}, off-peak = {main['offpeak']} (theo quy tắc chốt trước).",
             "- Dữ liệu travel time là dữ liệu MÔ PHỎNG, không phải giao thông thực tế.\n",
             "## Kiểm tra ghép dữ liệu", *[f"- {m}" for m in align_msgs], ""]
    for label, slot in main.items():
        d = summ[(summ["time_slot"] == slot) & (summ["method"].isin(methods))][cols].drop(columns="time_slot")
        parts += [f"## Khung {slot} ({label})", md_table(d), ""]
    parts += ["## So sánh từng cặp phương pháp (mọi khung giờ)", md_table(comp), ""]
    for a, b in [("Pred_GroupMean", "Pred_NeuralNet")]:
        c = comp[(comp["method_A"] == a) & (comp["method_B"] == b)]
        if len(c):
            total = int(c["days_route_differs"].sum())
            parts.append(f"**{a} so với {b}**: route khác nhau ở {total}/{int(c['n_days'].sum())} cặp (khung giờ, ngày). "
                         + ("Không có khác biệt về route - đây cũng là một kết quả cần ghi nhận."
                            if total == 0 else ""))
    (out / "results_summary.md").write_text("\n".join(parts) + "\n", encoding="utf-8")


# =============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="thư mục gốc repo RCSP")
    ap.add_argument("--out", type=Path, default=None, help="thư mục xuất kết quả")
    args = ap.parse_args()
    root = args.root
    out = args.out or (root / "workstream06" / "outputs")
    out.mkdir(parents=True, exist_ok=True)

    dist, adj, train, test = load_inputs(root)
    preds = load_predictions(root, test)
    align_msgs = check_alignment(root, test, preds)
    for m in align_msgs:
        print(m)

    # 1) Chốt quy tắc và ghi ra file TRƯỚC khi chạy routing
    sel = apply_rules(train, test, preds)
    write_rules(out, sel)
    (out / "selection.json").write_text(json.dumps(sel, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Baseline chính: {sel['primary_baseline']} | NN vào so sánh chính: {sel['nn_included_in_main_comparison']} "
          f"| khung peak/off-peak: {sel['main_slots']['peak']}/{sel['main_slots']['offpeak']}")

    # 2) Routing
    res, n_paths = run_experiment(dist, adj, train, test, preds)
    summ = summarize(res)

    core = [FIXED_DIST, FIXED_MEAN] + ["Pred_" + n for n in PRED_FILES] + [ORACLE]
    base = "Pred_" + sel["primary_baseline"]
    pairs = [(base, "Pred_NeuralNet"), ("Pred_GroupMean", "Pred_LinearRegression"),
             (FIXED_DIST, base), (FIXED_MEAN, base), (FIXED_DIST, FIXED_MEAN)]
    pairs = [(a, b) for a, b in pairs if a != b]
    comp = compare_pairs(res, pairs)

    # 3) Xuất bảng
    res.to_csv(out / "routing_results_all.csv", index=False, encoding="utf-8-sig")
    summ.to_csv(out / "summary_by_slot_method.csv", index=False, encoding="utf-8-sig")
    comp.to_csv(out / "model_comparison.csv", index=False, encoding="utf-8-sig")
    route_tbl = summ.pivot(index="method", columns="time_slot", values="modal_route")
    route_tbl.to_csv(out / "route_by_slot.csv", encoding="utf-8-sig")

    # 4) Biểu đồ
    slots = sorted(res["time_slot"].unique())
    slot_names = res.drop_duplicates("time_slot").set_index("time_slot")["slot_name"].to_dict()
    fig_main_slots(summ, sel["main_slots"], core, slot_names, out)
    fig_regret(summ, core, slots, out)
    fig_route_map(summ, core, slots, out)

    # 5) Tóm tắt
    write_summary(out, sel, summ, comp, n_paths, align_msgs, core, res["day"].nunique())
    print(f"Xong. Kết quả trong: {out}")


if __name__ == "__main__":
    main()