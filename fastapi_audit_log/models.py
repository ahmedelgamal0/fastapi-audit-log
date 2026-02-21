from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class AuditEntry(BaseModel):
    """
    Model representing a single audit log entry.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(
        default_factory=uuid4, examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        examples=["2024-03-21T12:34:56Z"],
    )

    user_id: str | None = Field(None, examples=["user_123"])
    username: str | None = Field(None, examples=["johndoe"])
    ip_address: str | None = Field(None, examples=["192.168.1.1"])
    user_agent: str | None = Field(
        None, examples=["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)..."]
    )
    method: str = Field(..., examples=["POST", "GET", "PUT", "DELETE"])
    path: str = Field(..., examples=["/api/v1/users", "/login"])
    query_params: dict[str, Any] = Field(
        default_factory=dict, examples=[{"q": "fastapi", "page": 1}]
    )
    status_code: int | None = Field(None, examples=[200, 201, 400, 401, 500])
    request_body: Any | None = Field(
        None, examples=[{"username": "johndoe", "password": "***REDACTED***"}]
    )
    response_body: Any | None = Field(
        None, examples=[{"status": "success", "id": "user_123"}]
    )
    duration_ms: float = Field(0.0, examples=[12.5, 45.2])
    action: str | None = Field(None, examples=["user.create", "order.place"])
    resource_type: str | None = Field(None, examples=["user", "order"])
    resource_id: str | None = Field(None, examples=["123", "order_abc"])
    extra: dict[str, Any] = Field(
        default_factory=dict, examples=[{"browser": "Chrome", "version": "122.0"}]
    )
    error: str | None = Field(None, examples=["ValueError: Invalid input"])
