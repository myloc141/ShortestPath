# Quy tắc chốt trước khi chạy routing (WS6)
Ghi lúc: 2026-10-11T13:48:03

Các quy tắc dưới đây chỉ dùng train set và metric dự báo (MAE/RMSE trên test). Chúng được tính và ghi
TRƯỚC khi chạy routing, nên kết quả routing không ảnh hưởng đến việc chọn mô hình hay khung giờ.

1. **Baseline chính của routing**: trong GroupMean và LinearRegression, chọn mô hình có MAE và RMSE đều thấp hơn.
   Nếu hai chỉ số mâu thuẫn, mặc định GroupMean và ghi rõ trong báo cáo.
   -> Kết quả: **GroupMean** (GroupMean tốt hơn hoặc bằng LinearRegression ở cả MAE và RMSE).
2. **NN trong so sánh chính**: NN được xem là phương pháp chính nếu MAE và RMSE đều thấp hơn baseline chính.
   Nếu không, NN vẫn được chạy nhưng chỉ là tham chiếu.
   -> Kết quả: NN **vào so sánh chính**.
3. **Hai khung giờ chính**: khung có travel time trung bình trên train cao nhất (peak) và thấp nhất (off-peak).
   -> Kết quả: peak = khung 4, off-peak = khung 1.
   Cả 5 khung giờ vẫn được chạy và báo cáo ở phần bổ sung.
4. **Trọng số cố định**: chạy cả hai phiên bản - `Fixed_distance` (distance trong network) và `Fixed_trainmean`
   (travel time trung bình của từng cạnh trên toàn bộ train).
5. **Đánh giá**: với mỗi (khung giờ, ngày test), route được đánh giá bằng tổng actual travel time của các cạnh
   trong đúng ngày đó. Predicted travel time không dùng để chấm điểm. Báo cáo trung bình và độ lệch chuẩn qua các ngày test,
   cùng "regret" = actual time của route - actual time của route tối ưu trong ngày đó (Oracle).
6. **Quy ước hòa**: khi nhiều route cùng tổng trọng số, chọn route ít cạnh hơn, rồi theo thứ tự chữ cái.
