import abc
import sys
import typing
from typing import Any, TypeVar

from simple_classproperty import classproperty

from . import base

T = TypeVar("T", bound="Path")


def enable_classproperties(cls: type[T]) -> None:  # pragma: nocover
    for name, method in vars(cls).items():
        if isinstance(method, classmethod):
            wrapped_method = method.__func__
            if isinstance(wrapped_method, classproperty):
                setattr(cls, name, wrapped_method)


class PropertyMeta(abc.ABCMeta):
    def __new__(
        cls: type["PropertyMeta"],
        name: str,
        bases: tuple[type, ...],
        attributes: dict[str, Any],
    ) -> "PropertyMeta":
        meta_class = super().__new__(cls, name, bases, attributes)
        if sys.version_info >= (3, 13):
            enable_classproperties(meta_class)  # pragma: nocover
        return meta_class


class Path(base.Path, metaclass=PropertyMeta):
    """Expose common folders as attributes.

    Use classmethod properties to ensure child classes return instance
    of child class. The classmethod and property decorators are combined
    in a single decorated because chaining them directly is deprecated
    since python3.11.
    """

    @classmethod
    @classproperty
    def HOME(cls: type[T]) -> T:  # noqa: N802
        return cls.home()

    @classmethod
    @classproperty
    def docs(cls: type[T]) -> T:
        path = cls.HOME / "Documents"
        return typing.cast(T, path)

    @classmethod
    @classproperty
    def scripts(cls: type[T]) -> T:
        path = cls.docs / "Scripts"
        return typing.cast(T, path)

    @classmethod
    @classproperty
    def script_assets(cls: type[T]) -> T:
        path = cls.scripts / "assets"
        return typing.cast(T, path)

    @classmethod
    @classproperty
    def assets(cls: type[T]) -> T:
        """
        Often overwritten by child classes for specific project.
        """
        return typing.cast(T, cls.script_assets)

    @classmethod
    @classproperty
    def draft(cls: type[T]) -> T:
        path = cls.docs / "draft.txt"
        return typing.cast(T, path)
