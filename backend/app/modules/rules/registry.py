from typing import Type

from app.modules.rules.base import BaseRule

_registry: dict[str, Type[BaseRule]] = {}


def register_rule(cls: Type[BaseRule]) -> Type[BaseRule]:
    _registry[cls.name] = cls
    return cls


def get_rule(name: str) -> Type[BaseRule] | None:
    return _registry.get(name)


def discover_rules() -> dict[str, Type[BaseRule]]:
    return dict(_registry)
