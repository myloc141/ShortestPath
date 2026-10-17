"""Static column contracts for the pipeline's named interfaces."""

from __future__ import annotations

from typing import TypedDict


ColumnType = type | tuple[type, ...]
ColumnSchema = dict[str, ColumnType]


class NetworkRecord(TypedDict):
    """One normalized network edge, matching the I1 network_edges contract."""

    edge_id: str
    u: str
    v: str
    distance: float
    directed: bool


INTERFACE_SCHEMAS: dict[str, dict[str, ColumnSchema]] = {
    "I1": {
        "network_nodes": {"node_id": str},
        "network_edges": {
            "edge_id": str,
            "u": str,
            "v": str,
            "distance": float,
            "directed": bool,
        },
    },
    "I4": {
        "train": {
            "day": int,
            "day_of_week": str,
            "time_slot": int,
            "edge_id": str,
            "node_u": str,
            "node_v": str,
            "distance": float,
            "travel_time": float,
        },
        "valid": {
            "day": int,
            "day_of_week": str,
            "time_slot": int,
            "edge_id": str,
            "node_u": str,
            "node_v": str,
            "distance": float,
            "travel_time": float,
        },
        "test": {
            "day": int,
            "day_of_week": str,
            "time_slot": int,
            "edge_id": str,
            "node_u": str,
            "node_v": str,
            "distance": float,
            "travel_time": float,
        },
        "split_manifest": {
            "split": str,
            "start_day": (int, str),
            "end_day": (int, str),
            "n_days": int,
            "n_rows": int,
        },
    },
    "I5": {
        "prediction": {
            "edge_id": str,
            "day": int,
            "time_slot": int,
            "y_pred": float,
        },
    },
    "I8": {
        "routing_results": {
            "time_slot": int,
            "day": int,
            "method": str,
            "method_family": str,
            "route": (str, tuple),
            "distance_km": float,
            "objective": (float, type(None)),
            "predicted_time": (float, type(None)),
            "actual_time": float,
            "oracle_route": (str, tuple),
            "oracle_time": float,
            "regret": float,
            "matches_oracle": bool,
            "n_ties": int,
        },
    },
}

REQUIRED_COLUMNS: dict[str, dict[str, tuple[str, ...]]] = {
    interface_id: {
        table_name: tuple(columns)
        for table_name, columns in tables.items()
    }
    for interface_id, tables in INTERFACE_SCHEMAS.items()
}

__all__ = [
    "ColumnSchema",
    "ColumnType",
    "INTERFACE_SCHEMAS",
    "NetworkRecord",
    "REQUIRED_COLUMNS",
]
