from abc import ABC, abstractmethod

from ..models import AuditEntry


class AuditStorage(ABC):
    @abstractmethod
    async def save(self, entry: AuditEntry) -> None: ...

    @abstractmethod
    async def save_batch(self, entries: list[AuditEntry]) -> None: ...

    @abstractmethod
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
        """Retrieve audit entries with filtering."""
        ...

    @abstractmethod
    async def startup(self) -> None:
        """
        Called once at app startup.
        - Create engine/session/connection pool
        - Run CREATE TABLE IF NOT EXISTS if auto_create_table=True
        - Validate connectivity (run a simple SELECT 1)
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Called once at app shutdown.
        - Flush any pending batch entries
        - Close connection pool / engine
        """
        ...
