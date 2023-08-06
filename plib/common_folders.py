from __future__ import annotations

from . import base


class Path(base.Path):
    """
    Expose common folders as attributes use properties and classmethods to ensure same
    behavior for child classes.
    """

    @classmethod
    @property
    def HOME(cls) -> Path:  # noqa
        return cls.home()

    @classmethod
    @property
    def docs(cls) -> Path:  # noqa
        return cls.HOME / "Documents"

    @classmethod
    @property
    def scripts(cls) -> Path:  # noqa
        return cls.docs / "Scripts"

    @classmethod
    @property
    def script_assets(cls) -> Path:  # noqa
        return cls.scripts / "assets"

    @classmethod
    @property
    def assets(cls) -> Path:  # noqa
        """
        Often overwritten by child classes for specific project.
        """
        return cls.script_assets  # noqa

    @classmethod
    @property
    def draft(cls) -> Path:  # noqa
        return cls.docs / "draft.txt"
