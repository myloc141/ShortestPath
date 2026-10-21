# Routing experiment summary
- Simple routes from `400479` to `400971`: **7**; test days: **28**.
- Primary baseline: **GroupMean**; Neural Network: in the main comparison.
- Peak slot: **4**; off-peak slot: **1**.
- Simulated travel times are not real-world traffic measurements.

## Prediction alignment
- GroupMean: 3780 predictions aligned with 3780 test observations
- NeuralNet: 3780 predictions aligned with 3780 test observations

## Main-slot results
| slot | time_slot | method | mean_actual_time | mean_regret | days_equal_oracle | n_days |
| --- | --- | --- | --- | --- | --- | --- |
| peak | 4 | Fixed_distance | 0.751 | 0.087 | 5 | 28 |
| peak | 4 | Fixed_trainmean | 0.675 | 0.011 | 2 | 28 |
| peak | 4 | Oracle | 0.664 | 0.000 | 28 | 28 |
| peak | 4 | Pred_GroupMean | 0.665 | 0.001 | 22 | 28 |
| peak | 4 | Pred_NeuralNet | 0.666 | 0.003 | 14 | 28 |
| offpeak | 1 | Fixed_distance | 0.435 | 0.008 | 2 | 28 |
| offpeak | 1 | Fixed_trainmean | 0.429 | 0.002 | 13 | 28 |
| offpeak | 1 | Oracle | 0.427 | 0.000 | 28 | 28 |
| offpeak | 1 | Pred_GroupMean | 0.432 | 0.005 | 4 | 28 |
| offpeak | 1 | Pred_NeuralNet | 0.430 | 0.003 | 6 | 28 |

## Pairwise method comparison
| method_a | method_b | time_slot | n_days | days_route_differs | days_same_route_but_different_predicted_time | mean_actual_a_minus_b |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed_distance | Fixed_trainmean | 1 | 28 | 28 | 0 | 0.006 |
| Fixed_distance | Fixed_trainmean | 2 | 28 | 28 | 0 | 0.016 |
| Fixed_distance | Fixed_trainmean | 3 | 28 | 28 | 0 | -0.010 |
| Fixed_distance | Fixed_trainmean | 4 | 28 | 28 | 0 | 0.076 |
| Fixed_distance | Fixed_trainmean | 5 | 28 | 28 | 0 | 0.003 |
| Fixed_distance | Pred_GroupMean | 1 | 28 | 12 | 0 | 0.003 |
| Fixed_distance | Pred_GroupMean | 2 | 28 | 16 | 0 | 0.025 |
| Fixed_distance | Pred_GroupMean | 3 | 28 | 16 | 0 | -0.010 |
| Fixed_distance | Pred_GroupMean | 4 | 28 | 20 | 0 | 0.086 |
| Fixed_distance | Pred_GroupMean | 5 | 28 | 8 | 0 | 0.003 |
| Fixed_distance | Pred_NeuralNet | 1 | 28 | 28 | 0 | 0.005 |
| Fixed_distance | Pred_NeuralNet | 2 | 28 | 28 | 0 | 0.017 |
| Fixed_distance | Pred_NeuralNet | 3 | 28 | 24 | 0 | -0.007 |
| Fixed_distance | Pred_NeuralNet | 4 | 28 | 20 | 0 | 0.084 |
| Fixed_distance | Pred_NeuralNet | 5 | 28 | 20 | 0 | 0.000 |
| Fixed_distance | Oracle | 1 | 28 | 26 | 0 | 0.008 |
| Fixed_distance | Oracle | 2 | 28 | 21 | 0 | 0.036 |
| Fixed_distance | Oracle | 3 | 28 | 18 | 0 | 0.013 |
| Fixed_distance | Oracle | 4 | 28 | 23 | 0 | 0.087 |
| Fixed_distance | Oracle | 5 | 28 | 26 | 0 | 0.008 |
| Fixed_trainmean | Pred_GroupMean | 1 | 28 | 28 | 0 | -0.003 |
| Fixed_trainmean | Pred_GroupMean | 2 | 28 | 28 | 0 | 0.009 |
| Fixed_trainmean | Pred_GroupMean | 3 | 28 | 24 | 4 | -0.001 |
| Fixed_trainmean | Pred_GroupMean | 4 | 28 | 28 | 0 | 0.010 |
| Fixed_trainmean | Pred_GroupMean | 5 | 28 | 28 | 0 | 0.000 |
| Fixed_trainmean | Pred_NeuralNet | 1 | 28 | 16 | 12 | -0.001 |
| Fixed_trainmean | Pred_NeuralNet | 2 | 28 | 24 | 4 | 0.002 |
| Fixed_trainmean | Pred_NeuralNet | 3 | 28 | 12 | 16 | 0.003 |
| Fixed_trainmean | Pred_NeuralNet | 4 | 28 | 16 | 12 | 0.008 |
| Fixed_trainmean | Pred_NeuralNet | 5 | 28 | 20 | 8 | -0.002 |
| Fixed_trainmean | Oracle | 1 | 28 | 15 | 0 | 0.002 |
| Fixed_trainmean | Oracle | 2 | 28 | 21 | 0 | 0.021 |
| Fixed_trainmean | Oracle | 3 | 28 | 21 | 0 | 0.023 |
| Fixed_trainmean | Oracle | 4 | 28 | 26 | 0 | 0.011 |
| Fixed_trainmean | Oracle | 5 | 28 | 21 | 0 | 0.006 |
| Pred_GroupMean | Pred_NeuralNet | 1 | 28 | 28 | 0 | 0.002 |
| Pred_GroupMean | Pred_NeuralNet | 2 | 28 | 16 | 12 | -0.007 |
| Pred_GroupMean | Pred_NeuralNet | 3 | 28 | 24 | 4 | 0.003 |
| Pred_GroupMean | Pred_NeuralNet | 4 | 28 | 12 | 16 | -0.002 |
| Pred_GroupMean | Pred_NeuralNet | 5 | 28 | 20 | 8 | -0.002 |
| Pred_GroupMean | Oracle | 1 | 28 | 24 | 0 | 0.005 |
| Pred_GroupMean | Oracle | 2 | 28 | 14 | 0 | 0.012 |
| Pred_GroupMean | Oracle | 3 | 28 | 22 | 0 | 0.024 |
| Pred_GroupMean | Oracle | 4 | 28 | 6 | 0 | 0.001 |
| Pred_GroupMean | Oracle | 5 | 28 | 19 | 0 | 0.005 |
| Pred_NeuralNet | Oracle | 1 | 28 | 22 | 0 | 0.003 |
| Pred_NeuralNet | Oracle | 2 | 28 | 16 | 0 | 0.019 |
| Pred_NeuralNet | Oracle | 3 | 28 | 20 | 0 | 0.020 |
| Pred_NeuralNet | Oracle | 4 | 28 | 14 | 0 | 0.003 |
| Pred_NeuralNet | Oracle | 5 | 28 | 23 | 0 | 0.008 |
