"""Common pipeline and interface-contract exceptions."""

from __future__ import annotations

from typing import Literal


InterfaceId = Literal["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8"]
_INTERFACE_IDS = frozenset(f"I{number}" for number in range(1, 9))


class PipelineError(Exception):
    """Base exception carrying the affected interface and a readable message."""

    def __init__(self, interface_id: InterfaceId, message: str) -> None:
        if not isinstance(interface_id, str) or interface_id not in _INTERFACE_IDS:
            raise ValueError(f"Unknown interface_id: {interface_id!r}")
        self.interface_id = interface_id
        self.message = message
        super().__init__(f"{interface_id}: {message}")


class SchemaError(PipelineError):
    """Raised when data cannot be represented by a declared schema."""


class ContractViolation(PipelineError):
    """Raised when data violates an interface contract."""


class DataQualityError(PipelineError):
    """Raised when data fails a quality rule beyond structural validation."""


__all__ = [
    "ContractViolation",
    "DataQualityError",
    "InterfaceId",
    "PipelineError",
    "SchemaError",
]
