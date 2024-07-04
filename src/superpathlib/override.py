import io
import shutil
import typing
from collections.abc import Callable, Generator
from functools import wraps
from pathlib import PurePath
from typing import IO, Any, TypeVar

from . import encryption
from .metadata_properties import catch_missing

T = TypeVar("T", bound="Path")


def create_parent_on_missing(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            res = func(*args, **kwargs)
        except FileNotFoundError:
            path = encryption.Path(args[0])
            path.create_parent()
            res = func(*args, **kwargs)
        return res

    return wrapper


class Path(encryption.Path):
    """
    Overwrite existing methods with exception handling.
    """

    @create_parent_on_missing
    def touch(
        self,
        mode: int = 0o666,
        *,
        exist_ok: bool = True,
        mtime: float | None = None,
    ) -> None:
        super().touch(mode=mode, exist_ok=exist_ok)
        if mtime is not None:
            self.mtime = mtime  # set time after touch or it is immediately overwritten

    @catch_missing(default=0)
    def rmdir(self) -> None:
        return super().rmdir()

    def iterdir(self: T, *, missing_ok: bool = True) -> Generator[T, None, None]:
        if self.exists() or not missing_ok:
            yield from super().iterdir()

    @create_parent_on_missing
    def rename(self: T, target: str | T, *, exist_ok: bool = False) -> T:
        target_path = self.__class__(target)
        rename = super().replace if exist_ok else super().rename
        try:
            target_path.create_parent()
            target_path = rename(target_path)
        except OSError as exception:
            if exist_ok and "Directory not empty" in str(exception):
                target_path.rmtree()
                target_path = rename(target_path)
            elif "Invalid cross-device link" in str(exception):
                # target is on different file system
                if target_path.exists():
                    if exist_ok:
                        if self.is_dir():
                            target_path.rmtree()
                        else:
                            target_path.unlink()  # pragma: nocover
                    else:
                        message = f"Target already exists: {target_path }"
                        raise RuntimeError(message) from exception
                else:
                    target_path.create_parent()
                target_path = shutil.move(self, target_path)
            else:
                raise
        return target_path

    def replace(self: T, target: str | PurePath) -> T:
        path = self.rename(target, exist_ok=True)
        return typing.cast(T, path)

    def open(self, mode: str = "r", **kwargs: Any) -> IO[Any]:  # type: ignore[override]
        try:
            res = super().open(mode, **kwargs)
        except FileNotFoundError:
            res = self.open_non_existing(mode, **kwargs)
        return res

    def open_non_existing(self, mode: str, **kwargs: Any) -> IO[Any]:
        if "w" in mode or "a" in mode:
            # exist_ok=True: catch race conditions when calling multiple times
            self.create_parent()
            res = self.open(mode, **kwargs)
        else:
            res = self.open_encrypted(mode)
        return res

    def open_encrypted(self, mode: str) -> IO[Any]:
        encrypted = self.encrypted.exists()
        res: IO[Any]
        if "b" in mode:
            byte_content = self.encrypted.byte_content if encrypted else b""
            res = io.BytesIO(byte_content)
        else:
            text = self.encrypted.text if encrypted else ""
            res = io.StringIO(text)
        return res
