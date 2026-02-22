import typing
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .exceptions import AuditAlreadyConfiguredError, AuditNotConfiguredError

if TYPE_CHECKING:
    from .storage.base import AuditStorage

ORMBackend = Literal["sqlalchemy", "tortoise", "sqlmodel", "beanie", "asyncpg"]


class AuditConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Required
    orm: ORMBackend
    dsn: str  # full connection string e.g. "postgresql+asyncpg://user:pass@host/db"

    # Table / collection config
    table_name: str = "audit_logs"
    auto_create_table: bool = True  # CREATE TABLE IF NOT EXISTS on startup

    # SQLAlchemy-specific
    sqlalchemy_pool_size: int = 10
    sqlalchemy_max_overflow: int = 20
    sqlalchemy_pool_timeout: int = 30
    sqlalchemy_echo: bool = False
    expose_metadata: bool = False  # if True, exposes Base.metadata for Alembic

    # Tortoise-specific
    tortoise_modules: dict[str, list[str]] | None = None

    # MongoDB / Beanie-specific
    mongodb_database: str = "audit"

    # Batching (for all backends)
    batch_size: int = 1  # set > 1 to enable batch inserts
    batch_flush_interval: float = 5.0  # seconds, used if batch_size > 1

    # PII masking
    mask_fields: list[str] = Field(default_factory=list)

    # Error handling
    on_storage_error: Any = None  # callable(exc: Exception, entry: AuditEntry) -> None


# Global registry holding the configured storage instance
_registry: dict[str, Any] = {}


def configure(config: AuditConfig) -> "AuditStorage":
    """
    Initialize and register the audit storage backend.
    Must be called once at app startup before serving requests.
    Returns the configured storage instance.
    Raises AuditConfigurationError if config is invalid or backend cannot connect.
    """
    from .registry import resolve_storage

    if "storage" in _registry:
        existing_config = _registry["config"]
        if existing_config == config:
            return typing.cast("AuditStorage", _registry["storage"])
        raise AuditAlreadyConfiguredError(
            "Audit storage is already configured with a different configuration."
        )

    storage = resolve_storage(config)
    _registry["storage"] = storage
    _registry["config"] = config
    return typing.cast("AuditStorage", storage)


def get_storage() -> "AuditStorage":
    """
    Retrieve the globally registered storage instance.
    Raises AuditNotConfiguredError if configure() has not been called.
    """
    if "storage" not in _registry:
        raise AuditNotConfiguredError(
            "Audit storage has not been configured. Call configure() first."
        )
    return typing.cast("AuditStorage", _registry["storage"])
