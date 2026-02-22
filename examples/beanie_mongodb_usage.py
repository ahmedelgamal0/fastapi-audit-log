from fastapi import FastAPI

from auditlog_fastapi import (
    AuditConfig,
    AuditMiddleware,
    add_audit_log_routes,
    create_audit_lifespan,
    set_audit_action,
)

# 1. MongoDB (Beanie) storage configuration
config = AuditConfig(
    orm="beanie",
    dsn="mongodb://localhost:27017",
    mongodb_database="audit_db",
    table_name="audit_logs",
)

# 2. Use lifespan integration to manage connections
lifespan = create_audit_lifespan(config)
app = FastAPI(title="MongoDB Audit Example", lifespan=lifespan)

# 3. Add middleware
app.add_middleware(
    AuditMiddleware,
    log_request_body=True,
    skip_path_prefixes=["/docs", "/openapi.json"],
)

# 4. Add the API routes
add_audit_log_routes(app)


@app.get("/")
async def index():
    set_audit_action("index.access")
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    print("Example running at http://localhost:8000")
    print("Audit logs available at http://localhost:8000/audit-logs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
