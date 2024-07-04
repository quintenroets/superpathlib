import contextlib
import hashlib
import mimetypes
import os
import subprocess
import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar, cast

from . import content_properties

T = TypeVar("T")


def catch_missing(
    default: Any = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    def wrap_function(function: Callable[..., T]) -> Callable[..., T]:
        @wraps(function)
        def wrap_args(*args: Any, **kwargs: Any) -> Any:
            try:
                res = function(*args, **kwargs)
            except FileNotFoundError:
                res = default
            return res

        return wrap_args

    return wrap_function


class Path(content_properties.Path):
    """
    Properties to read & write metadata.
    """

    @property
    @catch_missing(default=0.0)
    def mtime(self) -> float:
        return self.stat().st_mtime

    @mtime.setter
    def mtime(self, time: float) -> None:
        os.utime(self, (time, time))  # set create time as well

        command = "touch", "-d", f"@{time}", self
        with contextlib.suppress(
            subprocess.CalledProcessError,
        ):  # Doesn't work on Windows
            subprocess.run(command, check=False)  # noqa: S603

    @property
    def tags(self) -> list[str]:
        from .tags import XDGTags  # , autoimport

        return XDGTags(self).get()

    @tags.setter
    def tags(self, values: list[str | int | None]) -> None:
        from .tags import XDGTags  # , autoimport

        if len(values) == 0:
            XDGTags(self).clear()
        else:
            XDGTags(self).set(*values)

    @property
    def tag(self) -> str | None:
        return self.tags[0] if self.tags else None

    @tag.setter
    def tag(self, value: str | int | None) -> None:
        from .tags import XDGTags  # , autoimport

        XDGTags(self).set(value)

    @property
    @catch_missing(default=0)
    def size(self) -> int:
        return self.stat().st_size

    @property
    def is_root(self) -> bool:
        path = self
        while not path.exists():
            path = path.parent
        return path.owner() == "root"

    @property
    def has_children(self) -> bool:
        return next(self.iterdir(), None) is not None if self.is_dir() else False

    @property
    def number_of_children(self) -> int:
        return sum(1 for _ in self.iterdir()) if self.is_dir() else 0

    @property
    def filetype(self) -> str | None:
        filetype = mimetypes.guess_type(self)[0]
        if filetype:
            filetype = filetype.split("/")[0]
        return filetype

    @property
    def content_hash(self) -> str | None:
        return self.file_content_hash if self.is_file() else self.dir_content_hash

    @property
    def dir_content_hash(self) -> str | None:
        # dirhash package throws annoying warnings
        warnings.filterwarnings(
            action="ignore",
            module="pkg_resources|dirhash",
            category=DeprecationWarning,
        )

        import dirhash  # , autoimport

        # use default algorithm used in cloud provider checksums
        # can be efficient because not used for cryptographic security
        return cast(str, dirhash.dirhash(self, "md5")) if self.has_children else None

    @property
    def file_content_hash(self) -> str:
        return hashlib.new("sha512", data=self.byte_content).hexdigest()
