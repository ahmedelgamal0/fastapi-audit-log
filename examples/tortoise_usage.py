from fastapi import FastAPI

from auditlog_fastapi import (
    AuditConfig,
    AuditMiddleware,
    add_audit_log_routes,
    create_audit_lifespan,
    set_audit_action,
)

# 1. Tortoise ORM storage configuration
config = AuditConfig(
    orm="tortoise",
    dsn="sqlite://audit_logs_tortoise.db",
    table_name="audit_logs",
    auto_create_table=True,
)

# 2. Use lifespan integration to manage connections
lifespan = create_audit_lifespan(config)
app = FastAPI(title="Tortoise ORM Audit Example", lifespan=lifespan)

# 3. Add middleware
app.add_middleware(
    AuditMiddleware,
    log_request_body=True,
)

# 4. Add the API routes
add_audit_log_routes(app)


@app.get("/")
async def root():
    return {"message": "Audit logs are being saved using Tortoise ORM"}


@app.post("/users")
async def create_user(username: str):
    set_audit_action("user.create")
    return {"status": "created", "username": username}


if __name__ == "__main__":
    import uvicorn

    print("Example running at http://localhost:8000")
    print("Audit logs available at http://localhost:8000/audit-logs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
