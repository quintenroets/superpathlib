import io
import os

from pathlib import Path as BasePath, _posix_flavour, _windows_flavour

# Long import times relative to their usage frequency: lazily imported
# import yaml
# import subprocess

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


def create_parents(func):
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except FileNotFoundError:
            path = args[0]
            # exist_ok=True: catch race conditions when calling multiple times
            path.parent.mkdir(parents=True, exist_ok=True)
            res = func(*args, **kwargs)
        return res
    return wrapper


"""
Extend pathlib functionality and enable further extensions by inheriting
"""


class Path(BasePath):
    _flavour = _windows_flavour if os.name == 'nt' else _posix_flavour  # needed to inherit from pathlib.Path

    @create_parents
    def touch(self, mode=0o666, exist_ok=True, mtime=None):
        super().touch(mode=mode, exist_ok=exist_ok)
        if mtime is not None:
            self.mtime = mtime  # set time after touch or it is immediately overwritten

    @catch_missing(default=0)
    def rmdir(self):
        return super().rmdir()

    def iterdir(self, missing_ok=True):
        children = [] if missing_ok and not self.exists() else super().iterdir()
        return children
    
    def rename(self, target):
        target.parent.mkdir(parents=True, exist_ok=True)
        return super().rename(target)

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
        :param content: Content to be saved in yaml format
        :param names: subnames to add to path before writing
        :return: yaml dump result
        """
        
        import yaml # lazy import
        
        path = self.subpath(*names, suffix=yaml_suffix)
        with path.open("w") as fp:
            return yaml.dump(content, fp, Dumper=yaml.CDumper)  # C implementation much faster

    def load(self, *names, trusted=False):
        """
        :param names: subnames to add to path before reading
        :param trusted: if the path is trusted, an unsafe loader can be used to instantiate any object
        :return: Content in path that contains yaml format
        """
        
        import yaml # lazy import
        
        path = self.subpath(*names, suffix=yaml_suffix)
        with path.open() as fp:
            loader = yaml.CUnsafeLoader if trusted else yaml.CFullLoader  # C implementation much faster
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

    def rmtree(self, missing_ok=False):
        for path in self.iterdir():
            if path.is_dir():
                path.rmtree()
            else:
                path.unlink()
        self.rmdir()
    
    
    """
    Add properties to read and write path content and metadata
    """
    @property
    def content(self):
        return self.load()
    
    @content.setter
    def content(self, value):
        return self.save(value)
    
    @property
    def byte_content(self):
        return self.read_bytes()
    
    @byte_content.setter
    def byte_content(self, value):
        return self.write_bytes(value)
    
    @property
    def text(self):
        return self.read_text()
    
    @text.setter
    def text(self, value):
        return self.write_text(value)
    
    @property
    def lines(self):
        return self.text.split("\n")

    @property
    @catch_missing(default=0.0)
    def mtime(self):
        return self.stat().st_mtime
        
    @mtime.setter
    def mtime(self, time: float):
        os.utime(self, (time, time)) # set create time as well
        import subprocess
        try:
            subprocess.run(('touch', '-d', f'@{time}', self))
        except subprocess.CalledProcessError:
            pass # Doesn't work on Windows
        
    @property
    def tags(self):
        from .tags import XDGTags
        return XDGTags(self).get()
    
    @tags.setter
    def tags(self, *values):
        from .tags import XDGTags
        if len(values) == 1 and values[0] == None:
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
    
    
    def copy_to(self, dest):
        dest.byte_content = self.byte_content
    
    """
    Add common folders
    Make the common folders properties with classmethods such that 
    all child classes have common folders with all the right properties and methods
    """
    
    @classmethod
    @property
    def HOME(cls):
        return cls.home()
    
    @classmethod
    @property
    def docs(cls):
        return cls.HOME / "Documents"
    
    @classmethod
    @property
    def scripts(cls):
        return cls.docs / "Scripts"
    
    @classmethod
    @property
    def script_assets(cls):
        return cls.HOME / ".config" / "scripts"
    
    @classmethod
    @property
    def assets(cls):
        """
        Often overwritten by child classes for specific project
        """
        return cls.HOME / ".config" / "scripts"
