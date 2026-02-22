import uuid
from datetime import datetime
from typing import Any

from beanie import Document
from pydantic import Field


class AuditLogDocument(Document):
    """Beanie Document model for audit logs, with dynamic collection name set at runtime."""  # noqa: E501

    id: uuid.UUID = Field(default_factory=uuid.uuid4)  # type: ignore[assignment]
    timestamp: datetime
    user_id: str | None = None
    username: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    method: str
    path: str
    query_params: dict[str, Any] | None = None
    status_code: int | None = None
    request_body: dict[str, Any] | None = None
    response_body: dict[str, Any] | None = None
    duration_ms: float | None = None
    action: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    extra: dict[str, Any] | None = None
    error: str | None = None

    class Settings:
        """Settings for Beanie Document, with collection name set dynamically at runtime."""  # noqa: E501

        name = "audit_logs"  # overridden by config at runtime
        indexes = [
            "timestamp",
            "user_id",
            "path",
            "status_code",
            "action",
            "resource_type",
            "resource_id",
        ]
