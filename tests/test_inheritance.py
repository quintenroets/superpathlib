from typing import Self

from simple_classproperty import classproperty

import superpathlib


def test_inheritance() -> None:
    class Path(superpathlib.Path):
        @classmethod
        @classproperty
        def HOME(cls) -> Self:  # noqa: N802
            return cls("HOME")

    assert Path.docs.is_relative_to(Path.HOME)
