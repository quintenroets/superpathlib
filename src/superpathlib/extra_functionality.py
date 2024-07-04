import contextlib
import os
import shutil
import tempfile
import time
import typing
import urllib.parse
from collections.abc import Callable, Iterator
from functools import cached_property
from types import TracebackType
from typing import Any, TypeVar, cast

from . import cached_content
from .utils import find_first_match

PathType = TypeVar("PathType", bound="Path")


class Path(cached_content.Path):
    """
    Additional functionality.
    """

    def create_parent(self: PathType) -> PathType:
        self.parent.mkdir(parents=True, exist_ok=True)
        return self.parent

    def with_nonexistent_name(self: PathType) -> PathType:
        path = self
        if path.exists():
            stem = path.stem

            def with_number(i: int) -> PathType:
                return path.with_stem(f"{stem} ({i})")

            def nonexistent(i: int) -> bool:
                return not with_number(i).exists()

            first_free_number = find_first_match(nonexistent)
            path = with_number(first_free_number)

        return path

    def with_timestamp(self: PathType) -> PathType:
        from datetime import datetime, timezone

        timestamp = int(time.time())  # precision up to second
        datetime_timestamp = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return self.with_stem(f"{self.stem} {datetime_timestamp}")

    def copy_to(
        self,
        dest: PathType,
        *,
        include_properties: bool = True,
        only_if_newer: bool = False,
    ) -> None:
        if not only_if_newer or self.mtime > dest.mtime:
            dest.byte_content = self.byte_content
            if include_properties:
                self.copy_properties_to(dest)

    def copy_properties_to(self, dest: PathType) -> None:
        for path in dest.find():
            path.tag = self.tag
            path.mtime = self.mtime

    @cached_property
    def archive_format(self) -> str:
        # noinspection PyProtectedMember
        path_str = str(self)
        format_ = shutil._find_unpack_format(path_str)  # type: ignore[attr-defined] # noqa: SLF001
        return typing.cast(str, format_)

    def unpack_if_archive(
        self,
        *,
        extraction_directory: PathType | None = None,
        recursive: bool = True,
    ) -> None:
        if self.archive_format is not None:
            self.unpack(extraction_directory, recursive=recursive)

    def unpack(  # noqa: PLR0913
        self: PathType,
        extraction_directory: PathType | None = None,
        *,
        remove_existing: bool = True,
        preserve_properties: bool = True,
        remove_original: bool = True,
        archive_format: str | None = None,
        recursive: bool = True,
    ) -> None:
        def cleanup(cleanup_path: PathType) -> None:
            (cleanup_path / "__MACOSX").rmtree(missing_ok=True)
            subfolder = cleanup_path / cleanup_path.name
            if subfolder.exists() and cleanup_path.number_of_children == 1:
                subfolder.pop_parent()  # pragma: nocover

        if archive_format is None:
            archive_format = self.archive_format

        extraction_directory = (
            self.create_extraction_directory(archive_format=archive_format)
            if extraction_directory is None
            else extraction_directory
        )

        if remove_existing:
            if extraction_directory.is_dir():
                extraction_directory.rmtree(missing_ok=True)
            else:
                extraction_directory.unlink(missing_ok=True)

        shutil.unpack_archive(
            self,
            extract_dir=extraction_directory,
            format=archive_format,
        )

        cleanup(extraction_directory)
        if preserve_properties:
            self.copy_properties_to(extraction_directory)

        if remove_original:
            self.unlink()

        if recursive:
            for path in extraction_directory.find():
                path.unpack_if_archive()

    def create_extraction_directory(self: PathType, archive_format: str) -> PathType:
        extract_name = self.name
        # noinspection PyProtectedMember
        unpack_formats = shutil._UNPACK_FORMATS  # type: ignore[attr-defined] # noqa: SLF001
        unpack_info = unpack_formats[archive_format]
        for archive_ext in unpack_info[0]:
            if extract_name.endswith(archive_ext):
                extract_name = extract_name.replace(archive_ext, "")
        return self.with_name(extract_name)

    def pop_parent(self) -> None:
        """
        Remove first parent from path in filesystem.
        """
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
        """Load yaml content of trusted path with an unsafe loader.

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
            current_content = cast(dict[Any, Any], self.yaml)
            updated_content = current_content | value
            self.yaml = updated_content
        else:
            updated_content = value
        return updated_content

    def find(  # noqa: PLR0913
        self: PathType,
        condition: Callable[[PathType], bool] | None = None,
        exclude: Callable[[PathType], bool] = lambda _: False,
        *,
        recurse_on_match: bool = False,
        follow_symlinks: bool = False,
        only_folders: bool = False,
    ) -> Iterator[PathType]:
        """Find all subpaths under path that match condition.

        only_folders option can be used for efficiency reasons
        """

        def extract_children_to_recurse_on(path: PathType) -> Iterator[PathType]:
            # skip folders that do not allow listing
            with contextlib.suppress(PermissionError):
                for child in path.iterdir():
                    should_follow_symlink = follow_symlinks or not child.is_symlink()
                    should_follow_directories = not only_folders or child.is_dir()
                    if should_follow_symlink and should_follow_directories:
                        yield child

        if condition is None:
            recurse_on_match = True

            def condition(_: PathType) -> bool:
                return True

        to_traverse = [self] if self.exists() else []
        while to_traverse:
            path = to_traverse.pop(0)
            if not exclude(path):
                match = condition(path)
                if match:
                    yield path
                should_recurse = recurse_on_match or not match
                should_recurse_folder = only_folders or path.is_dir()
                if should_recurse and should_recurse_folder:
                    to_traverse += list(extract_children_to_recurse_on(path))

    def rmtree(
        self,
        *,
        missing_ok: bool = False,
        remove_root: bool = True,
        ignore_errors: bool = False,
    ) -> None:
        context = (
            contextlib.suppress(FileNotFoundError)
            if missing_ok
            else contextlib.nullcontext()
        )
        with context:
            shutil.rmtree(self, ignore_errors=ignore_errors, onerror=self._on_error)  # type: ignore[arg-type]
        if not remove_root:
            self.mkdir()

    @classmethod
    def _on_error(
        cls,
        _: bool,  # noqa: FBT001
        path_str: str,
        exc_info: tuple[type[Exception], Exception, TracebackType],
    ) -> None:
        if exc_info[0] is PermissionError and os.name == "nt":  # pragma: nocover
            path = Path(path_str)
            path.chmod(0o777)
            path.unlink()
        else:
            raise exc_info[0]

    def subpath(self: PathType, *parts: str) -> PathType:
        path = self
        tokens_to_replace = self._flavour.sep, "."
        for part in parts:
            for token in tokens_to_replace:
                part = part.replace(token, "_")  # noqa: PLW2901
            path /= part
        return path

    @classmethod
    def from_uri(cls: type[PathType], uri: str) -> PathType:
        path_str = urllib.parse.urlparse(uri).path
        return cls(path_str)

    @classmethod
    def tempfile(
        cls: type[PathType],
        *,
        in_memory: bool = True,
        create: bool = True,
        **kwargs: Any,
    ) -> PathType:
        """Usage:

        with Path.tempfile() as tmp:     run_command(log_file=tmp)     logs = tmp.text
        process_logs(logs)
        """
        if in_memory:
            in_memory_folder = cls("/") / "dev" / "shm"
            if in_memory_folder.exists():
                kwargs["dir"] = in_memory_folder
        file_handle, path_str = tempfile.mkstemp(**kwargs)
        os.close(file_handle)
        path = cls(path_str)
        if not create:
            path.unlink()
        return path

    @classmethod
    def tempdir(cls: type[PathType], *, in_memory: bool = True) -> PathType:
        path = cls.tempfile(in_memory=in_memory, create=False)
        path.mkdir()
        return path

    def __enter__(self: PathType) -> PathType:
        return self

    def __exit__(self, *_: object) -> None:
        if self.is_file():
            self.unlink(missing_ok=True)
        else:
            self.rmtree(missing_ok=True)
