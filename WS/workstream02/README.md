# BÁO CÁO WORKSTREAM 2: BÀI TOÁN ĐƯỜNG ĐI NGẮN NHẤT CÓ RÀNG BUỘC TÀI NGUYÊN (RCSP)
**Sinh viên phụ trách:** Ngọc Hân
**Quy trình:** MILP formulation → solver → solution → verification → sensitivity

---

## 1. Dữ liệu đầu vào

- Nguồn: `workstream03/seervada_rcsp_teaching.csv` (bàn giao từ Workstream 3).
- Mạng Seervada Park: 7 node {O, A, B, C, D, E, T}, 12 cạnh vô hướng; mỗi cạnh có `distance` (km) và `time` (phút).
- **Đối chiếu với network Seervada của Workstream 1** (`seervada_network.csv`): node, cạnh, distance và tính vô hướng **khớp 100%** (chi tiết tại `rcsp_network_consistency.csv`). Network RCSP = network WS1 + thuộc tính `time`.

## 2. Mô hình Quy hoạch tuyến tính nguyên 0–1 (MILP)

Mỗi cạnh vô hướng được tách thành 2 cung có hướng (24 cung). Với tập cung $A$, nguồn $O$, đích $T$:

**Biến quyết định:** $x_{ij} \in \{0, 1\}$ — cung $(i,j)$ có nằm trên đường đi hay không.

**Hàm mục tiêu:**
$$\min \sum_{(i,j) \in A} d_{ij} \, x_{ij}$$

**Ràng buộc cân bằng dòng** (đảm bảo tạo thành một đường đi O → T), với mỗi node $v$:
$$\sum_{j} x_{vj} - \sum_{i} x_{iv} = \begin{cases} +1 & v = O \\ -1 & v = T \\ 0 & \text{còn lại} \end{cases}$$

**Ràng buộc tài nguyên (thời gian):**
$$\sum_{(i,j) \in A} t_{ij} \, x_{ij} \le T_{max}$$

*Ghi chú:* vì mọi $d_{ij} > 0$ và bài toán cực tiểu hóa, chu trình tách rời không thể xuất hiện trong nghiệm tối ưu, nên không cần ràng buộc khử chu trình. Nghiệm vẫn được kiểm tra độc lập (mục 4).

## 3. Solver

- **Thư viện:** PuLP 2.9.0 (Python) — https://github.com/coin-or/pulp
- **Solver:** CBC (COIN-OR Branch and Cut), đi kèm sẵn trong PuLP, gọi qua `PULP_CBC_CMD`.
- **Excel Solver (bản đối chiếu):** cùng mô hình MILP 0–1 được dựng lại trong `rcsp_excel_solver.xlsx`, giải bằng Excel Solver (Simplex LP + Branch & Bound). Mô hình Solver đã lưu sẵn trong file.
- **Framework tham chiếu:** [torressa/cspy](https://github.com/torressa/cspy) — thư viện chuyên RCSP (công bố trên Journal of Open Source Software). Lý do chọn làm lớp kiểm chứng: cspy giải đúng lớp bài toán của dữ liệu này — đồ thị có cung mang cost (`distance`) và tiêu hao tài nguyên (`time`), tìm đường min-cost thỏa giới hạn `max_res` ($= T_{max}$), bằng thuật toán BiDirectional labeling (độc lập hoàn toàn với MILP).

## 4. Kiểm chứng nghiệm (Verification)

Bốn lớp kiểm chứng độc lập, chạy trên **mọi** mức $T_{max}$ (bảng đầy đủ của lớp 1–3: `rcsp_verification.csv`):

1. **Verify cấu trúc nghiệm MILP:** các cung được chọn ghép thành đúng một đường đi đơn liên tục O → T, không lặp node, không chu trình thừa, tổng distance/time khớp hàm mục tiêu, thỏa $T_{max}$. → **Đạt ở mọi mức.**
2. **Brute-force (phương pháp WS1):** liệt kê toàn bộ 28 simple paths O → T, tính time từng đường, lọc theo $T_{max}$, lấy min distance. → **Khớp MILP 100%.**
3. **cspy (BiDirectional labeling):** → **Khớp MILP 100%** (kể cả các mức infeasible).
4. **Excel Solver** (`rcsp_excel_solver.xlsx`, sheet `Độ nhạy`, $T_{max}$ = 16–23 và không ràng buộc): trạng thái và tổng khoảng cách tối ưu **khớp PuLP ở mọi mức**. Tại $T_{max} \ge 20$, Excel trả về tuyến đồng tối ưu O–A–B–E–D–T (13 km / 19 phút) thay vì O–A–B–D–T (13 km / 20 phút) — cả hai cùng tối ưu, chỉ khác cách solver chọn giữa các nghiệm hòa.

## 5. Phân tích độ nhạy theo $T_{max}$ (bảng đầy đủ: `rcsp_sensitivity.csv`)

| $T_{max}$ (phút) | Trạng thái | Đường đi tối ưu | Distance | Time | Ghi chú |
|---|---|---|---|---|---|
| < 18 | **Infeasible** | — | — | — | Không tồn tại đường nào thỏa ràng buộc (đường nhanh nhất cần 18 phút) |
| 18 | Optimal | **O–A–D–T** | **14** | 18 | Route đổi; chấp nhận +1 km để kịp thời gian. Đồng tối ưu: O–B–E–D–T, O–C–E–D–T (đều 14 km / 18 phút) |
| 19 | Optimal | **O–A–B–E–D–T** | **13** | 19 | Route đổi; nghiệm 13 km duy nhất còn khả thi |
| ≥ 20 | Optimal | **O–A–B–D–T** | **13** | 20 | Ràng buộc hết hiệu lực; đồng tối ưu: O–A–B–E–D–T (13 km / 19 phút) |

**Các điểm route thay đổi:** $T_{max} = 18$ (infeasible → 14 km), $T_{max} = 19$ (14 km → 13 km qua E), $T_{max} = 20$ (hết ràng buộc).

**⚠️ Đính chính so với tài liệu WS3:** `DATA_ENGINEERING_REPORT.md` (mục 2.2) ghi rằng tại $T_{max} = 18$ nghiệm chuyển sang O–B–E–T / O–C–E–T với distance 15. Kết quả giải thực tế (đã kiểm chứng bằng cả 3 phương pháp) cho thấy **tối ưu tại $T_{max} = 18$ là distance 14** với 3 tuyến đồng tối ưu: **O–A–D–T, O–B–E–D–T, O–C–E–D–T** (đều 18 phút). Tuyến O–B–E–T (15 km, 18 phút) khả thi nhưng không tối ưu.

## 6. So sánh Shortest Path (không ràng buộc) vs RCSP

| Kịch bản | Đường đi | Distance | Time |
|---|---|---|---|
| SP không ràng buộc (WS1) | O–A–B–D–T *(hoặc O–A–B–E–D–T)* | 13 | 20 *(19)* |
| RCSP, $T_{max} = 19$ | O–A–B–E–D–T | 13 | 19 |
| RCSP, $T_{max} = 18$ | O–A–D–T | 14 (+1) | 18 |
| RCSP, $T_{max} < 18$ | Vô nghiệm | — | — |

**Nhận xét trade-off:** Khi ngân sách thời gian còn rộng ($T_{max} \ge 19$), RCSP giữ nguyên khoảng cách tối ưu 13 km — ràng buộc chỉ "chọn lọc" giữa các tuyến đồng tối ưu. Khi siết xuống 18 phút, người ra quyết định phải **đánh đổi +1 km** (7,7%) để tiết kiệm 1–2 phút. Dưới 18 phút, không tồn tại phương án khả thi — đây chính là giá trị của mô hình RCSP so với shortest path thuần: phát hiện được giới hạn khả thi của hệ thống.

## 7. Sản phẩm bàn giao (cho Workstream 6)

| File | Nội dung |
|---|---|
| `rcsp_milp.py` | Mô hình MILP + solver + verification + sensitivity (chạy: `python workstream02/rcsp_milp.py` từ repo root) |
| `rcsp_sensitivity.csv` | Bảng độ nhạy: Tmax, status, path, distance, time, điểm route đổi |
| `rcsp_verification.csv` | Bảng kiểm chứng chéo MILP / brute-force / cspy, kèm các tuyến đồng tối ưu |
| `rcsp_network_consistency.csv` | Bảng đối chiếu network RCSP vs WS1 |
| `rcsp_excel_solver.xlsx` | Mô hình MILP trên Excel Solver: sheet `RCSP` (biến 0/1, mục tiêu, cân bằng dòng, ràng buộc $T_{max}$, nghiệm $T_{max} = 18$), sheet `Độ nhạy`. Giải lại: đổi ô `B5` → Data → Solver → Solve |

**Yêu cầu môi trường:** `pip install pulp==2.9.0` (bắt buộc — PuLP 4.x đổi API); `pip install cspy networkx numpy` (tùy chọn, cho lớp kiểm chứng thứ 3).
