from dataclasses import is_dataclass
import dataclasses
from enum import Enum
from functools import wraps
from typing import Any
from .metadata import parse


class DecoratorBackend(Enum):
    PYTHON = "python"
    PYTHON_WITH_METADATA = "python_with_metadata"
    PYIRON_WORKFLOW = "pyiron_workflow"
    PYIRON_CORE = "pyiron_core"


decorator_backend: DecoratorBackend = DecoratorBackend.PYTHON_WITH_METADATA


def node(author_name: str = "", author_email: str = ""):
    def decorator(func):
        if not callable(func):
            raise RuntimeError("Only functions can be decorated with @node!")

        if decorator_backend == DecoratorBackend.PYTHON:
            return func

        if not hasattr(func, "__metadata__"):
            metadata = parse(func, author_name, author_email)
            setattr(func, "__metadata__", metadata)

        match decorator_backend:
            case DecoratorBackend.PYTHON_WITH_METADATA:
                return func
            case DecoratorBackend.PYIRON_WORKFLOW:
                return func
            case DecoratorBackend.PYIRON_CORE:
                return func

    return decorator


# black magic below, do not try this at home
def to_dataclass_function(Dataclass: type):
    if not is_dataclass(Dataclass):
        raise RuntimeError(
            f"{Dataclass} is not a dataclass. Only dataclasses.dataclass is supported!"
        )

    Dataclass.__init__.__annotations__["return"] = Dataclass

    @wraps(Dataclass.__init__)
    def wrapper(*args, **kwds):
        return Dataclass(*args, **kwds)

    setattr(wrapper, "__wrapped__", Dataclass)

    return wrapper


# black magic below, do not try this at home
def from_dataclass_function(Dataclass: type):
    if not is_dataclass(Dataclass):
        raise RuntimeError(
            f"{Dataclass} is not a dataclass. Only dataclasses.dataclass is supported!"
        )

    def wrapper(input) -> tuple[Any]:
        return tuple(getattr(input, field.name) for field in dataclasses.fields(input))

    wrapper.__annotations__["input"] = Dataclass
    setattr(wrapper, "__wrapped__", Dataclass)
    return wrapper
