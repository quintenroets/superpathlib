import hashlib
import mimetypes
import os
import subprocess
import warnings
from collections.abc import Callable
from functools import wraps
from typing import Any

from . import content_properties

# Long import times relative to usage frequency: lazy imports
# from .tags import XDGTags


def catch_missing(default: Any = None) -> Callable:
    def wrap_function(func: Callable) -> Callable:
        @wraps(func)
        def wrap_args(*args: Any, **kwargs: Any) -> Any:
            try:
                res = func(*args, **kwargs)
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

        try:
            subprocess.run(("touch", "-d", "@%f" % time, self))
        except subprocess.CalledProcessError:
            pass  # Doesn't work on Windows

    @property
    def tags(self) -> list[str]:
        from .tags import XDGTags  # noqa: E402, autoimport

        return XDGTags(self).get()

    @tags.setter
    def tags(self, values: list[str | int | None]) -> None:
        from .tags import XDGTags  # noqa: E402, autoimport

        if len(values) == 0:
            XDGTags(self).clear()
        else:
            XDGTags(self).set(*values)

    @property
    def tag(self) -> str | None:
        return self.tags[0] if self.tags else None

    @tag.setter
    def tag(self, value: str | int | None) -> None:
        from .tags import XDGTags  # noqa: E402, autoimport

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
    def content_hash(self) -> str:
        return self.file_content_hash if self.is_file() else self.dir_content_hash

    @property
    def dir_content_hash(self) -> str:
        # dirhash package throws annoying warnings
        warnings.filterwarnings(
            action="ignore", module="pkg_resources|dirhash", category=DeprecationWarning
        )

        import dirhash  # noqa: E402, F401, autoimport

        # use default algorithm used in cloud provider checksums
        # can be efficient because not used for cryptographic security
        return dirhash.dirhash(self, "md5")

    @property
    def file_content_hash(self) -> str:
        return hashlib.new("sha512", data=self.byte_content).hexdigest()
