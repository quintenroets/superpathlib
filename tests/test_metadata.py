import math
import time

from content import byte_content, text_strategy
from hypothesis import given, strategies
from utils import ignore_fixture_warning

from plib import Path


@ignore_fixture_warning
@given(mtime=strategies.floats(min_value=0, max_value=time.time()))
def test_mtime(path: Path, mtime: float):
    assert isinstance(Path.mtime, property)
    path.mtime = mtime
    assert math.isclose(path.mtime, mtime, abs_tol=1e-3)


@ignore_fixture_warning
@given(content=text_strategy(blacklist_characters=","))
def test_tag(path: Path, content: str):
    assert isinstance(Path.tag, property)
    path.tag = content
    assert path.tag == content


@ignore_fixture_warning
@byte_content
def test_size(path, content):
    assert isinstance(Path.size, property)
    path.byte_content = content
    assert path.size == len(content)


def test_filetypes(path):
    filetype_mappings = {"text": "txt", "video": "mp4", "image": "jpg"}
    for filetype, extension in filetype_mappings.items():
        assert path.with_suffix(f".{extension}").filetype == filetype
