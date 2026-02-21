import contextlib
import json
from typing import Any

from sqlalchemy import insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..db.sqlalchemy_table import make_audit_table
from ..exceptions import AuditStorageConnectionError
from ..models import AuditEntry
from .base import AuditStorage


class SQLAlchemyStorage(AuditStorage):
    def __init__(self, config: Any):
        self.config = config

        # SQLite doesn't support pool_size, max_overflow, pool_timeout in the same way
        engine_kwargs = {
            "echo": config.sqlalchemy_echo,
        }

        if not config.dsn.startswith("sqlite"):
            engine_kwargs.update(
                {
                    "pool_size": config.sqlalchemy_pool_size,
                    "max_overflow": config.sqlalchemy_max_overflow,
                    "pool_timeout": config.sqlalchemy_pool_timeout,
                }
            )

        self.engine = create_async_engine(config.dsn, **engine_kwargs)
        self.SessionLocal = async_sessionmaker(
            bind=self.engine, expire_on_commit=False, class_=AsyncSession
        )
        self.AuditLog = None
        self._use_jsonb = False
        self._is_sqlite = config.dsn.startswith("sqlite")

    async def startup(self) -> None:
        try:
            async with self.engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
                dialect = self.engine.dialect.name
                self._use_jsonb = dialect == "postgresql"

            self.AuditLog = make_audit_table(
                self.config.table_name, use_jsonb=self._use_jsonb
            )

            if self.config.auto_create_table:
                async with self.engine.begin() as conn:
                    # Use the specific mapper for this storage instance
                    await conn.run_sync(self.AuditLog.metadata.create_all)
        except Exception as e:
            raise AuditStorageConnectionError(
                f"Failed to connect to SQLAlchemy backend: {e}"
            ) from e

    async def shutdown(self) -> None:
        await self.engine.dispose()

    def _to_db_dict(self, entry: AuditEntry) -> dict:
        data = entry.model_dump()

        # Handle SQLite-specific serialization
        if self._is_sqlite:
            data["id"] = str(data["id"])
            if data["timestamp"] and hasattr(data["timestamp"], "isoformat"):
                data["timestamp"] = data["timestamp"]

        if not self._use_jsonb:
            for field in ["query_params", "request_body", "response_body", "extra"]:
                if data.get(field) is not None:
                    data[field] = json.dumps(data[field])
        return data

    def _from_db_model(self, db_entry: Any) -> AuditEntry:
        data = {c.name: getattr(db_entry, c.name) for c in db_entry.__table__.columns}

        if not self._use_jsonb:
            for field in ["query_params", "request_body", "response_body", "extra"]:
                if isinstance(data.get(field), str):
                    with contextlib.suppress(Exception):
                        data[field] = json.loads(data[field])
        return AuditEntry.model_validate(data)

    async def save(self, entry: AuditEntry) -> None:
        async with self.SessionLocal() as session:
            async with session.begin():
                db_entry = self.AuditLog(**self._to_db_dict(entry))
                session.add(db_entry)
            await session.commit()

    async def save_batch(self, entries: list[AuditEntry]) -> None:
        if not entries:
            return
        async with self.SessionLocal() as session:
            async with session.begin():
                await session.execute(
                    insert(self.AuditLog), [self._to_db_dict(e) for e in entries]
                )
            await session.commit()

    async def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        method: str | None = None,
        path: str | None = None,
        status_code: int | None = None,
        user_id: str | None = None,
        action: str | None = None,
    ) -> list[AuditEntry]:
        async with self.SessionLocal() as session:
            stmt = select(self.AuditLog).order_by(self.AuditLog.timestamp.desc())

            if method:
                stmt = stmt.where(self.AuditLog.method == method)
            if path:
                stmt = stmt.where(self.AuditLog.path == path)
            if status_code:
                stmt = stmt.where(self.AuditLog.status_code == status_code)
            if user_id:
                stmt = stmt.where(self.AuditLog.user_id == user_id)
            if action:
                stmt = stmt.where(self.AuditLog.action == action)

            result = await session.execute(stmt.limit(limit).offset(offset))
            db_entries = result.scalars().all()
            return [self._from_db_model(e) for e in db_entries]

    @property
    def metadata(self):
        return self.AuditLog.metadata
