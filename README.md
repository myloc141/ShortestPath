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
python scripts\run_workstream05.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream06.py --dataset pemsbay --artifacts-root .
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
| M0 | `src/common` | Cấu hình pipeline, lỗi và contract, schema/validator dùng chung, I/O có metadata và regression metrics | Đã có |
| M1 | `src/network`, `src/adapters` | Schema network chuẩn, adjacency, validation; adapter Seervada/PEMS-BAY dựng network và observations | Đã có; PEMS-BAY cần dữ liệu traffic đã preprocess |
| M2 | `src/shortest_path` | Dijkstra (hỗ trợ edge weights tùy chọn), liệt kê simple paths và xác minh kết quả | Đã có |
| M3 | `src/rcsp` | Nạp/xác thực RCSP, vét cạn, 0–1 MILP, sensitivity và kiểm chứng | Đã có; MILP cần PuLP/CBC và WS2 cần RCSP input |
| M4 | `src/preprocess` | Làm sạch/tổng hợp observations, tạo features và chronological train/valid/test splits | Đã có; WS3 xuất I4 vào `data/processed/<dataset>/` |
| M5 | `src/models/baselines` | Group Mean và Linear Regression cho dự đoán travel time | Đã có; WS4 |
| M6 | `src/models/nn` | MLPRegressor, fit/predict và training history | Đã có; WS5 |
| M7 | `src/evaluation`, `src/common/metrics.py` | Regression metrics, kiểm tra alignment prediction và chọn model/slot bằng validation metrics | Đã có |
| M8 | `src/routing` | Chọn route theo edge weights hoặc route reference; chấm actual time/regret và so sánh phương pháp | Đã có; WS6 |
| M9 | `src/report` | Render I2, I3, I6, I8 thành Markdown và biểu đồ; `build_report` tổng hợp kết quả | Đã có |

Adapter implement `build_network()` và `build_observations()`; khoảng cách được
chuẩn hóa về km và travel time về phút. PEMS-BAY dùng Haversine xấp xỉ và gán
tốc độ sensor đích cho cạnh đi vào sensor đó.

Contract I3→M8: M3/WS2 xuất các route và giới hạn trong file CSV
`rcsp_sensitivity.csv`. M8 không phụ thuộc package RCSP; WS6 parse đường đi và
truyền mỗi nghiệm tối ưu qua `RouteReference`. Mỗi route phải nối đúng source
với target và chỉ đi trên cạnh có trong network. Actual test travel time dùng
để tính `actual_time` và regret so với Oracle.

## Dữ liệu, network và tiền xử lý

### 1. Tổng quan dữ liệu

| Thuộc tính | Seervada | PEMS-BAY |
|---|---|---|
| Loại dữ liệu | Network mẫu Seervada Park; 7 nút (`O, A, B, C, D, E, T`), 12 cạnh. Travel time là dữ liệu mô phỏng, không phải đo giao thông thực. | Dữ liệu tốc độ giao thông từ 325 cảm biến. Network con hiện tại có 25 cảm biến và 27 cạnh. |
| Nguồn | Network: `data/processed_seervada/seervada_network.csv`; observations mô phỏng: `data/processed_seervada/seervada_travel_time_SIMULATED.csv`. | Raw files trong `data/raw_pems_bay/`: `pems-bay.h5`, `graph_sensor_locations_bay.csv`, `adj_mx_bay.pkl`. Định dạng và tên file theo [DCRNN](https://github.com/liyaguang/DCRNN), nơi công bố PEMS-BAY. |
| Khoảng thời gian | 30 ngày đánh số 1–30; dữ liệu mô phỏng không có ngày lịch. | 2017-01-01 đến 2017-06-30 theo timestamp trong HDF5, tổng cộng 181 ngày lịch. |
| Tần suất quan sát | Đã tổng hợp thành 5 slot mỗi ngày; không phải chuỗi đo theo chu kỳ cố định. | Danh nghĩa 5 phút; kiểm tra HDF5 cho thấy một khoảng timestamp dài 65 phút, nên chuỗi không hoàn toàn đều. |
| Số quan sát sau xử lý | 1.800 dòng (30 ngày × 12 cạnh × 5 slot). | 24.435 dòng ở I4 sau tổng hợp (181 ngày × 27 cạnh × 5 slot); đây là số dòng edge/day/slot, không phải số mẫu tốc độ raw. |
| Đơn vị | Khoảng cách km; nhãn `travel_time` phút. | Tốc độ mph; khoảng cách Haversine km; nhãn `travel_time` phút. |

Các số dòng và số ngày sau xử lý khớp với
[`data/processed/seervada/split_manifest.csv`](data/processed/seervada/split_manifest.csv)
và
[`data/processed/pemsbay/split_manifest.csv`](data/processed/pemsbay/split_manifest.csv).
File `data/processed/pemsbay/data_quality_report.json` hiện không chứa thống
kê đầu vào (các trường để trống/`unavailable`); do đó không dùng file này để
khẳng định số mẫu thiếu hay số mẫu được nội suy. Kiểm tra trực tiếp raw HDF5
ghi nhận 52.116 timestamp, 325 cột cảm biến, không có NaN, có 521 giá trị tốc
độ bằng 0 và không có giá trị âm. Đây là thống kê raw, không phải số lỗi sau
tiền xử lý.

### 2. Dựng network

Cả hai adapter chuyển dữ liệu sang schema network chuẩn (nodes, edges, thuộc
tính cạnh và đơn vị), sau đó tạo adjacency list cho thuật toán đồ thị.
Seervada đọc 12 cạnh trực tiếp từ CSV; PEMS-BAY kết hợp tọa độ cảm biến,
adjacency matrix và traffic speed đã chuẩn hóa để dựng network con.
Kiểm tra network gồm ID nút/cạnh, cạnh trùng, self-loop, khoảng cách hữu hạn
và dương, đơn vị khoảng cách, tính liên thông; khi có endpoint, kiểm tra thêm
đường đi từ source tới target.

Cấu hình PEMS-BAY hiện để `sensor_ids`, `source` và `target` trống, đồng thời
đặt `n_sensors: 25`; adapter chọn tập cảm biến đủ điều kiện bằng BFS để tạo
network liên thông. Năm ID `400479, 400045, 404759, 400122, 400971` được nêu
trong đề xuất đều nằm trong network hiện tại, nhưng không phải toàn bộ tập:
25 ID thực tế được ghi trong `data/processed/pemsbay/preprocessing_pipeline.json`.
Không nên mô tả thí nghiệm đang chạy là network chỉ gồm 5 cảm biến. Khi không
cấu hình endpoint, adapter chọn cặp có đường đi ngắn nhất Haversine dài nhất
trong số các cặp có từ 5 đến 2.000 simple paths. Kết quả hiện tại là
`400479 → 400971` (7 simple paths); đây là lựa chọn theo tiêu chí của adapter,
không phải một cặp được cố định trong YAML.

Khoảng cách PEMS-BAY được tính bằng Haversine từ tọa độ cảm biến, tức xấp xỉ
đường chim bay chứ không phải chiều dài đường thực tế. Kết quả routing dựa
trên trọng số khoảng cách này cần được diễn giải với hạn chế đó.

### 3. Tiền xử lý

- **PEMS-BAY raw:** `scripts/run_preprocess_pems_bay.py` gọi
  `pemsbay_prepare.py` để xuất tốc độ dạng long-form Parquet cùng báo cáo
  chất lượng; bước này giữ giá trị thiếu, không tự nội suy.
- **Làm sạch tốc độ:** giá trị không phải số, không hữu hạn hoặc `<= 0` được
  xem là thiếu. Chỉ nội suy tuyến tính gap nội bộ tối đa 3 mẫu 5 phút (15
  phút), khi hai đầu gap đúng cadence; không ngoại suy đầu/cuối chuỗi và không
  lấp gap dài hoặc có timestamp bất thường. Không có ngưỡng trên để cắt tốc độ
  cao. Với cấu hình hiện tại, mỗi cạnh nhận tốc độ cảm biến ở endpoint `v`.
- **Tính travel time:** `distance_km / (speed_mph × 1.609344) × 60`, kết quả
  là phút. Sau đó lấy trung bình travel time trong từng (cạnh, ngày, slot);
  không lấy nghịch đảo tốc độ trung bình để tính nhãn.
- **Kiểm tra coverage:** mỗi ô cạnh/ngày/slot phải có ít nhất 50% mẫu 5 phút
  hợp lệ hoặc đã nội suy. Một ngày chỉ được giữ nếu mọi cạnh đều đạt ngưỡng ở
  cả 5 slot. Metadata pipeline ghi nhận 181 ngày được giữ, 0 ngày bị loại do
  coverage.
- **Seervada:** dùng CSV travel time mô phỏng đã tổng hợp sẵn theo cạnh,
  ngày và slot; adapter kiểm tra khóa, đơn vị, cạnh và khoảng cách so với
  network.

### 4. Định nghĩa time slot

Các khoảng giờ dùng dạng `[bắt đầu, kết thúc)` theo timezone của cấu hình;
PEMS-BAY dùng `America/Los_Angeles`.

| Dataset | Slot | Khoảng giờ |
|---|---|---|
| Seervada | 1 | 06:00–08:00 |
| Seervada | 2 | 08:00–10:00 |
| Seervada | 3 | 11:30–13:30 |
| Seervada | 4 | 16:30–18:30 |
| Seervada | 5 | 19:30–21:30 |
| PEMS-BAY | `night` | 00:00–06:00 |
| PEMS-BAY | `morning_peak` | 06:00–09:00 |
| PEMS-BAY | `midday` | 09:00–16:00 |
| PEMS-BAY | `evening_peak` | 16:00–19:00 |
| PEMS-BAY | `evening` | 19:00–24:00 |

### 5. Chia tập dữ liệu

Hai dataset được chia theo thứ tự ngày, không shuffle ngẫu nhiên. Với chuỗi
thời gian, chia ngẫu nhiên có thể đưa thông tin từ tương lai vào tập train.

| Dataset | Train | Validation | Test |
|---|---:|---:|---:|
| Seervada | 80%: 24 ngày, 1.440 dòng | 10%: 3 ngày, 180 dòng | 10%: 3 ngày (ngày 28–30), 180 dòng |
| PEMS-BAY | 70%: 126 ngày, 17.010 dòng | 15%: 27 ngày, 3.645 dòng | 15%: 28 ngày, 3.780 dòng |

Validation được dùng để chọn mô hình/slot; test dành cho đánh giá cuối cùng,
không dùng để chọn mô hình. Category vocabulary và thống kê chuẩn hóa khoảng
cách (mean/std) chỉ được fit trên train; không tính thống kê từ validation
hoặc test.

### 6. Đặc trưng và nhãn

Nhãn của cả hai dataset là `travel_time` (phút). Đặc trưng gồm khoảng cách
`distance`, cờ `is_weekend`, và one-hot encoding cho `edge_id`, `time_slot`,
`day_of_week`, như được lưu trong `preprocessing_pipeline.json`. `distance`
được chuẩn hóa z-score bằng mean/std của train; các cờ và biến one-hot là
0/1. Không chuẩn hóa nhãn.

Group Mean fit các trung bình theo thứ tự chi tiết đến tổng quát:
(edge, slot, day-of-week), (edge, slot), (edge), rồi fallback về trung bình
toàn cục; tất cả các trung bình chỉ fit trên train. Linear Regression dùng
các đặc trưng đã mã hóa và bỏ các cột baseline được cấu hình trong model.
MLP dùng cùng bộ đặc trưng đầu vào, không có bước chuẩn hóa riêng ngoài việc
chuẩn hóa `distance` ở pipeline.

### 7. Hạn chế dữ liệu

- Haversine là khoảng cách đường chim bay, không thay thế khoảng cách đường
  thực tế.
- `adj_mx_bay.pkl` là pickle; chỉ nạp file từ nguồn tin cậy vì pickle có thể
  thực thi mã khi mở.
- Seervada là network mẫu nhỏ và observations được mô phỏng. PEMS-BAY trong
  pipeline chỉ dùng network con 25 cảm biến, không đại diện cho toàn bộ mạng
  đô thị.
- Test Seervada chỉ có 3 ngày; kết luận so sánh mô hình trên dataset này có
  độ tin cậy hạn chế.
- Raw PEMS-BAY có một khoảng timestamp 65 phút dù cadence danh nghĩa là 5
  phút; báo cáo chất lượng hiện tại chưa có thống kê số mẫu được nội suy hoặc
  loại bỏ.

## Tạo báo cáo hợp nhất

`scripts/make_report.py` đọc các file kết quả của WS1–WS6 rồi gọi
`src.report.build_report(...)`; output mặc định là
`docs/report/<dataset>_report.md`. Nếu một nhóm kết quả chưa tồn tại, báo cáo
hiển thị `chưa có kết quả` cho mục tương ứng thay vì dừng.
