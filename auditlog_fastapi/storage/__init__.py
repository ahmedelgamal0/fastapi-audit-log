from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .asyncpg_storage import AsyncpgStorage
    from .base import AuditStorage
    from .beanie_storage import BeanieStorage
    from .sqlalchemy_storage import SQLAlchemyStorage
    from .sqlmodel_storage import SQLModelStorage
    from .tortoise_storage import TortoiseStorage

_LOOKUP = {
    "AsyncpgStorage": ".asyncpg_storage",
    "AuditStorage": ".base",
    "BeanieStorage": ".beanie_storage",
    "SQLAlchemyStorage": ".sqlalchemy_storage",
    "SQLModelStorage": ".sqlmodel_storage",
    "TortoiseStorage": ".tortoise_storage",
}


def __getattr__(name: str) -> Any:
    if name in _LOOKUP:
        import importlib

        module_path = _LOOKUP[name]
        module = importlib.import_module(module_path, __package__)
        return getattr(module, name)
    raise AttributeError(f"module {__name__} has no attribute {name}")


__all__ = [
    "AuditStorage",
    "SQLAlchemyStorage",
    "TortoiseStorage",
    "SQLModelStorage",
    "BeanieStorage",
    "AsyncpgStorage",
]
