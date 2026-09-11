import contextlib
import os
import sys
import time
import typing
from collections import deque
from collections.abc import Callable, Iterator
from functools import cached_property
from types import TracebackType
from typing import Any, Self, cast

from . import cached_content
from .utils import find_first_match

if typing.TYPE_CHECKING:
    from .archive import Archive
    from .encrypted import EncryptedPath


class Path(cached_content.Path):
    """
    Additional functionality.
    """

    def create_parent(self) -> Self:
        self.parent.mkdir(parents=True, exist_ok=True)
        return self.parent

    def with_nonexistent_name(self) -> Self:
        path = self
        if path.exists():
            stem = path.stem

            def with_number(i: int) -> "Path":
                return path.with_stem(f"{stem} ({i})")

            def nonexistent(i: int) -> bool:
                return not with_number(i).exists()

            first_free_number = find_first_match(nonexistent)
            path = cast("Self", with_number(first_free_number))

        return path

    def with_timestamp(self) -> Self:
        from datetime import UTC, datetime

        timestamp = int(time.time())  # precision up to second
        datetime_timestamp = datetime.fromtimestamp(timestamp, tz=UTC)
        return self.with_stem(f"{self.stem} {datetime_timestamp}")

    @property
    def encrypted(self) -> "EncryptedPath":
        # imports optional dependency
        from .encrypted import EncryptedPath

        path = self
        encryption_suffix = ".gpg"
        if path.suffix != encryption_suffix:
            path = path.with_suffix(path.suffix + encryption_suffix)
        return EncryptedPath(path)

    @cached_property
    def archive(self) -> "Archive[Self]":
        from .archive import Archive

        return Archive(self)

    def unpack_if_archive(
        self,
        *,
        extraction_directory: Self | None = None,
        recursive: bool = True,
    ) -> None:
        if self.archive.format_ is not None:
            self.archive.unpack(extraction_directory, recursive=recursive)

    def copy_to(
        self,
        dest: Self,
        *,
        include_properties: bool = True,
        only_if_newer: bool = False,
    ) -> None:
        if not only_if_newer or self.mtime > dest.mtime:
            dest.byte_content = self.byte_content
            if include_properties:
                self.copy_properties_to(dest)

    def copy_properties_to(self, dest: Self) -> None:
        for path in dest.find():
            path.tag = self.tag
            path.mtime = self.mtime

    def pop_parent(self) -> None:
        """
        Remove first parent from path in filesystem.
        """
        import shutil

        dest = self.parent.parent / self.name
        parent = self.parent
        temp_dest = dest.with_nonexistent_name()  # can only move to non-existing path
        self.rename(temp_dest)

        if not parent.has_children:
            parent.rmdir()
        if not parent.exists():
            temp_dest.rename(dest)
        else:  # pragma: nocover
            # merge in existing folder
            shutil.copytree(temp_dest, dest, dirs_exist_ok=True)
            temp_dest.rmtree()

    def is_empty(self) -> bool:
        return (
            not self.exists()
            or (self.is_dir() and next(self.iterdir(), None) is None)
            or (self.is_file() and self.size == 0)
        )

    def load_yaml(self) -> dict[Any, Any] | list[Any]:
        """
        Load yaml content of trusted path with an unsafe loader.

        This can be used to instantiate any object
        :return: Content in path that contains yaml format
        """
        import yaml  # , autoimport

        Loader: type[yaml.CFullLoader | yaml.FullLoader] = (  # noqa: N806
            yaml.CFullLoader if hasattr(yaml, "CFullLoader") else yaml.FullLoader
        )
        return yaml.load(self.text, Loader=Loader) or {}  # noqa: S506

    def update(self, value: dict[Any, Any]) -> dict[Any, Any]:
        # only read and write if value to add not empty
        if value:
            current_content = cast("dict[Any, Any]", self.yaml)
            updated_content = current_content | value
            self.yaml = updated_content
        else:
            updated_content = value
        return updated_content

    def find(
        self,
        condition: Callable[[Self], bool] | None = None,
        exclude: Callable[[Self], bool] = lambda _: False,
        *,
        recurse_on_match: bool = False,
        follow_symlinks: bool = False,
        only_folders: bool = False,
    ) -> Iterator[Self]:
        """
        Find all subpaths under path that match condition.

        only_folders option can be used for efficiency reasons
        """

        def extract_children_to_recurse_on(path: Self) -> Iterator[Self]:
            # skip folders that do not allow listing
            with contextlib.suppress(PermissionError):
                for child in path.iterdir():
                    should_follow_symlink = follow_symlinks or not child.is_symlink()
                    should_follow_directories = not only_folders or child.is_dir()
                    if should_follow_symlink and should_follow_directories:
                        yield child

        if condition is None:
            recurse_on_match = True

            def condition(_: Self) -> bool:
                return True

        to_traverse = deque([self] if self.exists() else [])
        while to_traverse:
            path = to_traverse.popleft()
            if not exclude(path):
                match = condition(path)
                if match:
                    yield path
                should_recurse = recurse_on_match or not match
                should_recurse_folder = only_folders or path.is_dir()
                if should_recurse and should_recurse_folder:
                    to_traverse.extend(extract_children_to_recurse_on(path))

    def remove(self) -> None:
        if self.is_dir():
            self.rmtree(missing_ok=True)
        else:
            self.unlink(missing_ok=True)

    def rmtree(
        self,
        *,
        missing_ok: bool = False,
        remove_root: bool = True,
        ignore_errors: bool = False,
    ) -> None:
        import shutil

        context = (
            contextlib.suppress(FileNotFoundError)
            if missing_ok
            else contextlib.nullcontext()
        )
        handler_name = "onexc" if sys.version_info >= (3, 12) else "onerror"
        handler_argument: dict[str, Any] = {handler_name: handle_removal_error}
        with context:
            shutil.rmtree(self, ignore_errors, **handler_argument)
        if not remove_root:
            self.mkdir()

    def subpath(self, *parts: str) -> Self:
        path = self
        tokens_to_replace = os.sep, "."
        for part in parts:
            for token in tokens_to_replace:
                part = part.replace(token, "_")  # noqa: PLW2901
            path /= part
        return path

    @classmethod
    def tempfile(
        cls,
        *,
        in_memory: bool = True,
        create: bool = True,
        **kwargs: Any,
    ) -> Self:
        """
        Context manager for temporary file creation.

        with Path.tempfile() as tmp:     run_command(log_file=tmp)     logs = tmp.text
        process_logs(logs)
        """
        import tempfile

        if in_memory:
            in_memory_folder = cls("/") / "dev" / "shm"
            if in_memory_folder.exists():  # pragma: nocover
                kwargs["dir"] = in_memory_folder
        file_handle, path_str = tempfile.mkstemp(**kwargs)
        os.close(file_handle)
        path = cls(path_str)
        if not create:
            path.unlink()
        return path

    @classmethod
    def tempdir(cls, *, in_memory: bool = True) -> Self:
        path = cls.tempfile(in_memory=in_memory, create=False)
        path.mkdir()
        return path

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.remove()


def handle_removal_error(
    function: Callable[[str], Any],
    path: str,
    error: BaseException | tuple[type[BaseException], BaseException, TracebackType],
) -> None:
    exception = error[1] if isinstance(error, tuple) else error
    if isinstance(exception, PermissionError) and os.name == "nt":  # pragma: nocover
        Path(path).chmod(0o777)
        function(path)
    else:
        raise exception
