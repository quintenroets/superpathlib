from __future__ import annotations

from simple_classproperty import classproperty

from . import base


class Path(base.Path):
    """Expose common folders as attributes.

    Use classmethod properties to ensure child classes return instance
    of child class. The classmethod and property decorators are combined
    in a single decorated because chaining them directly is deprecated
    since python3.11.
    """

    @classproperty
    def HOME(cls) -> Path:
        return cls.home()

    @classproperty
    def docs(cls) -> Path:
        return cls.HOME / "Documents"

    @classproperty
    def scripts(cls) -> Path:
        return cls.docs / "Scripts"

    @classproperty
    def script_assets(cls) -> Path:  # noqa
        return cls.scripts / "assets"

    @classproperty
    def assets(cls) -> Path:  # noqa
        """
        Often overwritten by child classes for specific project.
        """
        return cls.script_assets  # noqa

    @classproperty
    def draft(cls) -> Path:  # noqa
        return cls.docs / "draft.txt"
