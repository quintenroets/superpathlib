from content import byte_content
from utils import ignore_fixture_warning

from plib import Path


def test_tempfile():
    with Path.tempfile() as path:
        assert path.exists()
    assert not path.exists()


def test_deletion(path: Path):
    path.unlink()
    assert not path.exists()


def test_parent(path: Path):
    child_path = path / path.name
    assert child_path.parent == path


def test_tar_unpack(folder: Path):
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "test.tar.gz"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_recursive_unpack(folder: Path):
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "recursive.zip"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test" / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_unpack_check(folder: Path):
    non_archive_assets = Path(__file__).parent / "assets" / "non_archives"
    assert not non_archive_assets.is_empty()
    for path in non_archive_assets.iterdir():
        path.unpack_if_archive(folder)
        assert folder.is_empty()


@ignore_fixture_warning
@byte_content
def test_copy(path: Path, path2: Path, content: bytes):
    path.byte_content = content
    path.copy_to(path2)
    assert path2.byte_content == content


@ignore_fixture_warning
@byte_content
def test_copy_if_newer_copies(path: Path, path2: Path, content: bytes):
    path.byte_content = content
    path.mtime = path2.mtime + 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == content


@ignore_fixture_warning
@byte_content
def test_copy_if_newer_skips(path: Path, path2: Path, content: bytes):
    path.byte_content = content
    path.mtime = path2.mtime - 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == b""
