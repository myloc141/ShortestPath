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
adapter deterministically selects a connected sensor subset and a bounded
simple-path endpoint pair; the selected values and criteria are retained in
adapter metadata. The raw-preparation step is separate and runs before WS1;
WS1 publishes the I1 network consumed by the model-data builder:

```powershell
python scripts\run_preprocess_pems_bay.py `
  --input-dir data\raw_pems_bay `
  --artifacts-root . `
  --log-level INFO
python scripts\run_workstream01.py --dataset pemsbay --artifacts-root .
python scripts\build_dataset.py --dataset pemsbay --artifacts-root .
```

The first command calls `src.adapters.pemsbay_prepare.run_pipeline` directly
and writes long-form Parquet plus quality reports. The Parquet contract is
`time_index`, `sensor_id`, `speed`, and optional/nullable `timestamp`.
`PemsBayAdapter.build_observations` maps and cleans the five-minute sensor
readings, including travel-time conversion. `build_dataset.py` then passes
those observations through `src/preprocess/dataset.py` for hourly aggregation,
lag features, and chronological splits. Speeds are interpreted as mph by
default and converted with Haversine distance (an approximation); edge
direction follows `direction_policy`.

RCSP requires a configured resource input. WS2 requires PuLP/CBC. Model and
plot stages require scikit-learn and Matplotlib. CSV input/output uses Pandas.
The combined report is written to `docs/report/<dataset>_report.md`;
unavailable stage results are reported as `chưa có kết quả`.
