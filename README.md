# auditlog-fastapi

Production-grade, reusable audit logging for FastAPI applications.

## Features

- **Multi-ORM Support:** SQLAlchemy 2 (async), Tortoise ORM, SQLModel, Beanie (MongoDB), and raw asyncpg.
- **Flexible Storage:** PostgreSQL, MySQL, MariaDB, SQLite, and MongoDB.
- **Explicit Configuration:** Clean API with `AuditConfig` and `configure()`.
- **Middleware Integration:** Capture request/response data automatically.
- **PII Masking:** Redact sensitive fields from logs.
- **Context Helpers:** Enrich audit logs from route handlers.
- **Lifespan Integration:** Automatic startup/shutdown of database connections.
- **Async & Non-blocking:** Built with performance and safety in mind.

## Installation

```bash
# Basic install
pip install auditlog-fastapi

# With SQLAlchemy support (Postgres, MySQL, SQLite)
pip install auditlog-fastapi[sqlalchemy]

# With Tortoise ORM support
pip install auditlog-fastapi[tortoise]

# With SQLModel support
pip install auditlog-fastapi[sqlmodel]

# With MongoDB (Beanie) support
pip install auditlog-fastapi[mongodb]

# With raw asyncpg (PostgreSQL only) support
pip install auditlog-fastapi[asyncpg]

# Everything
pip install auditlog-fastapi[all]
```

## Quick Start (SQLAlchemy + SQLite)

```python
from fastapi import FastAPI
from fastapi_audit_log import AuditMiddleware, AuditConfig, create_audit_lifespan

# 1. Configure the audit log
config = AuditConfig(
    orm="sqlalchemy",
    dsn="sqlite+aiosqlite:///./audit.db",
    table_name="audit_logs",
    auto_create_table=True,
)

# 2. Create lifespan handler
app = FastAPI(lifespan=create_audit_lifespan(config))

# 3. Add middleware
app.add_middleware(
    AuditMiddleware,
    log_request_body=True
)

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## User Configuration Guide

### SQLAlchemy + PostgreSQL

```python
config = AuditConfig(
    orm="sqlalchemy",
    dsn="postgresql+asyncpg://user:pass@localhost:5432/mydb",
    table_name="audit_logs",
    auto_create_table=True,
    sqlalchemy_pool_size=10,
    mask_fields=["password", "token"],
)
```

### SQLAlchemy + MySQL

```python
config = AuditConfig(
    orm="sqlalchemy",
    dsn="mysql+aiomysql://user:pass@localhost:3306/mydb",
    auto_create_table=True,
)
```

### Tortoise ORM + PostgreSQL

```python
config = AuditConfig(
    orm="tortoise",
    dsn="postgres://user:pass@localhost:5432/mydb",
    auto_create_table=True,
)
```

### MongoDB via Beanie

```python
config = AuditConfig(
    orm="beanie",
    dsn="mongodb://localhost:27017",
    mongodb_database="myapp",
    table_name="audit_logs",   # becomes collection name
)
```

### Raw asyncpg (PostgreSQL, maximum performance)

```python
config = AuditConfig(
    orm="asyncpg",
    dsn="postgresql://user:pass@localhost:5432/mydb",
    batch_size=200,
)
```

### Using with Alembic (SQLAlchemy only)

```python
# In alembic/env.py — include audit table in your migrations
from fastapi_audit_log.db.sqlalchemy_table import AuditBase
target_metadata = [YourBase.metadata, AuditBase.metadata]
```

## Enriching Logs from Routes

```python
from fastapi_audit_log import set_audit_action, set_audit_resource, set_audit_extra

@app.post("/items")
async def create_item(item_id: str):
    set_audit_action("item.create")
    set_audit_resource("item", item_id)
    set_audit_extra("metadata", {"source": "admin_panel"})
    return {"status": "ok"}
```

## Retrieving Audit Logs

`fastapi-audit-log` provides a built-in helper to add a route for querying and filtering your audit logs.

```python
from fastapi import FastAPI
from fastapi_audit_log import add_audit_log_routes

app = FastAPI(...)

# Register the GET /audit-logs route
add_audit_log_routes(
    app,
    path="/audit-logs",      # default
    tags=["Audit Logs"]      # optional tags for OpenAPI
)
```

### Filtering and Pagination

The added route supports several query parameters:

*   **Pagination:** `limit` (default 100, max 1000) and `offset` (default 0).
*   **Filters:** `method`, `path`, `status_code`, `user_id`, and `action`.

Example request:
`GET /audit-logs?method=POST&status_code=201&limit=20`

## Configuration Reference (AuditConfig)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `orm` | `str` | **Required** | One of: `sqlalchemy`, `tortoise`, `sqlmodel`, `beanie`, `asyncpg`. |
| `dsn` | `str` | **Required** | Connection string for the database. |
| `table_name` | `str` | `"audit_logs"` | Name of the table or collection. |
| `auto_create_table`| `bool` | `True` | Whether to create the table on startup. |
| `batch_size` | `int` | `1` | Set > 1 to enable batching (not all backends yet). |
| `mask_fields` | `list[str]` | `[]` | PII fields to mask in request bodies. |
| `on_storage_error`| `Callable` | `None` | Optional callback for storage errors. |

## Development and Examples

To run the examples that require a real database (PostgreSQL, MongoDB, MySQL), you can use the provided Docker Compose file:

```bash
docker-compose up -d
```

This will start:

- **PostgreSQL** at `localhost:5432` (user: `user`, pass: `pass`, db: `audit_db`)
- **MongoDB** at `localhost:27017`
- **MySQL** at `localhost:3306` (user: `user`, pass: `pass`, db: `audit_db`)

### Running the MongoDB Example

```bash
poetry run python examples/beanie_mongodb_usage.py
```

### Running the Asyncpg Example

```bash
poetry run python examples/asyncpg_usage.py
```

## Future Features

- **Admin UI:** Build a simple web UI for viewing/searching audit logs.
- **Custom Storage Backends:** Allow users to plug in custom storage backends (e.g., S3, Redis, external APIs).
- **Event Hooks:** Add hooks for pre/post log processing (e.g., for enrichment, notifications).
- **Log Export:** Support exporting logs to CSV, JSON, or external log management systems.
- **Retention Policies:** Add configurable log retention and automatic cleanup.
- **Multi-Tenancy:** Support tenant-aware logging for SaaS apps.
- **Security:** Encrypt sensitive log fields at rest, and add role-based access for log viewing.
- **CLI Tooling:** Provide CLI commands for log inspection, export, and management.
- **OpenTelemetry Integration:** Integrate with OpenTelemetry for distributed tracing and correlation.
- **Documentation:** Expand usage examples and add troubleshooting guides.

## License

MIT
