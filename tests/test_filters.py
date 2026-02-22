from auditlog_fastapi.filters import mask_sensitive_fields


def test_mask_sensitive_fields_top_level():
    data = {"password": "secret123", "username": "admin"}
    masked = mask_sensitive_fields(data, ["password"])
    assert masked["password"] == "***REDACTED***"
    assert masked["username"] == "admin"


def test_mask_sensitive_fields_nested():
    data = {
        "user": {
            "name": "john",
            "api_key": "some-key",
            "details": {"token": "secret-token"},
        },
        "items": [{"id": 1, "secret": "123"}],
    }
    fields = ["api_key", "token", "secret"]
    masked = mask_sensitive_fields(data, fields)

    assert masked["user"]["api_key"] == "***REDACTED***"
    assert masked["user"]["details"]["token"] == "***REDACTED***"
    assert masked["items"][0]["secret"] == "***REDACTED***"
    assert masked["user"]["name"] == "john"


def test_mask_sensitive_fields_case_insensitive():
    data = {"PASSWORD": "abc", "Token": "xyz"}
    masked = mask_sensitive_fields(data, ["password", "token"])
    assert masked["PASSWORD"] == "***REDACTED***"
    assert masked["Token"] == "***REDACTED***"
