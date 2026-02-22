import uuid
from datetime import datetime

from sqlmodel import Field, SQLModel


def make_sqlmodel_table(table_name: str) -> type[SQLModel]:
    """Dynamically create the SQLModel ORM model class with the given table name."""

    class AuditLog(SQLModel, table=True):
        """SQLModel ORM model for audit logs, with dynamic table name set at runtime."""  # noqa: E501

        __tablename__ = table_name
        id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
        timestamp: datetime
        user_id: str | None = Field(default=None, index=True)
        username: str | None = None
        ip_address: str | None = None
        user_agent: str | None = None
        method: str
        path: str = Field(index=True)
        query_params: str | None = None  # JSON-serialized
        status_code: int | None = Field(default=None, index=True)
        request_body: str | None = None  # JSON-serialized
        response_body: str | None = None  # JSON-serialized
        duration_ms: float | None = None
        action: str | None = Field(default=None, index=True)
        resource_type: str | None = Field(default=None, index=True)
        resource_id: str | None = Field(default=None, index=True)
        extra: str | None = None  # JSON-serialized
        error: str | None = None

    return AuditLog
