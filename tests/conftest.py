from collections.abc import Iterator
from typing import cast
from unittest.mock import patch

import pytest

from superpathlib import Path
from superpathlib.encrypted import EncryptedPath


@pytest.fixture(autouse=True, scope="session")
def encryption_password() -> Iterator[None]:
    with patch.dict("os.environ", {"FILE_ENCRYPTION_PASSWORD": "test_password"}):
        yield


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


@pytest.fixture(params=[False, True], ids=["same_filesystem", "in_memory"])
def in_memory(request: pytest.FixtureRequest) -> bool:
    return cast("bool", request.param)


@pytest.fixture
def path() -> Iterator[Path]:
    yield from provision_path()


@pytest.fixture
def path2() -> Iterator[Path]:
    yield from provision_path()


@pytest.fixture
def target_path(*, in_memory: bool) -> Iterator[Path]:
    yield from provision_path(in_memory=in_memory)


@pytest.fixture
def directory() -> Iterator[Path]:
    yield from provision_directory()


@pytest.fixture
def directory2() -> Iterator[Path]:
    yield from provision_directory()


@pytest.fixture
def target_directory(*, in_memory: bool) -> Iterator[Path]:
    yield from provision_directory(in_memory=in_memory)


@pytest.fixture
def encrypted_path(path: Path) -> Iterator[EncryptedPath]:
    with path.encrypted as encrypted_path:
        yield encrypted_path
    assert not encrypted_path.exists()
