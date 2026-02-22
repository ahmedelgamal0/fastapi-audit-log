from fastapi import APIRouter, FastAPI, Query

from .config import get_storage


def add_audit_log_routes(
    app: FastAPI,
    path: str = "/audit-logs",
    tags: list[str] | None = None,
) -> None:
    """
    Automatically adds a GET route to the FastAPI application for retrieving
    and filtering audit logs.
    """
    router = APIRouter(tags=tags or ["Audit Logs"])

    @router.get(path)
    async def get_audit_logs(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        method: str | None = Query(None, description="Filter by HTTP method"),
        path: str | None = Query(None, description="Filter by request path"),
        status_code: int | None = Query(None, description="Filter by status code"),
        user_id: str | None = Query(None, description="Filter by user ID"),
        action: str | None = Query(None, description="Filter by action name"),
    ):
        storage = get_storage()
        entries = await storage.get_entries(
            limit=limit,
            offset=offset,
            method=method,
            path=path,
            status_code=status_code,
            user_id=user_id,
            action=action,
        )
        return [entry.model_dump() for entry in entries]

    app.include_router(router)
