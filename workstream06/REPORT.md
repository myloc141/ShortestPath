# Luồng công việc 6 — Báo cáo thử nghiệm định tuyến

## 1. Mục tiêu

Luồng công việc 6 đánh giá ảnh hưởng của các cách gán trọng số cạnh đến
các tuyến đường từ `O` đến `T` trên mạng lưới Seervada Park. Báo cáo so sánh
các tuyến được chọn dựa trên khoảng cách thực tế, thời gian di chuyển trung
bình của tập huấn luyện và dự đoán từ WS4/WS5. Các tuyến được đánh giá dựa
trên thời gian di chuyển thực tế mô phỏng của từng ngày và khung giờ kiểm
tra tương ứng.

Thử nghiệm được triển khai trong [`run_routing.py`](./run_routing.py). Dữ
liệu mạng lưới và giao thông đầu vào là dữ liệu dự án được mô phỏng/tổng hợp;
kết quả thời gian di chuyển **không phải số liệu đo giao thông ngoài thực tế**.

## 2. Dữ liệu và phạm vi

- Mạng lưới: 7 nút (`O, A, B, C, D, E, T`) và 12 cạnh vô hướng.
- Điểm xuất phát và điểm đến: `O` đến `T`.
- Giai đoạn huấn luyện: ngày 1–24.
- Giai đoạn kiểm tra: ngày 25–30, tổng cộng sáu ngày.
- Khung giờ: năm khung mỗi ngày, từ 06:00–08:00 đến 19:30–21:30.
- Quan sát giao thông: một giá trị thời gian di chuyển cho mỗi cạnh, ngày
  và khung giờ.
- Khoảng cách được tính bằng km; thời gian di chuyển mô phỏng được tính bằng phút.

WS3 cung cấp `data/seervada_network.csv`, dữ liệu giao thông huấn luyện/kiểm
tra và dữ liệu đầu vào mô hình đã tiền xử lý. WS4 cung cấp dự đoán Group Mean
và Linear Regression; WS5 cung cấp dự đoán Neural Network. WS2 cung cấp các
tuyến RCSP để tham chiếu. Cụ thể, WS2 đọc dữ liệu `seervada_rcsp_teaching.csv`
do WS3 cung cấp; WS6 sử dụng các tuyến thu được để so sánh và không dùng thời
gian trong dữ liệu giảng dạy làm thời gian thực tế mô phỏng.

## 3. Phương pháp

### 3.1 Chọn tuyến

Tập lệnh liệt kê 28 tuyến đơn (không lặp nút) từ `O` đến `T` trong mạng lưới.
Với mỗi ngày và khung giờ kiểm tra, tập lệnh chọn tuyến có tổng trọng số nhỏ
nhất theo các phương pháp sau:

- **Khoảng cách cố định:** khoảng cách cạnh trong mạng lưới.
- **Trung bình huấn luyện cố định:** thời gian di chuyển trung bình của mỗi
  cạnh, tính trên toàn bộ ngày và khung giờ huấn luyện.
- **Group Mean:** dự đoán WS4 cho từng dòng dữ liệu.
- **Linear Regression:** dự đoán WS4 cho từng dòng dữ liệu.
- **Neural Network:** dự đoán WS5 cho từng dòng dữ liệu.
- **Oracle:** thời gian di chuyển thực tế trong cùng ngày và khung giờ kiểm
  tra; đây là mốc tham chiếu lý tưởng hóa cận dưới, không phải mô hình dự đoán
  có thể triển khai.

Tập lệnh cũng đánh giá năm tuyến WS2 cố định: ba tuyến tối ưu với giới hạn
RCSP 18 phút, một tuyến với giới hạn 19 phút và một tuyến với giới hạn từ
20 phút trở lên. Trong WS6, đây chỉ là các tuyến cố định được tính điểm bằng
thời gian thực tế mô phỏng; ràng buộc thời gian trong dữ liệu giảng dạy của
WS2 không được áp dụng lại.

Nếu các tuyến có cùng trọng số, quy tắc chọn ưu tiên tuyến có ít cạnh hơn,
sau đó ưu tiên thứ tự từ điển của tuyến. Chi phí tuyến tối thiểu được đối
chiếu với thuật toán Dijkstra cho từng phương pháp/ngày/khung giờ.

### 3.2 Tính điểm và tổng hợp

Với mỗi tuyến được chọn, `actual_time` là tổng thời gian di chuyển thực tế
của các cạnh trong tuyến ở cùng ngày và khung giờ kiểm tra. Độ hối tiếc
(regret) được tính như sau:

```text
regret = actual_time(route) - actual_time(Oracle route)
```

Tập lệnh báo cáo thời gian thực tế trung bình, độ lệch chuẩn và độ hối tiếc
trung bình trên các ngày kiểm tra. Kết quả được tính cho cả năm khung giờ;
phần tóm tắt chính tập trung vào:

- **Khung giờ cao điểm:** khung có thời gian di chuyển cạnh trung bình cao
  nhất trong tập huấn luyện.
- **Khung giờ thấp điểm:** khung có thời gian di chuyển cạnh trung bình thấp
  nhất trong tập huấn luyện.

Với dữ liệu hiện tại, đây lần lượt là khung 4 (16:30–18:30) và khung 1
(06:00–08:00).

### 3.3 Đối chiếu dự đoán và lưu ý về cách chọn

Các tệp dự đoán WS4 có khóa được đối chiếu với tập kiểm tra và các tệp dự
đoán thô tương ứng. Tập lệnh cũng kiểm tra số dòng dự đoán và so sánh MAE/RMSE
kiểm tra được tính lại với các giá trị đã cấu hình khi có. Tệp NN không có
tệp đi kèm chứa khóa, vì vậy không thể thực hiện kiểm tra đối chiếu trực
tiếp theo khóa tương tự.

**Mã hiện tại chọn mô hình WS4 cơ sở chính và quyết định có đưa NN vào hay
không dựa trên MAE/RMSE của tập kiểm tra.** Mặc dù tệp
`precommitted_rules.md` được tạo trước vòng lặp định tuyến, điều đó không
khiến quyết định chọn mô hình độc lập với tập kiểm tra: việc chọn đã sử dụng
nhãn kiểm tra. Vì vậy, kết quả lựa chọn và so sánh định tuyến cần được xem
là kết quả thăm dò. Để có so sánh cuối cùng không thiên lệch, cần chọn mô
hình bằng dữ liệu huấn luyện/kiểm định, cố định lựa chọn đó, rồi chỉ đánh
giá một lần trên tập kiểm tra được giữ riêng.

## 4. Kiểm tra mô hình hiện tại

Các chỉ số dự đoán được tính lại từ dữ liệu đầu vào hiện tại:

| Mô hình | MAE (phút) | RMSE (phút) | Kiểm tra chỉ số đã báo cáo |
|---|---:|---:|---|
| Group Mean | 0.9841 | 1.4110 | Khớp với các giá trị WS4 đã cấu hình |
| Linear Regression | 1.2139 | 1.5832 | Không có giá trị báo cáo đã cấu hình để đối chiếu |
| Neural Network | 0.7038 | 0.9777 | Khớp với các giá trị WS5 đã cấu hình |

Theo quy tắc hiện tại của tập lệnh, **Group Mean** là mô hình WS4 cơ sở chính
vì có MAE và RMSE thấp hơn Linear Regression. **Neural Network được đưa vào
phần so sánh chính** vì cả MAE lẫn RMSE đều thấp hơn Group Mean. Các quyết
định này có tham khảo tập kiểm tra và chịu ảnh hưởng của lưu ý nêu trên.

Giá trị thời gian di chuyển cạnh trung bình của tập huấn luyện xác định
khung 4 là cao điểm và khung 1 là thấp điểm. Mạng lưới có 28 tuyến đơn; kết
quả định tuyến bao gồm cả năm khung giờ, sáu ngày kiểm tra và 11 phương pháp
(hai phương pháp trọng số cố định, ba phương pháp dự đoán, Oracle và năm
tuyến tham chiếu RCSP).

## 5. Kết quả cho các khung giờ chính

Các giá trị dưới đây được tính trên sáu ngày kiểm tra. Thời gian di chuyển
thực tế trung bình và độ lệch chuẩn được tính bằng phút; độ hối tiếc cũng
tính bằng phút. “Tuyến phổ biến nhất” là tuyến được chọn nhiều lần nhất,
không nhất thiết là tuyến được chọn mỗi ngày.

### 5.1 Cao điểm — khung 4 (16:30–18:30)

| Phương pháp | Tuyến phổ biến nhất | Khoảng cách trung bình (km) | Thời gian thực tế trung bình ± ĐLC (phút) | Độ hối tiếc trung bình (phút) | Số ngày bằng Oracle |
|---|---|---:|---:|---:|---:|
| Khoảng cách cố định | O–A–B–D–T | 13.000 | 35.047 ± 7.205 | 9.113 | 0/6 |
| Trung bình huấn luyện cố định | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Group Mean | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Linear Regression | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Neural Network | O–B–E–T | 14.833 | 26.927 ± 2.846 | 0.993 | 0/6 |
| Oracle | O–C–E–T | 14.833 | 25.933 ± 3.044 | 0.000 | 6/6 |

Trong khung giờ cao điểm, định tuyến chỉ dựa trên khoảng cách luôn chọn
tuyến có chiều dài vật lý ngắn nhất, nhưng tuyến đó có thời gian di chuyển
thực tế mô phỏng trung bình cao nhất trong các phương pháp được trình bày.
Tuyến NN có độ hối tiếc trung bình thấp nhất trong số các phương pháp không
phải Oracle ở khung giờ này. Đây là quan sát trên sáu ngày kiểm tra mô
phỏng, không phải bằng chứng về hiệu suất được đảm bảo ngoài phạm vi thử
nghiệm.

### 5.2 Thấp điểm — khung 1 (06:00–08:00)

| Phương pháp | Tuyến phổ biến nhất | Khoảng cách trung bình (km) | Thời gian thực tế trung bình ± ĐLC (phút) | Độ hối tiếc trung bình (phút) | Số ngày bằng Oracle |
|---|---|---:|---:|---:|---:|
| Khoảng cách cố định | O–A–B–D–T | 13.000 | 17.767 ± 0.527 | 2.953 | 0/6 |
| Trung bình huấn luyện cố định | O–B–E–T | 15.000 | 16.057 ± 1.756 | 1.243 | 1/6 |
| Group Mean | O–B–E–T | 15.000 | 16.057 ± 1.756 | 1.243 | 1/6 |
| Linear Regression | O–C–B–E–D–T | 14.000 | 16.878 ± 0.877 | 2.065 | 0/6 |
| Neural Network | O–C–E–D–T | 14.333 | 16.032 ± 0.821 | 1.218 | 2/6 |
| Oracle | O–A–D–T | 14.500 | 14.813 ± 1.554 | 0.000 | 6/6 |

Trong khung giờ thấp điểm, NN có thời gian thực tế trung bình và độ hối
tiếc thấp nhất trong số các phương pháp không phải Oracle được trình bày,
nhỉnh hơn Group Mean một chút. Tuyến phổ biến nhất của NN được chọn trong
ba trên sáu ngày kiểm tra; các ngày còn lại, mô hình chọn những tuyến khác.

### 5.3 So sánh tất cả khung giờ

Group Mean và NN chọn các tuyến khác nhau trong **18 trên 30** trường hợp
(năm khung giờ nhân sáu ngày kiểm tra). Chỉ riêng khác biệt về tuyến không
cho biết phương pháp dự đoán nào tốt hơn; hãy dùng thời gian di chuyển thực
tế và độ hối tiếc để đánh giá từng trường hợp. Kết quả chi tiết cho tất cả
các khung giờ nằm trong
[`outputs/summary_by_slot_method.csv`](./outputs/summary_by_slot_method.csv)
và [`outputs/model_comparison.csv`](./outputs/model_comparison.csv).

## 6. Diễn giải và giới hạn

1. **Khoảng cách và thời gian di chuyển là hai mục tiêu khác nhau.** Tuyến
   có khoảng cách vật lý ngắn nhất không nhất thiết có thời gian di chuyển
   mô phỏng ngắn nhất.
2. **Trung bình huấn luyện cố định không xét khung giờ.** Phương pháp này
   lấy trung bình các quan sát huấn luyện của từng cạnh trên mọi ngày và
   khung giờ, khác với dự đoán theo từng khung giờ của các mô hình.
3. **Oracle không phải phương pháp vận hành thực tế.** Oracle dùng thời
   gian di chuyển thực tế của chính ngày đó để chọn tuyến và chỉ được đưa
   vào làm mốc tham chiếu lý tưởng.
4. **WS6 đánh giá các tuyến RCSP, không giải lại bài toán.** Thời gian và
   giới hạn tài nguyên WS2 lấy từ tập dữ liệu giảng dạy; WS6 chấm điểm các
   tuyến cố định đó bằng tập dữ liệu giao thông mô phỏng riêng.
5. **Giai đoạn kiểm tra nhỏ và được mô phỏng.** Sáu ngày kiểm tra phù hợp
   với một so sánh có kiểm soát nhưng không đủ để đưa ra kết luận rộng hoặc
   khẳng định về thế giới thực.
6. **Chọn mô hình dựa trên tập kiểm tra có thể làm sai lệch kết quả.**
   Quyết định chọn mô hình cơ sở chính và đưa NN vào hiện phụ thuộc vào các
   chỉ số trên tập kiểm tra. Để có kết quả xác nhận, hãy chọn phương pháp
   bằng dữ liệu kiểm định trước khi đánh giá trên tập kiểm tra.

## 7. Tái tạo kết quả và các tệp đầu ra

Chạy lệnh sau từ thư mục gốc của kho mã nguồn:

```powershell
python workstream06/run_routing.py
```

Tập lệnh sử dụng NumPy, pandas và Matplotlib, đồng thời ghi kết quả vào
`workstream06/outputs/`. Các tệp được tạo gồm:

- `precommitted_rules.md` và `selection.json`
- `routing_results_all.csv`, `summary_by_slot_method.csv`,
  `route_by_slot.csv` và `model_comparison.csv`
- `results_summary.md`
- `fig_actual_time_main_slots.png`, `fig_regret_all_slots.png` và
  `fig_route_map.png`

Xem [`README.md`](./README.md) để biết chi tiết dữ liệu đầu vào và định
nghĩa các tệp đầu ra.
