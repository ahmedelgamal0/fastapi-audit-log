from typing import Any

from fastapi import Depends

from .context import get_current_audit_entry
from .models import AuditEntry


def audit_logger() -> Any:
    """
    Returns a FastAPI dependency that provides the current audit entry.
    """

    async def dependency() -> AuditEntry | None:
        return get_current_audit_entry()

    return Depends(dependency)
