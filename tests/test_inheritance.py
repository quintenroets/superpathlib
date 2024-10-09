from simple_classproperty import classproperty

import superpathlib
from superpathlib.common_folders import T


def test_inheritance() -> None:
    class Path(superpathlib.Path):
        @classmethod
        @classproperty
        def HOME(cls: type[T]) -> T:
            return cls("HOME")

    assert Path.docs.is_relative_to(Path.HOME)
