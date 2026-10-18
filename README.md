# ShortestPath pipeline

Pipeline cho Seervada và PEMS-BAY. Các phép biến đổi dữ liệu và hợp đồng
workstream nằm trong `src/`; script chỉ điều phối tham số, gọi API và lưu kết quả.
Chạy từ thư mục gốc repository.

Cài dependencies từ file chuẩn:

```powershell
python -m pip install -r requirements.txt
```

## Sơ đồ phụ thuộc

```text
M0 common ──> M1 network ──┬──> M2 shortest_path ──> M3 rcsp
                           ├──> M3 rcsp                │
                           ├──> M4 preprocess/adapter  │
                           └──> M8 routing <───────────┘
                                  ▲    ▲
                    ┌─────────────┘    └── I7: weighted shortest path
                    │
M4 ──> M5 baselines ─┼──> M7 evaluation ────────────┐
  └──> M6 nn ───────┘                               │
M5/M6 ── I5 ──> M7, M8                              │
M2 ── I2 ───────────────────────────────────────────┤
M3 ── I3 ───────────────────────────────────────────┼──> M9 report
M8 ── I8 ───────────────────────────────────────────┘
```

## Thứ tự chạy

```powershell
python scripts\run_workstream01.py --dataset seervada --artifacts-root .
python scripts\run_workstream02.py --dataset seervada --artifacts-root .
python scripts\run_workstream03.py --dataset seervada --artifacts-root .
python scripts\run_workstream04.py --dataset seervada --artifacts-root .
python scripts\run_workstream05.py --dataset seervada --artifacts-root .
python scripts\run_workstream06.py --dataset seervada --artifacts-root .
python scripts\make_report.py --dataset seervada --artifacts-root .
```

Tất cả runner dùng chung `stage_dir(dataset, stage, root)` để xác định đường
dẫn. `--artifacts-root` mặc định là gốc repository và là gốc thay thế cho cây
`artifacts/`, `data/processed/` và `docs/report/`. `--output-dir` vẫn được nhận
như alias tương thích nhưng phát cảnh báo deprecated. Root giống nhau phải được
truyền cho mọi stage để downstream đọc đúng các file upstream. Khi thiếu file
ở cấu trúc mới, runner chỉ với Seervada sẽ thử `workstreamXX/outputs/` cũ và
cảnh báo; file không bị di chuyển.

| Stage | Input chính | Output |
|---|---|---|
| WS1 | YAML adapter và nguồn network | `artifacts/<ds>/network/` (I1), `artifacts/<ds>/paths/` (I2) |
| WS2 | WS1 `network/` I1, cấu hình `rcsp_path` | `artifacts/<ds>/rcsp/` (I3) |
| WS3 | WS1 I1 network, adapter observations (PEMS-BAY Parquet trong `data/processed/<ds>/`) | `data/processed/<ds>/` (I4) |
| WS4 | WS1 `network/` I1, WS3 `data/processed/<ds>/` | `artifacts/<ds>/predictions/` (I5), `artifacts/<ds>/metrics/` (I6) |
| WS5 | WS1 `network/` I1, WS3 `data/processed/<ds>/` | `artifacts/<ds>/predictions/` (I5), `artifacts/<ds>/metrics/` (I6) |
| WS6 | WS1 I1, WS2 I3, WS3 I4, WS4/5 I5 | `artifacts/<ds>/routing/` (I7/I8); contract errors ở `artifacts/<ds>/_errors/` |
| make_report | WS1 paths, WS2 RCSP, WS4/5 metrics, WS6 routing | `docs/report/<ds>_report.md` |
| build_dataset (nhánh phụ) | WS1 I1 và PEMS-BAY `traffic_speed_long.parquet` | `data/processed/pemsbay/model_dataset/` (không được WS4–WS6 dùng) |

Raw PEMS-BAY Parquet và quality report được ghi vào
`data/processed/pemsbay/`. Luồng chính chạy WS1 rồi WS3; WS3 gọi adapter để
tổng hợp thành I4 trước khi chia ngày train/valid/test. WS4–WS6 chỉ đọc các
split I4 này. `build_dataset.py` là nhánh phụ tạo dữ liệu model riêng trong
`data/processed/pemsbay/model_dataset/`, không phải prerequisite của WS4–WS6.

Ví dụ luồng chính:

```powershell
python scripts\run_workstream01.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream03.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream04.py --dataset pemsbay --artifacts-root .
```

PEMS-BAY để `sensor_ids`, `source` và `target` trống theo mặc định. Adapter
chọn `n_sensors` cảm biến liên thông bằng BFS từ sensor bậc cao nhất (thử
các seed kế tiếp nếu component không đủ; `seed_sensor` đã cấu hình sẽ cố định
seed), duyệt neighbor theo ID; cảm biến thiếu tọa độ, adjacency hoặc tốc độ
hợp lệ bị loại. Cây BFS được bổ sung từ `extra_edges=3`
đến tối đa 9 cạnh ngoài cây, ưu tiên chu trình có tổng chiều dài Haversine
ngắn nhất, rồi tie-break theo ID. Với mỗi topology, chỉ chọn cặp source/target
có số simple path trong `[min_paths, max_paths]`; bộ đếm dừng khi đạt
`max_paths + 1`, không tự tăng `max_paths`. Cặp được ưu tiên theo khoảng cách
shortest-path Haversine lớn nhất, rồi số path gần khoảng 50–500
(ưu tiên gần 200) và ID.
Danh sách sensor, số cạnh/path, endpoint và tiêu chí được lưu trong metadata
adapter. Có thể cấu hình danh sách/cặp tường minh qua YAML.
`direction_policy` chọn giữ cung adjacency (`directed`) hoặc hợp nhất thành
cạnh vô hướng (`undirected`). Các khung giờ mặc định là night (00–06),
morning_peak (06–09), midday (09–16), evening_peak (16–19), evening (19–24);
có thể thay thế trong `configs/pemsbay.yaml`.

Luồng PEMS-BAY thống nhất:

```text
data/raw_pems_bay (H5/PKL/CSV)
  -> scripts/run_preprocess_pems_bay.py
  -> src/adapters/pemsbay_prepare.py
  -> traffic_speed_long.parquet + báo cáo chất lượng
  -> WS1 publishes I1 network
  -> WS3 PemsBayAdapter.build_observations
       -> clean 5-minute speeds, enforce min_slot_coverage
       -> average travel_time by (edge_id, day, time_slot)
       -> chronological I4 train/valid/test splits
  -> WS4–WS6 read the aggregated I4 splits
```

Parquet đầu vào adapter yêu cầu `time_index`, `sensor_id`, `speed`; `timestamp`
là tùy chọn. Preprocess raw hiện xuất đủ bốn cột, trong đó `timestamp` có thể
null.
`build_observations()` gán tốc độ sensor tại endpoint `edge.v` cho cạnh (với
cạnh directed đây là sensor downstream; cạnh undirected dùng endpoint `v`
theo thứ tự node ổn định), làm sạch và gộp thành travel-time trung bình theo
cạnh, ngày và `time_slots`. Mỗi cell cần tỷ lệ sample 5 phút hợp lệ ít nhất
`min_slot_coverage` (mặc định 0.5); ngày chỉ được giữ nếu mọi cạnh đạt ngưỡng
ở mọi khung giờ. Nội suy chỉ áp dụng cho gap nội bộ không dài hơn
`max_speed_imputation_gap`. Số ngày bị loại vì thiếu coverage được ghi trong
`preprocessing_pipeline.json` cùng metadata adapter.
Tốc độ được hiểu mặc định là mph; travel time (phút) dùng
`distance_km / (speed_mph * 1.609344) * 60`. Chiều dài Haversine là xấp xỉ
đường chim bay, không phải chiều dài đường thực tế. `build_dataset.py` chỉ đọc
Parquet đã preprocess và tạo nhánh phụ `model_dataset`; WS4–WS6 không đọc nhánh
này. RCSP vẫn chỉ chạy khi dataset có `rcsp_path` tương ứng được cấu hình.

Launcher nhận `--input-dir`, `--artifacts-root`, và `--log-level`; mặc định
lần lượt là `data/raw_pems_bay`, gốc repository, và `INFO`. `--output-dir` là
alias deprecated của `--artifacts-root`.

`run_workstream03.py` gọi `src.preprocess.prepare_observation_splits`: split
theo ngày tuần tự, không shuffle; one-hot category và scaler distance chỉ fit
trên train. Các tên file X/y, raw splits, manifest và pipeline JSON được giữ
tương thích với WS4/WS5 hiện tại.

## Hợp đồng I1–I8

Schema cột bắt buộc, file trao đổi và producer/consumer cụ thể được ghi trong
[docs/contracts/interfaces.md](docs/contracts/interfaces.md).

| ID | Từ → Đến | Nội dung / cơ chế | Trạng thái |
|---|---|---|---|
| I1 | M1 → M2, M3, M4, M8 | Network nodes/edges/problem parameters; CSV loader và adapter | Đã có |
| I2 | M2 → M3, M8, M9 | Simple paths và shortest path; file CSV + API | Đã có |
| I3 | M3 → M8, M9 | WS2 ghi `rcsp_sensitivity.csv`; WS6 đọc các dòng `Optimal`, chuyển route thành `RouteReference` trung gian và chấm bằng actual test. M8 không import `src.rcsp`. | Đã có cho dataset có RCSP input |
| I4 | M4 → M5, M6, M7, M8 | Train/valid/test, fitted pipeline, split manifest; file | Đã có |
| I5 | M5, M6 → M7, M8 | Prediction theo khóa `edge_id, day, time_slot`; file | Đã có |
| I6 | M7 ← M5, M6; M7 → M9 | Hàm evaluation và bảng metrics; API + file | Đã có |
| I7 | M8 → M2 | Gọi shortest path với edge weights tùy chọn | Đã có |
| I8 | M8 → M9 | Routing result theo slot và `method_family`/nguồn trọng số; file | Đã có |

## Module M0–M9

| ID | Module | Trách nhiệm | Trạng thái |
|---|---|---|---|
| M0 | `src/common` | Config, file I/O, schema validators, error contracts | Đã có; logging chuẩn hóa còn thiếu |
| M1 | `src/network`, `src/adapters` | Đọc/mã hóa/kiểm tra network Seervada hoặc subnetwork PEMS-BAY | Đã có |
| M2 | `src/shortest_path` | Dijkstra, simple paths, cross-check; Dijkstra nhận weights tùy chọn | Đã có |
| M3 | `src/rcsp` | 0–1 MILP, solver, kiểm chứng và sensitivity | Đã có, phụ thuộc input/solver |
| M4 | `src/preprocess`, `src/adapters` | Làm sạch, features, chronological split, pipeline và data dictionary | Đã có |
| M5 | `src/models/baselines` | Group Mean và Linear Regression | Đã có |
| M6 | `src/models/nn` | MLP, fit và training history | Đã có |
| M7 | `src/evaluation`, `src/common/metrics.py` | Regression metrics, alignment và lựa chọn model từ validation | Đã có |
| M8 | `src/routing` | Route weights, shortest-path selection và scoring bằng actual; RCSP routes chỉ nhận dạng tên + tuple node | Đã có |
| M9 | `src/report` | Render I2, I3, I6, I8; tổng hợp Markdown với `build_report` | Đã có |

Adapter implement `build_network()` và `build_observations()`; khoảng cách được
chuẩn hóa về km và travel time về phút. PEMS-BAY dùng Haversine xấp xỉ và gán
tốc độ sensor đích cho cạnh đi vào sensor đó.

Contract I3→M8: M3/WS2 xuất các route và giới hạn trong file CSV
`rcsp_sensitivity.csv`. M8 không phụ thuộc package RCSP; WS6 parse đường đi và
truyền mỗi nghiệm tối ưu qua `RouteReference`. Mỗi route phải nối đúng source
với target và chỉ đi trên cạnh có trong network. Actual test travel time dùng
để tính `actual_time` và regret so với Oracle.

## Tạo báo cáo hợp nhất

`scripts/make_report.py` đọc các file kết quả của WS1–WS6 rồi gọi
`src.report.build_report(...)`; output mặc định là
`docs/report/<dataset>_report.md`. Nếu một nhóm kết quả chưa tồn tại, báo cáo
hiển thị `chưa có kết quả` cho mục tương ứng thay vì dừng.
