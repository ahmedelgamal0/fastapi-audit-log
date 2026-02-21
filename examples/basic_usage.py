from fastapi import FastAPI

from fastapi_audit_log import (
    AuditConfig,
    AuditMiddleware,
    add_audit_log_routes,
    create_audit_lifespan,
)

# 1. Configure the audit log storage (SQLAlchemy + SQLite async)
config = AuditConfig(
    orm="sqlalchemy",
    dsn="sqlite+aiosqlite:///./audit.db",
    table_name="audit_logs",
    auto_create_table=True,
    mask_fields=["password", "api_key"],
)

# 2. Create the lifespan to manage storage startup/shutdown
lifespan = create_audit_lifespan(config)

app = FastAPI(title="Basic Audit Example", lifespan=lifespan)

# 3. Register the middleware
app.add_middleware(
    AuditMiddleware,
    log_request_body=True,
)

# 4. Automatically add filtering routes (GET /audit-logs)
add_audit_log_routes(app)


@app.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"item_id": item_id, "status": "active"}


@app.post("/login")
async def login(data: dict):
    return {"message": "Logged in successfully"}


if __name__ == "__main__":
    import uvicorn

    print("Example running at http://localhost:8000")
    print("Audit logs available at http://localhost:8000/audit-logs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
