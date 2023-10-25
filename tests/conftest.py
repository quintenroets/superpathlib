from collections.abc import Generator

import pytest

from plib import Path
from plib.encryption import EncryptedPath


def provision_path(in_memory: bool = False) -> Generator[Path, None, None]:
    with Path.tempfile(in_memory=in_memory) as path:
        yield path
    assert not path.exists()


def provision_folder(path: Path) -> Generator[Path, None, None]:
    path.unlink()
    path.mkdir()
    yield path


@pytest.fixture()
def path() -> Generator[Path, None, None]:
    yield from provision_path()


@pytest.fixture()
def path2() -> Generator[Path, None, None]:
    yield from provision_path()


@pytest.fixture()
def in_memory_path() -> Generator[Path, None, None]:
    yield from provision_path(in_memory=True)


@pytest.fixture()
def folder(path: Path) -> Generator[Path, None, None]:
    yield from provision_folder(path)


@pytest.fixture()
def folder2(path2: Path) -> Generator[Path, None, None]:
    yield from provision_folder(path2)


@pytest.fixture()
def in_memory_folder(in_memory_path: Path) -> Generator[Path, None, None]:
    yield from provision_folder(in_memory_path)


@pytest.fixture()
def encryption_path(path: Path) -> Generator[EncryptedPath, None, None]:
    with path.encrypted as encryption_path:
        yield encryption_path
    assert not encryption_path.exists()
