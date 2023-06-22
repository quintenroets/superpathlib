import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings, strategies

from plib import Path


def dictionary_strategy():
    return strategies.dictionaries(keys=strategies.text(), values=strategies.text())


def nested_dictionary_generator():
    return strategies.dictionaries(
        keys=strategies.text(),
        values=dictionary_strategy(),
    )


def text_strategy():
    alphabet = strategies.characters(blacklist_categories=("Cc", "Cs", "Zs"))
    return strategies.text(alphabet=alphabet)


dictionary_content = given(content=nested_dictionary_generator())
text_content = given(text=text_strategy())
ignore_fixture_warning = settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,)
)


@pytest.fixture()
def path():
    with Path.tempfile() as path:
        yield path
    assert not path.exists()


@pytest.fixture()
def encryption_path(path):
    with path.encrypted as encryption_path:
        yield encryption_path
    assert not encryption_path.exists()


@given(byte_content=strategies.binary())
@ignore_fixture_warning
def test_bytes(path, byte_content):
    path.byte_content = byte_content
    assert path.byte_content == byte_content


@text_content
@ignore_fixture_warning
def test_text(path, text):
    path.text = text
    assert path.text == text


def test_empty_file_text(path):
    path.unlink()
    assert path.text == ""


def test_empty_file_byte_content(path):
    path.unlink()
    assert path.byte_content == b""


@given(text_lines=strategies.lists(text_strategy()))
@ignore_fixture_warning
def test_lines(path, text_lines):
    path.lines = text_lines
    while text_lines and not text_lines[-1].strip():
        text_lines.pop(-1)
    text_lines = [line for line in text_lines if line]
    assert path.lines == text_lines


@dictionary_content
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,), max_examples=10)
def test_json(path, content):
    path.json = content
    assert path.json == content


@dictionary_content
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,), max_examples=10)
def test_yaml(path, content):
    path.yaml = content
    assert path.yaml == content


@given(content=strategies.lists(strategies.floats()))
@settings(suppress_health_check=(HealthCheck.function_scoped_fixture,), max_examples=10)
def test_numpy(path, content):
    numpy_content = np.array(content)
    path.numpy = numpy_content
    assert np.array_equal(path.numpy, numpy_content, equal_nan=True)


@settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(byte_content=strategies.binary())
def test_encrypted_bytes(encryption_path, byte_content):
    encryption_path.byte_content = byte_content
    assert encryption_path.byte_content == byte_content


@settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(text=text_strategy())
def test_encrypted_text(encryption_path, text):
    encryption_path.text = text
    assert encryption_path.text == text


@settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(byte_content=strategies.binary())
def test_encrypted_bytes_fallback(path, byte_content):
    # provided path reused across all cases for this function and exists in beginning
    # => need to delete it in the first test case
    path.unlink(missing_ok=True)

    try:
        path.encrypted.byte_content = byte_content
        assert not path.exists()
        assert path.byte_content == byte_content
    finally:
        path.encrypted.unlink()


@settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(text=text_strategy())
def test_encrypted_text_fallback(path, text):
    # provided path reused across all cases for this function and exists in beginning
    # => need to delete it in the first test case
    path.unlink(missing_ok=True)

    try:
        path.encrypted.text = text
        assert not path.exists()
        assert path.text == text
    finally:
        path.encrypted.unlink()


@settings(
    max_examples=2,
    deadline=2000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)
@given(text=text_strategy())
def test_no_double_extension(encryption_path, text):
    encryption_path.encrypted.text = text
    assert encryption_path.text == text
