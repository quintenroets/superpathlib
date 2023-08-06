import io
import shutil
from functools import wraps

from . import encryption
from .metadata_properties import catch_missing


def create_parent_on_missing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except FileNotFoundError:
            path: encryption.Path = args[0]
            path.create_parent()
            res = func(*args, **kwargs)
        return res

    return wrapper


class Path(encryption.Path):
    """
    Overwrite existing methods with exception handling.
    """

    @create_parent_on_missing
    def touch(self, mode=0o666, exist_ok=True, mtime=None):
        super().touch(mode=mode, exist_ok=exist_ok)
        if mtime is not None:
            self.mtime = mtime  # set time after touch or it is immediately overwritten

    @catch_missing(default=0)
    def rmdir(self):
        return super().rmdir()

    def iterdir(self, missing_ok=True):
        if self.exists() or not missing_ok:
            yield from super().iterdir()

    def rename(self, target):
        target = self.__class__(target)
        target.create_parent()
        try:
            target = super().rename(target)
        except OSError:
            target = shutil.move(self, target)
        return target

    def open(self, mode: str = "r", **kwargs):
        try:
            res = super().open(mode, **kwargs)
        except FileNotFoundError:
            res = self.open_non_existing(mode, **kwargs)
        return res

    def open_non_existing(self, mode: str, **kwargs):
        if "w" in mode or "a" in mode:
            # exist_ok=True: catch race conditions when calling multiple times
            self.create_parent()
            res = self.open(mode, **kwargs)
        else:
            res = self.open_encrypted(mode)
        return res

    def open_encrypted(self, mode: str):
        encrypted = self.encrypted.exists()
        if "b" in mode:
            byte_content = self.encrypted.byte_content if encrypted else b""
            res = io.BytesIO(byte_content)
        else:
            text = self.encrypted.text if encrypted else ""
            res = io.StringIO(text)
        return res
