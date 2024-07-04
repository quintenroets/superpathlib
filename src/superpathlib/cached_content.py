from __future__ import annotations

import typing
from functools import cached_property
from typing import Any, TypeVar

from . import metadata_properties

if typing.TYPE_CHECKING:  # pragma: nocover
    from package_utils.storage import CachedFileContent

T = TypeVar("T")


class Path(metadata_properties.Path):
    """
    Properties to for cached file content.
    """

    @cached_property
    def cached_content(self) -> CachedFileContent[dict[str, str]]:
        from package_utils.storage import CachedFileContent

        return CachedFileContent(self, default={})  # type: ignore[arg-type]

    def create_cached_content(self, default: T) -> CachedFileContent[T]:
        from package_utils.storage import CachedFileContent

        return CachedFileContent(self, default=default)  # type: ignore[arg-type]

    @cached_property
    def cached_text(self) -> CachedFileContent[str]:
        from package_utils.storage import CachedFileContent

        def load_function(_: Any) -> str:
            return self.text

        def save_function(_: Any, content: str) -> None:
            self.text = content

        return CachedFileContent(
            self,  # type: ignore[arg-type]
            default="",
            load_function=load_function,
            save_function=save_function,
        )

    @cached_property
    def cached_byte_content(self) -> CachedFileContent[bytes]:
        from package_utils.storage import CachedFileContent

        def load_function(_: Any) -> bytes:
            return self.byte_content

        def save_function(_: Any, content: bytes) -> None:
            self.byte_content = content

        return CachedFileContent(
            self,  # type: ignore[arg-type]
            default=b"",
            load_function=load_function,
            save_function=save_function,
        )
