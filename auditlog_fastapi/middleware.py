import json
import sys
import time
from collections.abc import Awaitable, Callable
from typing import Any, cast

from fastapi import Request, Response
from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from .config import get_storage
from .context import _current_entry
from .filters import DEFAULT_SENSITIVE_FIELDS, mask_sensitive_fields
from .models import AuditEntry
from .storage.base import AuditStorage


class AuditMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Any,
        storage: AuditStorage | None = None,
        get_user: Callable[[Request], Awaitable[dict[str, Any]]] | None = None,
        skip_paths: list[str] | None = None,
        skip_path_prefixes: list[str] | None = None,
        skip_methods: list[str] | None = None,
        log_request_body: bool = False,
        log_response_body: bool = False,
        max_body_size: int = 10_000,
        mask_fields: list[str] | None = None,
        on_error: Callable[[Exception, AuditEntry], None] | None = None,
    ):
        super().__init__(app)
        self._explicit_storage = storage
        self.get_user = get_user
        self.skip_paths = skip_paths or []
        self.skip_path_prefixes = skip_path_prefixes or []
        self.skip_methods = skip_methods or []
        self.log_request_body = log_request_body
        self.log_response_body = log_response_body
        self.max_body_size = max_body_size
        self.mask_fields = mask_fields or DEFAULT_SENSITIVE_FIELDS
        self.on_error = on_error

    @property
    def storage(self) -> AuditStorage:
        if self._explicit_storage:
            return self._explicit_storage
        return get_storage()

    def _get_on_error(self) -> Callable[[Exception, AuditEntry], None]:
        if self.on_error:
            return self.on_error

        # Try to get from config if available
        try:
            from .config import _registry

            config = _registry.get("config")
            if (
                config
                and hasattr(config, "on_storage_error")
                and config.on_storage_error
            ):
                return cast(
                    Callable[[Exception, AuditEntry], None], config.on_storage_error
                )
        except Exception:
            pass

        return self._default_on_error

    def _default_on_error(self, exc: Exception, entry: AuditEntry) -> None:  # noqa: ARG002
        print(f"Audit log storage failure: {exc}", file=sys.stderr)  # noqa: T201

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if self._should_skip(request):
            return await call_next(request)

        start_time = time.perf_counter()

        # Prepare entry
        entry = AuditEntry(
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Get user info if provided
        if self.get_user:
            try:
                user_info = await self.get_user(request)
                if user_info.get("user_id"):
                    entry.user_id = str(user_info.get("user_id"))
                entry.username = user_info.get("username")
            except Exception:
                pass

        # Request body
        if self.log_request_body:
            body = await self._get_request_body(request)
            if body:
                entry.request_body = mask_sensitive_fields(body, self.mask_fields)

        token = _current_entry.set(entry)

        response: Response | None = None

        try:
            response = await call_next(request)
        except Exception as e:
            entry.error = str(e)
            entry.duration_ms = (time.perf_counter() - start_time) * 1000
            # If we don't have a response, we still want to save the entry
            await self._safe_save(entry)
            raise e from None
        finally:
            if not entry.error:  # If no error, handle normally in finally
                duration = (time.perf_counter() - start_time) * 1000
                entry.duration_ms = duration
                if response:
                    entry.status_code = response.status_code

                # Use BackgroundTasks to save
                background_tasks = BackgroundTasks()
                background_tasks.add_task(self._safe_save, entry)

                if response:
                    response.background = background_tasks

            _current_entry.reset(token)

        assert response is not None
        return response

    async def _safe_save(self, entry: AuditEntry) -> None:
        try:
            await self.storage.save(entry)
        except Exception as e:
            on_error = self._get_on_error()
            on_error(e, entry)

    def _should_skip(self, request: Request) -> bool:
        if request.method in self.skip_methods:
            return True
        if request.url.path in self.skip_paths:
            return True
        if any(request.url.path.startswith(p) for p in self.skip_path_prefixes):
            return True
        return False

    async def _get_request_body(self, request: Request) -> Any:
        try:
            body_bytes = await request.body()
            if not body_bytes:
                return None

            # Reconstruct request for next middleware/route
            # This is a bit of a hack for BaseHTTPMiddleware
            async def receive() -> dict[str, Any]:
                return {"type": "http.request", "body": body_bytes}

            request._receive = receive

            if len(body_bytes) > self.max_body_size:
                return f"<Truncated: {len(body_bytes)} bytes>"

            try:
                return json.loads(body_bytes)
            except json.JSONDecodeError:
                return body_bytes.decode(errors="replace")
        except Exception:
            return None
