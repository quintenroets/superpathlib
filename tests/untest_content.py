import numpy as np
from content import (
    byte_content,
    dictionary_content,
    floats_content,
    text_content,
    text_lines_content,
)
from hypothesis import HealthCheck, settings
from utils import ignore_fixture_warning

from plib import Path

suppressed_health_checks = (HealthCheck.function_scoped_fixture,)
slower_test_settings = settings(
    max_examples=10, suppress_health_check=suppressed_health_checks
)


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
    assert path.lines == [line for line in content if line]


@ignore_fixture_warning
@text_lines_content
def test_content_lines(path: Path, content: list[str]) -> None:
    assert isinstance(Path.lines, property)
    path.lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.lines == text_lines


@slower_test_settings
@dictionary_content
def test_json(path: Path, content: dict) -> None:
    assert isinstance(Path.json, property)
    path.json = content
    assert path.json == content


@slower_test_settings
@dictionary_content
def test_yaml(path: Path, content: dict) -> None:
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
