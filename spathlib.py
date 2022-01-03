import os
import yaml
from pathlib import Path as BasePath, _posix_flavour, _windows_flavour

yaml_suffix = ".yaml"

"""
Add extra functionality to pathlib
"""

class Path(BasePath):
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour # needed to enherit from pathlib Path

    HOME = BasePath.home()
    docs = HOME / "Documents"
    scripts = docs / "Scripts"
    assets = HOME / ".config" / "scripts"

    trusted = False # property can be set by projects that use trusted config files

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

    def save(self, content, *names):
        """
        Exports content to path in yaml format
        """
        self = self.subpath(*names, suffix=yaml_suffix)
        try:
            with open(self, "w") as fp:
                res = yaml.dump(content, fp, Dumper=yaml.CDumper) # CDumper much faster
        except FileNotFoundError:
            self.touch()
            res = self.save(content)
        return res

    def load(self, *names):
        """
        Load content from path in yaml format
        """
        self = self.subpath(*names, suffix=yaml_suffix)
        try:
            with open(self) as fp:
                loader = yaml.CLoader if Path.trusted else yaml.SafeLoader # unsafe Cloader is much faster
                content = yaml.load(fp, Loader=loader)
        except FileNotFoundError:
            content = {}

        return content

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
                    if only_folders or self.is_dir():
                        try:
                            for child in self.iterdir():
                                if follow_symlinks or not child.is_symlink():
                                    if not only_folders or child.is_dir():
                                        to_traverse.append(child)
                        except PermissionError:
                            pass # skip folders that do not allow listing

    def mtime(self):
        return int(self.stat().st_mtime) # no huge precision needed

    def size(self):
        try:
            size = self.stat().st_size
        except FileNotFoundError:
            size = 0
        return size
