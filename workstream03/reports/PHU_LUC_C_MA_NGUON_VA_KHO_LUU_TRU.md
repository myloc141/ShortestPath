# PHỤ LỤC C — MÃ NGUỒN VÀ KHO LƯU TRỮ HỆ THỐNG
**Đề tài:** Mối liên hệ giữa bài toán đường đi ngắn nhất và machine learning / routing hiện đại (Chủ đề 5 - Mức độ C)  
**Nhóm sinh viên thực hiện:**
- Workstream 1: Mỹ Lộc (Mô hình hóa mạng lưới & Thuật toán Dijkstra)
- Workstream 2: Ngọc Hân (RCSP bằng Quy hoạch tuyến tính nguyên 0-1 & Excel Solver)
- Workstream 3: Lại Gia Huy (Data Engineering: Mô phỏng, Làm sạch, PeMS-Bay subnetwork & Chronological Split)
- Workstream 4: Quang Minh (Mô hình nền tảng: Group Mean & Hồi quy tuyến tính)
- Workstream 5: Yến Nhi (Mạng thần kinh nhân tạo MLPRegressor)
- Workstream 6: Mỹ Lộc (Thực nghiệm Dynamic Routing & Tổng hợp báo cáo)

---

## 1. Thông tin chung về kho lưu trữ và đường dẫn GitHub

- **Đường dẫn Repository chính thức trên GitHub:**  
  [https://github.com/myloc141/ShortestPath](https://github.com/myloc141/ShortestPath)  
  *(Đường dẫn cũ tự động chuyển hướng: `https://github.com/myloc141/RCSP`)*
- **Nhánh phát triển chính (Main Production Branch):** `main`
- **Nhánh nộp bài & nghiệm thu độc lập của Workstream 3:** `workstream03-final`  
  *(Pull Request nghiệm thu: `https://github.com/myloc141/ShortestPath/pull/new/workstream03-final`)*
- **Commit Hash kiểm chứng mới nhất:** `436af2d`
- **Ngôn ngữ và môi trường thực thi:**
  - Ngôn ngữ: Python 3.10 – 3.12 (khuyến nghị Python 3.12).
  - Hệ quản trị thư viện: Cài đặt toàn bộ phụ thuộc thông qua file `requirements.txt`.
  - Môi trường bổ trợ: Microsoft Excel 2016+ (hỗ trợ Solver Add-in cho file kiểm chứng RCSP).

---

## 2. Tổng quan kiến trúc hệ thống và Hợp đồng giao tiếp (Interfaces)

Hệ thống được thiết kế theo kiến trúc module hóa hướng dịch vụ dữ liệu, phân tách triệt để giữa logic thuật toán (`src/`), bộ điều phối thực thi dòng lệnh (`scripts/`) và không gian làm việc của từng thành viên (`WS/`). Mọi giao tiếp giữa các giai đoạn đều tuân thủ nghiêm ngặt chuẩn hợp đồng giao diện dữ liệu (Interface Contract I1 – I8).

### 2.1. Sơ đồ tương tác luồng dữ liệu giữa các Module (M0 – M9)

```text
M0 common (Config, IO, Validators) ── Dùng chung cho toàn bộ hệ thống
                   │
                   ▼
M1 network / adapters ────────┬──────────────I1───────────────┐
                              │                               │
                              ▼                               ▼
                     M2 shortest_path ──I2──┐          M4 preprocess / adapters
                              │             │                 │
                              │             │                 │ I4 (Train/Valid/Test)
                              ▼             │                 ▼
                           M3 rcsp          │          ┌──────┴──────┐
                              │             │          ▼             ▼
                              │ I3          │     M5 baselines     M6 nn
                              │             │          │             │
                              │             │          └──────┬──────┘
                              │             │                 │ I5 (Predictions)
                              ▼             │                 ▼
                        M8 routing ◄────────┴────────── M7 evaluation
                              │                               │
                              │                               │ I6 (Metrics)
                              ▼                               ▼
                        M9 report ◄───────────────────────────┘
```

### 2.2. Bảng mô tả Hợp đồng dữ liệu (Interface Contracts I1 – I8)

| Mã giao diện | Chiều truyền dữ liệu | Nội dung dữ liệu trao đổi | Định dạng / Cơ chế kỹ thuật |
|:---:|:---|:---|:---|
| **I1** | `M1` $\rightarrow$ `M2`, `M3`, `M4`, `M8` | Cấu trúc mạng chuẩn (danh sách nút, cung, khoảng cách, tính có hướng). | File CSV (`network_nodes.csv`, `network_edges.csv`) và đối tượng `Network` trong bộ nhớ. |
| **I2** | `M2` $\rightarrow$ `M3`, `M8`, `M9` | Toàn bộ các đường đi đơn giản (simple paths) và đường ngắn nhất Dijkstra. | File CSV `results_paths.csv` và cấu trúc `ShortestPathResult`. |
| **I3** | `M3` $\rightarrow$ `M8`, `M9` | Nghiệm tối ưu RCSP và bảng phân tích độ nhạy theo giới hạn $T_{max}$. | File CSV `rcsp_sensitivity.csv`, `rcsp_verification.csv` (M8 nạp qua `RouteReference`). |
| **I4** | `M4` $\rightarrow$ `M5`, `M6`, `M7`, `M8` | Tập dữ liệu phân chia thời gian (Train/Valid/Test), ma trận đặc trưng $X$, vector nhãn $y$, pipeline scaler/encoder. | Thư mục `data/processed/<dataset>/` chứa các file CSV chuẩn hóa và `preprocessing_pipeline.json`. |
| **I5** | `M5`, `M6` $\rightarrow$ `M7`, `M8` | Dự báo thời gian di chuyển theo từng quan sát test (`edge_id, day, time_slot, y_pred`). | File CSV `pred_groupmean_withkey.csv`, `pred_linearreg_withkey.csv`, `pred_nn_withkey.csv`. |
| **I6** | `M7` $\leftarrow$ `M5`, `M6`; $\rightarrow$ `M9` | Bảng tổng hợp các chỉ số đánh giá (MAE, RMSE, MSE, MAPE) toàn cục và theo khung giờ. | File CSV `metrics_*.csv` và file JSON `workstream04_metrics.json`, `workstream05_metrics.json`. |
| **I7** | `M8` $\rightarrow$ `M2` | Tái kích hoạt thuật toán tìm đường ngắn nhất với trọng số chi phí là thời gian dự báo. | Lời gọi hàm nội bộ `dijkstra(network, source, target, weights)`. |
| **I8** | `M8` $\rightarrow$ `M9` | Kết quả định tuyến theo khung giờ, thời gian thực tế, độ hối tiếc (Regret) so với Oracle. | File CSV `routing_results_all.csv`, `summary_by_slot_method.csv` và các biểu đồ PNG. |

---

## 3. Cây thư mục kho lưu trữ (Repository Structure)

Cấu trúc thư mục được đồng bộ nhất quán trên kho lưu trữ GitHub tại commit `436af2d`:

```text
ShortestPath/
├── .gitignore                          # Cấu hình lọc bỏ file rác, cache, build artifacts
├── README.md                           # Tài liệu tổng quan kiến trúc và hướng dẫn chạy hệ thống
├── requirements.txt                    # Danh mục thư viện Python bắt buộc
├── workstream_dependency_graph.svg     # Sơ đồ quan hệ phụ thuộc giữa các Workstream
│
├── src/                                # THƯ VIỆN LÕI CỦA TOÀN BỘ HỆ THỐNG
│   ├── common/                         # M0: Cấu hình, đọc/ghi dữ liệu, ngoại lệ và validators
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── io.py
│   │   ├── metrics.py                  # Các hàm tính MAE, RMSE, MSE, MAPE
│   │   ├── schemas.py
│   │   └── validators.py               # Kiểm tra tính hợp lệ của hợp đồng I1 - I8
│   ├── network/                        # M1: Mô hình hóa mạng lưới và kiểm chứng cấu trúc
│   │   ├── encoding.py                 # Xây dựng danh sách kề (Adjacency list)
│   │   ├── schema.py                   # Dataclass Network, NetworkEdge
│   │   └── validation.py               # Kiểm tra tính liên thông, self-loop, trọng số
│   ├── shortest_path/                  # M2: Thuật toán đường đi ngắn nhất
│   │   ├── dijkstra.py                 # Giải thuật Dijkstra với hàng đợi ưu tiên
│   │   ├── simple_paths.py             # Liệt kê đệ quy vét cạn mọi Simple Path
│   │   └── verify.py                   # Đối chiếu nghiệm Dijkstra và nghiệm vét cạn
│   ├── rcsp/                           # M3: Bài toán đường ngắn nhất ràng buộc tài nguyên
│   │   ├── data.py                     # Nạp bài toán RCSP Seervada
│   │   ├── schema.py                   # RCSPProblem, ResourceArc, RCSPResult
│   │   ├── solver.py                   # Solver MILP 0-1 (PuLP/CBC) và Brute-force
│   │   ├── sensitivity.py              # Phân tích độ nhạy theo giới hạn T_max
│   │   ├── validation.py
│   │   └── verify.py                   # Đối chiếu nghiệm MILP, Brute-force và cspy
│   ├── preprocess/                     # M4.1: Tiền xử lý dữ liệu và Adapter Contract
│   │   ├── dataset.py                  # Chia tập thời gian, làm sạch chuỗi tốc độ, lag features
│   │   ├── observations.py             # Schema TrafficObservation, nạp CSV quan sát
│   │   └── seervada.py                 # Adapter giao diện chuẩn phục vụ WS4, WS5, WS6
│   ├── adapters/                       # M4.2: Các bộ nạp dữ liệu đa nguồn
│   │   ├── base.py                     # Lớp cơ sở trừu tượng DatasetAdapter
│   │   ├── registry.py                 # Cơ chế đăng ký adapter tự động
│   │   ├── seervada.py                 # Nạp mạng và dữ liệu mô phỏng Seervada
│   │   ├── pemsbay.py                  # Trích xuất mạng con 25 sensor, Haversine, PeMS-Bay
│   │   └── pemsbay_prepare.py          # Pipeline trích xuất HDF5 sang Parquet
│   ├── models/                         # M5 & M6: Các mô hình dự báo thời gian di chuyển
│   │   ├── baselines/                  # M5: Mô hình nền tảng
│   │   │   ├── group_mean.py           # Group Mean 4 cấp độ fallback
│   │   │   └── linear_regression.py    # Hồi quy tuyến tính đa biến
│   │   └── nn/                         # M6: Mạng nơ-ron nhân tạo
│   │       └── neural_network.py       # MLPRegressor với Early Stopping
│   ├── evaluation/                     # M7: Đánh giá mô hình và căn chỉnh dữ liệu
│   │   └── regression.py               # Đánh giá theo từng khung giờ và so sánh cặp routing
│   ├── routing/                        # M8: Thí nghiệm Dynamic Routing
│   │   ├── comparison.py               # Tổng hợp và so sánh hiệu quả các phương pháp
│   │   └── experiment.py               # Chạy định tuyến thực nghiệm, tính Regret so với Oracle
│   └── report/                         # M9: Tự động kết xuất báo cáo
│       ├── markdown.py                 # Trình tạo bảng Markdown tổng hợp
│       └── plots.py                    # Vẽ biểu đồ loss, route map và regret
│
├── scripts/                            # BỘ RUNNER ĐIỀU PHỐI DÒNG LỆNH (ENTRY POINTS)
│   ├── _runner_utils.py                # Tiện ích nạp cấu hình, quản lý thư mục artifacts
│   ├── run_workstream01.py             # Runner WS1: Dựng mạng và tính Shortest Path
│   ├── run_workstream02.py             # Runner WS2: Giải bài toán RCSP và phân tích độ nhạy
│   ├── run_workstream03.py             # Runner WS3: Tiền xử lý dữ liệu và chia tập Train/Val/Test
│   ├── run_workstream04.py             # Runner WS4: Huấn luyện Group Mean & Linear Regression
│   ├── run_workstream05.py             # Runner WS5: Huấn luyện Neural Network MLP
│   ├── run_workstream06.py             # Runner WS6: Chạy thực nghiệm Dynamic Routing
│   ├── make_report.py                  # Runner M9: Tổng hợp báo cáo tổng thể
│   ├── run_preprocess_pems_bay.py      # Runner chuyển đổi dữ liệu PeMS-Bay thô
│   ├── build_dataset.py                # Runner phụ trợ xây dựng dataset
│   └── README.md                       # Hướng dẫn chi tiết sử dụng các runner
│
├── WS/                                 # KHÔNG GIAN LÀM VIỆC TỪNG WORKSTREAM
│   ├── common/                         # Cấu hình và chỉ số dùng chung
│   ├── workstream01/                   # Không gian WS1 (Mỹ Lộc)
│   │   ├── Dijkstra.py                 # Mã nguồn Dijkstra độc lập
│   │   ├── Task1.py, shortpath.py
│   │   ├── equivalent_paths.csv        # Bảng các đường đi tương đương
│   │   ├── results_paths.csv           # Kết quả 28 đường đi đơn giản
│   │   └── workstream01.md             # Báo cáo kỹ thuật WS1
│   ├── workstream02/                   # Không gian WS2 (Ngọc Hân)
│   │   ├── rcsp_milp.py                # Mô hình MILP 0-1 chạy độc lập
│   │   ├── rcsp_excel_solver.xlsx      # Mô hình đối chứng bằng Excel Solver
│   │   ├── rcsp_sensitivity.csv        # Kết quả độ nhạy theo T_max
│   │   ├── rcsp_verification.csv       # Kết quả kiểm chứng 4 lớp
│   │   └── README.md                   # Báo cáo kỹ thuật chi tiết WS2
│   ├── workstream03/                   # Không gian WS3 (Lại Gia Huy)
│   │   ├── BAO_CAO_WORKSTREAM_3_LAIGIAHUY.docx # Báo cáo Word chính thức của WS3
│   │   ├── DATA_DICTIONARY.md          # Từ điển dữ liệu Seervada
│   │   ├── DATA_DICTIONARY_PEMSBAY.md  # Từ điển dữ liệu PeMS-Bay
│   │   ├── DATA_ENGINEERING_REPORT.md  # Báo cáo Data Engineering độc lập
│   │   ├── data/                       # Dữ liệu gốc và dữ liệu chia tập I4
│   │   │   ├── raw/                    # Dữ liệu mô phỏng 1.800 dòng & mở rộng 5.400 dòng
│   │   │   └── processed/              # Tập Train/Test và pipeline JSON
│   │   ├── src/                        # Module mã nguồn độc lập của WS3
│   │   │   ├── data_simulation.py      # Thuật toán mô phỏng giao thông Log-Normal
│   │   │   ├── eda_analysis.py         # Phân tích khám phá dữ liệu (EDA)
│   │   │   ├── feature_pipeline.py     # Pipeline trích xuất đặc trưng và MinMax Scaler
│   │   │   ├── split_dataset.py        # Thuật toán chia tập thời gian bảo toàn nhân quả
│   │   │   ├── seervada.py             # Adapter tương thích ngược M4.1
│   │   │   └── pems_bay_pipeline.py    # Pipeline trích xuất mạng con PeMS-Bay
│   │   ├── tests/                      # Bộ kiểm thử tự động (41 unit tests pass 100%)
│   │   │   ├── test_artifact_contract.py
│   │   │   ├── test_feature_alignment.py
│   │   │   ├── test_no_target_leakage.py
│   │   │   ├── test_pems_bay_pipeline.py
│   │   │   ├── test_pipeline_reproducibility.py
│   │   │   ├── test_seervada_adapter.py
│   │   │   └── test_temporal_split.py
│   │   └── reports/                    # Báo cáo học thuật và tài liệu bàn giao
│   │       ├── BAO_CAO_SECTIONS_I3_III1_III2.md
│   │       ├── HANDOFF_MANIFEST.md
│   │       ├── REQUIREMENT_TRACEABILITY.md
│   │       └── artifact_hashes.json
│   ├── workstream04/                   # Không gian WS4 (Quang Minh)
│   │   ├── group_mean.py, linear_regression.py
│   │   ├── pred_*.csv, metrics_*.csv
│   │   └── README_WS04.md
│   ├── workstream05/                   # Không gian WS5 (Yến Nhi)
│   │   ├── train_nn.py, evaluate_nn.py
│   │   ├── nn_model.pkl, loss_curve.png
│   │   └── README_WS5.md
│   └── workstream06/                   # Không gian WS6 (Mỹ Lộc)
│       ├── run_routing.py
│       └── REPORT.md
│
├── data/                               # DỮ LIỆU ĐẦU VÀO VÀ ĐẦU RA TIỀN XỬ LÝ
│   ├── raw_pems_bay/                   # File thô: adj_mx_bay.pkl, graph_sensor_locations_bay.csv, pems-bay.h5
│   └── processed/
│       ├── seervada/                   # Dữ liệu I4 của Seervada (train, valid, test, pipeline JSON)
│       ├── pemsbay/                    # Dữ liệu I4 của PeMS-Bay và các file Parquet
│       └── pemsbay_subnetwork/         # Mạng con 25 cảm biến và 139 cạnh trích xuất
│
├── artifacts/                          # KẾT QUẢ THỰC NGHIỆM ĐÃ KẾT XUẤT VÀ KIỂM CHỨNG
│   ├── seervada/                       # Sản phẩm hoàn chỉnh của mạng Seervada Park
│   │   ├── network/                    # I1: network_nodes.csv, network_edges.csv
│   │   ├── paths/                      # I2: results_paths.csv, shortest_path_summary.csv
│   │   ├── rcsp/                       # I3: rcsp_sensitivity.csv, rcsp_verification.csv
│   │   ├── predictions/                # I5: pred_*.csv, nn_model.pkl, loss_curve.png
│   │   ├── metrics/                    # I6: metrics_*.csv, workstream04/05_metrics.json
│   │   └── routing/                    # I8: routing_results_all.csv, biểu đồ regret/route
│   └── pemsbay/                        # Sản phẩm hoàn chỉnh của mạng PeMS-Bay California
│       ├── network/, paths/, predictions/, metrics/, routing/
│
└── docs/                               # TÀI LIỆU HỢP ĐỒNG VÀ BÁO CÁO HỢP NHẤT
    ├── contracts/                      # Đặc tả interfaces.md
    └── report/                         # seervada_report.md, pemsbay_report.md
```

---

## 4. Các Entry Point quan trọng và Hướng dẫn chạy nhanh (Quickstart)

### 4.1. Thiết lập môi trường thực thi

Khởi tạo môi trường ảo Python và cài đặt toàn bộ phụ thuộc từ file `requirements.txt`:

```powershell
# Tạo và kích hoạt môi trường ảo (khuyến nghị)
python -m venv venv
.\venv\Scripts\activate

# Cài đặt danh mục thư viện chuẩn
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

> **Lưu ý đặc biệt:** Thư viện `pulp==2.9.0` được chỉ định phiên bản cố định để tương thích với CBC solver đi kèm. Thư viện `tables` và `pyarrow` được yêu cầu để đọc định dạng HDF5 (`.h5`) và Parquet (`.parquet`).

### 4.2. Lệnh thực thi nhanh toàn bộ chuỗi cho mạng Seervada Park

Chạy lần lượt các runner theo thứ tự phụ thuộc kiến trúc từ thư mục gốc repository:

```powershell
# Bước 1: Dựng mạng chuẩn hóa và tìm đường ngắn nhất (WS1)
python scripts\run_workstream01.py --dataset seervada --artifacts-root .

# Bước 2: Giải bài toán RCSP bằng MILP 0-1 và phân tích độ nhạy (WS2)
python scripts\run_workstream02.py --dataset seervada --artifacts-root .

# Bước 3: Tiền xử lý dữ liệu và chia tập Train/Valid/Test không rò rỉ (WS3)
python scripts\run_workstream03.py --dataset seervada --artifacts-root .

# Bước 4: Huấn luyện và dự báo các mô hình Baseline Group Mean & Linear Regression (WS4)
python scripts\run_workstream04.py --dataset seervada --artifacts-root .

# Bước 5: Huấn luyện mạng thần kinh nhân tạo MLPRegressor (WS5)
python scripts\run_workstream05.py --dataset seervada --artifacts-root .

# Bước 6: Chạy thực nghiệm Dynamic Routing theo khung giờ và tính Regret (WS6)
python scripts\run_workstream06.py --dataset seervada --artifacts-root .

# Bước 7: Tự động kết xuất báo cáo tổng hợp Markdown (M9)
python scripts\make_report.py --dataset seervada --artifacts-root .
```

*Kết quả hoàn chỉnh được tự động lưu trữ tại thư mục:* `artifacts/seervada/` và báo cáo tại `docs/report/seervada_report.md`.

### 4.3. Lệnh thực thi nhanh toàn bộ chuỗi cho mạng PeMS-Bay California

```powershell
# Bước 0: Chuẩn hóa dữ liệu thô (HDF5/Pickle/CSV) sang Parquet
python scripts\run_preprocess_pems_bay.py --input-dir data\raw_pems_bay --artifacts-root . --log-level INFO

# Bước 1: Trích xuất mạng con 25 cảm biến liên thông và tính khoảng cách Haversine (WS1)
python scripts\run_workstream01.py --dataset pemsbay --artifacts-root .

# Bước 2: Chuyển đổi tốc độ sang travel time, gom khung giờ và chia tập I4 (WS3)
python scripts\run_workstream03.py --dataset pemsbay --artifacts-root .

# Bước 3: Huấn luyện Baseline trên dữ liệu PeMS-Bay (WS4)
python scripts\run_workstream04.py --dataset pemsbay --artifacts-root .

# Bước 4: Huấn luyện Neural Network trên dữ liệu PeMS-Bay (WS5)
python scripts\run_workstream05.py --dataset pemsbay --artifacts-root .

# Bước 5: Thực nghiệm Dynamic Routing trên dữ liệu thực tế PeMS-Bay (WS6)
python scripts\run_workstream06.py --dataset pemsbay --artifacts-root .

# Bước 6: Tổng hợp báo cáo Markdown cho PeMS-Bay
python scripts\make_report.py --dataset pemsbay --artifacts-root .
```

### 4.4. Lệnh chạy bộ kiểm thử tự động (Unit Test Suite)

Để kiểm chứng tính toàn vẹn, bảo toàn cấu trúc không rò rỉ dữ liệu (No Target Leakage) và tính tái lập hoàn toàn của pipeline Workstream 3:

```powershell
# Chạy toàn bộ 41 test cases tự động
pytest WS/workstream03/tests/ -v
```
*(Kết quả kiểm thử: **41/41 test cases PASSED 100%** trong ~2.8 giây).*

---

## 5. Bảng tra cứu vị trí mã nguồn chi tiết (Code Locator & Traceability Matrix)

Bảng tra cứu giúp giảng viên và người đọc nhanh chóng định vị chính xác vị trí mã nguồn, thuật toán, class/hàm chịu trách nhiệm và nơi lưu trữ kết quả kiểm chứng:

| Thành phần nghiên cứu | Workstream phụ trách | Vị trí file mã nguồn chính | Hàm / Class nòng cốt | File sản phẩm / Kết quả thực nghiệm |
|:---|:---:|:---|:---|:---|
| **Dijkstra & Simple Paths** | **WS1** *(Mỹ Lộc)* | • `src/shortest_path/dijkstra.py`<br>• `src/shortest_path/simple_paths.py`<br>• `src/shortest_path/verify.py`<br>• `WS/workstream01/Dijkstra.py` | • `dijkstra()`<br>• `ShortestPathResult`<br>• `iter_simple_paths()`<br>• `verify_shortest_path()` | • `artifacts/seervada/paths/results_paths.csv`<br>• `shortest_path_summary.csv`<br>• `WS/workstream01/workstream01.md` |
| **RCSP (QHTT 0-1 & Solver)** | **WS2** *(Ngọc Hân)* | • `src/rcsp/solver.py`<br>• `src/rcsp/data.py`<br>• `src/rcsp/sensitivity.py`<br>• `src/rcsp/verify.py`<br>• `WS/workstream02/rcsp_milp.py` | • `solve_rcsp_milp()`<br>• `brute_force_rcsp()`<br>• `sensitivity_analysis()`<br>• `verify_solution()` | • `artifacts/seervada/rcsp/rcsp_sensitivity.csv`<br>• `rcsp_verification.csv`<br>• `rcsp_network_consistency.csv`<br>• `WS/workstream02/rcsp_excel_solver.xlsx`<br>• `WS/workstream02/README.md` |
| **Tiền xử lý & Data Engineering** | **WS3** *(Lại Gia Huy)* | • `src/preprocess/dataset.py`<br>• `src/preprocess/observations.py`<br>• `src/preprocess/seervada.py`<br>• `src/adapters/seervada.py`<br>• `src/adapters/pemsbay.py`<br>• `WS/workstream03/src/*.py` | • `prepare_observation_splits()`<br>• `clean_speed_series()`<br>• `aggregate_hourly()`<br>• `select_pemsbay_sensors()`<br>• `SeervadaAdapter`<br>• `PemsBayAdapter` | • `data/processed/seervada/train.csv`, `test.csv`<br>• `X_train_preprocessed.csv`, `y_train.csv`<br>• `preprocessing_pipeline.json`<br>• `data/processed/pemsbay_subnetwork/`<br>• `WS/workstream03/DATA_DICTIONARY.md`<br>• `WS/workstream03/BAO_CAO_WORKSTREAM_3_LAIGIAHUY.docx` |
| **Mô hình nền tảng (Baselines)** | **WS4** *(Quang Minh)* | • `src/models/baselines/group_mean.py`<br>• `src/models/baselines/linear_regression.py`<br>• `WS/workstream04/group_mean.py`<br>• `WS/workstream04/linear_regression.py` | • `GroupMeanModel.fit()` / `predict()`<br>• `LinearRegressionModel.fit()` / `predict()`<br>• `GroupMeanPrediction` | • `artifacts/<dataset>/predictions/pred_groupmean_raw.csv`<br>• `pred_linearreg_raw.csv`<br>• `artifacts/<dataset>/metrics/metrics_groupmean.csv`<br>• `metrics_linearreg.csv`<br>• `workstream04_metrics.json` |
| **Mạng thần kinh nhân tạo (NN)** | **WS5** *(Yến Nhi)* | • `src/models/nn/neural_network.py`<br>• `WS/workstream05/train_nn.py`<br>• `WS/workstream05/evaluate_nn.py` | • `NeuralNetworkModel.fit()`<br>• `NeuralNetworkModel.predict()`<br>• `MLPRegressor` (Adam, ReLU) | • `artifacts/<dataset>/predictions/pred_nn.csv`<br>• `pred_nn_withkey.csv`<br>• `nn_model.pkl`<br>• `loss_curve.png`<br>• `artifacts/<dataset>/metrics/metrics_nn.csv`<br>• `workstream05_metrics.json` |
| **Dynamic Routing & So sánh** | **WS6** *(Mỹ Lộc)* | • `src/routing/experiment.py`<br>• `src/routing/comparison.py`<br>• `src/evaluation/regression.py`<br>• `WS/workstream06/run_routing.py` | • `run_routing_experiment()`<br>• `summarize_routing_results()`<br>• `compare_routing_pairs()`<br>• `evaluate_by_time_slot()` | • `artifacts/<dataset>/routing/routing_results_all.csv`<br>• `summary_by_slot_method.csv`<br>• `route_by_slot.csv`<br>• `model_comparison.csv`<br>• `fig_actual_time_main_slots.png`<br>• `fig_regret_all_slots.png`<br>• `fig_route_map.png`<br>• `docs/report/<dataset>_report.md` |

---
*Tài liệu này được biên soạn độc lập bởi Lại Gia Huy (Workstream 3 - Data Engineering) nhằm phục vụ công tác nghiệm thu mã nguồn, tái lập thực nghiệm và nộp báo cáo tiểu luận học thuật Chủ đề 5.*
