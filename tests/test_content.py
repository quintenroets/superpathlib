import operator
from collections.abc import Callable, Iterator
from functools import partial
from typing import Any, NamedTuple

import numpy as np
import pytest
from hypothesis import given, strategies
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


def equals_split_lines(result: list[str], content: list[str]) -> bool:
    return result == "\n".join(content).splitlines()


def equals_non_empty(result: list[str], content: list[str]) -> bool:
    return result == [line for line in content if line]


equals_numpy = partial(np.array_equal, equal_nan=True)


@pytest.mark.parametrize(
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
@slower_test_settings
@given(data=strategies.data())
def test_content_property(
    path: Path,
    content_property: ContentProperty,
    data: strategies.DataObject,
) -> None:
    content = data.draw(content_property.strategy)
    setattr(path, content_property.setter, content)
    result = getattr(path, content_property.getter)
    assert content_property.equals(result, content)


def test_missing_content(path: Path) -> None:
    path.unlink()
    assert path.text == ""
    assert path.yaml is None
    assert path.json is None


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
