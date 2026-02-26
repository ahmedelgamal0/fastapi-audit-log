import urllib.parse

import pytest
from fastapi import FastAPI, Request
from httpx import AsyncClient

from auditlog_fastapi import get_storage
from auditlog_fastapi.filters import MASK_VALUE, mask_sensitive_fields


def test_mask_query_string():
    fields = ["password", "secret"]

    # Test simple query string
    qs = "username=user1&password=mysecret&other=val"
    masked = mask_sensitive_fields(qs, fields)
    # urlencode encodes * as %2A
    expected_masked = urllib.parse.quote(MASK_VALUE)
    assert f"password={expected_masked}" in masked
    assert "username=user1" in masked
    assert "other=val" in masked

    # Test single query parameter
    qs = "password=mysecret"
    masked = mask_sensitive_fields(qs, fields)
    assert masked == f"password={expected_masked}"

    # Test with special characters
    qs = "token=abc%3D123&secret=shh"
    masked = mask_sensitive_fields(qs, fields)
    assert f"secret={expected_masked}" in masked

    # Let's check default fields
    from auditlog_fastapi.filters import DEFAULT_SENSITIVE_FIELDS

    masked_default = mask_sensitive_fields(qs, DEFAULT_SENSITIVE_FIELDS)
    assert f"token={expected_masked}" in masked_default
    assert f"secret={expected_masked}" in masked_default


@pytest.mark.asyncio
async def test_user_capture_from_state(app: FastAPI, client: AsyncClient):
    @app.get("/test-user-state")
    async def route_with_user(request: Request):
        request.state.user = {"user_id": "state-id", "username": "state-user"}
        return {"ok": True}

    await client.get("/test-user-state")

    import asyncio

    await asyncio.sleep(0.1)

    storage = get_storage()
    entries = await storage.get_entries(limit=1)
    # Filter for our specific path to avoid interference from other tests if any
    entries = [e for e in entries if e.path == "/test-user-state"]
    assert len(entries) > 0
    entry = entries[0]
    assert entry.user_id == "state-id"
    assert entry.username == "state-user"


@pytest.mark.asyncio
async def test_user_capture_from_object(app: FastAPI, client: AsyncClient):
    class User:
        def __init__(self, id, name):
            self.id = id
            self.username = name

    @app.get("/test-user-obj")
    async def route_with_user_obj(request: Request):
        request.state.user = User("obj-id", "obj-user")
        return {"ok": True}

    await client.get("/test-user-obj")

    import asyncio

    await asyncio.sleep(0.1)

    storage = get_storage()
    entries = await storage.get_entries(limit=10)
    entries = [e for e in entries if e.path == "/test-user-obj"]
    assert len(entries) > 0
    entry = entries[0]
    assert entry.user_id == "obj-id"
    assert entry.username == "obj-user"
