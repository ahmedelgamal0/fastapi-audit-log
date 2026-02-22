import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class AuditBase(DeclarativeBase):
    pass


def make_audit_table(table_name: str, use_jsonb: bool = False) -> type[AuditBase]:
    """
    Dynamically create the ORM model class with the given table name.
    use_jsonb=True for PostgreSQL (JSONB), False for MySQL/SQLite
    (TEXT + JSON serialization).
    """
    # Use a unique class name to avoid SQLAlchemy warnings about re-defining models
    class_name = f"AuditLog_{uuid.uuid4().hex}"
    suffix = uuid.uuid4().hex[:8]

    class AuditLog(AuditBase):
        __tablename__ = table_name
        __table_args__ = (
            Index(f"ix_{table_name}_timestamp_{suffix}", "timestamp"),
            Index(f"ix_{table_name}_user_id_{suffix}", "user_id"),
            Index(f"ix_{table_name}_path_{suffix}", "path"),
            Index(f"ix_{table_name}_status_code_{suffix}", "status_code"),
            Index(f"ix_{table_name}_action_{suffix}", "action"),
            Index(f"ix_{table_name}_resource_type_{suffix}", "resource_type"),
            Index(f"ix_{table_name}_resource_id_{suffix}", "resource_id"),
            {"extend_existing": True},
        )

        id: Mapped[uuid.UUID] = mapped_column(
            PG_UUID(as_uuid=True) if use_jsonb else String(36),
            primary_key=True,
            default=uuid.uuid4,
        )
        timestamp: Mapped[datetime] = mapped_column(
            DateTime(timezone=True), nullable=False
        )
        user_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
        username: Mapped[str | None] = mapped_column(String(255), nullable=True)
        ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
        user_agent: Mapped[str | None] = mapped_column(String(512), nullable=True)
        method: Mapped[str] = mapped_column(String(10), nullable=False)
        path: Mapped[str] = mapped_column(String(2048), nullable=False)
        query_params: Mapped[Any | None] = mapped_column(
            JSONB if use_jsonb else Text, nullable=True
        )
        status_code: Mapped[int | None] = mapped_column(Integer, nullable=True)
        request_body: Mapped[Any | None] = mapped_column(
            JSONB if use_jsonb else Text, nullable=True
        )
        response_body: Mapped[Any | None] = mapped_column(
            JSONB if use_jsonb else Text, nullable=True
        )
        duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
        action: Mapped[str | None] = mapped_column(String(255), nullable=True)
        resource_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
        resource_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
        extra: Mapped[Any | None] = mapped_column(
            JSONB if use_jsonb else Text, nullable=True
        )
        error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Override class name
    AuditLog.__name__ = class_name

    return AuditLog
