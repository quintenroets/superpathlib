from plib import Path
import pytest


def provision_path():
    with Path.tempfile() as path:
        yield path
    assert not path.exists()


@pytest.fixture()
def path():
    yield from provision_path()


@pytest.fixture()
def path2():
    yield from provision_path()


@pytest.fixture()
def encryption_path(path):
    with path.encrypted as encryption_path:
        yield encryption_path
    assert not encryption_path.exists()


@pytest.fixture()
def folder(path):
    path.unlink()
    path.mkdir()
    yield path
    path.rmtree()
    path.touch()
