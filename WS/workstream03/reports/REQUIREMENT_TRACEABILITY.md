# MA TRẬN TRUY XUẤT YÊU CẦU DỰ ÁN (REQUIREMENT TRACEABILITY MATRIX)
**Học phần:** Vận trù học | UEL / ĐHQG-HCM  
**Chủ đề:** 5. Mối liên hệ giữa bài toán đường đi ngắn nhất và machine learning / routing hiện đại (Mức độ C)  
**Người phụ trách:** Lại Gia Huy (Workstream 3: Data Engineering)  
**Thời điểm cập nhật:** 2026-10-12  

---

## 1. MA TRẬN TRUY XUẤT YÊU CẦU KỸ THUẬT VÀ QUY CHUẨN NHÓM

| Yêu cầu kỹ thuật | Nguồn gốc | Người phụ trách | Tài liệu / Artifact chứng minh | Trạng thái | Ghi chú & Đánh giá |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Quy chuẩn Input – Processing – Output – Downstream** | Google Sheet Dòng 2 & Chỉ đạo Nhóm trưởng | Toàn nhóm (WS3 tiên phong) | Docstring chuẩn hóa ở đầu mọi file Python: `data_simulation.py`, `split_dataset.py`, `feature_pipeline.py`, `eda_analysis.py`, `pems_bay_pipeline.py`, `common/metrics.py`. | **PASS** | Đã tuân thủ 100% trên toàn bộ các tập lệnh của WS3 và common module. |
| **Tập trung hóa Metrics tại `common/metrics.py`** | Google Sheet Dòng 5 & Note Nhóm trưởng | Lại Gia Huy | `common/metrics.py` (MSE, RMSE, MAE, MAPE có bảo vệ chia cho 0). | **PASS** | 100% kiểm thử qua test suite, các workstream WS4, WS5, WS6 bắt buộc import dùng chung. |
| **Chống rò rỉ dữ liệu (Zero Data Leakage)** | Prompt & Phương pháp luận Học thuật | Lại Gia Huy | `workstream03/tests/test_temporal_split.py`, `test_no_target_leakage.py`. | **PASS** | `max(Train Day) = 24 < min(Test Day) = 25`. Scaler & Encoder fit duy nhất trên Train. Biến mục tiêu `travel_time` vắng mặt trong $X$. |
| **Phân chia theo chuỗi thời gian (Temporal Split)** | Đề bài & Thiết kế WS3 | Lại Gia Huy | `workstream03/src/split_dataset.py`, `train.csv` (1.440 dòng), `test.csv` (360 dòng). | **PASS** | Tách theo ngày nguyên vẹn (Days 1–24 vs 25–30), không random shuffle, tỷ lệ chuẩn 80% - 20%. |
| **Hợp đồng bàn giao WS4 (Baselines)** | Google Sheet Dòng 67-83 | Hà Minh $\leftarrow$ Lại Gia Huy | `HANDOFF_MANIFEST.md`, `X_train_preprocessed.csv`, `y_train.csv`, `X_test_preprocessed.csv`, `y_test.csv`. | **PASS** | Đã sẵn sàng nạp trực tiếp cho Group Mean và Linear Regression. |
| **Hợp đồng bàn giao WS5 (Neural Network)** | Google Sheet Dòng 84-101 | Yến Nhi $\leftarrow$ Lại Gia Huy | `HANDOFF_MANIFEST.md`, khuyến nghị phân tách Validation Set từ Train hoặc dùng bộ 5.400 dòng. | **PASS** | Đảm bảo cố định 26 neurons đầu vào, nghiêm cấm dùng Test set làm early stopping. |
| **Hợp đồng bàn giao WS6 (Dynamic Routing)** | Google Sheet Dòng 102-126 | Mỹ Lộc $\leftarrow$ Lại Gia Huy | `HANDOFF_MANIFEST.md`, `test.csv` chứa `travel_time` thực tế (ground truth). | **PASS** | Khóa kết nối `edge_id` và `time_slot`, kiểm định tuyến đường dựa trên actual Test travel time. |
| **Đường dẫn độc lập, không hardcode (Reproducibility)** | Quy tắc Tái lập | Lại Gia Huy | Toàn bộ script trong `workstream03/src/` dùng `pathlib.Path(__file__).resolve()`. | **PASS** | Có thể chạy từ repo root `python workstream03/src/...` hoặc bất kỳ thư mục con nào mà không phụ thuộc CWD. |
| **Từ điển Dữ liệu (Data Dictionary)** | Đề tài & Báo cáo | Lại Gia Huy | `workstream03/DATA_DICTIONARY.md`. | **PASS** | Mô tả chi tiết kiểu dữ liệu, đơn vị, miền giá trị cho cả mạng Seervada và cấu trúc PeMS-BAY. |
| **Tính nhất quán giữa Báo cáo và Số liệu** | Phương pháp luận | Lại Gia Huy | `workstream03/DATA_ENGINEERING_REPORT.md`, hiệu đính nghiệm RCSP $T_{max}=18$ (14 km). | **PASS** | Mọi con số đều được kiểm chứng độc lập bằng Python, không có số liệu bịa đặt. |
| **Hạ tầng Pipeline dữ liệu thực tế PeMS-BAY** | Google Sheet Dòng 59-66 & Rubric Mức độ C | Lại Gia Huy | `workstream03/src/pems_bay_pipeline.py`, `workstream03/tests/test_pems_bay_pipeline.py`. | **PASS** (Code & Test Ready) | Đầy đủ CLI, xử lý lưới 5 phút, kiểm tra hợp đồng cảm biến WS1, nội suy nhân quả (causal ffill), gom cụm 5 khung giờ, test suite 9 unit tests. |

---

## 2. MA TRẬN TRUY XUẤT THEO RUBRIC ĐÁNH GIÁ CỦA GIẢNG VIÊN (TOPICS.PDF)

| Tiêu chí Rubric | Tỷ trọng | Mức đạt tốt theo yêu cầu của Giảng viên | Minh chứng thực tế từ Workstream 3 | Trạng thái đánh giá |
| :--- | :--- | :--- | :--- | :--- |
| **1. Mô hình và ký hiệu** | 20% | Mô hình đúng, đầy đủ; ký hiệu nhất quán; nêu rõ giả định. | Định nghĩa nhất quán các ký hiệu: đồ thị $G=(V, E)$, cự ly $d_{uv}$, tốc độ proxy $v_{uv}(t) = \frac{v_u(t) + v_v(t)}{2}$, thời gian di chuyển $t_{uv}(t) = \frac{d_{uv}}{v_{uv}(t)} \times 60$, Z-score chuẩn hóa $z = \frac{x - \bar{x}}{s}$. | **PASS** |
| **2. Dữ liệu và khả năng tái lập** | 15% | Nêu nguồn, ngày truy xuất, tiền xử lý; phân biệt loại dữ liệu; tệp nộp tái lập được mọi con số. | - Phân định rõ: `seervada_network.csv` (dữ liệu giáo trình), `seervada_rcsp_teaching.csv` (dạy học), `seervada_travel_time_SIMULATED.csv` (mô phỏng, có chữ SIMULATED theo đúng quy ước trang 13), `pems-bay.h5` (dữ liệu thực Caltrans PeMS).<br>- Toàn bộ 38 bài kiểm thử unit tests `pytest` đạt 100% PASS.<br>- Cung cấp mã hash SHA-256 đối chiếu toàn vẹn (`artifact_hashes.json`). | **PASS** |
| **3. Phương pháp và kiểm chứng** | 20% | Trình bày các bước; nêu quy ước; kiểm chứng bằng Solver hoặc code. | - Kiểm chứng chéo mọi bước bằng Python độc lập.<br>- Chứng minh tính toán phân phối Log-Normal lệch phải, chu kỳ giờ cao điểm.<br>- Viết test suite kiểm chứng chống rò rỉ dữ liệu thời gian. | **PASS** |
| **4. Phân tích và diễn giải** | 20% | Có bảng/hình so sánh; diễn giải đúng dưới góc nhìn quản trị/kinh tế/logistics. | Báo cáo kỹ thuật phân tích sâu sắc ý nghĩa của phân phối lệch phải (Right-skewed Delay), chi phí rủi ro ùn tắc giao thông, và sự đánh đổi giữa thời gian hành trình và cự ly trong bài toán logistics. | **PASS** |
| **5. Mở rộng (Tiêu chí 15%)** | 15% | Vượt nội dung trên lớp, có kết quả cụ thể, tương xứng mức C. | - Xây dựng bộ dữ liệu mở rộng 5.400 dòng (`seervada_travel_time_EXTENDED_NN.csv`) cho Deep Learning.<br>- Thiết kế hoàn chỉnh pipeline chuẩn công nghiệp cho dữ liệu thực tế PeMS-BAY (`pems_bay_pipeline.py`) với đầy đủ cơ chế lọc lỗi cảm biến, kiểm tra hợp đồng WS1 và gom cụm động. | **PASS** |
| **6. Trình bày và hỏi–đáp** | 10% | Đúng thời gian, rõ ràng, trả lời chính xác. | Cung cấp tài liệu bàn giao rõ ràng, súc tích, có dẫn chứng số liệu thực nghiệm bảo vệ trước hội đồng phản biện. | **PASS** |
