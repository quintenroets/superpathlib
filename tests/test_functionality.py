import pytest

from plib import Path


@pytest.fixture()
def path():
    with Path.tempfile() as path:
        yield path
    assert not path.exists()


@pytest.fixture()
def folder():
    with Path.tempfile() as path:
        path.unlink()
        path.mkdir()
        yield path
        path.rmtree()
        path.touch()


def test_tempfile():
    with Path.tempfile() as path:
        assert path.exists()
    assert not path.exists()


def test_deletion(path):
    path.unlink()
    assert not path.exists()


def test_parent(path):
    child_path = path / "child.txt"
    assert child_path.parent == path


def test_tar_unpack(folder):
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "test.tar.gz"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_recursive_unpack(folder):
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "recursive.zip"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test" / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_unpack_check(folder):
    non_archive_assets = Path(__file__).parent / "assets" / "non_archives"
    assert not non_archive_assets.is_empty()
    for path in non_archive_assets.iterdir():
        path.unpack_if_archive(folder)
        assert folder.is_empty()
