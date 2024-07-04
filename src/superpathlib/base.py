import os
import pathlib
import sys


class Path(pathlib.Path):  # pragma: nocover
    """
    Extend pathlib functionality and enable further extensions by inheriting.
    """

    # _flavour attribute explicitly required to inherit from pathlib
    if sys.version_info < (3, 12):
        _flavour = (
            pathlib._windows_flavour  # type: ignore[attr-defined] # noqa: SLF001
            if os.name == "nt"
            else pathlib._posix_flavour  # type: ignore[attr-defined] # noqa: SLF001
        )
    else:
        _flavour = (
            pathlib.ntpath  # type: ignore[attr-defined]
            if os.name == "nt"
            else pathlib.posixpath  # type: ignore[attr-defined]
        )
