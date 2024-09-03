from collections.abc import Iterator

import pytest

from superpathlib import Path
from superpathlib.encryption import EncryptedPath


def provision_path(*, in_memory: bool = False) -> Iterator[Path]:
    path = Path.tempfile(in_memory=in_memory)
    with path:
        yield path
    assert not path.exists()


def provision_directory(*, in_memory: bool = False) -> Iterator[Path]:
    path = Path.tempdir(in_memory=in_memory)
    with path:
        yield path
    assert not path.exists()


@pytest.fixture
def path() -> Iterator[Path]:
    yield from provision_path()


@pytest.fixture
def path2() -> Iterator[Path]:
    yield from provision_path()


@pytest.fixture
def in_memory_path() -> Iterator[Path]:
    yield from provision_path(in_memory=True)


@pytest.fixture
def directory() -> Iterator[Path]:
    yield from provision_directory()


@pytest.fixture
def directory2() -> Iterator[Path]:
    yield from provision_directory()


@pytest.fixture
def in_memory_directory() -> Iterator[Path]:
    yield from provision_directory(in_memory=True)


@pytest.fixture
def encryption_path(path: Path) -> Iterator[EncryptedPath]:
    with path.encrypted as encryption_path:
        yield encryption_path
    assert not encryption_path.exists()
