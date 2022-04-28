from __future__ import annotations  # https://www.python.org/dev/peps/pep-0563/

import io
import os
import pathlib
from functools import wraps
from typing import Any, Iterable, List

from .utils import find_first_match

# Long import times relative to their usage frequency: lazily imported
# import json
# import yaml
# import subprocess
# import tempfile


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


def create_parents(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except FileNotFoundError:
            path = args[0]
            path.create_parent()
            res = func(*args, **kwargs)
        return res

    return wrapper


class Path(pathlib.Path):
    """
    Extend pathlib functionality and enable further extensions by inheriting
    """

    _flavour = (
        pathlib._windows_flavour if os.name == "nt" else pathlib._posix_flavour
    )  # _flavour attribute needs to inherited explicitely from pathlib

    """
    Overwrite existing methods with exception handling and default values
    """

    @create_parents
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
        target = Path(target)
        target.create_parent()
        try:
            target = super().rename(target)
        except OSError:
            # thrown when target is on different filesystem
            import shutil  # noqa:autoimport

            target = shutil.move(self, target)
        return target

    def create_parent(self):
        self.parent.mkdir(parents=True, exist_ok=True)
        return self.parent

    def with_nonexistent_name(self):
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

    def with_timestamp(self):
        import time  # noqa: autoimport
        from datetime import datetime  # noqa: autoimport

        timestamp = datetime.fromtimestamp(int(time.time()))  # precision up to second
        return self.with_stem(f"{self.stem} {timestamp}")

    def open(self, mode="r", **kwargs):
        try:
            res = super().open(mode, **kwargs)
        except FileNotFoundError:
            if "w" in mode or "a" in mode:
                # exist_ok=True: catch race conditions when calling multiple times
                self.create_parent()
                res = super().open(mode, **kwargs)
            elif "b" in mode:
                res = io.BytesIO(b"")
            else:
                res = io.StringIO("")
            return res
        return res

    """
    Properties to read & write content in different formats
    """

    @property
    def byte_content(self) -> bytes:
        return self.read_bytes()

    @byte_content.setter
    def byte_content(self, value: bytes) -> None:
        self.write_bytes(value)

    @property
    def text(self) -> str:
        return self.read_text()

    @text.setter
    def text(self, value: str) -> None:
        self.write_text(value)

    @property
    def lines(self) -> List[str]:
        lines = self.text.strip().split("\n")
        lines = [l for l in lines if l]
        return lines

    @lines.setter
    def lines(self, lines: Iterable[Any]) -> None:
        self.text = "\n".join(str(line) for line in lines)

    @property
    def json(self):
        import json  # noqa: autoimport

        return json.loads(self.text or "{}")

    @json.setter
    def json(self, content):
        import json  # noqa: autoimport

        self.text = json.dumps(content)

    @property
    def yaml(self):
        import yaml  # noqa: autoimport

        # C implementation much faster but only supported on Linux
        Loader = yaml.CFullLoader if hasattr(yaml, "CFullLoader") else yaml.FullLoader
        return yaml.load(self.text, Loader=Loader) or {}

    @yaml.setter
    def yaml(self, value):
        import yaml  # noqa: autoimport

        # C implementation much faster but only supported on Linux
        Dumper = yaml.CDumper if hasattr(yaml, "CDumper") else yaml.Dumper
        self.text = yaml.dump(value, Dumper=Dumper, width=1024)

    @property
    def content(self):
        return self.yaml_path.yaml

    @content.setter
    def content(self, value):
        self.yaml_path.yaml = value

    @property
    def yaml_path(self):
        return (
            self.with_suffix(".yaml") if self.suffix not in (".yaml", ".yml") else self
        )

    """
    Properties to read & write metadata
    """

    @property
    @catch_missing(default=0.0)
    def mtime(self):
        return self.stat().st_mtime

    @mtime.setter
    def mtime(self, time: float):
        os.utime(self, (time, time))  # set create time as well

        import subprocess  # noqa: autoimport

        try:
            subprocess.run(("touch", "-d", f"@{time}", self))
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

    """
    Additional functionality
    """

    def copy_to(self, dest):
        dest.byte_content = self.byte_content

    def is_empty(self):
        return (
            not self.exists()
            or (self.is_dir() and next(self.iterdir(), None) == None)
            or self.size == 0
        )

    def write(self, content):
        if isinstance(content, str):
            self.write_text(content)
        elif isinstance(content, bytes):
            self.write_bytes(content)
        else:
            self.save(content)

    def load(self, trusted=False):
        """
        :param trusted: if the path is trusted, an unsafe loader can be used to instantiate any object
        :return: Content in path that contains yaml format
        """
        import yaml  # noqa: autoimport

        loader = yaml.CUnsafeLoader if trusted else yaml.CFullLoader
        return yaml.load(self.yaml_path.text, Loader=loader) or {}

    def save(self, content):
        self.content = content

    def update(self, value):
        # only read and write if value to add not empty
        if value:
            content = self.content | value
            self.content = content
            return content

    def find(
        self,
        condition=None,
        exclude=None,
        recurse_on_match=False,
        follow_symlinks=False,
        only_folders=False,
    ):
        """
        Find all subpaths under path that match condition

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
    def tempfile(cls, **kwargs) -> Path:
        """
        Usage:
            with Path.tempfile() as tmp:
                run_command(log_file=tmp)
                logs = tmp.text
            process_logs(logs)
        """
        import tempfile  # noqa: autoimport

        _, path = tempfile.mkstemp(**kwargs)
        return cls(path)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.unlink()

    """
    Common folders: properties with classmethods such that 
    all child classes have common folders with all the right properties and methods
    """

    @classmethod
    @property
    def HOME(cls) -> Path:
        return cls.home()

    @classmethod
    @property
    def docs(cls) -> Path:
        return cls.HOME / "Documents"

    @classmethod
    @property
    def scripts(cls) -> Path:
        return cls.docs / "Scripts"

    @classmethod
    @property
    def script_assets(cls) -> Path:
        return cls.scripts / "assets"

    @classmethod
    @property
    def assets(cls) -> Path:
        """
        Often overwritten by child classes for specific project
        """
        return cls.script_assets

    @classmethod
    @property
    def draft(cls) -> Path:
        return cls.docs / "draft.txt"
