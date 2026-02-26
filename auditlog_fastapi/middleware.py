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

    def _default_on_error(
        self,
        exc: Exception,
        entry: AuditEntry,  # noqa: ARG002
    ) -> None:
        print(f"Audit log storage failure: {exc}", file=sys.stderr)  # noqa: T201

    async def _resolve_user(self, request: Request) -> dict[str, Any]:
        """
        Try all known patterns to extract user identity from the request.
        Priority order:
          1. Caller-provided get_user callable (most explicit)
          2. Starlette's built-in AuthenticationMiddleware (request.scope['user'])
          3. Common convention: request.state.user set by app middleware
        Returns a dict with 'user_id' and/or 'username', empty dict on failure.
        """
        # Pattern 1: caller-provided async callable
        if self.get_user:
            try:
                return await self.get_user(request)
            except Exception as e:
                print(f"[audit] get_user() raised: {e}", file=sys.stderr)  # noqa: T201

        # Pattern 2: Starlette's built-in AuthenticationMiddleware
        # Direct scope check avoids AssertionError if middleware is missing
        starlette_user = request.scope.get("user")
        if starlette_user and getattr(starlette_user, "is_authenticated", False):
            return {
                "user_id": str(getattr(starlette_user, "identity", "") or ""),
                "username": getattr(starlette_user, "display_name", None),
            }

        # Pattern 3: request.state.user set by app middleware or dependency
        state_user = getattr(request.state, "user", None)
        if state_user:
            if isinstance(state_user, dict):
                return state_user

            # Object — try common attribute names
            user_id = None
            for attr in ("user_id", "id", "sub"):
                val = getattr(state_user, attr, None)
                if val is not None:
                    user_id = str(val)
                    break

            username = None
            for attr in ("username", "email", "name"):
                val = getattr(state_user, attr, None)
                if val is not None:
                    username = str(val)
                    break

            if user_id or username:
                return {"user_id": user_id, "username": username}

        return {}

    def _apply_user(self, entry: AuditEntry, user_info: dict[str, Any]) -> None:
        """Apply user info to entry, never overwriting an already-set value."""
        if not entry.user_id and user_info.get("user_id"):
            entry.user_id = str(user_info["user_id"])
        if not entry.username and user_info.get("username"):
            entry.username = str(user_info["username"])

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if self._should_skip(request):
            return await call_next(request)

        start_time = time.perf_counter()

        entry = AuditEntry(
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )

        # Attempt 1: capture user BEFORE call_next
        # Works when auth middleware runs before AuditMiddleware
        self._apply_user(entry, await self._resolve_user(request))

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
            _current_entry.reset(token)
            await self._safe_save(entry)
            raise

        _current_entry.reset(token)

        # Attempt 2: capture user AFTER call_next
        # Works when auth is handled inside route dependencies that set request.state.user  # noqa: E501
        # _apply_user will not overwrite values already set in Attempt 1
        self._apply_user(entry, await self._resolve_user(request))

        entry.duration_ms = (time.perf_counter() - start_time) * 1000
        entry.status_code = response.status_code

        background_tasks = BackgroundTasks()
        background_tasks.add_task(self._safe_save, entry)
        response.background = background_tasks

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

            # Reconstruct the receive channel so the route handler
            # can still read the body after we consumed it
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
