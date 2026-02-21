class AuditError(Exception):
    """Base exception for all audit-related errors."""


class StorageError(AuditError):
    """Raised when a storage backend fails to save an entry."""


class AuditConfigurationError(AuditError):
    """Raised when the audit storage configuration is invalid."""


class AuditNotConfiguredError(AuditError):
    """Raised when the audit storage has not been configured."""


class AuditAlreadyConfiguredError(AuditError):
    """Raised when the audit storage has already been configured."""


class AuditStorageConnectionError(AuditError):
    """Raised when the audit storage backend cannot connect to the database."""
