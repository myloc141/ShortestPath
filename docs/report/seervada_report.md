# Pipeline report — seervada

## I2 — Simple paths và shortest path

### Simple paths
| rank | source | target | path | total_distance | num_nodes | num_edges | algorithm | is_optimal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | O | T | O-A-B-D-T | 13.0 | 5 | 4 | brute_force | True |
| 2 | O | T | O-A-B-E-D-T | 13.0 | 6 | 5 | brute_force | True |
| 3 | O | T | O-A-B-E-T | 14.0 | 5 | 4 | brute_force | False |
| 4 | O | T | O-A-D-T | 14.0 | 4 | 3 | brute_force | False |
| 5 | O | T | O-B-D-T | 14.0 | 4 | 3 | brute_force | False |
| 6 | O | T | O-B-E-D-T | 14.0 | 5 | 4 | brute_force | False |
| 7 | O | T | O-C-B-D-T | 14.0 | 5 | 4 | brute_force | False |
| 8 | O | T | O-C-B-E-D-T | 14.0 | 6 | 5 | brute_force | False |
| 9 | O | T | O-C-E-D-T | 14.0 | 5 | 4 | brute_force | False |
| 10 | O | T | O-A-B-C-E-D-T | 15.0 | 7 | 6 | brute_force | False |
| 11 | O | T | O-B-E-T | 15.0 | 4 | 3 | brute_force | False |
| 12 | O | T | O-C-B-E-T | 15.0 | 5 | 4 | brute_force | False |
| 13 | O | T | O-C-E-T | 15.0 | 4 | 3 | brute_force | False |
| 14 | O | T | O-A-B-C-E-T | 16.0 | 6 | 5 | brute_force | False |
| 15 | O | T | O-A-B-D-E-T | 16.0 | 6 | 5 | brute_force | False |
| 16 | O | T | O-B-C-E-D-T | 16.0 | 6 | 5 | brute_force | False |
| 17 | O | T | O-A-D-E-T | 17.0 | 5 | 4 | brute_force | False |
| 18 | O | T | O-B-C-E-T | 17.0 | 5 | 4 | brute_force | False |
| 19 | O | T | O-B-D-E-T | 17.0 | 5 | 4 | brute_force | False |
| 20 | O | T | O-C-B-D-E-T | 17.0 | 6 | 5 | brute_force | False |
| 21 | O | T | O-B-A-D-T | 19.0 | 5 | 4 | brute_force | False |
| 22 | O | T | O-C-B-A-D-T | 19.0 | 6 | 5 | brute_force | False |
| 23 | O | T | O-C-E-B-D-T | 20.0 | 6 | 5 | brute_force | False |
| 24 | O | T | O-B-A-D-E-T | 22.0 | 6 | 5 | brute_force | False |
| 25 | O | T | O-C-B-A-D-E-T | 22.0 | 7 | 6 | brute_force | False |
| 26 | O | T | O-A-D-B-E-T | 23.0 | 6 | 5 | brute_force | False |
| 27 | O | T | O-A-D-B-C-E-T | 25.0 | 7 | 6 | brute_force | False |
| 28 | O | T | O-C-E-B-A-D-T | 25.0 | 7 | 6 | brute_force | False |

### Shortest-path summary
| source | target | path | total_distance | paths_checked | verified |
| --- | --- | --- | --- | --- | --- |
| O | T | O-A-B-D-T | 13.0 | 28 | True |

## I3 — RCSP và sensitivity

### RCSP results
| resource_limit | milp_status | milp_path | milp_distance | milp_resource | brute_force_status | brute_force_distance | n_paths_total | n_paths_feasible | solution_valid | cross_check_matches |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 17 | Infeasible |  |  |  | Infeasible |  | 28 | 0 |  | True |
| 18 | Optimal | O-B-E-D-T | 14.0 | 18.0 | Optimal | 14.0 | 28 | 5 | True | True |
| 19 | Optimal | O-A-B-E-D-T | 13.0 | 19.0 | Optimal | 13.0 | 28 | 10 | True | True |
| 20 | Optimal | O-A-B-D-T | 13.0 | 20.0 | Optimal | 13.0 | 28 | 12 | True | True |
|  | Optimal | O-A-B-D-T | 13.0 | 20.0 | Optimal | 13.0 | 28 | 28 | True | True |

### Sensitivity by resource limit
| resource_limit | status | optimal_path | total_distance | total_resource | route_changed_vs_previous |
| --- | --- | --- | --- | --- | --- |
| 17 | Infeasible |  |  |  | False |
| 18 | Optimal | O-A-D-T | 14.0 | 18.0 | True |
| 19 | Optimal | O-A-B-E-D-T | 13.0 | 19.0 | True |
| 20 | Optimal | O-A-B-D-T | 13.0 | 20.0 | True |
|  | Optimal | O-A-B-D-T | 13.0 | 20.0 | False |

## I6 — Evaluation metrics

| time_slot | model | MAE | RMSE | MSE | MAPE_percent | n_obs |
| --- | --- | --- | --- | --- | --- | --- |
| all | GroupMean | 0.6231 | 0.8871 | 0.7869 | 9.56 | 180 |
| 1 | GroupMean | 0.4341 | 0.5939 | 0.3527 | 9.45 | 36 |
| 2 | GroupMean | 0.9348 | 1.2452 | 1.5506 | 12.02 | 36 |
| 3 | GroupMean | 0.481 | 0.6324 | 0.3999 | 9.06 | 36 |
| 4 | GroupMean | 0.7469 | 1.0568 | 1.1167 | 8.95 | 36 |
| 5 | GroupMean | 0.5187 | 0.7173 | 0.5145 | 8.34 | 36 |
| all | LinearRegression | 1.1851 | 1.5036 | 2.2609 | 21.13 | 180 |
| 1 | LinearRegression | 0.9334 | 1.1737 | 1.3777 | 27.24 | 36 |
| 2 | LinearRegression | 1.3413 | 1.6217 | 2.6298 | 19.86 | 36 |
| 3 | LinearRegression | 1.0519 | 1.2771 | 1.631 | 17.59 | 36 |
| 4 | LinearRegression | 1.2664 | 1.6823 | 2.8302 | 21.07 | 36 |
| 5 | LinearRegression | 1.3325 | 1.6841 | 2.8361 | 19.92 | 36 |
| all | Neural_Network_MLP | 0.6007 | 0.8465 | 0.7166 | 9.53 | 180 |
| 1 | Neural_Network_MLP | 0.4386 | 0.6236 | 0.3889 | 9.54 | 36 |
| 2 | Neural_Network_MLP | 0.8108 | 1.0973 | 1.204 | 10.79 | 36 |
| 3 | Neural_Network_MLP | 0.5002 | 0.6633 | 0.44 | 9.46 | 36 |
| 4 | Neural_Network_MLP | 0.7051 | 0.9716 | 0.9441 | 8.83 | 36 |
| 5 | Neural_Network_MLP | 0.549 | 0.7784 | 0.6059 | 9.05 | 36 |

## I8 — Routing results

| time_slot | slot_name | day | day_of_week | method | route | distance_km | objective | predicted_time | actual_time | oracle_route | oracle_time | regret | matches_oracle | n_ties | selection_warning | method_family |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 06:00-08:00 | 28 | Sun | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 16.85 | O-B-E-T | 14.39 | 2.460000000000001 | False | 2 |  | fixed |
| 1 | 06:00-08:00 | 28 | Sun | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 14.39 | O-B-E-T | 14.39 | 0.0 | True | 1 |  | fixed |
| 1 | 06:00-08:00 | 28 | Sun | Pred_GroupMean | O-C-E-D-T | 14.0 | 14.99 | 14.99 | 16.32 | O-B-E-T | 14.39 | 1.9299999999999997 | False | 1 |  | predicted |
| 1 | 06:00-08:00 | 28 | Sun | Pred_NeuralNet | O-B-E-D-T | 14.0 | 14.579406165 | 14.579406165 | 15.54 | O-B-E-T | 14.39 | 1.1499999999999986 | False | 1 |  | predicted |
| 1 | 06:00-08:00 | 28 | Sun | Oracle | O-B-E-T | 15.0 | 14.39 |  | 14.39 | O-B-E-T | 14.39 | 0.0 | True | 1 |  | oracle |
| 1 | 06:00-08:00 | 28 | Sun | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 17.37 | O-B-E-T | 14.39 | 2.9800000000000004 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 28 | Sun | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 17.05 | O-B-E-T | 14.39 | 2.66 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 28 | Sun | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 16.85 | O-B-E-T | 14.39 | 2.460000000000001 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 28 | Sun | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 16.85 | O-B-E-T | 14.39 | 2.460000000000001 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 29 | Mon | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 18.34 | O-C-E-T | 15.5 | 2.84 | False | 2 |  | fixed |
| 1 | 06:00-08:00 | 29 | Mon | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 15.870000000000001 | O-C-E-T | 15.5 | 0.370000000000001 | False | 1 |  | fixed |
| 1 | 06:00-08:00 | 29 | Mon | Pred_GroupMean | O-C-E-T | 15.0 | 15.6375 | 15.6375 | 15.5 | O-C-E-T | 15.5 | 0.0 | True | 1 |  | predicted |
| 1 | 06:00-08:00 | 29 | Mon | Pred_NeuralNet | O-C-E-T | 15.0 | 16.437128305 | 16.437128305 | 15.5 | O-C-E-T | 15.5 | 0.0 | True | 1 |  | predicted |
| 1 | 06:00-08:00 | 29 | Mon | Oracle | O-C-E-T | 15.0 | 15.5 |  | 15.5 | O-C-E-T | 15.5 | 0.0 | True | 1 |  | oracle |
| 1 | 06:00-08:00 | 29 | Mon | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 15.82 | O-C-E-T | 15.5 | 0.3200000000000003 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 29 | Mon | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 17.81 | O-C-E-T | 15.5 | 2.3099999999999987 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 29 | Mon | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 18.34 | O-C-E-T | 15.5 | 2.84 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 29 | Mon | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 18.34 | O-C-E-T | 15.5 | 2.84 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 30 | Tue | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 17.64 | O-A-D-T | 13.9 | 3.74 | False | 2 |  | fixed |
| 1 | 06:00-08:00 | 30 | Tue | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 16.919999999999998 | O-A-D-T | 13.9 | 3.019999999999998 | False | 1 |  | fixed |
| 1 | 06:00-08:00 | 30 | Tue | Pred_GroupMean | O-A-D-T | 14.0 | 16.55 | 16.55 | 13.9 | O-A-D-T | 13.9 | 0.0 | True | 1 |  | predicted |
| 1 | 06:00-08:00 | 30 | Tue | Pred_NeuralNet | O-C-E-T | 15.0 | 16.171128784 | 16.171128784 | 16.95 | O-A-D-T | 13.9 | 3.049999999999999 | False | 1 |  | predicted |
| 1 | 06:00-08:00 | 30 | Tue | Oracle | O-A-D-T | 14.0 | 13.9 |  | 13.9 | O-A-D-T | 13.9 | 0.0 | True | 1 |  | oracle |
| 1 | 06:00-08:00 | 30 | Tue | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 13.9 | O-A-D-T | 13.9 | 0.0 | True | 1 |  | rcsp |
| 1 | 06:00-08:00 | 30 | Tue | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 16.41 | O-A-D-T | 13.9 | 2.51 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 30 | Tue | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 17.64 | O-A-D-T | 13.9 | 3.74 | False | 1 |  | rcsp |
| 1 | 06:00-08:00 | 30 | Tue | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 17.64 | O-A-D-T | 13.9 | 3.74 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 28 | Sun | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 27.16 | O-C-E-T | 21.0 | 6.16 | False | 2 |  | fixed |
| 2 | 08:00-10:00 | 28 | Sun | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 21.57 | O-C-E-T | 21.0 | 0.5700000000000003 | False | 1 |  | fixed |
| 2 | 08:00-10:00 | 28 | Sun | Pred_GroupMean | O-C-E-T | 15.0 | 20.563333333 | 20.563333333 | 21.0 | O-C-E-T | 21.0 | 0.0 | True | 1 |  | predicted |
| 2 | 08:00-10:00 | 28 | Sun | Pred_NeuralNet | O-C-E-T | 15.0 | 21.177271237 | 21.177271237 | 21.0 | O-C-E-T | 21.0 | 0.0 | True | 1 |  | predicted |
| 2 | 08:00-10:00 | 28 | Sun | Oracle | O-C-E-T | 15.0 | 21.0 |  | 21.0 | O-C-E-T | 21.0 | 0.0 | True | 1 |  | oracle |
| 2 | 08:00-10:00 | 28 | Sun | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 21.22 | O-C-E-T | 21.0 | 0.21999999999999886 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 28 | Sun | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 22.590000000000003 | O-C-E-T | 21.0 | 1.5900000000000034 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 28 | Sun | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 27.16 | O-C-E-T | 21.0 | 6.16 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 28 | Sun | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 27.16 | O-C-E-T | 21.0 | 6.16 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 29 | Mon | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 40.14 | O-B-E-T | 26.58 | 13.560000000000002 | False | 2 |  | fixed |
| 2 | 08:00-10:00 | 29 | Mon | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 26.58 | O-B-E-T | 26.58 | 0.0 | True | 1 |  | fixed |
| 2 | 08:00-10:00 | 29 | Mon | Pred_GroupMean | O-B-E-T | 15.0 | 26.495 | 26.495 | 26.58 | O-B-E-T | 26.58 | 0.0 | True | 1 |  | predicted |
| 2 | 08:00-10:00 | 29 | Mon | Pred_NeuralNet | O-B-E-T | 15.0 | 26.2155969 | 26.2155969 | 26.58 | O-B-E-T | 26.58 | 0.0 | True | 1 |  | predicted |
| 2 | 08:00-10:00 | 29 | Mon | Oracle | O-B-E-T | 15.0 | 26.58 |  | 26.58 | O-B-E-T | 26.58 | 0.0 | True | 1 |  | oracle |
| 2 | 08:00-10:00 | 29 | Mon | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 32.65 | O-B-E-T | 26.58 | 6.07 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 29 | Mon | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 35.660000000000004 | O-B-E-T | 26.58 | 9.080000000000005 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 29 | Mon | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 40.14 | O-B-E-T | 26.58 | 13.560000000000002 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 29 | Mon | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 40.14 | O-B-E-T | 26.58 | 13.560000000000002 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 30 | Tue | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 39.48 | O-B-E-T | 23.34 | 16.139999999999997 | False | 2 |  | fixed |
| 2 | 08:00-10:00 | 30 | Tue | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 23.34 | O-B-E-T | 23.34 | 0.0 | True | 1 |  | fixed |
| 2 | 08:00-10:00 | 30 | Tue | Pred_GroupMean | O-C-E-T | 15.0 | 26.675 | 26.675 | 26.11 | O-B-E-T | 23.34 | 2.7699999999999996 | False | 1 |  | predicted |
| 2 | 08:00-10:00 | 30 | Tue | Pred_NeuralNet | O-B-E-T | 15.0 | 26.734410747 | 26.734410747 | 23.34 | O-B-E-T | 23.34 | 0.0 | True | 1 |  | predicted |
| 2 | 08:00-10:00 | 30 | Tue | Oracle | O-B-E-T | 15.0 | 23.34 |  | 23.34 | O-B-E-T | 23.34 | 0.0 | True | 1 |  | oracle |
| 2 | 08:00-10:00 | 30 | Tue | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 31.93 | O-B-E-T | 23.34 | 8.59 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 30 | Tue | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 34.04 | O-B-E-T | 23.34 | 10.7 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 30 | Tue | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 39.48 | O-B-E-T | 23.34 | 16.139999999999997 | False | 1 |  | rcsp |
| 2 | 08:00-10:00 | 30 | Tue | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 39.48 | O-B-E-T | 23.34 | 16.139999999999997 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 28 | Sun | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 26.849999999999994 | O-A-D-T | 24.69 | 2.159999999999993 | False | 2 |  | fixed |
| 3 | 11:30-13:30 | 28 | Sun | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 27.2 | O-A-D-T | 24.69 | 2.509999999999998 | False | 1 |  | fixed |
| 3 | 11:30-13:30 | 28 | Sun | Pred_GroupMean | O-A-D-T | 14.0 | 25.036666667 | 25.036666667 | 24.689999999999998 | O-A-D-T | 24.69 | -3.552713678800501e-15 | True | 1 |  | predicted |
| 3 | 11:30-13:30 | 28 | Sun | Pred_NeuralNet | O-A-D-T | 14.0 | 25.333098049 | 25.333098049 | 24.689999999999998 | O-A-D-T | 24.69 | -3.552713678800501e-15 | True | 1 |  | predicted |
| 3 | 11:30-13:30 | 28 | Sun | Oracle | O-A-D-T | 14.0 | 24.69 |  | 24.689999999999998 | O-A-D-T | 24.69 | -3.552713678800501e-15 | True | 1 |  | oracle |
| 3 | 11:30-13:30 | 28 | Sun | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 24.689999999999998 | O-A-D-T | 24.69 | -3.552713678800501e-15 | True | 1 |  | rcsp |
| 3 | 11:30-13:30 | 28 | Sun | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 26.18 | O-A-D-T | 24.69 | 1.4899999999999984 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 28 | Sun | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 26.849999999999994 | O-A-D-T | 24.69 | 2.159999999999993 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 28 | Sun | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 26.849999999999994 | O-A-D-T | 24.69 | 2.159999999999993 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 29 | Mon | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 23.75 | O-C-E-D-T | 18.83 | 4.920000000000002 | False | 2 |  | fixed |
| 3 | 11:30-13:30 | 29 | Mon | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 19.45 | O-C-E-D-T | 18.83 | 0.620000000000001 | False | 1 |  | fixed |
| 3 | 11:30-13:30 | 29 | Mon | Pred_GroupMean | O-A-D-T | 14.0 | 19.0925 | 19.0925 | 19.470000000000002 | O-C-E-D-T | 18.83 | 0.6400000000000041 | False | 1 |  | predicted |
| 3 | 11:30-13:30 | 29 | Mon | Pred_NeuralNet | O-C-E-D-T | 14.0 | 19.251676976 | 19.251676976 | 18.83 | O-C-E-D-T | 18.83 | 0.0 | True | 1 |  | predicted |
| 3 | 11:30-13:30 | 29 | Mon | Oracle | O-C-E-D-T | 14.0 | 18.83 |  | 18.83 | O-C-E-D-T | 18.83 | 0.0 | True | 1 |  | oracle |
| 3 | 11:30-13:30 | 29 | Mon | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 19.470000000000002 | O-C-E-D-T | 18.83 | 0.6400000000000041 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 29 | Mon | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 21.74 | O-C-E-D-T | 18.83 | 2.91 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 29 | Mon | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 23.75 | O-C-E-D-T | 18.83 | 4.920000000000002 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 29 | Mon | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 23.75 | O-C-E-D-T | 18.83 | 4.920000000000002 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 30 | Tue | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 21.28 | O-B-E-T | 18.86 | 2.4200000000000017 | False | 2 |  | fixed |
| 3 | 11:30-13:30 | 30 | Tue | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 18.86 | O-B-E-T | 18.86 | 0.0 | True | 1 |  | fixed |
| 3 | 11:30-13:30 | 30 | Tue | Pred_GroupMean | O-C-E-T | 15.0 | 18.2725 | 18.2725 | 19.75 | O-B-E-T | 18.86 | 0.8900000000000006 | False | 1 |  | predicted |
| 3 | 11:30-13:30 | 30 | Tue | Pred_NeuralNet | O-C-E-D-T | 14.0 | 18.95975282 | 18.95975282 | 20.529999999999998 | O-B-E-T | 18.86 | 1.6699999999999982 | False | 1 |  | predicted |
| 3 | 11:30-13:30 | 30 | Tue | Oracle | O-B-E-T | 15.0 | 18.86 |  | 18.86 | O-B-E-T | 18.86 | 0.0 | True | 1 |  | oracle |
| 3 | 11:30-13:30 | 30 | Tue | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 19.24 | O-B-E-T | 18.86 | 0.379999999999999 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 30 | Tue | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 21.18 | O-B-E-T | 18.86 | 2.3200000000000003 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 30 | Tue | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 21.28 | O-B-E-T | 18.86 | 2.4200000000000017 | False | 1 |  | rcsp |
| 3 | 11:30-13:30 | 30 | Tue | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 21.28 | O-B-E-T | 18.86 | 2.4200000000000017 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 28 | Sun | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 25.12 | O-C-B-E-T | 22.06 | 3.0600000000000023 | False | 2 |  | fixed |
| 4 | 16:30-18:30 | 28 | Sun | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 22.84 | O-C-B-E-T | 22.06 | 0.7800000000000011 | False | 1 |  | fixed |
| 4 | 16:30-18:30 | 28 | Sun | Pred_GroupMean | O-C-E-T | 15.0 | 21.706666667 | 21.706666667 | 22.25 | O-C-B-E-T | 22.06 | 0.19000000000000128 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 28 | Sun | Pred_NeuralNet | O-C-E-T | 15.0 | 22.291059723 | 22.291059723 | 22.25 | O-C-B-E-T | 22.06 | 0.19000000000000128 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 28 | Sun | Oracle | O-C-B-E-T | 15.0 | 22.06 |  | 22.060000000000002 | O-C-B-E-T | 22.06 | 3.552713678800501e-15 | True | 1 |  | oracle |
| 4 | 16:30-18:30 | 28 | Sun | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 25.810000000000002 | O-C-B-E-T | 22.06 | 3.7500000000000036 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 28 | Sun | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 24.8 | O-C-B-E-T | 22.06 | 2.740000000000002 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 28 | Sun | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 25.12 | O-C-B-E-T | 22.06 | 3.0600000000000023 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 28 | Sun | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 25.12 | O-C-B-E-T | 22.06 | 3.0600000000000023 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 29 | Mon | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 40.57 | O-C-E-T | 29.96 | 10.61 | False | 2 |  | fixed |
| 4 | 16:30-18:30 | 29 | Mon | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 30.810000000000002 | O-C-E-T | 29.96 | 0.8500000000000014 | False | 1 |  | fixed |
| 4 | 16:30-18:30 | 29 | Mon | Pred_GroupMean | O-B-E-T | 15.0 | 28.66 | 28.66 | 30.810000000000002 | O-C-E-T | 29.96 | 0.8500000000000014 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 29 | Mon | Pred_NeuralNet | O-B-E-T | 15.0 | 28.913796789 | 28.913796789 | 30.810000000000002 | O-C-E-T | 29.96 | 0.8500000000000014 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 29 | Mon | Oracle | O-C-E-T | 15.0 | 29.96 |  | 29.96 | O-C-E-T | 29.96 | 0.0 | True | 1 |  | oracle |
| 4 | 16:30-18:30 | 29 | Mon | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 36.6 | O-C-E-T | 29.96 | 6.640000000000001 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 29 | Mon | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 35.81 | O-C-E-T | 29.96 | 5.850000000000001 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 29 | Mon | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 40.57 | O-C-E-T | 29.96 | 10.61 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 29 | Mon | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 40.57 | O-C-E-T | 29.96 | 10.61 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 30 | Tue | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 36.2 | O-C-E-T | 27.38 | 8.820000000000004 | False | 2 |  | fixed |
| 4 | 16:30-18:30 | 30 | Tue | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 28.27 | O-C-E-T | 27.38 | 0.8900000000000006 | False | 1 |  | fixed |
| 4 | 16:30-18:30 | 30 | Tue | Pred_GroupMean | O-B-E-T | 15.0 | 28.1975 | 28.1975 | 28.27 | O-C-E-T | 27.38 | 0.8900000000000006 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 30 | Tue | Pred_NeuralNet | O-B-E-T | 15.0 | 27.841373332 | 27.841373332 | 28.27 | O-C-E-T | 27.38 | 0.8900000000000006 | False | 1 |  | predicted |
| 4 | 16:30-18:30 | 30 | Tue | Oracle | O-C-E-T | 15.0 | 27.38 |  | 27.38 | O-C-E-T | 27.38 | 0.0 | True | 1 |  | oracle |
| 4 | 16:30-18:30 | 30 | Tue | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 32.51 | O-C-E-T | 27.38 | 5.129999999999999 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 30 | Tue | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 34.21 | O-C-E-T | 27.38 | 6.830000000000002 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 30 | Tue | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 36.2 | O-C-E-T | 27.38 | 8.820000000000004 | False | 1 |  | rcsp |
| 4 | 16:30-18:30 | 30 | Tue | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 36.2 | O-C-E-T | 27.38 | 8.820000000000004 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 28 | Sun | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 36.55 | O-B-E-T | 27.71 | 8.839999999999996 | False | 2 |  | fixed |
| 5 | 19:30-21:30 | 28 | Sun | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 27.709999999999997 | O-B-E-T | 27.71 | -3.552713678800501e-15 | True | 1 |  | fixed |
| 5 | 19:30-21:30 | 28 | Sun | Pred_GroupMean | O-B-E-T | 15.0 | 27.02 | 27.02 | 27.709999999999997 | O-B-E-T | 27.71 | -3.552713678800501e-15 | True | 1 |  | predicted |
| 5 | 19:30-21:30 | 28 | Sun | Pred_NeuralNet | O-A-D-T | 14.0 | 27.680401391 | 27.680401391 | 30.490000000000002 | O-B-E-T | 27.71 | 2.780000000000001 | False | 1 |  | predicted |
| 5 | 19:30-21:30 | 28 | Sun | Oracle | O-B-E-T | 15.0 | 27.71 |  | 27.709999999999997 | O-B-E-T | 27.71 | -3.552713678800501e-15 | True | 1 |  | oracle |
| 5 | 19:30-21:30 | 28 | Sun | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 30.490000000000002 | O-B-E-T | 27.71 | 2.780000000000001 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 28 | Sun | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 32.480000000000004 | O-B-E-T | 27.71 | 4.770000000000003 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 28 | Sun | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 36.55 | O-B-E-T | 27.71 | 8.839999999999996 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 28 | Sun | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 36.55 | O-B-E-T | 27.71 | 8.839999999999996 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 29 | Mon | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 22.56 | O-C-E-D-T | 18.65 | 3.91 | False | 2 |  | fixed |
| 5 | 19:30-21:30 | 29 | Mon | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 21.619999999999997 | O-C-E-D-T | 18.65 | 2.969999999999999 | False | 1 |  | fixed |
| 5 | 19:30-21:30 | 29 | Mon | Pred_GroupMean | O-C-E-T | 15.0 | 19.1475 | 19.1475 | 20.05 | O-C-E-D-T | 18.65 | 1.4000000000000021 | False | 1 |  | predicted |
| 5 | 19:30-21:30 | 29 | Mon | Pred_NeuralNet | O-C-E-T | 15.0 | 19.062221703 | 19.062221703 | 20.05 | O-C-E-D-T | 18.65 | 1.4000000000000021 | False | 1 |  | predicted |
| 5 | 19:30-21:30 | 29 | Mon | Oracle | O-C-E-D-T | 14.0 | 18.65 |  | 18.65 | O-C-E-D-T | 18.65 | 0.0 | True | 1 |  | oracle |
| 5 | 19:30-21:30 | 29 | Mon | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 19.83 | O-C-E-D-T | 18.65 | 1.1799999999999997 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 29 | Mon | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 19.78 | O-C-E-D-T | 18.65 | 1.1300000000000026 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 29 | Mon | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 22.56 | O-C-E-D-T | 18.65 | 3.91 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 29 | Mon | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 22.56 | O-C-E-D-T | 18.65 | 3.91 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 30 | Tue | Fixed_distance | O-A-B-D-T | 13.0 | 13.0 |  | 22.259999999999998 | O-C-E-T | 17.66 | 4.599999999999998 | False | 2 |  | fixed |
| 5 | 19:30-21:30 | 30 | Tue | Fixed_trainmean | O-B-E-T | 15.0 | 22.243833333 | 22.243833333 | 19.66 | O-C-E-T | 17.66 | 2.0 | False | 1 |  | fixed |
| 5 | 19:30-21:30 | 30 | Tue | Pred_GroupMean | O-A-D-T | 14.0 | 18.7275 | 18.7275 | 19.770000000000003 | O-C-E-T | 17.66 | 2.110000000000003 | False | 1 |  | predicted |
| 5 | 19:30-21:30 | 30 | Tue | Pred_NeuralNet | O-C-E-D-T | 14.0 | 18.67110123 | 18.67110123 | 18.32 | O-C-E-T | 17.66 | 0.6600000000000001 | False | 1 |  | predicted |
| 5 | 19:30-21:30 | 30 | Tue | Oracle | O-C-E-T | 15.0 | 17.66 |  | 17.66 | O-C-E-T | 17.66 | 0.0 | True | 1 |  | oracle |
| 5 | 19:30-21:30 | 30 | Tue | RCSP_limit_18 | O-A-D-T | 14.0 |  |  | 19.770000000000003 | O-C-E-T | 17.66 | 2.110000000000003 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 30 | Tue | RCSP_limit_19 | O-A-B-E-D-T | 13.0 |  |  | 20.47 | O-C-E-T | 17.66 | 2.8099999999999987 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 30 | Tue | RCSP_limit_20 | O-A-B-D-T | 13.0 |  |  | 22.259999999999998 | O-C-E-T | 17.66 | 4.599999999999998 | False | 1 |  | rcsp |
| 5 | 19:30-21:30 | 30 | Tue | RCSP_limit_unbounded | O-A-B-D-T | 13.0 |  |  | 22.259999999999998 | O-C-E-T | 17.66 | 4.599999999999998 | False | 1 |  | rcsp |
