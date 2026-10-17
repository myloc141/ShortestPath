"""Dataset-specific implementations of the canonical adapter contract."""

from .base import DatasetAdapter
from .pemsbay import (
    PemsBayAdapter,
    build_pemsbay_dataset,
    select_pemsbay_sensors,
)
from .registry import ADAPTERS, get_adapter
from .seervada import SeervadaAdapter, load_seervada_network

__all__ = [
    "ADAPTERS",
    "DatasetAdapter",
    "PemsBayAdapter",
    "SeervadaAdapter",
    "build_pemsbay_dataset",
    "get_adapter",
    "load_seervada_network",
    "select_pemsbay_sensors",
]
