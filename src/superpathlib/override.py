import contextlib
from collections.abc import Generator
from os import PathLike
from typing import IO, Any, Self

from . import extra_functionality


class Path(extra_functionality.Path):
    """
    Overwrite existing methods with exception handling.
    """

    def touch(  # type: ignore[override]
        self,
        mode: int = 0o666,
        *,
        exist_ok: bool = True,
        mtime: float | None = None,
    ) -> None:
        try:
            super().touch(mode=mode, exist_ok=exist_ok)
        except FileNotFoundError:
            self.create_parent()
            super().touch(mode=mode, exist_ok=exist_ok)
        if mtime is not None:
            self.mtime = mtime  # set time after touch or it is immediately overwritten

    def rmdir(self) -> None:
        with contextlib.suppress(FileNotFoundError):
            super().rmdir()

    def iterdir(self, *, missing_ok: bool = True) -> Generator[Self, None, None]:
        if self.exists() or not missing_ok:
            yield from super().iterdir()

    def rename(self, target: str | PathLike[str], *, exist_ok: bool = False) -> Self:
        target_path = self.__class__(target)
        rename = super().replace if exist_ok else super().rename
        try:
            target_path = rename(target_path)
        except FileNotFoundError:
            target_path.create_parent()
            target_path = rename(target_path)
        except OSError as exception:
            if exist_ok and "Directory not empty" in str(exception):
                target_path.rmtree()
                target_path = rename(target_path)
            elif "Invalid cross-device link" in str(exception):  # pragma: nocover
                # target is on different file system
                import shutil

                if target_path.exists():
                    if exist_ok:
                        if self.is_dir():
                            target_path.rmtree()
                        else:
                            target_path.unlink()  # pragma: nocover
                    else:
                        message = f"Target already exists: {target_path}"
                        raise RuntimeError(message) from exception
                else:
                    target_path.create_parent()
                target_path = self.__class__(shutil.move(self, target_path))
            else:
                raise
        return target_path

    def replace(self, target: str | PathLike[str]) -> Self:
        return self.rename(target, exist_ok=True)

    def open(self, mode: str = "r", **kwargs: Any) -> IO[Any]:  # type: ignore[override]
        try:
            res = super().open(mode, **kwargs)
        except FileNotFoundError:
            if "w" in mode or "a" in mode:
                self.create_parent()
                res = super().open(mode, **kwargs)
            else:
                raise
        return res
