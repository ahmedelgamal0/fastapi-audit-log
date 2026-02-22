from typing import TYPE_CHECKING

from .exceptions import AuditConfigurationError

if TYPE_CHECKING:
    from .config import AuditConfig
    from .storage.base import AuditStorage

DSN_VALIDATORS: dict[str, list[str]] = {
    "sqlalchemy": [
        "postgresql+asyncpg://",
        "mysql+aiomysql://",
        "sqlite+aiosqlite:///",
    ],
    "tortoise": ["postgres://", "postgresql://", "mysql://", "sqlite://"],
    "sqlmodel": [
        "postgresql+asyncpg://",
        "mysql+aiomysql://",
        "sqlite+aiosqlite:///",
    ],
    "beanie": ["mongodb://", "mongodb+srv://"],
    "asyncpg": ["postgresql://", "postgres://"],
}


def validate_dsn(orm: str, dsn: str) -> None:
    """Raise AuditConfigurationError if DSN prefix doesn't match the selected ORM."""
    prefixes = DSN_VALIDATORS.get(orm, [])
    if not any(dsn.startswith(prefix) for prefix in prefixes):
        msg = f"Invalid DSN for ORM '{orm}'. Expected prefixes: {', '.join(prefixes)}"
        raise AuditConfigurationError(msg)


def resolve_storage(config: "AuditConfig") -> "AuditStorage":
    """Instantiate and return the correct storage backend for the given config."""
    validate_dsn(config.orm, config.dsn)

    if config.orm == "sqlalchemy":
        from .storage.sqlalchemy_storage import SQLAlchemyStorage

        return SQLAlchemyStorage(config)

    if config.orm == "tortoise":
        from .storage.tortoise_storage import TortoiseStorage

        return TortoiseStorage(config)

    if config.orm == "sqlmodel":
        from .storage.sqlmodel_storage import SQLModelStorage

        return SQLModelStorage(config)

    if config.orm == "beanie":
        from .storage.beanie_storage import BeanieStorage

        return BeanieStorage(config)

    if config.orm == "asyncpg":
        from .storage.asyncpg_storage import AsyncpgStorage

        return AsyncpgStorage(config)

    raise AuditConfigurationError(f"Unsupported ORM backend: {config.orm}")
