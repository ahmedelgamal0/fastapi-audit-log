from fastapi import FastAPI

from fastapi_audit_log import (
    AuditConfig,
    AuditMiddleware,
    add_audit_log_routes,
    create_audit_lifespan,
    set_audit_action,
    set_audit_extra,
    set_audit_resource,
)

# SQLite for simplicity, but can use Postgres with "postgresql+asyncpg://..."
DATABASE_URL = "sqlite+aiosqlite:///audit_logs.db"

# 1. SQLAlchemy storage configuration
config = AuditConfig(
    orm="sqlalchemy",
    dsn=DATABASE_URL,
    table_name="audit_logs",
    auto_create_table=True,
    sqlalchemy_echo=False,
)

# 2. Use lifespan integration to manage connections
lifespan = create_audit_lifespan(config)
app = FastAPI(title="SQL Database Audit Example", lifespan=lifespan)

# 3. Add middleware
app.add_middleware(
    AuditMiddleware,
    skip_paths=["/health"],
)

# 4. Add the API routes
add_audit_log_routes(app, path="/admin/audit-logs", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/orders")
async def create_order(order_id: str, amount: float):
    set_audit_action("order.create")
    set_audit_resource("order", order_id)
    set_audit_extra("amount", amount)
    return {"order_id": order_id, "status": "processing"}


if __name__ == "__main__":
    import uvicorn

    print("Example running at http://localhost:8000")
    print("Audit logs available at http://localhost:8000/admin/audit-logs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
