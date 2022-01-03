import io
import os
from typing import Optional

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
Add extra functionality to pathlib
"""
class Path(BasePath):
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour # needed to enherit from pathlib Path
    trusted = False # property can be set by projects that use trusted config files

    def open(self, **kwargs):
        try:
            res = super().open(**kwargs)
        except FileNotFoundError:
            mode = kwargs.get('mode', 'r')
            if 'w' in mode:
                self.parent.mkdir(parents=True)
                res = super().open(**kwargs)
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
        self = self.subpath(*names, suffix=yaml_suffix)
        with self.open("w") as fp:
            return yaml.dump(content, fp, Dumper=yaml.CDumper) # CDumper much faster

    def load(self, *names):
        """
        Load content from path in yaml format
        """
        self = self.subpath(*names, suffix=yaml_suffix)
        with self.open() as fp:
            loader = yaml.CLoader if Path.trusted else yaml.SafeLoader # unsafe Cloader is much faster
            content = yaml.load(fp, Loader=loader) or {}
            return content

    @catch_missing(default=0)
    def mtime(self):
        return int(self.stat().st_mtime) # no huge precision needed

    @catch_missing(default=0)
    def size(self):
        return self.stat().st_size

    def is_root(self):
        while not self.exists():
            self = self.parent
        return self.stat().st_uid == 0

    def write(self, content):
        if isinstance(content, str):
            self.write_text(content)
        elif isinstance(content, bytes):
            self.write_bytes(content)
        else:
            self.save(content)

    def subpath(self, *names, suffix=None):
        """
        Returns new path with subnames and suffix added
        """
        for name in names:
            self /= name
        if suffix is not None and self.suffix != suffix:
            self = self.with_suffix(suffix)
        return self

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
                            pass # skip folders that do not allow listing


"""
Add common folders
this needs to be done in separate class to give all folders the extended functionality
"""
class Path(Path):
    HOME = Path.home()
    docs = HOME / "Documents"
    scripts = docs / "Scripts"
    assets = HOME / ".config" / "scripts"
