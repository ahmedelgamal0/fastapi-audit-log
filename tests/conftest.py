import asyncio
from collections.abc import AsyncGenerator
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastapi_audit_log import (
    AuditConfig,
    AuditMiddleware,
    create_audit_lifespan,
)
from fastapi_audit_log.config import _registry


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def app() -> FastAPI:
    _registry.clear()
    config = AuditConfig(
        orm="sqlalchemy",
        dsn="sqlite+aiosqlite:///:memory:",
        table_name="test_audit_logs",
        auto_create_table=True,
    )

    app = FastAPI(lifespan=create_audit_lifespan(config))

    app.add_middleware(AuditMiddleware, log_request_body=True)

    @app.get("/hello")
    async def hello():
        return {"message": "world"}

    @app.post("/echo")
    async def echo(data: dict):
        return data

    @app.get("/error")
    async def error_route():
        raise ValueError("Something went wrong")

    return app


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# Helper for manual lifespan management in tests
@pytest_asyncio.fixture(autouse=True)
async def manage_lifespan(app: FastAPI):
    # If storage is already configured, it's likely from the 'app'
    # fixture's 'configure()' call inside 'create_audit_lifespan'
    # But for ASGITransport, we must explicitly enter the lifespan.
    if "config" not in _registry:
        yield
        return

    config = _registry["config"]
    # Ensure each test gets a unique table name if using same memory DB
    unique_table = f"test_logs_{uuid4().hex[:8]}"
    config.table_name = unique_table

    async with create_audit_lifespan(config)(app):
        yield
