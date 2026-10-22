# ShortestPath pipeline

Pipeline cho Seervada và PEMS-BAY. Các phép biến đổi dữ liệu và hợp đồng
workstream nằm trong `src/`; script chỉ điều phối tham số, gọi API và lưu kết quả.
Chạy từ thư mục gốc repository.

Cài dependencies từ file chuẩn:

```powershell
python -m pip install -r requirements.txt
```

## Thứ tự chạy

**Seervada Network**
```powershell
python scripts\run_workstream01.py --dataset seervada --artifacts-root .
python scripts\run_workstream02.py --dataset seervada --artifacts-root .
python scripts\run_workstream03.py --dataset seervada --artifacts-root .
python scripts\run_workstream04.py --dataset seervada --artifacts-root .
python scripts\run_workstream05.py --dataset seervada --artifacts-root .
python scripts\run_workstream06.py --dataset seervada --artifacts-root .
python scripts\make_report.py --dataset seervada --artifacts-root .
```

**PeMS-BAY**
```powershell
python scripts\run_preprocess_pems_bay.py --input-dir data\raw_pems_bay --artifacts-root . --log-level INFO
python scripts\run_workstream01.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream03.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream04.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream05.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream06.py --dataset pemsbay --artifacts-root .
python scripts\make_report.py --dataset pemsbay --artifacts-root .
```

Tất cả runner dùng chung `stage_dir(dataset, stage, root)` để xác định đường
dẫn. `--artifacts-root` mặc định là gốc repository và là gốc thay thế cho cây
`artifacts/`, `data/processed/` và `docs/report/`. `--output-dir` vẫn được nhận
như alias tương thích nhưng phát cảnh báo deprecated. Root giống nhau phải được
truyền cho mọi stage để downstream đọc đúng các file upstream. Khi thiếu file
ở cấu trúc mới, runner chỉ với Seervada sẽ thử `workstreamXX/outputs/` cũ và
cảnh báo; file không bị di chuyển.

## Workstreams
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

## Dataset

### Seervada

Seervada là mạng mẫu gồm 7 nút (`O, A, B, C, D, E, T`) và 12 cạnh. Bộ dữ liệu
nghiên cứu được lưu thành ba CSV theo các mục đích khác nhau:

| Tệp | Nội dung |
|---|---|
| `data/processed_seervada/seervada_network.csv` | Danh sách cạnh với hai đầu nút, khoảng cách (km) và cờ hướng cạnh (`directed`). |
| `data/processed_seervada/seervada_rcsp_teaching.csv` | Danh sách cạnh, khoảng cách, thời gian tài nguyên (`time`, phút) và cờ hướng cạnh; 12 dòng cạnh. |
| `data/processed_seervada/seervada_travel_time_SIMULATED.csv` | Travel time mô phỏng theo cạnh, ngày và time slot; có khóa thời gian và thông tin cạnh để dùng làm dữ liệu dự báo. |

`seervada_network.csv` là đầu vào network cho adapter Seervada: tập nút được
suy ra từ hai đầu cạnh, cạnh được chuyển sang schema chuẩn rồi thành
adjacency list. Network này được dùng trong các phép tìm đường; cấu hình
hiện tại đặt source–target là `O → T`.

`seervada_rcsp_teaching.csv` cung cấp giá trị tài nguyên `time` trên từng
cạnh để tạo bài toán RCSP và được đối chiếu với topology, hướng cạnh, khoảng
cách của network. Các giới hạn tài nguyên là tham số của bài toán, không phải
cột trong CSV; cấu hình `configs/seervada.yaml` hiện để `time_limits` và
`slots` rỗng.

`seervada_travel_time_SIMULATED.csv` cung cấp nhãn travel time theo ngày/slot
cho các workstream tiền xử lý, huấn luyện và đánh giá mô hình dự báo. Adapter
kiểm tra các khóa quan sát, đơn vị, cạnh và tính nhất quán khoảng cách với
network.

Dữ liệu mô phỏng có 30 ngày đánh số, không có ngày lịch, 5 time slot và
1.800 dòng (30 ngày × 12 cạnh × 5 slot). Các slot lần lượt là 06:00–08:00,
08:00–10:00, 11:30–13:30, 16:30–18:30 và 19:30–21:30. Chia theo thứ tự ngày
với tỷ lệ train/validation/test 80%/10%/10%: train 24 ngày (1.440 dòng),
validation 3 ngày (180 dòng), test ngày 28–30 (180 dòng).

Vì đây là network nhỏ và travel time mô phỏng, thí nghiệm Seervada chủ yếu
giúp kiểm tra cách vận hành của phương pháp trong môi trường có cấu trúc rõ
ràng. Kết quả không phải bằng chứng về độ chính xác trên giao thông thực tế;
test chỉ gồm 3 ngày nên so sánh mô hình cũng có độ tin cậy hạn chế.

### PeMS-Bay

PeMS-Bay là dữ liệu tốc độ giao thông khu vực Bay Area được sử dụng trong
công trình DCRNN. BibTeX:

```bibtex
@inproceedings{li2018dcrnn_traffic,
  title={Diffusion Convolutional Recurrent Neural Network: Data-Driven Traffic Forecasting},
  author={Li, Yaguang and Yu, Rose and Shahabi, Cyrus and Liu, Yan},
  booktitle={International Conference on Learning Representations (ICLR '18)},
  year={2018}
}
```

Ba nguồn dữ liệu được công bố cùng dự án
[DCRNN](https://github.com/liyaguang/DCRNN):

| Tệp | Cấu trúc và vai trò |
|---|---|
| [`pems-bay.h5`](https://drive.google.com/open?id=10FOTa6HXPqX8PfWRoRwcFnW9BrNZEIX) ([Baidu Yun mirror](https://pan.baidu.com/s/14Yy9isAIZYdU__OYEQGa_g)) | HDF5 chứa DataFrame tốc độ dạng wide: hàng là timestamp, cột là sensor ID. |
| [`graph_sensor_locations_bay.csv`](https://github.com/liyaguang/DCRNN/blob/master/data/sensor_graph/graph_sensor_locations_bay.csv) | CSV ánh xạ sensor ID tới latitude/longitude. |
| [`adj_mx_bay.pkl`](https://github.com/liyaguang/DCRNN/blob/master/data/sensor_graph/adj_mx_bay.pkl) | Pickle chứa danh sách sensor ID, index map và adjacency matrix vuông; biểu diễn kết nối giữa cảm biến. |

Bản HDF5 trong repo có 52.116 timestamp và 325 cảm biến, từ 2017-01-01 đến
2017-06-30 (181 ngày). Cadence danh nghĩa là 5 phút; kiểm tra index thấy một
khoảng dài 65 phút. Đây là thống kê kiểm tra trực tiếp raw HDF5. Quality
report hiện lưu trong repo chưa có thống kê đầu vào nên không dùng report đó
để khẳng định số mẫu được nội suy hoặc loại bỏ.

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

## Tiền xử lý và chuẩn hóa dữ liệu

### Tiền xử lý dữ liệu Seervada

Adapter đọc `seervada_network.csv`, suy ra nút từ hai đầu cạnh, chuẩn hóa
khoảng cách về km và kiểm tra ID, cạnh trùng, self-loop, khoảng cách dương,
tính liên thông và đường đi `O → T`. RCSP loader đối chiếu topology, hướng
cạnh và khoảng cách của `seervada_rcsp_teaching.csv` với network; trường
`time` được nạp thành chi phí tài nguyên (phút), còn giới hạn tài nguyên được
cấu hình riêng.

Adapter đọc travel time mô phỏng từ
`seervada_travel_time_SIMULATED.csv`, kiểm tra khóa `(day, time_slot,
edge_id)`, đơn vị và tính khớp cạnh/khoảng cách. Dữ liệu đã được tổng hợp theo
5 slot; không có bước làm sạch chuỗi tốc độ raw cho Seervada. Tạo đặc trưng
và chia train/validation/test theo ngày được thực hiện sau đó, giữ nguyên
thứ tự thời gian và các tỷ lệ đã nêu ở III.1.1.3.

### Tiền xử lý dữ liệu PeMS-Bay

1. **Đọc và xác thực nguồn:** `scripts/run_preprocess_pems_bay.py` gọi
   `pemsbay_prepare.py` để nhận diện định dạng, kiểm tra schema và đối chiếu
   sensor ID giữa HDF5, adjacency pickle và CSV vị trí.
2. **Chuẩn hóa traffic raw:** HDF5 wide được xuất thành Parquet long-form
   cùng metadata, mapping ID và quality report. Bước này giữ giá trị thiếu;
   không nội suy hay loại bỏ tốc độ trong lúc xuất.
3. **Chọn sensor và dựng topology:** adapter lọc sensor có traffic hợp lệ,
   tọa độ và adjacency; BFS chọn 25 sensor liên thông. Cây BFS bảo đảm kết
   nối ban đầu; các cạnh khép chu trình có thể được thêm theo cấu hình để
   đáp ứng điều kiện endpoint/simple-path. `direction_policy: undirected`
   hiện hợp nhất hai chiều khi một trong hai hướng adjacency có kết nối.
4. **Tính khoảng cách:** với mỗi cạnh được chọn, khoảng cách giữa tọa độ hai
   sensor tính bằng Haversine, chuẩn hóa về km. Đây là ước lượng đường chim
   bay, không phải khoảng cách đường bộ.
5. **Làm sạch tốc độ:** giá trị không phải số, không hữu hạn hoặc `<= 0`
   được xem là thiếu. Chỉ nội suy tuyến tính gap nội bộ tối đa 3 mẫu 5 phút
   khi timestamp hai đầu xác nhận cadence; không ngoại suy đầu/cuối, không
   nội suy gap dài hoặc gap có thời gian bất thường. Không đặt ngưỡng trên để
   loại tốc độ cao. Tốc độ tại endpoint `v` được gán cho cạnh đi vào `v`.
6. **Tạo nhãn và tổng hợp slot:** đổi mph sang km/h trong công thức
   `travel_time_minutes = distance_km / (speed_mph × 1.609344) × 60`, rồi lấy
   trung bình travel time theo `(edge, day, time_slot)`. Mỗi ô cần coverage
   ít nhất 50% số mẫu 5 phút hợp lệ hoặc nội suy; một ngày chỉ giữ khi mọi
   cạnh đạt ngưỡng ở cả 5 slot. Metadata hiện ghi 181 ngày giữ lại và 0 ngày
   bị loại vì coverage.
7. **Chia tập theo thời gian:** I4 sau tổng hợp có 24.435 dòng (181 × 27 × 5).
   Chia tuần tự theo ngày theo tỷ lệ 70%/15%/15%: train 126 ngày/17.010 dòng,
   validation 27 ngày/3.645 dòng, test 28 ngày/3.780 dòng. Các số này lấy
   từ `data/processed/pemsbay/split_manifest.csv`.

### Chuẩn hóa dữ liệu đầu vào cho mô hình dự báo và routing

Hai adapter cung cấp network theo schema chuẩn gồm nodes, edges, khoảng cách
km, thuộc tính hướng cạnh và adjacency list. Validator kiểm tra ID, cạnh
trùng, self-loop, khoảng cách hữu hạn/dương, đơn vị và liên thông; kiểm tra
khả năng đi từ source đến target khi cặp endpoint được cung cấp. Seervada
dùng khoảng cách từ CSV; PeMS-Bay dùng khoảng cách Haversine. Khác biệt về
topology vẫn được giữ nguyên, không ép hai network có cùng số nút/cạnh.

Với dữ liệu dự báo, nhãn của cả hai bộ là `travel_time` tính bằng phút.
Feature matrix gồm `distance`, `is_weekend` và one-hot encoding cho `edge_id`,
`time_slot`, `day_of_week`. Mean/std chuẩn hóa `distance` và category
vocabulary chỉ được fit trên train; các biến nhị phân/one-hot là 0/1 và nhãn
không chuẩn hóa. Group Mean backoff qua `(edge, slot, day-of-week)`,
`(edge, slot)`, `(edge)` rồi trung bình toàn cục; Linear Regression dùng các
feature đã mã hóa và bỏ các cột baseline cấu hình; MLP dùng cùng đầu vào mà
không có bước chuẩn hóa riêng ngoài `distance`.

Dữ liệu được chia theo ngày, không shuffle: Seervada 80%/10%/10% (24/3/3
ngày), PeMS-Bay 70%/15%/15% (126/27/28 ngày). Validation dùng chọn mô hình
hoặc lựa chọn theo slot; test chỉ dùng chấm cuối cùng. Với routing, trọng số
cạnh được lấy từ network và các dự đoán/quan sát travel time theo cạnh-slot;
source/target và quy ước directed/undirected phải thuộc network tương ứng.
Seervada hiện cấu hình `O → T`; PeMS-Bay dùng endpoint được adapter chọn tự
động nếu YAML không chỉ định cặp.

## Tạo báo cáo hợp nhất

`scripts/make_report.py` đọc các file kết quả của WS1–WS6 rồi gọi
`src.report.build_report(...)`; output mặc định là
`docs/report/<dataset>_report.md`. Nếu một nhóm kết quả chưa tồn tại, báo cáo
hiển thị `chưa có kết quả` cho mục tương ứng thay vì dừng.

## Repo

```
ShortestPath/
├── data/
│   ├── raw/
│   └── processed/<ds>/
├── src/
│   ├── common/               # M0
│   ├── network/              # M1
│   ├── shortest_path/        # M2
│   ├── rcsp/                 # M3
│   ├── preprocess/           # M4
│   ├── models/
│   │   ├── baselines/        # M5
│   │   └── nn/               # M6
│   ├── evaluation/           # M7
│   ├── routing/              # M8
│   ├── report/               # M9
│   └── adapters/	
│       ├── base.py          # lớp DatasetAdapter: khai báo hàm bắt buộc
│       ├── seervada.py
│       ├── pemsbay.py
│       └── registry.py      # tên dataset → adapter
├── scripts/                  # CLI
├── artifacts/<ds>/
│   ├── network/  paths/  rcsp/
│   └──predictions/  metrics/  routing/
├── configs/                  # dataset, time_limits, slots, seed
│   ├── seervada.yaml
│   └── pemsbay.yaml
├── docs/
│   ├── workstreams/   # WS1–WS6: Overview, Tasks, Tech Specs, Deliverables
│   ├── contracts/            # I1–I8, quy ước chung
│   └── report/
├── README.md                 # cách cài và chạy từ môi trường sạch
└── requirements.txt          # khóa phiên bản thư viện
```
