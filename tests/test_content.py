import numpy as np

from superpathlib import Path
from tests.content import Given, slower_test_settings
from tests.utils import ignore_fixture_warning


@ignore_fixture_warning
@Given.bytes
def test_bytes(path: Path, content: bytes) -> None:
    assert isinstance(Path.byte_content, property)
    path.byte_content = content
    assert path.byte_content == content


@ignore_fixture_warning
@Given.text
def test_text(path: Path, content: str) -> None:
    assert isinstance(Path.text, property)
    path.text = content
    assert path.text == content


@ignore_fixture_warning
@Given.lines
def test_lines(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.lines = content
    assert path.lines == "\n".join(content).splitlines()


@ignore_fixture_warning
@Given.lines
def test_content_lines(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.content_lines == text_lines


@ignore_fixture_warning
@Given.lines
def test_content_lines_setter(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.content_lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.content_lines == text_lines


@slower_test_settings
@Given.dictionaries
def test_json(path: Path, content: dict[str, dict[str, str]]) -> None:
    assert isinstance(Path.json, property)
    path.json = content
    assert path.json == content


@slower_test_settings
@Given.dictionaries
def test_yaml(path: Path, content: dict[str, dict[str, str]]) -> None:
    assert isinstance(Path.yaml, property)
    path.yaml = content
    assert path.yaml == content


def test_missing_content(path: Path) -> None:
    path.unlink()
    assert path.text == ""
    assert path.yaml is None
    assert path.json is None


@slower_test_settings
@Given.floats
def test_numpy(path: Path, content: list[float]) -> None:
    assert isinstance(Path.numpy, property)
    numpy_content = np.array(content)
    path.numpy = numpy_content
    assert np.array_equal(path.numpy, numpy_content, equal_nan=True)
