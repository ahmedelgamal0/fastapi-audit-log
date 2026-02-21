from contextvars import ContextVar
from typing import Any

from .models import AuditEntry

_current_entry: ContextVar[AuditEntry | None] = ContextVar("audit_entry", default=None)


def get_current_audit_entry() -> AuditEntry | None:
    """Returns the current audit entry from the context."""
    return _current_entry.get()


def set_audit_action(action: str) -> None:
    """Sets the action field on the current audit entry."""
    entry = get_current_audit_entry()
    if entry:
        entry.action = action


def set_audit_resource(resource_type: str, resource_id: str) -> None:
    """Sets resource_type and resource_id fields on the current audit entry."""
    entry = get_current_audit_entry()
    if entry:
        entry.resource_type = resource_type
        entry.resource_id = resource_id


def set_audit_extra(key: str, value: Any) -> None:
    """Adds a key-value pair to the extra field of the current audit entry."""
    entry = get_current_audit_entry()
    if entry:
        entry.extra[key] = value
