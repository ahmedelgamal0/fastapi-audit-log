import uuid

from sqlalchemy import Column, DateTime, Float, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase


class AuditBase(DeclarativeBase):
    pass


def make_audit_table(table_name: str, use_jsonb: bool = False):
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

        id = Column(
            PG_UUID(as_uuid=True) if use_jsonb else String(36),
            primary_key=True,
            default=uuid.uuid4,
        )
        timestamp = Column(DateTime(timezone=True), nullable=False)
        user_id = Column(String(255), nullable=True)
        username = Column(String(255), nullable=True)
        ip_address = Column(String(45), nullable=True)
        user_agent = Column(String(512), nullable=True)
        method = Column(String(10), nullable=False)
        path = Column(String(2048), nullable=False)
        query_params = Column(JSONB if use_jsonb else Text, nullable=True)
        status_code = Column(Integer, nullable=True)
        request_body = Column(JSONB if use_jsonb else Text, nullable=True)
        response_body = Column(JSONB if use_jsonb else Text, nullable=True)
        duration_ms = Column(Float, nullable=True)
        action = Column(String(255), nullable=True)
        resource_type = Column(String(255), nullable=True)
        resource_id = Column(String(255), nullable=True)
        extra = Column(JSONB if use_jsonb else Text, nullable=True)
        error = Column(Text, nullable=True)

    # Override class name
    AuditLog.__name__ = class_name

    return AuditLog
