import io
import os

import yaml
from pathlib import Path as BasePath, _posix_flavour, _windows_flavour

yaml_suffix = ".yaml"


def catch_missing(default=None):
    def wrap_function(func):
        def wrap_args(*args, **kwargs):
            try:
                res = func(*args, **kwargs)
            except FileNotFoundError:
                res = default
            return res
        return wrap_args
    return wrap_function


"""
Extend pathlib functionality and enable further extensions by inheriting
"""


class Path(BasePath):
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour  # needed to inherit from pathlib Path
    trusted = False  # property can be set by projects that use trusted config files

    @catch_missing(default=0)
    def mtime(self):
        return int(self.stat().st_mtime)  # no huge precision needed

    @catch_missing(default=0)
    def size(self):
        return self.stat().st_size

    @catch_missing(default=[])
    def iterdir(self):
        return super().iterdir()

    def is_root(self):
        path = self
        while not path.exists():
            path = path.parent
        return path.stat().st_uid == 0

    def write(self, content):
        if isinstance(content, str):
            self.write_text(content)
        elif isinstance(content, bytes):
            self.write_bytes(content)
        else:
            self.save(content)

    def open(self, mode='r', **kwargs):
        try:
            res = super().open(mode, **kwargs)
        except FileNotFoundError:
            if 'w' in mode:
                # exist_ok=True: catch race conditions when calling multiple times
                self.parent.mkdir(parents=True, exist_ok=True)
                res = super().open(mode, **kwargs)
            elif 'b' in mode:
                res = io.BytesIO(b"")
            else:
                res = io.StringIO("")
            return res
        return res

    def save(self, content, *names):
        """
        Exports content to path in yaml format
        """
        path = self.subpath(*names, suffix=yaml_suffix)
        with path.open("w") as fp:
            return yaml.dump(content, fp, Dumper=yaml.CDumper)  # CDumper much faster

    def load(self, *names):
        """
        Load content from path in yaml format
        """
        path = self.subpath(*names, suffix=yaml_suffix)
        with path.open() as fp:
            loader = yaml.CLoader if Path.trusted else yaml.CSafeLoader  # unsafe Cloader is faster
            content = yaml.load(fp, Loader=loader) or {}
            return content

    def subpath(self, *names, suffix=None):
        """
        Returns new path with subnames and suffix added
        """
        path = self
        for name in names:
            path /= name
        if suffix is not None and path.suffix != suffix:
            path = path.with_suffix(suffix)
        return path

    def find(self, condition=None, exclude=None, recurse_on_match=False, follow_symlinks=True, only_folders=False):
        """
        Find all subpaths under path that match condition

        only_folders can be used for efficiency reasons
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


"""
Add common folders
this needs to be done in separate class to give all folders the extended functionality
"""


class Path(Path):
    HOME = Path.home()
    docs = HOME / "Documents"
    scripts = docs / "Scripts"
    assets = HOME / ".config" / "scripts"
