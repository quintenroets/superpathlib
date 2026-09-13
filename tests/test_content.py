import operator
from collections.abc import Callable, Iterator
from functools import partial
from typing import Any, NamedTuple

import numpy as np
import pytest
from hypothesis import given, settings, strategies
from hypothesis.strategies import SearchStrategy

from superpathlib import Path
from tests.content import Strategies, slower_test_settings


class ContentProperty(NamedTuple):
    setter: str
    strategy: SearchStrategy[Any]
    equals: Callable[[Any, Any], bool] = operator.eq
    getter_override: str | None = None

    @property
    def getter(self) -> str:
        return self.getter_override or self.setter

    def verify_round_trip(self, path: Path, data: strategies.DataObject) -> None:
        content = data.draw(self.strategy)
        setattr(path, self.setter, content)
        result = getattr(path, self.getter)
        assert self.equals(result, content)


def equals_split_lines(result: list[str], content: list[str]) -> bool:
    return result == "\n".join(content).splitlines()


def equals_non_empty(result: list[str], content: list[str]) -> bool:
    return result == [line for line in content if line]


equals_numpy = partial(np.array_equal, equal_nan=True)

parametrize_content_properties = pytest.mark.parametrize(
    "content_property",
    [
        ContentProperty("byte_content", strategies.binary()),
        ContentProperty("text", Strategies.text),
        ContentProperty("json", Strategies.serializable),
        ContentProperty("yaml", Strategies.serializable),
        ContentProperty("lines", Strategies.lines, equals_split_lines),
        ContentProperty("numpy", Strategies.arrays, equals_numpy),
        ContentProperty("lines", Strategies.lines, equals_non_empty, "content_lines"),
        ContentProperty("content_lines", Strategies.lines, equals_non_empty, "lines"),
    ],
    ids=lambda property_: f"{property_.setter}_to_{property_.getter}",
)


@parametrize_content_properties
@slower_test_settings
@given(data=strategies.data())
def test_content_property(
    path: Path,
    content_property: ContentProperty,
    data: strategies.DataObject,
) -> None:
    content_property.verify_round_trip(path, data)


@parametrize_content_properties
@settings(slower_test_settings, max_examples=2, deadline=3000)
@given(data=strategies.data())
def test_encrypted_content_property(
    encrypted_path: Path,
    content_property: ContentProperty,
    data: strategies.DataObject,
) -> None:
    content_property.verify_round_trip(encrypted_path, data)


def test_content_encrypted_on_disk(encrypted_path: Path) -> None:
    content = b"content"
    encrypted_path.byte_content = content
    assert Path(encrypted_path).byte_content != content


def test_no_double_extension(encrypted_path: Path) -> None:
    assert encrypted_path.encrypted == encrypted_path


@pytest.mark.parametrize("mode", ["w", "wb"])
def test_failed_encrypted_write_keeps_content(encrypted_path: Path, mode: str) -> None:
    content = "content"
    encrypted_path.text = content
    with pytest.raises(RuntimeError), encrypted_path.open(mode):
        raise RuntimeError
    assert encrypted_path.text == content


def test_missing_content(path: Path) -> None:
    path.unlink()
    for missing_path in (path, path.encrypted):
        assert missing_path.text == ""
        assert missing_path.yaml is None
        assert missing_path.json is None


@pytest.fixture
def cache_path(path: Path) -> Iterator[Path]:
    with path.with_name(path.name + ".cache") as cache_path:
        yield cache_path


@pytest.mark.usefixtures("cache_path")
def test_fresh_cache_used(path: Path) -> None:
    path.yaml = {"cached": {}}
    mtime = path.mtime
    assert path.cached_yaml == {"cached": {}}
    path.yaml = {"ignored": {}}
    path.mtime = mtime
    assert path.cached_yaml == {"cached": {}}


def test_stale_cache_refreshed_through_json(path: Path, cache_path: Path) -> None:
    path.yaml = {2025: "a"}
    cache_path.json = {"outdated": {}}
    path.mtime = cache_path.mtime - 1
    assert path.cached_yaml == {"2025": "a"}


def test_missing_file_ignores_cache(path: Path, cache_path: Path) -> None:
    path.unlink()
    cache_path.json = {"stale": {}}
    assert path.cached_yaml is None
    assert cache_path.json == {"stale": {}}
