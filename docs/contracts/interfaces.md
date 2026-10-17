# Pipeline interface contracts I1–I8

This document records the finalized required fields and the producer/consumer
files or APIs. Table validators accept additional columns, but every required
column below must be present and have the declared type. Runners use
`ContractViolation` handling to print the interface ID/message, write a JSON
record under `artifacts/<dataset>/_errors/`, and exit non-zero.

## I1 — Network

Produced from the adapter `Network` and exported by WS1.

| File/table | Required columns | Types |
|---|---|---|
| `artifacts/<dataset>/network/network_nodes.csv` / `network_nodes` | `node_id` | string |
| `artifacts/<dataset>/network/network_edges.csv` / `network_edges` | `edge_id`, `u`, `v`, `distance`, `directed` | string, string, string, finite number, boolean |

`node_id` and `edge_id` are unique within their respective tables.

## I2 — Simple paths and shortest path

WS1 consumes I1 and exports these files under
`artifacts/<dataset>/paths/`:

| File | Required columns |
|---|---|
| `results_paths.csv` | `rank`, `source`, `target`, `path`, `total_distance`, `num_nodes`, `num_edges`, `algorithm`, `is_optimal` |
| `shortest_path_summary.csv` | `source`, `target`, `path`, `total_distance`, `paths_checked`, `verified` |

These files are not currently covered by a `validate_i2` function.

## I3 — RCSP

WS2 writes `artifacts/<dataset>/rcsp/rcsp_sensitivity.csv` with `resource_limit`, `status`,
`optimal_path`, `total_distance`, `total_resource`, and
`route_changed_vs_previous`. WS6 reads `resource_limit`, `status`, and
`optimal_path`; every `Optimal` route becomes a routing reference. See
[I3-routing.md](./I3-routing.md) for the M3-to-M8 handoff.

## I4 — Chronological observations and splits

WS3 consumes I1 from `artifacts/<dataset>/network/` and writes
`data/processed/<dataset>/train.csv`, `valid.csv`, and `test.csv`. Each must include:

`day` (integer), `day_of_week` (string), `time_slot` (integer),
`edge_id` (string), `node_u` and `node_v` (strings), `distance` and
`travel_time` (finite numbers). The unique row key is
`(day, time_slot, edge_id)`. Extra fields such as `time_slot_name` and
`is_weekend` are allowed.

`data/processed/<dataset>/split_manifest.csv` requires `split` (string), `start_day` and `end_day`
(integer or string), `n_days` and `n_rows` (integers). `split` is unique.
This matches the manifest emitted by WS3.

## I5 — Keyed predictions

WS4 and WS5 export keyed validation/test predictions under
`artifacts/<dataset>/predictions/`; WS6 reads these files.
Required columns are:

| Column | Type |
|---|---|
| `edge_id` | string |
| `day` | integer |
| `time_slot` | integer |
| `y_pred` | finite number |

`(edge_id, day, time_slot)` is unique. Legacy one-column raw prediction files
are auxiliary exports and are not I5 payloads.

## I6 — Evaluation metrics

WS4/WS5 metric CSVs under `artifacts/<dataset>/metrics/` contain `time_slot`, `model`, `MAE`, `RMSE`, `MSE`,
`MAPE_percent`, and `n_obs`. The `time_slot` value is `"all"` or a slot label;
the four metrics are finite numbers and `n_obs` is an integer. Metric
calculation is provided by `src.common.metrics.evaluate_all` and
`src.evaluation.evaluate_by_time_slot`.

## I7 — Weighted shortest-path call

M8 calls `src.shortest_path.dijkstra.dijkstra(network, source, target,
weights=None)`. When supplied, `weights` maps every `edge_id` to a finite,
non-negative number. An undirected network edge uses the same edge weight in
both directions. No file is required.

## I8 — Routing results

WS6 exports `artifacts/<dataset>/routing/routing_results_all.csv`. The required columns and types are:

| Column | Type |
|---|---|
| `time_slot`, `day`, `n_ties` | integers |
| `method`, `method_family` | strings |
| `route`, `oracle_route` | node tuples or hyphen-delimited strings |
| `distance_km`, `actual_time`, `oracle_time`, `regret` | finite numbers |
| `objective`, `predicted_time` | finite numbers or null |
| `matches_oracle` | boolean |

The unique result key is `(time_slot, day, method)`. `method_family` is
`fixed`, `predicted`, `oracle`, `rcsp`, or `reference`; `selection_warning`
may be present as an additional column.

## Metadata opt-in

Runner option `--artifacts-root` selects a repository-level root for the
`artifacts/`, `data/processed/`, and `docs/report/` trees. The deprecated
`--output-dir` option is accepted as an alias. For missing Seervada files,
downstream readers warn and fall back to an existing legacy
`workstreamXX/outputs/` file; no files are moved.

Runner option `--with-meta` adds JSON sidecars to contract table CSVs using
`write_with_meta`. By default, CSVs remain in their current format without
metadata sidecars. Auxiliary legacy raw prediction files remain unkeyed and
are not declared as I5 tables.
