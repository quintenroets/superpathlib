from __future__ import annotations

import shutil
import tempfile
import time
import urllib.parse
from functools import cached_property

from . import metadata_properties
from .utils import find_first_match

# Long import times relative to usage frequency: lazy imports
# from datetime import datetime
# import dirhash


class Path(metadata_properties.Path):
    """
    Additional functionality.
    """

    def create_parent(self) -> Path:
        self.parent.mkdir(parents=True, exist_ok=True)
        return self.parent

    def with_nonexistent_name(self) -> Path:
        path = self
        if path.exists():
            stem = path.stem

            def with_number(i: int):
                return path.with_stem(f"{stem} ({i})")

            def nonexistent(i):
                return not with_number(i).exists()

            first_free_number = find_first_match(nonexistent)
            path = with_number(first_free_number)

        return path

    def with_timestamp(self) -> Path:
        from datetime import datetime  # noqa: autoimport

        timestamp = datetime.fromtimestamp(int(time.time()))  # precision up to second
        return self.with_stem(f"{self.stem} {timestamp}")

    def copy_to(self, dest: Path, include_properties=True, only_if_newer=False):
        if not only_if_newer or self.mtime > dest.mtime:
            dest.byte_content = self.byte_content
            if include_properties:
                self.copy_properties_to(dest)

    def copy_properties_to(self, dest: Path):
        for path in dest.find():
            path.tag = self.tag
            path.mtime = self.mtime

    @cached_property
    def archive_format(self) -> str:
        return shutil._find_unpack_format(str(self))  # noqa

    def unpack_if_archive(self, extract_dir: Path = None, recursive=True):
        if self.archive_format is not None:
            self.unpack(extract_dir, recursive=recursive)

    def unpack(
        self,
        extract_dir: Path | None = None,
        remove_existing: bool = True,
        preserve_properties: bool = True,
        remove_original: bool = True,
        archive_format: str = None,
        recursive: bool = True,
    ):
        def cleanup(path: Path):
            (path / "__MACOSX").rmtree()
            subfolder = path / path.name
            if subfolder.exists() and path.number_of_children == 1:
                subfolder.pop_parent()

        if archive_format is None:
            archive_format = self.archive_format

        if extract_dir is None:
            extract_name = self.name
            unpack_info = shutil._UNPACK_FORMATS[archive_format]  # noqa
            for archive_ext in unpack_info[0]:
                if extract_name.endswith(archive_ext):
                    extract_name = extract_name.replace(archive_ext, "")
            extract_dir = self.with_name(extract_name)

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

    def pop_parent(self):
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

    def is_empty(self):
        return (
            not self.exists()
            or (self.is_dir() and next(self.iterdir(), None) is None)
            or (self.is_file() and self.size == 0)
        )

    def load_yaml(self, trusted=False):
        """
        :param trusted: if the path is trusted, an unsafe loader
                        can be used to instantiate any object
        :return: Content in path that contains yaml format
        """
        import yaml  # noqa: autoimport

        loader = yaml.CUnsafeLoader if trusted else yaml.CFullLoader
        return yaml.load(self.text, Loader=loader) or {}

    def update(self, value):
        # only read and write if value to add not empty
        if value:
            updated_content = self.yaml | value
            self.yaml = updated_content
            return updated_content

    def find(
        self,
        condition=None,
        exclude=None,
        recurse_on_match=False,
        follow_symlinks=False,
        only_folders=False,
    ):
        """Find all subpaths under path that match condition.

        only_folders option can be used for efficiency reasons
        """
        if condition is None:
            recurse_on_match = True

            def condition(_):
                return True

        if exclude is None:

            def exclude(_):
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

    def rmtree(self, missing_ok=False, remove_root=True):
        for path in self.iterdir():
            if path.is_dir():
                path.rmtree()
            else:
                path.unlink()
        if remove_root:
            self.rmdir()

    def subpath(self, *parts):
        path = self
        for part in parts:
            path /= part.replace(self._flavour.sep, "_")
        return path

    @classmethod
    def from_uri(cls, uri: str):
        path_str = urllib.parse.urlparse(uri).path
        return cls(path_str)

    @classmethod
    def tempfile(cls, in_memory=True, **kwargs) -> Path:
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

    def __enter__(self):
        return self

    def __exit__(self, *_):
        if self.is_file():
            self.unlink(missing_ok=True)
        else:
            self.rmtree()
