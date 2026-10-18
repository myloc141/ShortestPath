# Workstream 3: Data Engineering & Pipeline Architecture
**Sinh viên phụ trách:** Lại Gia Huy (MSSV: K24419)  
**Học phần:** Vận trù học | Đại học Kinh tế – Luật (UEL) / ĐHQG-HCM  
**Chủ đề nghiên cứu:** Chủ đề 5 (Mức độ C) – Mối liên hệ giữa bài toán đường đi ngắn nhất và machine learning / routing hiện đại  

---

## 1. MỤC TIÊU CỦA WORKSTREAM 3 (WS3 PURPOSE)
Workstream 3 chịu trách nhiệm toàn bộ hạ tầng kỹ thuật dữ liệu (Data Engineering) cho dự án:
1. Chuẩn hóa cấu trúc đồ thị mạng Seervada Park và dữ liệu dạy học RCSP cho WS1, WS2.
2. Mô phỏng dữ liệu thời gian di chuyển 30 ngày (1.800 dòng) và mở rộng 90 ngày (5.400 dòng) với phân phối lệch phải Log-Normal.
3. Phân chia tập Train/Test theo khối chuỗi thời gian (Time-series Block Split) đảm bảo **Zero Data Leakage**.
4. Xây dựng Feature Pipeline trích xuất 26 chiều đặc trưng chuẩn hóa, fit duy nhất trên Train set, cung cấp đầu vào đồng bộ cho WS4 và WS5.
5. Xây dựng và kiểm thử Pipeline dữ liệu thực tế PeMS-BAY (`pems_bay_pipeline.py`) đáp ứng tiêu chuẩn mở rộng 15% của đề tài Mức độ C.

---

## 2. CÂY THƯ MỤC CHUẨN (DIRECTORY TREE)

```
workstream03/
├── README.md                              # Tài liệu hướng dẫn tổng quan WS3
├── requirements.txt                       # Danh mục thư viện phụ thuộc và phiên bản
├── DATA_DICTIONARY.md                     # Từ điển dữ liệu toàn diện (Seervada & PeMS-BAY)
├── DATA_ENGINEERING_REPORT.md             # Báo cáo kỹ thuật chi tiết
├── data/
│   ├── raw/                               # Dữ liệu gốc và dữ liệu mô phỏng
│   │   ├── seervada_network.csv
│   │   ├── seervada_rcsp_teaching.csv
│   │   ├── seervada_travel_time_SIMULATED.csv
│   │   └── seervada_travel_time_EXTENDED_NN.csv
│   ├── processed/                         # Dữ liệu đã phân chia và ma trận đặc trưng
│   │   ├── train.csv
│   │   ├── test.csv
│   │   ├── X_train_preprocessed.csv
│   │   ├── X_test_preprocessed.csv
│   │   ├── y_train.csv
│   │   ├── y_test.csv
│   │   └── preprocessing_pipeline.json
│   └── pems_bay/                          # Thư mục đích cho pipeline PeMS-BAY
├── src/                                   # Mã nguồn thực thi chuẩn
│   ├── data_simulation.py                 # Mã nguồn sinh dữ liệu mô phỏng Seervada
│   ├── split_dataset.py                   # Mã nguồn phân chia chuỗi thời gian
│   ├── feature_pipeline.py                # Pipeline tiền xử lý 26 đặc trưng
│   ├── eda_analysis.py                    # Khám phá và phân tích thống kê EDA
│   └── pems_bay_pipeline.py               # Pipeline xử lý dữ liệu thực tế PeMS-BAY
├── reports/                               # Báo cáo audit, bàn giao và kiểm định
│   ├── AUDIT_BEFORE_CHANGES.md            # Báo cáo kiểm kê trước thay đổi
│   ├── HANDOFF_MANIFEST.md                # Biên bản bàn giao dữ liệu chuẩn cho WS4, WS5, WS6
│   ├── REQUIREMENT_TRACEABILITY.md        # Ma trận truy xuất yêu cầu và Rubric giảng viên
│   ├── artifact_hashes.json               # Mã băm SHA-256 các artifacts bàn giao
│   └── eda_summary.json                   # Báo cáo thống kê EDA xuất tự động
├── tests/                                 # Bộ kiểm thử tự động toàn diện (38 unit tests)
│   ├── test_temporal_split.py             # Kiểm thử không rò rỉ thời gian
│   ├── test_feature_alignment.py          # Kiểm thử căn chỉnh ma trận X và y
│   ├── test_no_target_leakage.py          # Kiểm thử cô lập target và train-only fit
│   ├── test_pipeline_reproducibility.py   # Kiểm thử tính tái lập 100%
│   ├── test_artifact_contract.py          # Kiểm thử tính toàn vẹn SHA-256
│   └── test_pems_bay_pipeline.py          # Kiểm thử pipeline PeMS-BAY & failure cases
└── [Các file tương thích ngược tại root] # train.csv, test.csv, X_train_preprocessed.csv,...
```

---

## 3. MÔI TRƯỜNG & HƯỚNG DẪN CÀI ĐẶT (ENVIRONMENT & INSTALL)
- **Môi trường thử nghiệm:** Python 3.12.10 trên nền tảng Windows 11 (hỗ trợ Linux/macOS).
- **Lệnh cài đặt môi trường:**
```bash
pip install -r workstream03/requirements.txt
```

---

## 4. LỆNH THỰC THI TÁI LẬP DỰ ÁN (RUN COMMANDS)

Chạy trực tiếp từ thư mục gốc của repository (đường dẫn hoàn toàn độc lập với CWD):

```bash
# 1. Sinh dữ liệu mô phỏng Seervada và RCSP teaching data
python workstream03/src/data_simulation.py

# 2. Phân chia Train/Test theo khối thời gian (Zero Data Leakage)
python workstream03/src/split_dataset.py

# 3. Tiền xử lý ma trận 26 đặc trưng và xuất JSON metadata
python workstream03/src/feature_pipeline.py

# 4. Phân tích khám phá dữ liệu (EDA) và xuất báo cáo JSON
python workstream03/src/eda_analysis.py
```

---

## 5. LỆNH CHẠY KIỂM THỬ TỰ ĐỘNG (TEST COMMANDS)

Chạy toàn bộ 38 bài kiểm thử đơn vị, kiểm thử hợp đồng và kiểm thử ngoại lệ:

```bash
pytest workstream03/tests -v
```

---

## 6. HƯỚNG DẪN PIPELINE THỰC TẾ PEMS-BAY (PEMS PIPELINE CLI)

Khi nhận file raw HDF5 từ giảng viên và danh sách cạnh từ WS1:

```bash
python workstream03/src/pems_bay_pipeline.py \
  --h5 data/raw/pems-bay.h5 \
  --edges workstream01/data/pems_bay_subnetwork_edges.csv \
  --output-dir workstream03/data/pems_bay \
  --train-ratio 0.7 \
  --val-ratio 0.1 \
  --test-ratio 0.2
```

---

## 7. HỢP ĐỒNG BÀN GIAO DOWNSTREAM (DOWNSTREAM CONTRACT)
- **WS4 (Baselines - Hà Minh):**
  + Nhận `train.csv`, `test.csv` cho Group Mean.
  + Nhận `X_train_preprocessed.csv`, `y_train.csv`, `X_test_preprocessed.csv`, `y_test.csv` cho Linear Regression.
  + Bắt buộc import hàm đánh giá: `from common.metrics import evaluate_all`.
- **WS5 (Neural Network - Yến Nhi):**
  + Nhận ma trận 26 đặc trưng. Input layer cố định đúng 26 neurons.
  + **Quy tắc bắt buộc:** Tuyệt đối không dùng `test.csv` làm early stopping. Trích xuất validation từ phần cuối Train set hoặc dùng bộ 5.400 dòng `seervada_travel_time_EXTENDED_NN.csv`.
- **WS6 (Dynamic Routing - Mỹ Lộc):**
  + Nhận `test.csv` để lấy `travel_time` thực tế (ground truth) chấm điểm tuyến đường được chọn.

---

## 8. HẠN CHẾ VÀ GIẢ ĐỊNH KỸ THUẬT (KNOWN LIMITATIONS & ASSUMPTIONS)
1. **Dữ liệu Seervada là Synthetic:** Dữ liệu có gắn chữ `SIMULATED` theo đúng yêu cầu đề bài của giảng viên, tuân thủ phân phối Log-Normal và chu kỳ giờ cao điểm.
2. **Proxy tốc độ cạnh PeMS-BAY:** Vận tốc cạnh được tính bằng proxy trung bình cộng 2 trạm cảm biến đầu và cuối ($v_{uv} = (v_u + v_v) / 2$). Đây là mô hình proxy, không phải đo lường trực tiếp toàn tuyến.
3. **Scaler Semantics:** Cự ly `distance` được chuẩn hóa Z-score với mẫu độ lệch chuẩn sample std ($ddof=1$, $s = 1.963885...$) để đảm bảo khớp 100% với các artifacts đã xuất.

---

## 9. TRẠNG THÁI HIỆN THỜI CỦA PEMS-BAY (PEMS-BAY READINESS)
- **CODE READY:** **YES** (Pipeline hoàn chỉnh, hỗ trợ CLI argparse).
- **MOCK TESTED:** **YES** (Đã kiểm thử toàn diện trên synthetic fixture, 9/9 tests pass).
- **RAW DATA AVAILABLE:** **NO** (File `pems-bay.h5` chưa có trong repo).
- **REAL RUN COMPLETE:** **NO** (Đang chờ cung cấp file thật).
- **WS1 CONTRACT READY:** **YES** (Giao diện hợp đồng 4 cột `edge_id, sensor_u, sensor_v, distance_miles` đã được kiểm định).
- **DOWNSTREAM READY:** **YES** (Sẵn sàng phục vụ WS4, WS5, WS6).
