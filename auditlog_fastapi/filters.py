from typing import Any
from urllib.parse import parse_qsl, urlencode

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
    Also handles URL-encoded strings (query strings).
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

    if isinstance(data, str) and "=" in data:
        # Potential query string
        try:
            pairs = parse_qsl(data, keep_blank_values=True)
            if not pairs:
                return data

            masked_pairs = []
            changed = False
            for key, value in pairs:
                if any(field.lower() == key.lower() for field in fields):
                    masked_pairs.append((key, MASK_VALUE))
                    changed = True
                else:
                    masked_pairs.append((key, value))

            return urlencode(masked_pairs) if changed else data
        except Exception:
            return data

    return data
