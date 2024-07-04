import typing
from typing import Any

from package_utils.storage import CachedFileContent
from superpathlib import Path

from tests.content import byte_content, text_content
from tests.utils import ignore_fixture_warning


@ignore_fixture_warning
@byte_content
def test_bytes(path: Path, content: bytes) -> None:
    class Storage:
        content = path.cached_byte_content

    verify_storage(Storage, content)


@text_content
def test_text(content: str) -> None:
    with Path.tempfile() as path:

        class Storage:
            content = path.cached_text

        verify_storage(Storage, content)


@ignore_fixture_warning
@text_content
def test_content(path: Path, content: dict[str, dict[str, str]]) -> None:
    class Storage:
        content: CachedFileContent[dict[str, dict[str, str]]] = typing.cast(
            CachedFileContent[dict[str, dict[str, str]]],
            path.cached_content,
        )

    verify_storage(Storage, content)


@ignore_fixture_warning
@text_content
def test_created_content(path: Path, content: dict[str, dict[str, str]]) -> None:
    class Storage:
        content: CachedFileContent[dict[str, dict[str, str]]] = typing.cast(
            CachedFileContent[dict[str, dict[str, str]]],
            path.create_cached_content({}),
        )

    verify_storage(Storage, content)


def verify_storage(
    storage_class: type[Any],
    content: str | bytes | dict[str, dict[str, str]],
) -> None:
    storage = storage_class()
    assert storage.content is not None
    storage.content = content
    assert storage.content == content
