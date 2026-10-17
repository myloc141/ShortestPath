"""Registry for supported dataset adapter implementations."""

from __future__ import annotations

from typing import Callable

from .base import DatasetAdapter
from .pemsbay import PemsBayAdapter
from .seervada import SeervadaAdapter


AdapterFactory = Callable[..., DatasetAdapter]
ADAPTERS: dict[str, AdapterFactory] = {
    "seervada": SeervadaAdapter,
    "pemsbay": PemsBayAdapter,
}


def get_adapter(name: str, **options: object) -> DatasetAdapter:
    """Instantiate the registered adapter for ``name``."""
    try:
        factory = ADAPTERS[name.casefold()]
    except KeyError as error:
        supported = ", ".join(sorted(ADAPTERS))
        raise ValueError(
            f"Unknown dataset adapter {name!r}; supported datasets: {supported}"
        ) from error
    return factory(**options)


__all__ = ["ADAPTERS", "AdapterFactory", "get_adapter"]
