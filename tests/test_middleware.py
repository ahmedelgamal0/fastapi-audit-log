import asyncio

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select

from auditlog_fastapi import (
    get_storage,
    set_audit_action,
    set_audit_extra,
    set_audit_resource,
)
from auditlog_fastapi.filters import MASK_VALUE


@pytest.mark.asyncio
async def test_middleware_captures_fields(client: AsyncClient, app: FastAPI):
    response = await client.get("/hello")
    assert response.status_code == 200

    # Wait for background task
    await asyncio.sleep(0.1)

    storage = get_storage()
    async with storage.SessionLocal() as session:
        result = await session.execute(select(storage.AuditLog))
        entries = result.scalars().all()
        assert len(entries) == 1
        entry = entries[0]
        assert entry.method == "GET"
        assert entry.path == "/hello"
        assert entry.status_code == 200
        assert entry.duration_ms > 0


@pytest.mark.asyncio
async def test_middleware_captures_body(client: AsyncClient, app: FastAPI):
    data = {"name": "test-item", "password": "dont-log-me"}
    response = await client.post("/echo", json=data)
    assert response.status_code == 200

    await asyncio.sleep(0.1)

    storage = get_storage()
    async with storage.SessionLocal() as session:
        # Get the latest entry
        result = await session.execute(
            select(storage.AuditLog).order_by(storage.AuditLog.timestamp.desc())
        )
        entry = result.scalars().first()

        import json

        request_body = json.loads(entry.request_body)
        assert request_body["name"] == "test-item"
        assert request_body["password"] == MASK_VALUE


@pytest.mark.asyncio
async def test_middleware_captures_error(client: AsyncClient, app: FastAPI):
    with pytest.raises(ValueError):
        await client.get("/error")

    await asyncio.sleep(0.1)

    storage = get_storage()
    async with storage.SessionLocal() as session:
        result = await session.execute(
            select(storage.AuditLog).where(storage.AuditLog.path == "/error")
        )
        entry = result.scalars().first()
        assert "Something went wrong" in entry.error


@pytest.mark.asyncio
async def test_context_helpers(client: AsyncClient, app: FastAPI):
    @app.get("/context-test")
    async def context_route():
        set_audit_action("test.action")
        set_audit_resource("user", "123")
        set_audit_extra("foo", "bar")
        return {"status": "ok"}

    await client.get("/context-test")
    await asyncio.sleep(0.1)

    storage = get_storage()
    async with storage.SessionLocal() as session:
        result = await session.execute(
            select(storage.AuditLog).where(storage.AuditLog.path == "/context-test")
        )
        entry = result.scalars().first()
        assert entry.action == "test.action"
        assert entry.resource_type == "user"
        assert entry.resource_id == "123"

        import json

        extra = json.loads(entry.extra)
        assert extra["foo"] == "bar"
