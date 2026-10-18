# PeMS-BAY data quality report

## Inputs
- **traffic:** `data\raw_pems_bay\pems-bay.h5` (format: hdf5)
- **adjacency:** `data\raw_pems_bay\adj_mx_bay.pkl` (format: pickle)
- **locations:** `data\raw_pems_bay\graph_sensor_locations_bay.csv` (format: csv_text)

## Traffic
- Layout: wide
- Time steps/rows: 52116
- Sensors: 325
- Timestamp source: datetime index
- Temporal ordering valid: True
- First timestamp: 2017-01-01T00:00:00
- Last timestamp: 2017-06-30T23:55:00
- Uniform sampling interval (ns): None
- Missing speed values: 0
- Invalid speed values (non-numeric, infinite, or negative): 0

## Adjacency
- Shape: (325, 325)
- Symmetric: False
- Contains self-loops: True
- Binary weights: False
- Nonzero weights: 2694

## Cross-source validation
- All required checks passed.

## Outputs
- `traffic_speed_long.parquet`: 16937700 rows
- `sensor_metadata.parquet`: 325 rows
- `adjacency_matrix.parquet`: 2694 rows
- `sensor_id_mapping.parquet`: 325 rows

## Transformations and assumptions
- Sensor data is aligned by explicit sensor ID, never by assumed row order.
- Missing speed values are preserved as Parquet nulls; no imputation is performed.
- Traffic timestamps are preserved only when present and parseable; otherwise time_index is used.
- The adjacency edge table preserves every nonzero matrix entry, including self-loops.
- The original adjacency direction, weights, and sensor ordering are preserved.
