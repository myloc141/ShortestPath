# Workstream runners

Run commands from the repository root. Every workstream runner, `build_dataset.py`,
and `make_report.py` uses `stage_dir(dataset, stage, root)` from
`_runner_utils.py`. `--artifacts-root` defaults to the repository root and
accepts the same root for every stage. `--output-dir` is a deprecated alias and
prints a warning. For missing Seervada inputs only, runners fall back to an
existing `workstreamXX/outputs/` file and warn; they do not move it.

Stage locations are `artifacts/<dataset>/network/` and `paths/` (WS1),
`artifacts/<dataset>/rcsp/` (WS2),
`data/processed/<dataset>/` (WS3 and raw PEMS-BAY Parquet),
`artifacts/<dataset>/predictions/` and `metrics/` (WS4/5),
`artifacts/<dataset>/routing/` (WS6),
`data/processed/pemsbay/model_dataset/` (`build_dataset.py`, separate from
WS3's I4 files), and `docs/report/<dataset>_report.md` (`make_report.py`).
Contract errors are saved under `artifacts/<dataset>/_errors/`.
Install runtime dependencies with `python -m pip install -r requirements.txt`;
the `tables` package provides PyTables support for HDF5 input.

Run workstreams in dependency order, then generate the combined M9 report:

```powershell
python scripts\run_workstream01.py --dataset seervada --artifacts-root .
python scripts\run_workstream02.py --dataset seervada --artifacts-root .
python scripts\run_workstream03.py --dataset seervada --artifacts-root .
python scripts\run_workstream04.py --dataset seervada --artifacts-root .
python scripts\run_workstream05.py --dataset seervada --artifacts-root .
python scripts\run_workstream06.py --dataset seervada --artifacts-root .
python scripts\make_report.py --dataset seervada --artifacts-root .
```

PEMS-BAY leaves `sensor_ids`, `source`, and `target` empty by default. Its
adapter uses deterministic BFS for a connected sensor subset, then adds 3–9
non-tree edges ranked by shortest Haversine cycle length. It accepts endpoint
pairs only when the bounded simple-path count is within `min_paths` and
`max_paths`; the chosen sensors, edge/path counts, endpoints, and criteria are
retained in adapter metadata. The raw-preparation step is separate and runs
before WS1; then run WS1 and WS3–WS6. WS3 writes the aggregated I4 splits
that WS4–WS6 read directly:

```powershell
python scripts\run_preprocess_pems_bay.py `
  --input-dir data\raw_pems_bay `
  --artifacts-root . `
  --log-level INFO
python scripts\run_workstream01.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream03.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream04.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream05.py --dataset pemsbay --artifacts-root .
python scripts\run_workstream06.py --dataset pemsbay --artifacts-root .
```

The first command calls `src.adapters.pemsbay_prepare.run_pipeline` directly
and writes long-form Parquet plus quality reports. The Parquet contract is
`time_index`, `sensor_id`, `speed`, and optional/nullable `timestamp`.
`PemsBayAdapter.build_observations` maps and cleans five-minute readings, then
averages travel time by `(edge_id, day, time_slot)`. A cell needs at least
`min_slot_coverage` valid readings (default 0.5); only days complete for every
edge and configured slot are retained. WS3 splits those days chronologically
without shuffling. WS4–WS6 consume that WS3 I4 output. `build_dataset.py` is an
optional auxiliary model-data branch and is not used downstream. Speeds are
interpreted as mph by default and converted with approximate Haversine edge
length; short-gap-only interpolation is capped by `max_speed_imputation_gap`.

WS6 always includes NeuralNet in the routing comparison, even when validation
metrics favor GroupMean or LinearRegression. Validation metrics still determine
the primary baseline; NN results remain visible in the routing outputs.

RCSP requires a configured resource input. WS2 requires PuLP/CBC. Model and
plot stages require scikit-learn and Matplotlib. CSV input/output uses Pandas.
The combined report is written to `docs/report/<dataset>_report.md`;
unavailable stage results are reported as `chưa có kết quả`.
