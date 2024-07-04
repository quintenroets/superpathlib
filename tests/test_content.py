import numpy as np
from superpathlib import Path

from tests.content import (
    byte_content,
    dictionary_content,
    floats_content,
    slower_test_settings,
    text_content,
    text_lines_content,
)
from tests.utils import ignore_fixture_warning


@ignore_fixture_warning
@byte_content
def test_bytes(path: Path, content: bytes) -> None:
    assert isinstance(Path.byte_content, property)
    path.byte_content = content
    assert path.byte_content == content


@ignore_fixture_warning
@text_content
def test_text(path: Path, content: str) -> None:
    assert isinstance(Path.text, property)
    path.text = content
    assert path.text == content


def test_empty_file_text(path: Path) -> None:
    path.unlink()
    assert path.text == ""


def test_empty_file_byte_content(path: Path) -> None:
    path.unlink()
    assert path.byte_content == b""


@ignore_fixture_warning
@text_lines_content
def test_lines(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.lines = content
    assert path.lines == "\n".join(content).splitlines()


@ignore_fixture_warning
@text_lines_content
def test_content_lines(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.content_lines == text_lines


@ignore_fixture_warning
@text_lines_content
def test_content_lines_setter(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.content_lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.content_lines == text_lines


@slower_test_settings
@dictionary_content
def test_json(path: Path, content: dict[str, dict[str, str]]) -> None:
    assert isinstance(Path.json, property)
    path.json = content
    assert path.json == content


@slower_test_settings
@dictionary_content
def test_yaml(path: Path, content: dict[str, dict[str, str]]) -> None:
    assert isinstance(Path.yaml, property)
    path.yaml = content
    assert path.yaml == content


@slower_test_settings
@floats_content
def test_numpy(path: Path, content: list[float]) -> None:
    assert isinstance(Path.numpy, property)
    numpy_content = np.array(content)
    path.numpy = numpy_content
    assert np.array_equal(path.numpy, numpy_content, equal_nan=True)


@ignore_fixture_warning
@byte_content
def test_bytes_in_memory(in_memory_path: Path, content: bytes) -> None:
    assert isinstance(Path.byte_content, property)
    in_memory_path.byte_content = content
    assert in_memory_path.byte_content == content
