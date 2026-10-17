"""Shared pipeline configuration, contracts, schemas, I/O, and metrics."""

from .config import PipelineConfig, load_config
from .exceptions import (
    ContractViolation,
    DataQualityError,
    InterfaceId,
    PipelineError,
    SchemaError,
)
from .io import Metadata, read_with_meta, write_with_meta
from .metrics import (
    evaluate_all,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    root_mean_squared_error,
)
from .schemas import (
    INTERFACE_SCHEMAS,
    REQUIRED_COLUMNS,
    ColumnSchema,
    ColumnType,
    NetworkRecord,
)
from .validators import validate_i1, validate_i4, validate_i5, validate_i8

__all__ = [
    "ContractViolation",
    "ColumnSchema",
    "ColumnType",
    "DataQualityError",
    "INTERFACE_SCHEMAS",
    "InterfaceId",
    "Metadata",
    "NetworkRecord",
    "PipelineConfig",
    "PipelineError",
    "REQUIRED_COLUMNS",
    "SchemaError",
    "evaluate_all",
    "load_config",
    "mean_absolute_error",
    "mean_absolute_percentage_error",
    "mean_squared_error",
    "read_with_meta",
    "root_mean_squared_error",
    "validate_i1",
    "validate_i4",
    "validate_i5",
    "validate_i8",
    "write_with_meta",
]
