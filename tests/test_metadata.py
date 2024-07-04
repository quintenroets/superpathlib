import hashlib
import math
import time

from hypothesis import given, strategies
from hypothesis.strategies import lists
from superpathlib import Path

from tests.content import byte_content, text_strategy
from tests.utils import ignore_fixture_warning


@ignore_fixture_warning
@given(mtime=strategies.floats(min_value=0, max_value=time.time()))
def test_mtime(path: Path, mtime: float) -> None:
    assert isinstance(Path.mtime, property)
    path.mtime = mtime
    assert math.isclose(path.mtime, mtime, abs_tol=1e-3)


@ignore_fixture_warning
@given(content=lists(text_strategy(blacklist_characters=",", min_size=1)))
def test_tags(path: Path, content: str) -> None:
    assert isinstance(Path.tags, property)
    path.tags = content
    assert path.tags == list(set(content))


@ignore_fixture_warning
@given(content=lists(text_strategy(blacklist_characters=",", min_size=1)))
def test_tags_removal(path: Path, content: str) -> None:
    assert isinstance(Path.tags, property)
    path.tags = content
    path.tags = []
    assert path.tags == []


@ignore_fixture_warning
@given(content=text_strategy(blacklist_characters=","))
def test_tag(path: Path, content: str) -> None:
    assert isinstance(Path.tag, property)
    path.tag = content
    assert path.tag == content


@ignore_fixture_warning
@byte_content
def test_size(path: Path, content: bytes) -> None:
    assert isinstance(Path.size, property)
    path.byte_content = content
    assert path.size == len(content)


def test_filetypes(path: Path) -> None:
    filetype_mappings = {"text": "txt", "video": "mp4", "image": "jpg"}
    for filetype, extension in filetype_mappings.items():
        assert path.with_suffix(f".{extension}").filetype == filetype


@ignore_fixture_warning
@byte_content
def test_content_hash(path: Path, content: bytes) -> None:
    path.byte_content = content
    content_hash = hashlib.new("sha512", data=content).hexdigest()
    assert path.content_hash == content_hash


def test_number_of_children(directory: Path) -> None:
    assert directory.number_of_children == 0


def test_is_root(directory: Path) -> None:
    directory.rmdir()
    assert directory.is_root is not None


def test_default(path: Path) -> None:
    path.unlink()
    assert path.mtime == 0
