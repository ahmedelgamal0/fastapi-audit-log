from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import func, select

from auditlog_fastapi.config import AuditConfig
from auditlog_fastapi.models import AuditEntry
from auditlog_fastapi.storage.sqlalchemy_storage import SQLAlchemyStorage


@pytest.fixture
async def sqlalchemy_storage():
    config = AuditConfig(
        orm="sqlalchemy",
        dsn="sqlite+aiosqlite:///:memory:",
        table_name="test_audit_logs",
        auto_create_table=True,
    )
    storage = SQLAlchemyStorage(config)
    await storage.startup()
    yield storage
    await storage.shutdown()


async def test_sqlalchemy_save(sqlalchemy_storage):
    entry = AuditEntry(
        id=uuid4(),
        timestamp=datetime.now(UTC),
        method="GET",
        path="/test",
        query_params={"a": "1"},
        status_code=200,
        duration_ms=10.5,
    )

    await sqlalchemy_storage.save(entry)

    # Verify in DB
    async with sqlalchemy_storage.SessionLocal() as session:
        result = await session.execute(select(sqlalchemy_storage.AuditLog))
        db_entry = result.scalar_one()
        assert db_entry.path == "/test"
        assert db_entry.method == "GET"
        assert db_entry.status_code == 200
        # Check JSON round-trip for SQLite (stored as string)
        import json

        assert json.loads(db_entry.query_params) == {"a": "1"}


async def test_sqlalchemy_save_batch(sqlalchemy_storage):
    entries = [
        AuditEntry(
            id=uuid4(),
            timestamp=datetime.now(UTC),
            method="POST",
            path=f"/test/{i}",
            duration_ms=1.0,
        )
        for i in range(5)
    ]

    await sqlalchemy_storage.save_batch(entries)

    # Verify in DB
    async with sqlalchemy_storage.SessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(sqlalchemy_storage.AuditLog)
        )
        count = result.scalar()
        assert count == 5
