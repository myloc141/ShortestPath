"""Structural and key validation for declared pipeline interfaces."""

from __future__ import annotations

import math
from numbers import Integral, Real
from typing import Mapping, Sequence

from .exceptions import ContractViolation, InterfaceId
from .schemas import ColumnType, INTERFACE_SCHEMAS


Record = Mapping[str, object]
TableInput = object


def _records(
    data: TableInput,
    *,
    interface_id: InterfaceId,
    name: str,
) -> tuple[Record, ...]:
    columns = getattr(data, "columns", None)
    if columns is not None and hasattr(data, "to_dict"):
        return tuple(data.to_dict(orient="records"))
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        if all(isinstance(row, Mapping) for row in data):
            return tuple(data)
    raise ContractViolation(
        interface_id,
        f"{name} must be a DataFrame or a sequence of mapping rows",
    )


def _validate_table(
    data: TableInput,
    *,
    interface_id: InterfaceId,
    table_name: str,
    key_columns: tuple[str, ...],
) -> None:
    schema = INTERFACE_SCHEMAS[interface_id][table_name]
    rows = _records(data, interface_id=interface_id, name=table_name)
    if hasattr(data, "columns"):
        available_columns = set(data.columns)
    elif rows:
        available_columns = set.intersection(*(set(row) for row in rows))
    else:
        available_columns = set()
    missing = set(schema) - available_columns
    if missing:
        raise ContractViolation(
            interface_id,
            f"{table_name} is missing required columns: {sorted(missing)}",
        )

    for row_number, row in enumerate(rows, start=1):
        for column, expected_type in schema.items():
            value = row.get(column)
            if not _matches_type(value, expected_type):
                expected_name = (
                    " or ".join(item.__name__ for item in expected_type)
                    if isinstance(expected_type, tuple)
                    else expected_type.__name__
                )
                raise ContractViolation(
                    interface_id,
                    f"{table_name} row {row_number} column {column!r} "
                    f"must be {expected_name}",
                )

    if key_columns:
        seen: set[tuple[object, ...]] = set()
        for row_number, row in enumerate(rows, start=1):
            key = tuple(row[column] for column in key_columns)
            if key in seen:
                raise ContractViolation(
                    interface_id,
                    f"{table_name} has duplicate key {key!r} at row {row_number}",
                )
            seen.add(key)


def _matches_type(value: object, expected_type: ColumnType) -> bool:
    if isinstance(expected_type, tuple):
        if value is None:
            return type(None) in expected_type
        if (
            isinstance(value, float)
            and math.isnan(value)
            and type(None) in expected_type
        ):
            return True
        return any(_matches_type(value, item_type) for item_type in expected_type)
    if expected_type is str:
        return isinstance(value, str)
    if expected_type is bool:
        return type(value) is bool
    if expected_type is int:
        return isinstance(value, Integral) and not isinstance(value, bool)
    if expected_type is float:
        return (
            isinstance(value, Real)
            and not isinstance(value, bool)
            and math.isfinite(float(value))
        )
    if expected_type is tuple:
        return isinstance(value, tuple) and all(
            isinstance(item, str) for item in value
        )
    return isinstance(value, expected_type)


def validate_i1(network_nodes: TableInput, network_edges: TableInput) -> None:
    """Validate I1 node/edge tables, types, and unique identifiers."""
    _validate_table(
        network_nodes,
        interface_id="I1",
        table_name="network_nodes",
        key_columns=("node_id",),
    )
    _validate_table(
        network_edges,
        interface_id="I1",
        table_name="network_edges",
        key_columns=("edge_id",),
    )


def validate_i4(
    train: TableInput,
    valid: TableInput,
    test: TableInput,
    split_manifest: TableInput,
) -> None:
    """Validate I4 train/valid/test splits and their split manifest."""
    for name, data in (("train", train), ("valid", valid), ("test", test)):
        _validate_table(
            data,
            interface_id="I4",
            table_name=name,
            key_columns=("day", "time_slot", "edge_id"),
        )
    _validate_table(
        split_manifest,
        interface_id="I4",
        table_name="split_manifest",
        key_columns=("split",),
    )


def validate_i5(prediction: TableInput) -> None:
    """Validate keyed I5 predictions and uniqueness of their row keys."""
    _validate_table(
        prediction,
        interface_id="I5",
        table_name="prediction",
        key_columns=("edge_id", "day", "time_slot"),
    )


def validate_i8(routing_results: TableInput) -> None:
    """Validate I8 routing result rows and their method/day keys."""
    _validate_table(
        routing_results,
        interface_id="I8",
        table_name="routing_results",
        key_columns=("time_slot", "day", "method"),
    )


__all__ = ["validate_i1", "validate_i4", "validate_i5", "validate_i8"]
