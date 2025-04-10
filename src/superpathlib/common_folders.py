import abc
import sys
import typing
from typing import Any, TypeVar

from simple_classproperty import classproperty
from typing_extensions import Self

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
    def HOME(cls) -> Self:  # noqa: N802
        return cls.home()

    @classmethod
    @classproperty
    def docs(cls) -> Self:
        path = cls.HOME / "Documents"
        return typing.cast("Self", path)

    @classmethod
    @classproperty
    def scripts(cls) -> Self:
        path = cls.docs / "Scripts"
        return typing.cast("Self", path)

    @classmethod
    @classproperty
    def script_assets(cls) -> Self:
        path = cls.scripts / "assets"
        return typing.cast("Self", path)

    @classmethod
    @classproperty
    def assets(cls) -> Self:
        """
        Often overwritten by child classes for specific project.
        """
        return typing.cast("Self", cls.script_assets)

    @classmethod
    @classproperty
    def draft(cls) -> Self:
        path = cls.docs / "draft.txt"
        return typing.cast("Self", path)
