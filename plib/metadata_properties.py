import mimetypes
import os
import subprocess
import warnings
from functools import wraps

from . import content_properties

# Long import times relative to usage frequency: lazy imports
# from .tags import XDGTags


def catch_missing(default=None):
    def wrap_function(func):
        @wraps(func)
        def wrap_args(*args, **kwargs):
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
    def mtime(self):
        return self.stat().st_mtime

    @mtime.setter
    def mtime(self, time: float):
        os.utime(self, (time, time))  # set create time as well

        try:
            subprocess.run(("touch", "-d", "@%f" % time, self))
        except subprocess.CalledProcessError:
            pass  # Doesn't work on Windows

    @property
    def tags(self):
        from .tags import XDGTags  # noqa: autoimport

        return XDGTags(self).get()

    @tags.setter
    def tags(self, *values):
        from .tags import XDGTags  # noqa: autoimport

        if len(values) == 1 and values[0] in (None, []):
            XDGTags(self).clear()
        else:
            XDGTags(self).set(*values)

    @property
    def tag(self):
        return self.tags[0] if self.tags else None

    @tag.setter
    def tag(self, value):
        self.tags = value

    @property
    @catch_missing(default=0)
    def size(self):
        return self.stat().st_size

    @property
    def is_root(self):
        path = self
        while not path.exists():
            path = path.parent
        return path.owner() == "root"

    @property
    def has_children(self):
        return next(self.iterdir(), None) is not None if self.is_dir() else False

    @property
    def number_of_children(self):
        return sum(1 for _ in self.iterdir()) if self.is_dir() else 0

    @property
    def filetype(self):
        filetype = mimetypes.guess_type(self)[0]
        if filetype:
            filetype = filetype.split("/")[0]
        return filetype

    @property
    def content_hash(self):
        # dirhash package throws annoying warnings
        warnings.filterwarnings(
            action="ignore", module="pkg_resources|dirhash", category=DeprecationWarning
        )

        import dirhash  # noqa: E402, F401, autoimport

        # use default algorithm used in cloud provider checksums
        # can be efficient because not used for cryptographic security
        return dirhash.dirhash(self, "md5")
