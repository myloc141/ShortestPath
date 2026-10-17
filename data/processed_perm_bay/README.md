# PeMS-BAY preprocessing

This is a legacy output location retained for existing data; files here are
not moved or deleted. The preprocessing module does not run when imported.
The launcher now writes Parquet and quality reports to
`data/processed/pemsbay/` under the canonical stage layout.

## Inputs

By default, the script searches recursively in `data/raw_perm_bay/` for one
file with each expected base name:

- `pems-bay` — traffic speed observations; HDF5, Parquet, or CSV content.
- `adj_mx_bay` — adjacency object; trusted pickle, Parquet, or CSV content.
- `graph_sensor_locations_bay` — locations; Parquet or CSV content.

The script inspects file signatures/content rather than trusting the extension.
It fails clearly if a source is missing, duplicated, ambiguous, or has an
unsupported schema. HDF5 input is inspected for keys and must contain one
unambiguous pandas table. Traffic IDs must be explicit in wide column names or
long-format sensor ID values. Sensor order is aligned using IDs, never by row
position.

**Security:** only use `adj_mx_bay` pickle files from a trusted source. Loading a
pickle can execute code.

## Run later

Install dependencies from this folder, then invoke the script from the
repository root:

```powershell
python scripts\run_preprocess_pems_bay.py
```

Paths are configurable:

```powershell
python scripts\run_preprocess_pems_bay.py `
  --input-dir data/raw_perm_bay `
  --artifacts-root . `
  --log-level INFO
```

After raw preprocessing completes, build the cleaned hourly model dataset:

```powershell
python scripts\build_dataset.py --dataset pemsbay --artifacts-root .
```

## Outputs

- `traffic_speed_long.parquet`: `time_index` (int64), nullable `timestamp`
  (ISO-8601 string), `sensor_id` (string), and nullable `speed` (float64).
  Missing speed values remain null; no rows are imputed or dropped. Data is
  written in bounded time chunks.
- `sensor_metadata.parquet`: normalized `sensor_id`, `latitude`, `longitude`.
- `adjacency_matrix.parquet`: long edge table of every original nonzero
  `source_sensor_id`, `target_sensor_id`, `weight`. Zero entries are omitted;
  nonzero diagonal/self-loop entries are preserved. Original weights,
  direction, and sensor ordering are not normalized or symmetrized.
- `sensor_id_mapping.parquet`: source indices and presence flags for each
  adjacency sensor ID. Traffic-column indices are populated for wide-format
  input; location indices point to original source record positions.
- `data_quality_report.json` and `data_quality_report.md`: detected formats,
  source schemas/dimensions, adjacency properties, alignment, data quality,
  transformations, and output row counts/schema.

The long Parquet contract is `time_index` (int64), nullable `timestamp`
(ISO-8601 string), `sensor_id` (string), and nullable `speed` (float64).
The adapter requires `time_index`, `sensor_id`, and `speed`; timestamp is used
when available and otherwise the configured five-minute cadence is used.

Canonical raw outputs are in `data/processed/pemsbay/`; the hourly dataset
builder writes separately to `data/processed/pemsbay/model_dataset/`.
Outputs are replaced only after the datasets have been written and read back
successfully. If validation fails, the quality reports record the issue and
processed datasets are not published.

## Assumptions and limitations

- A timestamp is retained only when explicitly present and parseable. Otherwise
  the dataset uses an integer observation index; the script does not invent a
  start time or sampling interval.
- The script reports the observed ordering but does not claim a five-minute
  interval unless timestamps support that conclusion.
- Conflicting/duplicate location IDs fail validation; no silent deduplication
  or coordinate selection is performed.
- Adjacency pickle structures must expose exactly one sensor-ID sequence and
  one square numeric matrix. Ambiguous objects fail instead of guessing.
- Traffic data is expected either as wide data with sensor IDs as columns or
  long data with explicit sensor ID and speed fields. Unsupported layouts fail.
- Matrix-level adjacency properties such as symmetry, binary/weighted values,
  and self-loops are reported without changing the matrix.
- This pipeline performs data preparation only; it does not train a model.
