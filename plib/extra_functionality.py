from __future__ import annotations

import shutil
import tempfile
import time
import urllib.parse
from collections.abc import Callable, Generator
from functools import cached_property
from typing import Any, TypeVar

from . import metadata_properties
from .utils import find_first_match

PathType = TypeVar("PathType", bound="Path")

# Long import times relative to usage frequency: lazy imports
# from datetime import datetime
# import dirhash


class Path(metadata_properties.Path):
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
        return shutil._find_unpack_format(str(self))  # type: ignore[attr-defined]

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
            (cleanup_path / "__MACOSX").rmtree()
            subfolder = cleanup_path / cleanup_path.name
            if subfolder.exists() and cleanup_path.number_of_children == 1:
                subfolder.pop_parent()

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
            extract_dir.rmtree()

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
        else:
            # merge in existing folder
            shutil.copytree(temp_dest, dest, dirs_exist_ok=True)
            temp_dest.rmtree()

    def is_empty(self) -> bool:
        return (
            not self.exists()
            or (self.is_dir() and next(self.iterdir(), None) is None)
            or (self.is_file() and self.size == 0)
        )

    def load_yaml(self, trusted: bool = False) -> dict | list:
        """
        :param trusted: if the path is trusted, an unsafe loader
                        can be used to instantiate any object
        :return: Content in path that contains yaml format
        """
        import yaml  # noqa: E402, autoimport

        Loader: type[yaml.CFullLoader | yaml.FullLoader] = (
            yaml.CFullLoader if hasattr(yaml, "CFullLoader") else yaml.FullLoader
        )
        return yaml.load(self.text, Loader=Loader) or {}

    def update(self, value: dict) -> dict:
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
        condition: Callable | None = None,
        exclude: Callable | None = None,
        recurse_on_match: bool = False,
        follow_symlinks: bool = False,
        only_folders: bool = False,
    ) -> Generator[PathType, None, None]:
        """Find all subpaths under path that match condition.

        only_folders option can be used for efficiency reasons
        """
        if condition is None:
            recurse_on_match = True

            def condition(_: Any) -> bool:
                return True

        if exclude is None:

            def exclude(_: Any) -> bool:
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
                        except PermissionError:
                            pass  # skip folders that do not allow listing

    def rmtree(self, missing_ok: bool = False, remove_root: bool = True) -> None:
        for path in self.iterdir():
            if path.is_dir() and not path.is_symlink():
                path.rmtree()
            else:
                path.unlink()
        if remove_root:
            self.rmdir()

    def subpath(self: PathType, *parts: str) -> PathType:
        path = self
        for part in parts:
            path /= part.replace(self._flavour.sep, "_")
        return path

    @classmethod
    def from_uri(cls: type[PathType], uri: str) -> PathType:
        path_str = urllib.parse.urlparse(uri).path
        return cls(path_str)

    @classmethod
    def tempfile(
        cls: type[PathType], in_memory: bool = True, **kwargs: Any
    ) -> PathType:
        """Usage:

        with Path.tempfile() as tmp:     run_command(log_file=tmp)     logs = tmp.text
        process_logs(logs)
        """
        if in_memory:
            in_memory_folder = cls("/") / "dev" / "shm"
            if in_memory_folder.exists():
                kwargs["dir"] = in_memory_folder
        _, path = tempfile.mkstemp(**kwargs)
        return cls(path)

    def __enter__(self: PathType) -> PathType:
        return self

    def __exit__(self, *_: Any) -> None:
        if self.is_file():
            self.unlink(missing_ok=True)
        else:
            self.rmtree()
