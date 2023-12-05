import os
import pathlib


class Path(pathlib.Path):
    """
    Extend pathlib functionality and enable further extensions by inheriting.
    """

    # _flavour attribute explicitly required to inherit from pathlib
    _flavour = (
        pathlib._windows_flavour  # type: ignore # noqa
        if os.name == "nt"
        else pathlib._posix_flavour  # type: ignore[attr-defined] # noqa
    )