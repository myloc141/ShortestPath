# Workstream 6 — Routing Experiment Report

## 1. Objective

Workstream 6 evaluates how edge-weight choices affect routes from `O` to `T`
on the Seervada Park network. It compares routes selected using physical
distance, training-set travel-time averages, and predictions from WS4/WS5.
The routes are evaluated against the simulated actual travel times for each
corresponding test day and time slot.

The experiment is implemented in [`run_routing.py`](./run_routing.py). Input
network and traffic data are simulated/curated project data; the travel-time
results are **not real-world traffic measurements**.

## 2. Data and scope

- Network: 7 nodes (`O, A, B, C, D, E, T`) and 12 undirected edges.
- Source and destination: `O` to `T`.
- Training period: days 1–24.
- Test period: days 25–30, six days.
- Time slots: five slots per day, from 06:00–08:00 through 19:30–21:30.
- Traffic observations: one travel-time value per edge, day, and time slot.
- Distance is reported in km; simulated travel time is reported in minutes.

WS3 supplies `data/seervada_network.csv`, train/test traffic data, and
preprocessed model inputs. WS4 supplies Group Mean and Linear Regression
predictions; WS5 supplies Neural Network predictions. WS2 supplies RCSP
routes as route references. In particular, WS2 reads the
`seervada_rcsp_teaching.csv` data supplied by WS3; WS6 uses the resulting
routes for comparison and does not use the teaching times as simulated
actual travel times.

## 3. Method

### 3.1 Route selection

The script enumerates the 28 simple O-to-T routes in the network. For every
test day and time slot, it selects a minimum-weight route under:

- **Fixed distance:** edge distances from the network.
- **Fixed training mean:** average travel time per edge calculated over all
  training days and slots.
- **Group Mean:** per-row WS4 prediction.
- **Linear Regression:** per-row WS4 prediction.
- **Neural Network:** per-row WS5 prediction.
- **Oracle:** actual travel times for the same test day and slot; an
  idealized lower-bound reference, not a deployable predictor.

The script also evaluates five fixed WS2 routes: three routes optimal under
the 18-minute RCSP limit, one route for the 19-minute limit, and one route
for limits of at least 20 minutes. For WS6, these are simply fixed paths
scored with simulated actual times; the WS2 teaching-time constraint is not
reapplied.

For a tie in route weight, the selection rule prefers fewer edges and then
lexicographic route order. The minimum route cost is cross-checked against
Dijkstra for each method/day/slot.

### 3.2 Scoring and aggregation

For each chosen route, `actual_time` is the sum of the edge-level actual
travel times for the same test day and time slot. Regret is calculated as:

```text
regret = actual_time(route) - actual_time(Oracle route)
```

The script reports mean actual time, standard deviation, and mean regret
across test days. It computes results for all five time slots; the main
summary highlights:

- **Peak slot:** highest mean edge travel time on the training set.
- **Off-peak slot:** lowest mean edge travel time on the training set.

For the current data these are slot 4 (16:30–18:30) and slot 1
(06:00–08:00), respectively.

### 3.3 Prediction alignment and selection caveat

WS4 keyed prediction files are checked against the test set and their raw
prediction files. The script also checks prediction row counts and compares
recalculated test MAE/RMSE with configured reported values where available.
The NN file has no keyed companion, so it does not receive the same direct
key-based alignment check.

**The current code selects the primary WS4 baseline and decides whether to
include NN using MAE/RMSE on the test set.** Although the generated
`precommitted_rules.md` is written before the routing loop, that does not
make the model decision independent of the test set: the selection already
uses test labels. Consequently, the reported selection and routing
comparisons should be treated as exploratory. A final unbiased comparison
should determine the model using training/validation data, lock the choice,
and then evaluate once on a reserved test set.

## 4. Current model checks

Recalculated prediction metrics from the current inputs:

| Model | MAE (minutes) | RMSE (minutes) | Reported metric check |
|---|---:|---:|---|
| Group Mean | 0.9841 | 1.4110 | Matches configured WS4 values |
| Linear Regression | 1.2139 | 1.5832 | No configured reported values for comparison |
| Neural Network | 0.7038 | 0.9777 | Matches configured WS5 values |

Under the script's current rule, **Group Mean** is the primary WS4 baseline
because it has lower MAE and RMSE than Linear Regression. **Neural Network
is included in the main comparison** because both its MAE and RMSE are lower
than Group Mean's. These decisions are test-informed and subject to the
caveat above.

The training-set edge travel-time means select slot 4 as peak and slot 1 as
off-peak. The network has 28 simple routes; routing results cover all five
slots, six test days, and 11 methods (two fixed-weight methods, three
prediction methods, Oracle, and five RCSP route references).

## 5. Results for main slots

Values below are across the six test days. Mean actual travel time and its
standard deviation are in minutes; regret is also in minutes. “Modal route”
is the most frequent selected route and need not be the route selected on
every day.

### 5.1 Peak — slot 4 (16:30–18:30)

| Method | Modal route | Mean distance (km) | Mean actual time ± SD (min) | Mean regret (min) | Days equal to Oracle |
|---|---|---:|---:|---:|---:|
| Fixed distance | O–A–B–D–T | 13.000 | 35.047 ± 7.205 | 9.113 | 0/6 |
| Fixed training mean | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Group Mean | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Linear Regression | O–B–E–T | 15.000 | 27.185 ± 2.673 | 1.252 | 0/6 |
| Neural Network | O–B–E–T | 14.833 | 26.927 ± 2.846 | 0.993 | 0/6 |
| Oracle | O–C–E–T | 14.833 | 25.933 ± 3.044 | 0.000 | 6/6 |

At the peak slot, distance-only routing consistently selected the shortest
physical route, but that route had the highest mean simulated actual travel
time among the methods shown. The NN route had the lowest mean regret among
the non-Oracle methods in this slot. This is an observation on six simulated
test days, not evidence of guaranteed performance outside this experiment.

### 5.2 Off-peak — slot 1 (06:00–08:00)

| Method | Modal route | Mean distance (km) | Mean actual time ± SD (min) | Mean regret (min) | Days equal to Oracle |
|---|---|---:|---:|---:|---:|
| Fixed distance | O–A–B–D–T | 13.000 | 17.767 ± 0.527 | 2.953 | 0/6 |
| Fixed training mean | O–B–E–T | 15.000 | 16.057 ± 1.756 | 1.243 | 1/6 |
| Group Mean | O–B–E–T | 15.000 | 16.057 ± 1.756 | 1.243 | 1/6 |
| Linear Regression | O–C–B–E–D–T | 14.000 | 16.878 ± 0.877 | 2.065 | 0/6 |
| Neural Network | O–C–E–D–T | 14.333 | 16.032 ± 0.821 | 1.218 | 2/6 |
| Oracle | O–A–D–T | 14.500 | 14.813 ± 1.554 | 0.000 | 6/6 |

At the off-peak slot, NN had the lowest mean actual time and regret among
the non-Oracle methods shown, narrowly below Group Mean. Its modal route
occurred on three of the six test days; it selected other routes on the
remaining days.

### 5.3 All-slot comparison

Group Mean and NN selected different routes on **18 of 30** (five slots by
six test days) slot/day cases. Route differences alone do not establish
which prediction method is better; use actual travel time and regret for
the per-case evaluation. Detailed results for all slots are in
[`outputs/summary_by_slot_method.csv`](./outputs/summary_by_slot_method.csv)
and [`outputs/model_comparison.csv`](./outputs/model_comparison.csv).

## 6. Interpretation and limitations

1. **Distance and travel time optimize different objectives.** A route
   minimizing physical distance need not minimize simulated travel time.
2. **The fixed training mean is time-slot agnostic.** It averages each
   edge's training observations across all days and slots, unlike the
   per-slot model predictions.
3. **Oracle is not an operational method.** It uses the actual same-day
   travel times to select its route and is included only as an ideal
   reference.
4. **RCSP paths are evaluated, not re-solved, in WS6.** Their WS2 resource
   times and limits come from the teaching dataset; WS6 scores those fixed
   paths using the separate simulated traffic dataset.
5. **The test period is small and simulated.** The six test days support a
   controlled comparison but not broad statistical or real-world claims.
6. **Test-informed model selection can bias comparisons.** The primary
   baseline and NN inclusion decisions currently depend on test metrics.
   For confirmatory results, choose methods using validation data before
   test evaluation.

## 7. Reproduction and output files

Run from the repository root:

```powershell
python workstream06/run_routing.py
```

The script uses NumPy, pandas, and Matplotlib and writes results to
`workstream06/outputs/`. It produces:

- `precommitted_rules.md` and `selection.json`
- `routing_results_all.csv`, `summary_by_slot_method.csv`,
  `route_by_slot.csv`, and `model_comparison.csv`
- `results_summary.md`
- `fig_actual_time_main_slots.png`, `fig_regret_all_slots.png`, and
  `fig_route_map.png`

See [`README.md`](./README.md) for input details and output definitions.
