from typing import Any

DEFAULT_SENSITIVE_FIELDS = [
    "password",
    "token",
    "secret",
    "authorization",
    "api_key",
    "credit_card",
    "ssn",
    "cvv",
]

MASK_VALUE = "***REDACTED***"


def mask_sensitive_fields(data: Any, fields: list[str]) -> Any:
    """
    Recursively walk dicts and lists to mask sensitive fields.
    Replaces matched field values with `MASK_VALUE`.
    """
    if isinstance(data, dict):
        masked_dict = {}
        for key, value in data.items():
            if any(field.lower() == key.lower() for field in fields):
                masked_dict[key] = MASK_VALUE
            else:
                masked_dict[key] = mask_sensitive_fields(value, fields)
        return masked_dict

    if isinstance(data, list):
        return [mask_sensitive_fields(item, fields) for item in data]

    return data
