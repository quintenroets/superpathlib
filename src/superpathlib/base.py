import os
import pathlib
import sys


class Path(pathlib.Path):
    """
    Extend pathlib functionality and enable further extensions by inheriting.
    """

    # _flavour attribute explicitly required to inherit from pathlib
    if sys.version_info.minor <= 11:
        _flavour = (
            pathlib._windows_flavour  # type: ignore[attr-defined] # noqa
            if os.name == "nt"
            else pathlib._posix_flavour  # type: ignore[attr-defined] # noqa
        )
    else:  # pragma: nocover
        _flavour = (
            pathlib.ntpath  # type: ignore[attr-defined] # noqa
            if os.name == "nt"
            else pathlib.posixpath  # type: ignore[attr-defined] # noqa
        )
