from typing import Any

from tortoise import Tortoise

from ..db.tortoise_model import make_tortoise_model
from ..exceptions import AuditStorageConnectionError
from ..models import AuditEntry
from .base import AuditStorage


class TortoiseStorage(AuditStorage):
    def __init__(self, config: Any):
        self.config = config
        self.AuditLog = None

    async def startup(self) -> None:
        try:
            modules = {"audit": ["fastapi_audit_log.db.tortoise_model"]}
            if self.config.tortoise_modules:
                modules.update(self.config.tortoise_modules)

            await Tortoise.init(db_url=self.config.dsn, modules=modules)
            self.AuditLog = make_tortoise_model(self.config.table_name)

            if self.config.auto_create_table:
                await Tortoise.generate_schemas(safe=True)
        except Exception as e:
            raise AuditStorageConnectionError(
                f"Failed to connect to Tortoise backend: {e}"
            ) from e

    async def shutdown(self) -> None:
        await Tortoise.close_connections()

    async def save(self, entry: AuditEntry) -> None:
        await self.AuditLog.create(**entry.model_dump())

    async def save_batch(self, entries: list[AuditEntry]) -> None:
        if not entries:
            return
        await self.AuditLog.bulk_create(
            [self.AuditLog(**e.model_dump()) for e in entries]
        )

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
        query = self.AuditLog.all().order_by("-timestamp")

        if method:
            query = query.filter(method=method)
        if path:
            query = query.filter(path=path)
        if status_code:
            query = query.filter(status_code=status_code)
        if user_id:
            query = query.filter(user_id=user_id)
        if action:
            query = query.filter(action=action)

        db_entries = await query.limit(limit).offset(offset)
        return [AuditEntry.model_validate(e.__dict__) for e in db_entries]
