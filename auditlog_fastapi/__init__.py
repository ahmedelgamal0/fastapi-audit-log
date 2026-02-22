from contextlib import asynccontextmanager

from .config import AuditConfig, configure, get_storage
from .context import set_audit_action, set_audit_extra, set_audit_resource
from .middleware import AuditMiddleware
from .routes import add_audit_log_routes


def create_audit_lifespan(config: AuditConfig):
    storage = configure(config)

    @asynccontextmanager
    async def lifespan(app):
        # Store config in app for testing/access if needed
        if not hasattr(app, "extra"):
            app.extra = {}
        app.extra["audit_config"] = config

        await storage.startup()
        yield
        await storage.shutdown()

    return lifespan


__all__ = [
    "AuditConfig",
    "configure",
    "get_storage",
    "AuditMiddleware",
    "create_audit_lifespan",
    "set_audit_action",
    "set_audit_resource",
    "set_audit_extra",
    "add_audit_log_routes",
]
