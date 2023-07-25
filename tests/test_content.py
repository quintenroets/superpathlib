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

slower_test_settings = settings(
    max_examples=10,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)


@ignore_fixture_warning
@byte_content
def test_bytes(path: Path, content: bytes):
    path.byte_content = content
    assert path.byte_content == content


@ignore_fixture_warning
@text_content
def test_text(path: Path, content: str):
    path.text = content
    assert path.text == content


def test_empty_file_text(path: Path):
    path.unlink()
    assert path.text == ""


def test_empty_file_byte_content(path: Path):
    path.unlink()
    assert path.byte_content == b""


@ignore_fixture_warning
@text_lines_content
def test_lines(path: Path, content: list[str]):
    path.lines = content
    while content and not content[-1].strip():
        content.pop(-1)
    text_lines = [line for line in content if line]
    assert path.lines == text_lines


@slower_test_settings
@dictionary_content
def test_json(path: Path, content: dict):
    path.json = content
    assert path.json == content


@slower_test_settings
@dictionary_content
def test_yaml(path: Path, content: dict):
    path.yaml = content
    assert path.yaml == content


@slower_test_settings
@floats_content
def test_numpy(path: Path, content: list[float]):
    numpy_content = np.array(content)
    path.numpy = numpy_content
    assert np.array_equal(path.numpy, numpy_content, equal_nan=True)
