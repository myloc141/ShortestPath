# Routing experiment summary
- Simple routes from `O` to `T`: **28**; test days: **3**.
- Primary baseline: **GroupMean**; Neural Network: in the main comparison.
- Peak slot: **4**; off-peak slot: **1**.
- Simulated travel times are not real-world traffic measurements.

## Prediction alignment
- GroupMean: 180 predictions aligned with 180 test observations
- NeuralNet: 180 predictions aligned with 180 test observations

## Main-slot results
| slot | time_slot | method | mean_actual_time | mean_regret | days_equal_oracle | n_days |
| --- | --- | --- | --- | --- | --- | --- |
| peak | 4 | Fixed_distance | 33.963 | 7.497 | 0 | 3 |
| peak | 4 | Fixed_trainmean | 27.307 | 0.840 | 0 | 3 |
| peak | 4 | Oracle | 26.467 | 0.000 | 3 | 3 |
| peak | 4 | Pred_GroupMean | 27.110 | 0.643 | 0 | 3 |
| peak | 4 | Pred_NeuralNet | 27.110 | 0.643 | 0 | 3 |
| peak | 4 | RCSP_limit_18 | 31.640 | 5.173 | 0 | 3 |
| peak | 4 | RCSP_limit_19 | 31.607 | 5.140 | 0 | 3 |
| peak | 4 | RCSP_limit_20 | 33.963 | 7.497 | 0 | 3 |
| peak | 4 | RCSP_limit_unbounded | 33.963 | 7.497 | 0 | 3 |
| offpeak | 1 | Fixed_distance | 17.610 | 3.013 | 0 | 3 |
| offpeak | 1 | Fixed_trainmean | 15.727 | 1.130 | 1 | 3 |
| offpeak | 1 | Oracle | 14.597 | 0.000 | 3 | 3 |
| offpeak | 1 | Pred_GroupMean | 15.240 | 0.643 | 2 | 3 |
| offpeak | 1 | Pred_NeuralNet | 15.997 | 1.400 | 1 | 3 |
| offpeak | 1 | RCSP_limit_18 | 15.697 | 1.100 | 1 | 3 |
| offpeak | 1 | RCSP_limit_19 | 17.090 | 2.493 | 0 | 3 |
| offpeak | 1 | RCSP_limit_20 | 17.610 | 3.013 | 0 | 3 |
| offpeak | 1 | RCSP_limit_unbounded | 17.610 | 3.013 | 0 | 3 |

## Pairwise method comparison
| method_a | method_b | time_slot | n_days | days_route_differs | days_same_route_but_different_predicted_time | mean_actual_a_minus_b |
| --- | --- | --- | --- | --- | --- | --- |
| Fixed_distance | Fixed_trainmean | 1 | 3 | 3 | 0 | 1.883 |
| Fixed_distance | Fixed_trainmean | 2 | 3 | 3 | 0 | 11.763 |
| Fixed_distance | Fixed_trainmean | 3 | 3 | 3 | 0 | 2.123 |
| Fixed_distance | Fixed_trainmean | 4 | 3 | 3 | 0 | 6.657 |
| Fixed_distance | Fixed_trainmean | 5 | 3 | 3 | 0 | 4.127 |
| Fixed_distance | Pred_GroupMean | 1 | 3 | 3 | 0 | 2.370 |
| Fixed_distance | Pred_GroupMean | 2 | 3 | 3 | 0 | 11.030 |
| Fixed_distance | Pred_GroupMean | 3 | 3 | 3 | 0 | 2.657 |
| Fixed_distance | Pred_GroupMean | 4 | 3 | 3 | 0 | 6.853 |
| Fixed_distance | Pred_GroupMean | 5 | 3 | 3 | 0 | 4.613 |
| Fixed_distance | Pred_NeuralNet | 1 | 3 | 3 | 0 | 1.613 |
| Fixed_distance | Pred_NeuralNet | 2 | 3 | 3 | 0 | 11.953 |
| Fixed_distance | Pred_NeuralNet | 3 | 3 | 3 | 0 | 2.610 |
| Fixed_distance | Pred_NeuralNet | 4 | 3 | 3 | 0 | 6.853 |
| Fixed_distance | Pred_NeuralNet | 5 | 3 | 3 | 0 | 4.170 |
| Fixed_distance | Oracle | 1 | 3 | 3 | 0 | 3.013 |
| Fixed_distance | Oracle | 2 | 3 | 3 | 0 | 11.953 |
| Fixed_distance | Oracle | 3 | 3 | 3 | 0 | 3.167 |
| Fixed_distance | Oracle | 4 | 3 | 3 | 0 | 7.497 |
| Fixed_distance | Oracle | 5 | 3 | 3 | 0 | 5.783 |
| Fixed_distance | RCSP_limit_18 | 1 | 3 | 3 | 0 | 1.913 |
| Fixed_distance | RCSP_limit_18 | 2 | 3 | 3 | 0 | 6.993 |
| Fixed_distance | RCSP_limit_18 | 3 | 3 | 3 | 0 | 2.827 |
| Fixed_distance | RCSP_limit_18 | 4 | 3 | 3 | 0 | 2.323 |
| Fixed_distance | RCSP_limit_18 | 5 | 3 | 3 | 0 | 3.760 |
| Fixed_distance | RCSP_limit_19 | 1 | 3 | 3 | 0 | 0.520 |
| Fixed_distance | RCSP_limit_19 | 2 | 3 | 3 | 0 | 4.830 |
| Fixed_distance | RCSP_limit_19 | 3 | 3 | 3 | 0 | 0.927 |
| Fixed_distance | RCSP_limit_19 | 4 | 3 | 3 | 0 | 2.357 |
| Fixed_distance | RCSP_limit_19 | 5 | 3 | 3 | 0 | 2.880 |
| Fixed_distance | RCSP_limit_20 | 1 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_20 | 2 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_20 | 3 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_20 | 4 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_20 | 5 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_unbounded | 1 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_unbounded | 2 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_unbounded | 3 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_unbounded | 4 | 3 | 0 | 0 | 0.000 |
| Fixed_distance | RCSP_limit_unbounded | 5 | 3 | 0 | 0 | 0.000 |
| Fixed_trainmean | Pred_GroupMean | 1 | 3 | 3 | 0 | 0.487 |
| Fixed_trainmean | Pred_GroupMean | 2 | 3 | 2 | 1 | -0.733 |
| Fixed_trainmean | Pred_GroupMean | 3 | 3 | 3 | 0 | 0.533 |
| Fixed_trainmean | Pred_GroupMean | 4 | 3 | 1 | 2 | 0.197 |
| Fixed_trainmean | Pred_GroupMean | 5 | 3 | 2 | 1 | 0.487 |
| Fixed_trainmean | Pred_NeuralNet | 1 | 3 | 3 | 0 | -0.270 |
| Fixed_trainmean | Pred_NeuralNet | 2 | 3 | 1 | 2 | 0.190 |
| Fixed_trainmean | Pred_NeuralNet | 3 | 3 | 3 | 0 | 0.487 |
| Fixed_trainmean | Pred_NeuralNet | 4 | 3 | 1 | 2 | 0.197 |
| Fixed_trainmean | Pred_NeuralNet | 5 | 3 | 3 | 0 | 0.043 |
| Fixed_trainmean | Oracle | 1 | 3 | 2 | 0 | 1.130 |
| Fixed_trainmean | Oracle | 2 | 3 | 1 | 0 | 0.190 |
| Fixed_trainmean | Oracle | 3 | 3 | 2 | 0 | 1.043 |
| Fixed_trainmean | Oracle | 4 | 3 | 3 | 0 | 0.840 |
| Fixed_trainmean | Oracle | 5 | 3 | 2 | 0 | 1.657 |
| Fixed_trainmean | RCSP_limit_18 | 1 | 3 | 3 | 0 | 0.030 |
| Fixed_trainmean | RCSP_limit_18 | 2 | 3 | 3 | 0 | -4.770 |
| Fixed_trainmean | RCSP_limit_18 | 3 | 3 | 3 | 0 | 0.703 |
| Fixed_trainmean | RCSP_limit_18 | 4 | 3 | 3 | 0 | -4.333 |
| Fixed_trainmean | RCSP_limit_18 | 5 | 3 | 3 | 0 | -0.367 |
| Fixed_trainmean | RCSP_limit_19 | 1 | 3 | 3 | 0 | -1.363 |
| Fixed_trainmean | RCSP_limit_19 | 2 | 3 | 3 | 0 | -6.933 |
| Fixed_trainmean | RCSP_limit_19 | 3 | 3 | 3 | 0 | -1.197 |
| Fixed_trainmean | RCSP_limit_19 | 4 | 3 | 3 | 0 | -4.300 |
| Fixed_trainmean | RCSP_limit_19 | 5 | 3 | 3 | 0 | -1.247 |
| Fixed_trainmean | RCSP_limit_20 | 1 | 3 | 3 | 0 | -1.883 |
| Fixed_trainmean | RCSP_limit_20 | 2 | 3 | 3 | 0 | -11.763 |
| Fixed_trainmean | RCSP_limit_20 | 3 | 3 | 3 | 0 | -2.123 |
| Fixed_trainmean | RCSP_limit_20 | 4 | 3 | 3 | 0 | -6.657 |
| Fixed_trainmean | RCSP_limit_20 | 5 | 3 | 3 | 0 | -4.127 |
| Fixed_trainmean | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -1.883 |
| Fixed_trainmean | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -11.763 |
| Fixed_trainmean | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -2.123 |
| Fixed_trainmean | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -6.657 |
| Fixed_trainmean | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -4.127 |
| Pred_GroupMean | Pred_NeuralNet | 1 | 3 | 2 | 1 | -0.757 |
| Pred_GroupMean | Pred_NeuralNet | 2 | 3 | 1 | 2 | 0.923 |
| Pred_GroupMean | Pred_NeuralNet | 3 | 3 | 2 | 1 | -0.047 |
| Pred_GroupMean | Pred_NeuralNet | 4 | 3 | 0 | 3 | 0.000 |
| Pred_GroupMean | Pred_NeuralNet | 5 | 3 | 2 | 1 | -0.443 |
| Pred_GroupMean | Oracle | 1 | 3 | 1 | 0 | 0.643 |
| Pred_GroupMean | Oracle | 2 | 3 | 1 | 0 | 0.923 |
| Pred_GroupMean | Oracle | 3 | 3 | 2 | 0 | 0.510 |
| Pred_GroupMean | Oracle | 4 | 3 | 3 | 0 | 0.643 |
| Pred_GroupMean | Oracle | 5 | 3 | 2 | 0 | 1.170 |
| Pred_GroupMean | RCSP_limit_18 | 1 | 3 | 2 | 0 | -0.457 |
| Pred_GroupMean | RCSP_limit_18 | 2 | 3 | 3 | 0 | -4.037 |
| Pred_GroupMean | RCSP_limit_18 | 3 | 3 | 1 | 0 | 0.170 |
| Pred_GroupMean | RCSP_limit_18 | 4 | 3 | 3 | 0 | -4.530 |
| Pred_GroupMean | RCSP_limit_18 | 5 | 3 | 2 | 0 | -0.853 |
| Pred_GroupMean | RCSP_limit_19 | 1 | 3 | 3 | 0 | -1.850 |
| Pred_GroupMean | RCSP_limit_19 | 2 | 3 | 3 | 0 | -6.200 |
| Pred_GroupMean | RCSP_limit_19 | 3 | 3 | 3 | 0 | -1.730 |
| Pred_GroupMean | RCSP_limit_19 | 4 | 3 | 3 | 0 | -4.497 |
| Pred_GroupMean | RCSP_limit_19 | 5 | 3 | 3 | 0 | -1.733 |
| Pred_GroupMean | RCSP_limit_20 | 1 | 3 | 3 | 0 | -2.370 |
| Pred_GroupMean | RCSP_limit_20 | 2 | 3 | 3 | 0 | -11.030 |
| Pred_GroupMean | RCSP_limit_20 | 3 | 3 | 3 | 0 | -2.657 |
| Pred_GroupMean | RCSP_limit_20 | 4 | 3 | 3 | 0 | -6.853 |
| Pred_GroupMean | RCSP_limit_20 | 5 | 3 | 3 | 0 | -4.613 |
| Pred_GroupMean | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -2.370 |
| Pred_GroupMean | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -11.030 |
| Pred_GroupMean | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -2.657 |
| Pred_GroupMean | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -6.853 |
| Pred_GroupMean | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -4.613 |
| Pred_NeuralNet | Oracle | 1 | 3 | 2 | 0 | 1.400 |
| Pred_NeuralNet | Oracle | 2 | 3 | 0 | 0 | 0.000 |
| Pred_NeuralNet | Oracle | 3 | 3 | 1 | 0 | 0.557 |
| Pred_NeuralNet | Oracle | 4 | 3 | 3 | 0 | 0.643 |
| Pred_NeuralNet | Oracle | 5 | 3 | 3 | 0 | 1.613 |
| Pred_NeuralNet | RCSP_limit_18 | 1 | 3 | 3 | 0 | 0.300 |
| Pred_NeuralNet | RCSP_limit_18 | 2 | 3 | 3 | 0 | -4.960 |
| Pred_NeuralNet | RCSP_limit_18 | 3 | 3 | 2 | 0 | 0.217 |
| Pred_NeuralNet | RCSP_limit_18 | 4 | 3 | 3 | 0 | -4.530 |
| Pred_NeuralNet | RCSP_limit_18 | 5 | 3 | 2 | 0 | -0.410 |
| Pred_NeuralNet | RCSP_limit_19 | 1 | 3 | 3 | 0 | -1.093 |
| Pred_NeuralNet | RCSP_limit_19 | 2 | 3 | 3 | 0 | -7.123 |
| Pred_NeuralNet | RCSP_limit_19 | 3 | 3 | 3 | 0 | -1.683 |
| Pred_NeuralNet | RCSP_limit_19 | 4 | 3 | 3 | 0 | -4.497 |
| Pred_NeuralNet | RCSP_limit_19 | 5 | 3 | 3 | 0 | -1.290 |
| Pred_NeuralNet | RCSP_limit_20 | 1 | 3 | 3 | 0 | -1.613 |
| Pred_NeuralNet | RCSP_limit_20 | 2 | 3 | 3 | 0 | -11.953 |
| Pred_NeuralNet | RCSP_limit_20 | 3 | 3 | 3 | 0 | -2.610 |
| Pred_NeuralNet | RCSP_limit_20 | 4 | 3 | 3 | 0 | -6.853 |
| Pred_NeuralNet | RCSP_limit_20 | 5 | 3 | 3 | 0 | -4.170 |
| Pred_NeuralNet | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -1.613 |
| Pred_NeuralNet | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -11.953 |
| Pred_NeuralNet | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -2.610 |
| Pred_NeuralNet | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -6.853 |
| Pred_NeuralNet | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -4.170 |
| Oracle | RCSP_limit_18 | 1 | 3 | 2 | 0 | -1.100 |
| Oracle | RCSP_limit_18 | 2 | 3 | 3 | 0 | -4.960 |
| Oracle | RCSP_limit_18 | 3 | 3 | 2 | 0 | -0.340 |
| Oracle | RCSP_limit_18 | 4 | 3 | 3 | 0 | -5.173 |
| Oracle | RCSP_limit_18 | 5 | 3 | 3 | 0 | -2.023 |
| Oracle | RCSP_limit_19 | 1 | 3 | 3 | 0 | -2.493 |
| Oracle | RCSP_limit_19 | 2 | 3 | 3 | 0 | -7.123 |
| Oracle | RCSP_limit_19 | 3 | 3 | 3 | 0 | -2.240 |
| Oracle | RCSP_limit_19 | 4 | 3 | 3 | 0 | -5.140 |
| Oracle | RCSP_limit_19 | 5 | 3 | 3 | 0 | -2.903 |
| Oracle | RCSP_limit_20 | 1 | 3 | 3 | 0 | -3.013 |
| Oracle | RCSP_limit_20 | 2 | 3 | 3 | 0 | -11.953 |
| Oracle | RCSP_limit_20 | 3 | 3 | 3 | 0 | -3.167 |
| Oracle | RCSP_limit_20 | 4 | 3 | 3 | 0 | -7.497 |
| Oracle | RCSP_limit_20 | 5 | 3 | 3 | 0 | -5.783 |
| Oracle | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -3.013 |
| Oracle | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -11.953 |
| Oracle | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -3.167 |
| Oracle | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -7.497 |
| Oracle | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -5.783 |
| RCSP_limit_18 | RCSP_limit_19 | 1 | 3 | 3 | 0 | -1.393 |
| RCSP_limit_18 | RCSP_limit_19 | 2 | 3 | 3 | 0 | -2.163 |
| RCSP_limit_18 | RCSP_limit_19 | 3 | 3 | 3 | 0 | -1.900 |
| RCSP_limit_18 | RCSP_limit_19 | 4 | 3 | 3 | 0 | 0.033 |
| RCSP_limit_18 | RCSP_limit_19 | 5 | 3 | 3 | 0 | -0.880 |
| RCSP_limit_18 | RCSP_limit_20 | 1 | 3 | 3 | 0 | -1.913 |
| RCSP_limit_18 | RCSP_limit_20 | 2 | 3 | 3 | 0 | -6.993 |
| RCSP_limit_18 | RCSP_limit_20 | 3 | 3 | 3 | 0 | -2.827 |
| RCSP_limit_18 | RCSP_limit_20 | 4 | 3 | 3 | 0 | -2.323 |
| RCSP_limit_18 | RCSP_limit_20 | 5 | 3 | 3 | 0 | -3.760 |
| RCSP_limit_18 | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -1.913 |
| RCSP_limit_18 | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -6.993 |
| RCSP_limit_18 | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -2.827 |
| RCSP_limit_18 | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -2.323 |
| RCSP_limit_18 | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -3.760 |
| RCSP_limit_19 | RCSP_limit_20 | 1 | 3 | 3 | 0 | -0.520 |
| RCSP_limit_19 | RCSP_limit_20 | 2 | 3 | 3 | 0 | -4.830 |
| RCSP_limit_19 | RCSP_limit_20 | 3 | 3 | 3 | 0 | -0.927 |
| RCSP_limit_19 | RCSP_limit_20 | 4 | 3 | 3 | 0 | -2.357 |
| RCSP_limit_19 | RCSP_limit_20 | 5 | 3 | 3 | 0 | -2.880 |
| RCSP_limit_19 | RCSP_limit_unbounded | 1 | 3 | 3 | 0 | -0.520 |
| RCSP_limit_19 | RCSP_limit_unbounded | 2 | 3 | 3 | 0 | -4.830 |
| RCSP_limit_19 | RCSP_limit_unbounded | 3 | 3 | 3 | 0 | -0.927 |
| RCSP_limit_19 | RCSP_limit_unbounded | 4 | 3 | 3 | 0 | -2.357 |
| RCSP_limit_19 | RCSP_limit_unbounded | 5 | 3 | 3 | 0 | -2.880 |
| RCSP_limit_20 | RCSP_limit_unbounded | 1 | 3 | 0 | 0 | 0.000 |
| RCSP_limit_20 | RCSP_limit_unbounded | 2 | 3 | 0 | 0 | 0.000 |
| RCSP_limit_20 | RCSP_limit_unbounded | 3 | 3 | 0 | 0 | 0.000 |
| RCSP_limit_20 | RCSP_limit_unbounded | 4 | 3 | 0 | 0 | 0.000 |
| RCSP_limit_20 | RCSP_limit_unbounded | 5 | 3 | 0 | 0 | 0.000 |

## RCSP vs unconstrained shortest path
| method | route | distance_km | resource_limit |
| --- | --- | --- | --- |
| RCSP_limit_unbounded | O-A-B-D-T | 13.000 |  |
| Unconstrained shortest path | O-A-B-D-T | 13.000 |  |

## RCSP route scores on actual test travel time
| method | time_slot | day | route | actual_time | oracle_time | regret | method_family |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RCSP_limit_18 | 1 | 28 | O-A-D-T | 17.370 | 14.390 | 2.980 | rcsp |
| RCSP_limit_19 | 1 | 28 | O-A-B-E-D-T | 17.050 | 14.390 | 2.660 | rcsp |
| RCSP_limit_20 | 1 | 28 | O-A-B-D-T | 16.850 | 14.390 | 2.460 | rcsp |
| RCSP_limit_unbounded | 1 | 28 | O-A-B-D-T | 16.850 | 14.390 | 2.460 | rcsp |
| RCSP_limit_18 | 1 | 29 | O-A-D-T | 15.820 | 15.500 | 0.320 | rcsp |
| RCSP_limit_19 | 1 | 29 | O-A-B-E-D-T | 17.810 | 15.500 | 2.310 | rcsp |
| RCSP_limit_20 | 1 | 29 | O-A-B-D-T | 18.340 | 15.500 | 2.840 | rcsp |
| RCSP_limit_unbounded | 1 | 29 | O-A-B-D-T | 18.340 | 15.500 | 2.840 | rcsp |
| RCSP_limit_18 | 1 | 30 | O-A-D-T | 13.900 | 13.900 | 0.000 | rcsp |
| RCSP_limit_19 | 1 | 30 | O-A-B-E-D-T | 16.410 | 13.900 | 2.510 | rcsp |
| RCSP_limit_20 | 1 | 30 | O-A-B-D-T | 17.640 | 13.900 | 3.740 | rcsp |
| RCSP_limit_unbounded | 1 | 30 | O-A-B-D-T | 17.640 | 13.900 | 3.740 | rcsp |
| RCSP_limit_18 | 2 | 28 | O-A-D-T | 21.220 | 21.000 | 0.220 | rcsp |
| RCSP_limit_19 | 2 | 28 | O-A-B-E-D-T | 22.590 | 21.000 | 1.590 | rcsp |
| RCSP_limit_20 | 2 | 28 | O-A-B-D-T | 27.160 | 21.000 | 6.160 | rcsp |
| RCSP_limit_unbounded | 2 | 28 | O-A-B-D-T | 27.160 | 21.000 | 6.160 | rcsp |
| RCSP_limit_18 | 2 | 29 | O-A-D-T | 32.650 | 26.580 | 6.070 | rcsp |
| RCSP_limit_19 | 2 | 29 | O-A-B-E-D-T | 35.660 | 26.580 | 9.080 | rcsp |
| RCSP_limit_20 | 2 | 29 | O-A-B-D-T | 40.140 | 26.580 | 13.560 | rcsp |
| RCSP_limit_unbounded | 2 | 29 | O-A-B-D-T | 40.140 | 26.580 | 13.560 | rcsp |
| RCSP_limit_18 | 2 | 30 | O-A-D-T | 31.930 | 23.340 | 8.590 | rcsp |
| RCSP_limit_19 | 2 | 30 | O-A-B-E-D-T | 34.040 | 23.340 | 10.700 | rcsp |
| RCSP_limit_20 | 2 | 30 | O-A-B-D-T | 39.480 | 23.340 | 16.140 | rcsp |
| RCSP_limit_unbounded | 2 | 30 | O-A-B-D-T | 39.480 | 23.340 | 16.140 | rcsp |
| RCSP_limit_18 | 3 | 28 | O-A-D-T | 24.690 | 24.690 | -0.000 | rcsp |
| RCSP_limit_19 | 3 | 28 | O-A-B-E-D-T | 26.180 | 24.690 | 1.490 | rcsp |
| RCSP_limit_20 | 3 | 28 | O-A-B-D-T | 26.850 | 24.690 | 2.160 | rcsp |
| RCSP_limit_unbounded | 3 | 28 | O-A-B-D-T | 26.850 | 24.690 | 2.160 | rcsp |
| RCSP_limit_18 | 3 | 29 | O-A-D-T | 19.470 | 18.830 | 0.640 | rcsp |
| RCSP_limit_19 | 3 | 29 | O-A-B-E-D-T | 21.740 | 18.830 | 2.910 | rcsp |
| RCSP_limit_20 | 3 | 29 | O-A-B-D-T | 23.750 | 18.830 | 4.920 | rcsp |
| RCSP_limit_unbounded | 3 | 29 | O-A-B-D-T | 23.750 | 18.830 | 4.920 | rcsp |
| RCSP_limit_18 | 3 | 30 | O-A-D-T | 19.240 | 18.860 | 0.380 | rcsp |
| RCSP_limit_19 | 3 | 30 | O-A-B-E-D-T | 21.180 | 18.860 | 2.320 | rcsp |
| RCSP_limit_20 | 3 | 30 | O-A-B-D-T | 21.280 | 18.860 | 2.420 | rcsp |
| RCSP_limit_unbounded | 3 | 30 | O-A-B-D-T | 21.280 | 18.860 | 2.420 | rcsp |
| RCSP_limit_18 | 4 | 28 | O-A-D-T | 25.810 | 22.060 | 3.750 | rcsp |
| RCSP_limit_19 | 4 | 28 | O-A-B-E-D-T | 24.800 | 22.060 | 2.740 | rcsp |
| RCSP_limit_20 | 4 | 28 | O-A-B-D-T | 25.120 | 22.060 | 3.060 | rcsp |
| RCSP_limit_unbounded | 4 | 28 | O-A-B-D-T | 25.120 | 22.060 | 3.060 | rcsp |
| RCSP_limit_18 | 4 | 29 | O-A-D-T | 36.600 | 29.960 | 6.640 | rcsp |
| RCSP_limit_19 | 4 | 29 | O-A-B-E-D-T | 35.810 | 29.960 | 5.850 | rcsp |
| RCSP_limit_20 | 4 | 29 | O-A-B-D-T | 40.570 | 29.960 | 10.610 | rcsp |
| RCSP_limit_unbounded | 4 | 29 | O-A-B-D-T | 40.570 | 29.960 | 10.610 | rcsp |
| RCSP_limit_18 | 4 | 30 | O-A-D-T | 32.510 | 27.380 | 5.130 | rcsp |
| RCSP_limit_19 | 4 | 30 | O-A-B-E-D-T | 34.210 | 27.380 | 6.830 | rcsp |
| RCSP_limit_20 | 4 | 30 | O-A-B-D-T | 36.200 | 27.380 | 8.820 | rcsp |
| RCSP_limit_unbounded | 4 | 30 | O-A-B-D-T | 36.200 | 27.380 | 8.820 | rcsp |
| RCSP_limit_18 | 5 | 28 | O-A-D-T | 30.490 | 27.710 | 2.780 | rcsp |
| RCSP_limit_19 | 5 | 28 | O-A-B-E-D-T | 32.480 | 27.710 | 4.770 | rcsp |
| RCSP_limit_20 | 5 | 28 | O-A-B-D-T | 36.550 | 27.710 | 8.840 | rcsp |
| RCSP_limit_unbounded | 5 | 28 | O-A-B-D-T | 36.550 | 27.710 | 8.840 | rcsp |
| RCSP_limit_18 | 5 | 29 | O-A-D-T | 19.830 | 18.650 | 1.180 | rcsp |
| RCSP_limit_19 | 5 | 29 | O-A-B-E-D-T | 19.780 | 18.650 | 1.130 | rcsp |
| RCSP_limit_20 | 5 | 29 | O-A-B-D-T | 22.560 | 18.650 | 3.910 | rcsp |
| RCSP_limit_unbounded | 5 | 29 | O-A-B-D-T | 22.560 | 18.650 | 3.910 | rcsp |
| RCSP_limit_18 | 5 | 30 | O-A-D-T | 19.770 | 17.660 | 2.110 | rcsp |
| RCSP_limit_19 | 5 | 30 | O-A-B-E-D-T | 20.470 | 17.660 | 2.810 | rcsp |
| RCSP_limit_20 | 5 | 30 | O-A-B-D-T | 22.260 | 17.660 | 4.600 | rcsp |
| RCSP_limit_unbounded | 5 | 30 | O-A-B-D-T | 22.260 | 17.660 | 4.600 | rcsp |

## RCSP sensitivity by resource limit
| resource_limit | status | optimal_path | total_distance | total_resource | route_changed_vs_previous |
| --- | --- | --- | --- | --- | --- |
| 17.000 | Infeasible |  |  |  | False |
| 18.000 | Optimal | O-A-D-T | 14.000 | 18.000 | True |
| 19.000 | Optimal | O-A-B-E-D-T | 13.000 | 19.000 | True |
| 20.000 | Optimal | O-A-B-D-T | 13.000 | 20.000 | True |
|  | Optimal | O-A-B-D-T | 13.000 | 20.000 | False |
