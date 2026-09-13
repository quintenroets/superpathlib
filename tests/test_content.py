import operator
from collections.abc import Callable
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

    @property
    def id(self) -> str:
        return f"{self.setter}_to_{self.getter or self.setter}"


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
    ids=operator.attrgetter("id"),
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
