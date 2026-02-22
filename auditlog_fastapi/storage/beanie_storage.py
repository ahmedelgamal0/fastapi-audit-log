from typing import Any

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from ..db.beanie_document import AuditLogDocument
from ..exceptions import AuditStorageConnectionError
from ..models import AuditEntry
from .base import AuditStorage


class BeanieStorage(AuditStorage):
    def __init__(self, config: Any):
        self.config = config
        self.client = None

    async def startup(self) -> None:
        try:
            self.client = AsyncIOMotorClient(self.config.dsn)
            # Override collection name
            AuditLogDocument.Settings.name = self.config.table_name

            await init_beanie(
                database=self.client[self.config.mongodb_database],
                document_models=[AuditLogDocument],
            )
        except Exception as e:
            raise AuditStorageConnectionError(
                f"Failed to connect to Beanie backend: {e}"
            ) from e

    async def shutdown(self) -> None:
        if self.client:
            self.client.close()

    async def save(self, entry: AuditEntry) -> None:
        doc = AuditLogDocument(**entry.model_dump())
        await doc.insert()

    async def save_batch(self, entries: list[AuditEntry]) -> None:
        if not entries:
            return
        docs = [AuditLogDocument(**e.model_dump()) for e in entries]
        await AuditLogDocument.insert_many(docs)

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
        query = AuditLogDocument.find_all()

        if method:
            query = query.find(AuditLogDocument.method == method)
        if path:
            query = query.find(AuditLogDocument.path == path)
        if status_code:
            query = query.find(AuditLogDocument.status_code == status_code)
        if user_id:
            query = query.find(AuditLogDocument.user_id == user_id)
        if action:
            query = query.find(AuditLogDocument.action == action)

        docs = await query.sort("-timestamp").skip(offset).limit(limit).to_list()
        return [AuditEntry.model_validate(doc.model_dump()) for doc in docs]
