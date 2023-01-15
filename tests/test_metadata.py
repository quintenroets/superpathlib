import math
import time

import pytest
from hypothesis import HealthCheck, given, settings, strategies

from plib import Path


def text_strategy():
    alphabet = strategies.characters(
        blacklist_categories=("Cc", "Cs", "Zs"), blacklist_characters=(",",)
    )
    return strategies.text(alphabet=alphabet)


ignore_fixture_warning = settings(
    suppress_health_check=(HealthCheck.function_scoped_fixture,)
)


@pytest.fixture()
def path():
    with Path.tempfile() as path:
        yield path
    assert not path.exists()


@given(mtime=strategies.floats(min_value=0, max_value=time.time()))
@ignore_fixture_warning
def test_mtime(path, mtime):
    path.mtime = mtime
    assert math.isclose(path.mtime, mtime, abs_tol=1e-3)


@given(tag=text_strategy())
@ignore_fixture_warning
def test_tag(path, tag):
    path.tag = tag
    assert path.tag == tag


@given(byte_content=strategies.binary())
@ignore_fixture_warning
def test_size(path, byte_content):
    path.byte_content = byte_content
    assert path.size == len(byte_content)


def test_filetypes(path):
    filetype_mappings = {"text": "txt", "video": "mp4", "image": "jpg"}
    for filetype, extension in filetype_mappings.items():
        assert path.with_suffix(f".{extension}").filetype == filetype
