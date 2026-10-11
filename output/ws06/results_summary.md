# Kết quả WS6 - Routing Experiment

- Số đường đi đơn từ O đến T: **28**; số ngày test: **6** (mẫu nhỏ nên kết quả mang tính mô tả).
- Baseline chính: **GroupMean**; NN: trong so sánh chính.
- Khung peak = 4, off-peak = 1 (theo quy tắc chốt trước).
- Dữ liệu travel time là dữ liệu MÔ PHỎNG, không phải giao thông thực tế.

## Kiểm tra ghép dữ liệu
- [ok] GroupMean: file withkey khớp test.csv và file raw
- [ok] LinearRegression: file withkey khớp test.csv và file raw
- [ok] GroupMean: MAE=0.9841, RMSE=1.4110 khớp số WS đã báo cáo
- [info] LinearRegression: MAE=1.2139, RMSE=1.5832 (chưa có số báo cáo để đối chiếu)
- [ok] NeuralNet: MAE=0.7038, RMSE=0.9777 khớp số WS đã báo cáo

## Khung 4 (peak)
| method | modal_route | n_distinct_routes | mean_distance_km | mean_predicted_time | mean_actual_time | std_actual_time | mean_regret | days_equal_oracle |
|---|---|---|---|---|---|---|---|---|
| Fixed_distance | O-A-B-D-T | 1 | 13.000 |  | 35.047 | 7.205 | 9.113 | 0 |
| Fixed_trainmean | O-B-E-T | 1 | 15.000 | 22.244 | 27.185 | 2.673 | 1.252 | 0 |
| Pred_GroupMean | O-B-E-T | 1 | 15.000 | 27.056 | 27.185 | 2.673 | 1.252 | 0 |
| Pred_LinearRegression | O-B-E-T | 1 | 15.000 | 27.967 | 27.185 | 2.673 | 1.252 | 0 |
| Pred_NeuralNet | O-B-E-T | 2 | 14.833 | 26.862 | 26.927 | 2.846 | 0.993 | 0 |
| Oracle | O-C-E-T | 3 | 14.833 |  | 25.933 | 3.044 | 0.000 | 6 |

## Khung 1 (offpeak)
| method | modal_route | n_distinct_routes | mean_distance_km | mean_predicted_time | mean_actual_time | std_actual_time | mean_regret | days_equal_oracle |
|---|---|---|---|---|---|---|---|---|
| Fixed_distance | O-A-B-D-T | 1 | 13.000 |  | 17.767 | 0.527 | 2.953 | 0 |
| Fixed_trainmean | O-B-E-T | 1 | 15.000 | 22.244 | 16.057 | 1.756 | 1.243 | 1 |
| Pred_GroupMean | O-B-E-T | 1 | 15.000 | 15.932 | 16.057 | 1.756 | 1.243 | 1 |
| Pred_LinearRegression | O-C-B-E-D-T | 1 | 14.000 | 14.001 | 16.878 | 0.877 | 2.065 | 0 |
| Pred_NeuralNet | O-C-E-D-T | 3 | 14.333 | 15.181 | 16.032 | 0.821 | 1.218 | 2 |
| Oracle | O-A-D-T | 4 | 14.500 |  | 14.813 | 1.554 | 0.000 | 6 |

## So sánh từng cặp phương pháp (mọi khung giờ)
| method_A | method_B | time_slot | n_days | days_route_differs | days_same_route_but_different_predicted_time | mean_actual_A_minus_B |
|---|---|---|---|---|---|---|
| Pred_GroupMean | Pred_NeuralNet | 1 | 6 | 6 | 0 | 0.025 |
| Pred_GroupMean | Pred_NeuralNet | 2 | 6 | 1 | 5 | -0.015 |
| Pred_GroupMean | Pred_NeuralNet | 3 | 6 | 4 | 2 | -0.722 |
| Pred_GroupMean | Pred_NeuralNet | 4 | 6 | 1 | 5 | 0.258 |
| Pred_GroupMean | Pred_NeuralNet | 5 | 6 | 6 | 0 | 0.532 |
| Pred_GroupMean | Pred_LinearRegression | 1 | 6 | 6 | 0 | -0.822 |
| Pred_GroupMean | Pred_LinearRegression | 2 | 6 | 0 | 6 | 0.000 |
| Pred_GroupMean | Pred_LinearRegression | 3 | 6 | 6 | 0 | -1.215 |
| Pred_GroupMean | Pred_LinearRegression | 4 | 6 | 0 | 6 | 0.000 |
| Pred_GroupMean | Pred_LinearRegression | 5 | 6 | 6 | 0 | 0.305 |
| Fixed_distance | Pred_GroupMean | 1 | 6 | 6 | 0 | 1.710 |
| Fixed_distance | Pred_GroupMean | 2 | 6 | 6 | 0 | 9.623 |
| Fixed_distance | Pred_GroupMean | 3 | 6 | 6 | 0 | 3.170 |
| Fixed_distance | Pred_GroupMean | 4 | 6 | 6 | 0 | 7.862 |
| Fixed_distance | Pred_GroupMean | 5 | 6 | 6 | 0 | 2.307 |
| Fixed_trainmean | Pred_GroupMean | 1 | 6 | 0 | 6 | 0.000 |
| Fixed_trainmean | Pred_GroupMean | 2 | 6 | 0 | 6 | 0.000 |
| Fixed_trainmean | Pred_GroupMean | 3 | 6 | 6 | 0 | 1.410 |
| Fixed_trainmean | Pred_GroupMean | 4 | 6 | 0 | 6 | 0.000 |
| Fixed_trainmean | Pred_GroupMean | 5 | 6 | 6 | 0 | -0.305 |
| Fixed_distance | Fixed_trainmean | 1 | 6 | 6 | 0 | 1.710 |
| Fixed_distance | Fixed_trainmean | 2 | 6 | 6 | 0 | 9.623 |
| Fixed_distance | Fixed_trainmean | 3 | 6 | 6 | 0 | 1.760 |
| Fixed_distance | Fixed_trainmean | 4 | 6 | 6 | 0 | 7.862 |
| Fixed_distance | Fixed_trainmean | 5 | 6 | 6 | 0 | 2.612 |

**Pred_GroupMean so với Pred_NeuralNet**: route khác nhau ở 18/30 cặp (khung giờ, ngày). 
