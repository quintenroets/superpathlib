import os
import shutil
import tempfile
import time
import typing
import urllib.parse
from collections.abc import Callable, Generator
from functools import cached_property
from types import TracebackType
from typing import Any, TypeVar

from . import cached_content
from .utils import find_first_match

PathType = TypeVar("PathType", bound="Path")

# Long import times relative to usage frequency: lazy imports
# from datetime import datetime
# import dirhash


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
        from datetime import datetime  # noqa: E402, autoimport

        timestamp = datetime.fromtimestamp(int(time.time()))  # precision up to second
        return self.with_stem(f"{self.stem} {timestamp}")

    def copy_to(
        self,
        dest: PathType,
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
        format_ = shutil._find_unpack_format(path_str)  # type: ignore[attr-defined]
        return typing.cast(str, format_)

    def unpack_if_archive(
        self, extract_dir: PathType | None = None, recursive: bool = True
    ) -> None:
        if self.archive_format is not None:
            self.unpack(extract_dir, recursive=recursive)

    def unpack(
        self: PathType,
        extract_dir: PathType | None = None,
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

        def cast_path(casted_path: PathType | None) -> PathType:
            return casted_path  # type: ignore

        if archive_format is None:
            archive_format = self.archive_format

        if extract_dir is None:
            extract_name = self.name
            # noinspection PyProtectedMember
            unpack_formats = shutil._UNPACK_FORMATS  # type: ignore[attr-defined]
            unpack_info = unpack_formats[archive_format]
            for archive_ext in unpack_info[0]:
                if extract_name.endswith(archive_ext):
                    extract_name = extract_name.replace(archive_ext, "")
            extract_dir = self.with_name(extract_name)

        extract_dir = cast_path(extract_dir)

        if remove_existing:
            if extract_dir.is_dir():
                extract_dir.rmtree(missing_ok=True)
            else:
                extract_dir.unlink(missing_ok=True)

        shutil.unpack_archive(self, extract_dir=extract_dir, format=archive_format)

        cleanup(extract_dir)
        if preserve_properties:
            self.copy_properties_to(extract_dir)

        if remove_original:
            self.unlink()

        if recursive:
            for path in extract_dir.find():
                path.unpack_if_archive()

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
        import yaml  # noqa: E402, autoimport

        Loader: type[yaml.CFullLoader | yaml.FullLoader] = (
            yaml.CFullLoader if hasattr(yaml, "CFullLoader") else yaml.FullLoader
        )
        return yaml.load(self.text, Loader=Loader) or {}

    def update(self, value: dict[Any, Any]) -> dict[Any, Any]:
        # only read and write if value to add not empty
        if value:
            current_content = self.yaml
            assert isinstance(current_content, dict)
            updated_content = current_content | value
            self.yaml = updated_content
        else:
            updated_content = value
        return updated_content

    def find(
        self: PathType,
        condition: Callable[[PathType], bool] | None = None,
        exclude: Callable[[PathType], bool] | None = None,
        recurse_on_match: bool = False,
        follow_symlinks: bool = False,
        only_folders: bool = False,
    ) -> Generator[PathType, None, None]:
        """Find all subpaths under path that match condition.

        only_folders option can be used for efficiency reasons
        """
        if condition is None:
            recurse_on_match = True

            def condition(_: PathType) -> bool:
                return True

        if exclude is None:

            def exclude(_: PathType) -> bool:
                return False

        to_traverse = [self] if self.exists() else []
        while to_traverse:
            path = to_traverse.pop(0)

            if not exclude(path):
                match = condition(path)
                if match:
                    yield path

                if not match or recurse_on_match:
                    if only_folders or path.is_dir():
                        try:
                            for child in path.iterdir():
                                if follow_symlinks or not child.is_symlink():
                                    if not only_folders or child.is_dir():
                                        to_traverse.append(child)
                        except PermissionError:  # pragma: nocover
                            # skip folders that do not allow listing
                            pass

    def rmtree(
        self,
        missing_ok: bool = False,
        remove_root: bool = True,
        ignore_errors: bool = False,
    ) -> None:
        try:
            shutil.rmtree(self, ignore_errors=ignore_errors, onerror=self._on_error)  # type: ignore
        except FileNotFoundError as exception:
            if missing_ok:
                pass
            else:
                raise exception
        if not remove_root:
            self.mkdir()

    @classmethod
    def _on_error(
        cls,
        _: bool,
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
                part = part.replace(token, "_")
            path /= part
        return path

    @classmethod
    def from_uri(cls: type[PathType], uri: str) -> PathType:
        path_str = urllib.parse.urlparse(uri).path
        return cls(path_str)

    @classmethod
    def tempfile(
        cls: type[PathType], in_memory: bool = True, create: bool = True, **kwargs: Any
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
    def tempdir(cls: type[PathType], in_memory: bool = True) -> PathType:
        path = cls.tempfile(in_memory=in_memory, create=False)
        path.mkdir()
        return path

    def __enter__(self: PathType) -> PathType:
        return self

    def __exit__(self, *_: Any) -> None:
        if self.is_file():
            self.unlink(missing_ok=True)
        else:
            self.rmtree(missing_ok=True)
