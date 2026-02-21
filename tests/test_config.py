import pytest

from fastapi_audit_log.config import AuditConfig, _registry, configure, get_storage
from fastapi_audit_log.exceptions import (
    AuditAlreadyConfiguredError,
    AuditConfigurationError,
    AuditNotConfiguredError,
)
from fastapi_audit_log.storage.sqlalchemy_storage import SQLAlchemyStorage


@pytest.fixture(autouse=True)
def clear_registry():
    _registry.clear()
    yield
    _registry.clear()


def test_configure_invalid_dsn():
    config = AuditConfig(orm="sqlalchemy", dsn="invalid://dsn")
    with pytest.raises(AuditConfigurationError, match="Invalid DSN for ORM"):
        configure(config)


def test_get_storage_not_configured():
    with pytest.raises(AuditNotConfiguredError):
        get_storage()


def test_configure_success():
    config = AuditConfig(orm="sqlalchemy", dsn="sqlite+aiosqlite:///:memory:")
    storage = configure(config)
    assert isinstance(storage, SQLAlchemyStorage)
    assert get_storage() == storage


def test_configure_already_configured():
    config1 = AuditConfig(orm="sqlalchemy", dsn="sqlite+aiosqlite:///:memory:")
    configure(config1)

    # Same config should be no-op
    configure(config1)

    # Different config should raise error
    config2 = AuditConfig(orm="sqlalchemy", dsn="sqlite+aiosqlite:///another.db")
    with pytest.raises(AuditAlreadyConfiguredError):
        configure(config2)
