   # Workstream 6 — Thử nghiệm định tuyến

   Workstream 6 so sánh các tuyến đường từ trọng số cạnh cố định và trọng số
   cạnh dự đoán trên mạng Seervada Park. Mỗi tuyến đường được đánh giá bằng
   thời gian di chuyển thực tế mô phỏng tương ứng với ngày kiểm thử.

   > Các quan sát thời gian di chuyển là mô phỏng, không phải số liệu đo thực tế
   > trên giao thông ngoài đời. Thời gian kiểm thử chỉ có sáu ngày, vì vậy kết
   > quả mang tính mô tả và không nên suy rộng thành đảm bảo hiệu suất thực tế.

   ## Quy trình

```text
data/seervada_network.csv
                  ┐
workstream03/train.csv ──┼──> workstream06/run_routing.py
workstream03/test.csv  ──┤       │
   WS4/WS5 prediction files ┘       ├── xác thực đầu vào và sự đồng bộ của dự đoán
                                   ├── chọn khung giờ báo cáo và nhãn so sánh
                                   ├── tìm tuyến đường cho từng ngày kiểm thử và từng khung giờ
                                   ├── chấm điểm từng tuyến bằng thời gian thực tế của ngày đó
                                   └── ghi bảng dữ liệu, đồ thị và bản tóm tắt Markdown
```

   WS3 tạo và cung cấp mạng lưới, dữ liệu giảng dạy RCSP và dữ liệu thời gian
   đi chuyển mô phỏng. WS2 sử dụng `seervada_rcsp_teaching.csv` để giải RCSP;
   WS6 sử dụng các tuyến đường RCSP từ WS2 như các tuyến đường tham chiếu cố
   định. WS6 không cộng thêm thời gian giảng dạy vào mạng lưới cũng như không
   dùng các thời gian giảng dạy đó để chấm điểm thí nghiệm thời gian di chuyển
   mô phỏng.

   ## Đầu vào

   Các đường dẫn được cấu hình gần đầu file [`run_routing.py`](./run_routing.py);
   tuỳ chọn dòng lệnh `--root` đặt gốc dự án.

   | Đầu vào | Mục đích |
   |---|---|
   | `data/seervada_network.csv` | 12 cạnh mạng không hướng và khoảng cách cố định của chúng |
   | `workstream03/train.csv` | Quan sát huấn luyện mô phỏng theo từng cạnh; dùng để tính trọng số trung bình huấn luyện cố định và chọn hai khung giờ báo cáo |
   | `workstream03/test.csv` | Thời gian di chuyển mô phỏng thực tế theo cạnh trong các ngày kiểm thử 25–30 |
   | `workstream04/pred_groupmean_raw.csv` | Dự đoán Group Mean; một `y_pred` cho mỗi hàng kiểm thử |
   | `workstream04/pred_linearreg_raw.csv` | Dự đoán Linear Regression; một `y_pred` cho mỗi hàng kiểm thử |
   | `workstream05/pred_nn.csv` | Dự đoán Neural Network; một `y_pred` cho mỗi hàng kiểm thử |
   | Các tệp WS4 `*_withkey.csv` | Xác minh sự khớp hàng dự đoán Group Mean và Linear Regression với hàng kiểm thử |

   Các tệp dự đoán phải có cùng thứ tự hàng như `test.csv`. Script kiểm tra số
   hàng, phạm vi cạnh mạng và các dự đoán WS4 có khóa. Nó cũng tính lại MAE/RMSE
   của dự đoán trên tập kiểm thử và so sánh với các chỉ số đã báo cáo khi có
   sẵn. Dự đoán Neural Network không có tệp đi kèm có khóa, nên việc căn chỉnh
   của nó không được kiểm tra trực tiếp bằng khóa.

   ## Các phương pháp so sánh

   Với mỗi trong năm khung giờ và mỗi trong sáu ngày kiểm thử, script tìm tuyến
   đường từ nguồn `O` đến đích `T` dưới các trọng số sau:

   1. **`Fixed_distance`** — khoảng cách mạng; tuyến đường thu được tối ưu hóa
      khoảng cách, không phải thời gian dự đoán.
   2. **`Fixed_trainmean`** — trung bình thời gian di chuyển mô phỏng trên mỗi
      cạnh trong toàn bộ tập huấn luyện, gom tất cả ngày và khung giờ.
   3. **`Pred_GroupMean`** — thời gian dự đoán Group Mean cho cạnh, ngày kiểm
      thử và khung giờ.
   4. **`Pred_LinearRegression`** — thời gian dự đoán Linear Regression cho hàng
      kiểm thử đó.
   5. **`Pred_NeuralNet`** — thời gian dự đoán Neural Network cho hàng kiểm thử
      đó.
   6. **`Oracle`** — tuyến đường tối ưu hóa thời gian thực tế cho cùng ngày và
      khung giờ kiểm thử. Đây là tham chiếu lý tưởng, không phải phương pháp dự
      đoán có thể triển khai, vì nó sử dụng các giá trị thực tế đang được đánh
      giá.
   7. **Năm phương pháp `RCSP_*`** — các tuyến đường cố định lấy từ kết quả RCSP
      của WS2, được chấm điểm trên thời gian mô phỏng thực tế của WS6. Các giá
      trị ràng buộc thời gian giảng dạy của WS2 không được áp dụng lại trong WS6.

   Mạng có 28 đường đi đơn giản từ O đến T. WS6 liệt kê các đường đi này để
   chọn tuyến đường có trọng số nhỏ nhất và đối chiếu chi phí tối thiểu với
   Dijkstra. Các trường hợp hòa được đếm; tuyến đường được chọn ưu tiên ít cạnh
   hơn trước, sau đó là thứ tự từ điển của tuyến đường.

   ## Đánh giá

   `actual_time` của mỗi tuyến đường là tổng thời gian di chuyển thực tế mô
   phỏng trên các cạnh của tuyến đó trong ngày và khung giờ kiểm thử tương ứng.
   `regret` là `actual_time - oracle_time`; giá trị thấp hơn là tốt hơn. Bản
   tóm tắt báo cáo trung bình và độ lệch chuẩn trên sáu ngày kiểm thử.

   Các khung giờ báo cáo chính được chọn là:

   - **Peak:** khung giờ có thời gian di chuyển trung bình trên các cạnh huấn
     luyện cao nhất.
   - **Off-peak:** khung giờ có thời gian di chuyển trung bình trên các cạnh
     huấn luyện thấp nhất.

   Trong dữ liệu hiện tại, đó là khung giờ 4 (16:30–18:30) và khung giờ 1
   (06:00–08:00). Script vẫn chạy và ghi kết quả cho cả năm khung giờ.

   ### Cách diễn giải quan trọng về lựa chọn mô hình

   Script hiện tại chọn baseline WS4 chính và quyết định xem NN có được đưa vào
   so sánh chính hay không bằng MAE/RMSE tính trên tập kiểm thử. Nó ghi
   `precommitted_rules.md` trước khi tính toán định tuyến, nhưng quy tắc lựa chọn
   mô hình bản thân vì vậy được thông tin từ nhãn kiểm thử. Hãy coi những lựa
   chọn và so sánh định tuyến này là nghiên cứu khám phá, không phải bài kiểm tra
   cuối cùng độc lập về hiệu suất mô hình. Để đánh giá cuối cùng không thiên lệch,
   cần cố định quyết định lựa chọn mô hình bằng dữ liệu huấn luyện/kiểm định trước
   khi xem kết quả kiểm thử, sau đó dành tập kiểm thử cho đánh giá cuối cùng.

   ## Chạy

   Từ thư mục gốc của repository:

   ```powershell
   python workstream06/run_routing.py
   ```

   Các đối số tùy chọn:

   ```powershell
   python workstream06/run_routing.py --root C:\path\to\RCSP
   python workstream06/run_routing.py --out C:\path\to\output
   ```

   Các dependency Python được script sử dụng:

   ```text
   numpy
   pandas
   matplotlib
   ```

   Script sử dụng backend Matplotlib không tương tác và ghi các tệp vào
   `workstream06/outputs/` theo mặc định. Các tệp hiện có cùng tên đầu ra sẽ bị
   ghi đè khi chạy lại script.

   ## Đầu ra

   | Đầu ra | Nội dung |
   |---|---|
   | `precommitted_rules.md` | Các quy tắc lựa chọn/báo cáo đã áp dụng và mô hình/khung giờ được chọn |
   | `selection.json` | MAE/RMSE kiểm thử được tính lại, quyết định baseline/NN, giá trị trung bình khung giờ huấn luyện |
   | `routing_results_all.csv` | Một hàng cho mỗi khung giờ/ngày/phương pháp, bao gồm tuyến đường, khoảng cách, thời gian dự đoán và thực tế, tuyến Oracle, thời gian Oracle, regret và số lượng hòa |
   | `summary_by_slot_method.csv` | Chế độ tuyến đường và hiệu suất trung bình theo khung giờ và phương pháp |
   | `route_by_slot.csv` | Bảng xoay các tuyến đường phổ biến theo phương pháp và khung giờ |
   | `model_comparison.csv` | Sự khác biệt tuyến đường theo cặp và so sánh thời gian thực tế |
   | `results_summary.md` | Báo cáo văn bản cho các khung giờ được chọn và so sánh theo cặp |
   | `fig_actual_time_main_slots.png` | Thời gian di chuyển tuyến thực tế cho các khung giờ peak và off-peak |
   | `fig_regret_all_slots.png` | Regret trung bình theo phương pháp cho tất cả năm khung giờ |
   | `fig_route_map.png` | Tuyến đường phổ biến theo phương pháp và khung giờ |

   Xem [`REPORT.md`](./REPORT.md) để biết kết quả thí nghiệm hiện tại và cách giải
   thích chúng.
