from tortoise import fields
from tortoise.models import Model


def make_tortoise_model(table_name: str):
    """Dynamically create the Tortoise ORM model class with the given table name."""

    class AuditLog(Model):
        """Tortoise ORM model for audit logs, with dynamic table name set at runtime."""

        id = fields.UUIDField(pk=True)
        timestamp = fields.DatetimeField(auto_now_add=True, index=True)
        user_id = fields.CharField(max_length=255, null=True, index=True)
        username = fields.CharField(max_length=255, null=True)
        ip_address = fields.CharField(max_length=45, null=True)
        user_agent = fields.CharField(max_length=512, null=True)
        method = fields.CharField(max_length=10)
        path = fields.CharField(max_length=2048, index=True)
        query_params = fields.JSONField(null=True)
        status_code = fields.IntField(null=True, index=True)
        request_body = fields.JSONField(null=True)
        response_body = fields.JSONField(null=True)
        duration_ms = fields.FloatField(null=True)
        action = fields.CharField(max_length=255, null=True, index=True)
        resource_type = fields.CharField(max_length=255, null=True, index=True)
        resource_id = fields.CharField(max_length=255, null=True, index=True)
        extra = fields.JSONField(null=True)
        error = fields.TextField(null=True)

        class Meta:
            table = table_name

    return AuditLog
