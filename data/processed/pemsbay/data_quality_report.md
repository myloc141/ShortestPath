# PeMS-BAY data quality report

## Inputs

## Traffic
- Layout: unavailable
- Time steps/rows: unavailable
- Sensors: unavailable
- Timestamp source: unavailable
- Temporal ordering valid: unavailable
- First timestamp: unavailable
- Last timestamp: unavailable
- Uniform sampling interval (ns): unavailable
- Missing speed values: unavailable
- Invalid speed values (non-numeric, infinite, or negative): unavailable

## Adjacency
- Shape: unavailable
- Symmetric: unavailable
- Contains self-loops: unavailable
- Binary weights: unavailable
- Nonzero weights: unavailable

## Cross-source validation
- All required checks passed.

## Transformations and assumptions
- Sensor data is aligned by explicit sensor ID, never by assumed row order.
- Missing speed values are preserved as Parquet nulls; no imputation is performed.
- Traffic timestamps are preserved only when present and parseable; otherwise time_index is used.
- The adjacency edge table preserves every nonzero matrix entry, including self-loops.
- The original adjacency direction, weights, and sensor ordering are preserved.
