"""Explicit table persistence with adjacent JSON interface metadata."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import TYPE_CHECKING, Mapping

from .exceptions import ContractViolation

if TYPE_CHECKING:
    import pandas as pd


Metadata = dict[str, object]
_META_KEYS = ("interface_id", "dataset", "schema_version")
_INTERFACE_IDS = frozenset(f"I{number}" for number in range(1, 9))


def _metadata_path(path: Path) -> Path:
    return path.with_suffix(path.suffix + ".meta.json")


def _validate_meta(meta: Mapping[str, object]) -> Metadata:
    missing = set(_META_KEYS) - meta.keys()
    interface_id = meta.get("interface_id")
    valid_interface = (
        interface_id if isinstance(interface_id, str) and interface_id in _INTERFACE_IDS
        else "I1"
    )
    if missing:
        raise ContractViolation(
            valid_interface, f"Metadata is missing required keys: {sorted(missing)}"
        )
    if not isinstance(interface_id, str) or interface_id not in _INTERFACE_IDS:
        raise ContractViolation("I1", f"Invalid metadata interface_id: {interface_id!r}")
    for key in ("dataset", "schema_version"):
        value = meta[key]
        if not isinstance(value, (str, int, float)) or isinstance(value, bool):
            raise ContractViolation(
                interface_id, f"Metadata {key!r} must be a string or number"
            )
    if "created_at" not in meta:
        created_at = datetime.now(timezone.utc).isoformat()
    else:
        created_at = meta["created_at"]
    if not isinstance(created_at, str):
        raise ContractViolation(interface_id, "Metadata 'created_at' must be a string")
    return {**meta, "created_at": created_at}


def write_with_meta(
    path: str | Path,
    df: pd.DataFrame,
    meta: Mapping[str, object],
) -> None:
    """Write a CSV/Parquet DataFrame and a sibling ``.meta.json`` file."""
    data_path = Path(path)
    metadata = _validate_meta(meta)
    suffix = data_path.suffix.casefold()
    if suffix == ".csv":
        df.to_csv(data_path, index=False)
    elif suffix in {".parquet", ".pq"}:
        df.to_parquet(data_path, index=False)
    else:
        raise ValueError(f"Unsupported table format for {data_path}")
    _metadata_path(data_path).write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def read_with_meta(path: str | Path) -> tuple[pd.DataFrame, Metadata]:
    """Read a CSV/Parquet DataFrame and its sibling ``.meta.json`` file."""
    data_path = Path(path)
    metadata_path = _metadata_path(data_path)
    suffix = data_path.suffix.casefold()
    if suffix == ".csv":
        frame = pd.read_csv(data_path)
    elif suffix in {".parquet", ".pq"}:
        frame = pd.read_parquet(data_path)
    else:
        raise ValueError(f"Unsupported table format for {data_path}")
    raw_meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    if not isinstance(raw_meta, dict):
        raise ContractViolation("I1", "Metadata sidecar must contain a JSON object")
    metadata = _validate_meta(raw_meta)
    if "created_at" not in raw_meta:
        raise ContractViolation("I1", "Metadata is missing required key: 'created_at'")
    return frame, metadata


__all__ = ["Metadata", "read_with_meta", "write_with_meta"]
