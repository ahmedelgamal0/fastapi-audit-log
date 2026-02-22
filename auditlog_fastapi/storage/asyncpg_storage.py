import json
from typing import Any

import asyncpg

from ..exceptions import AuditStorageConnectionError
from ..models import AuditEntry
from .base import AuditStorage


class AsyncpgStorage(AuditStorage):
    def __init__(self, config: Any):
        self.config = config
        self._pool = None

    async def startup(self) -> None:
        try:
            self._pool = await asyncpg.create_pool(
                self.config.dsn, min_size=2, max_size=self.config.sqlalchemy_pool_size
            )

            if self.config.auto_create_table:
                async with self._pool.acquire() as conn:
                    await conn.execute(f"""
                        CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                            id UUID PRIMARY KEY,
                            timestamp TIMESTAMPTZ NOT NULL,
                            user_id VARCHAR(255),
                            username VARCHAR(255),
                            ip_address VARCHAR(45),
                            user_agent VARCHAR(512),
                            method VARCHAR(10) NOT NULL,
                            path TEXT NOT NULL,
                            query_params JSONB,
                            status_code INTEGER,
                            request_body JSONB,
                            response_body JSONB,
                            duration_ms FLOAT,
                            action VARCHAR(255),
                            resource_type VARCHAR(255),
                            resource_id VARCHAR(255),
                            extra JSONB,
                            error TEXT
                        )
                    """)
                    await conn.execute(
                        f"CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_ts "
                        f"ON {self.config.table_name} (timestamp)"
                    )
                    await conn.execute(
                        f"CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_uid "
                        f"ON {self.config.table_name} (user_id)"
                    )
                    await conn.execute(
                        f"CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_path "
                        f"ON {self.config.table_name} (path)"
                    )
        except Exception as e:
            raise AuditStorageConnectionError(
                f"Failed to connect to asyncpg backend: {e}"
            ) from e

    async def shutdown(self) -> None:
        if self._pool:
            await self._pool.close()

    def _to_db_tuple(self, entry: AuditEntry) -> tuple:
        return (
            entry.id,
            entry.timestamp,
            entry.user_id,
            entry.username,
            entry.ip_address,
            entry.user_agent,
            entry.method,
            entry.path,
            json.dumps(entry.query_params) if entry.query_params else None,
            entry.status_code,
            json.dumps(entry.request_body) if entry.request_body else None,
            json.dumps(entry.response_body) if entry.response_body else None,
            entry.duration_ms,
            entry.action,
            entry.resource_type,
            entry.resource_id,
            json.dumps(entry.extra) if entry.extra else None,
            entry.error,
        )

    def _from_row(self, row: asyncpg.Record) -> AuditEntry:
        data = dict(row)
        for field in ["query_params", "request_body", "response_body", "extra"]:
            if isinstance(data.get(field), str):
                data[field] = json.loads(data[field])
        return AuditEntry.model_validate(data)

    async def save(self, entry: AuditEntry) -> None:
        sql = f"""
            INSERT INTO {self.config.table_name} (
                id, timestamp, user_id, username, ip_address, user_agent,
                method, path, query_params, status_code, request_body,
                response_body, duration_ms, action, resource_type,
                resource_id, extra, error
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                $10, $11, $12, $13, $14, $15, $16, $17, $18
            )
        """
        async with self._pool.acquire() as conn:
            await conn.execute(sql, *self._to_db_tuple(entry))

    async def save_batch(self, entries: list[AuditEntry]) -> None:
        if not entries:
            return
        sql = f"""
            INSERT INTO {self.config.table_name} (
                id, timestamp, user_id, username, ip_address, user_agent,
                method, path, query_params, status_code, request_body,
                response_body, duration_ms, action, resource_type,
                resource_id, extra, error
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9,
                $10, $11, $12, $13, $14, $15, $16, $17, $18
            )
        """
        async with self._pool.acquire() as conn:
            await conn.executemany(sql, [self._to_db_tuple(e) for e in entries])

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
        conditions = []
        params = []

        if method:
            params.append(method)
            conditions.append(f"method = ${len(params)}")
        if path:
            params.append(path)
            conditions.append(f"path = ${len(params)}")
        if status_code:
            params.append(status_code)
            conditions.append(f"status_code = ${len(params)}")
        if user_id:
            params.append(user_id)
            conditions.append(f"user_id = ${len(params)}")
        if action:
            params.append(action)
            conditions.append(f"action = ${len(params)}")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        sql = f"""
            SELECT * FROM {self.config.table_name}
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}
        """

        async with self._pool.acquire() as conn:
            rows = await conn.fetch(sql, *params, limit, offset)
            return [self._from_row(row) for row in rows]
