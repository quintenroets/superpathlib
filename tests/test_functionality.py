import shutil

import pytest
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


def test_uri(path: Path):
    uri = path.as_uri()
    assert Path.from_uri(uri) == path


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


@ignore_fixture_warning
@byte_content
def test_move(path: Path, path2: Path, content: bytes):
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@ignore_fixture_warning
@byte_content
def test_move_existing(path: Path, path2: Path, content: bytes):
    path.byte_content = content
    path2.byte_content = content
    path.rename(path2)

    assert_moved(path, path2, content)


@ignore_fixture_warning
@byte_content
def test_move_folder(folder: Path, folder2: Path, content: bytes):
    filename = folder.name
    subpath = folder / filename
    subpath.byte_content = content

    folder2.rmtree()
    folder.rename(folder2)

    subpath2 = folder2 / filename
    assert_moved(subpath, subpath2, content)
    subpath2.unlink()
    assert_empty(folder, folder2)


@ignore_fixture_warning
@byte_content
def test_move_folder_existing(folder: Path, folder2: Path, content: bytes):
    def move_function():
        folder.rename(folder2, exist_ok=True)

    verify_move_existing(move_function, folder, folder2, content)


@ignore_fixture_warning
@byte_content
def test_replace_folder_existing(folder: Path, folder2: Path, content: bytes):
    def move_function():
        folder.replace(folder2)

    verify_move_existing(move_function, folder, folder2, content)


@ignore_fixture_warning
@byte_content
def test_move_folder_different_filesystem(
    folder: Path, in_memory_folder: Path, content: bytes
):
    filename = folder.name
    subpath = folder / filename
    subpath.byte_content = content

    in_memory_folder.rmtree()
    folder.rename(in_memory_folder)

    subpath2 = in_memory_folder / filename
    assert_moved(subpath, subpath2, content)
    subpath2.unlink()
    assert_empty(folder, in_memory_folder)


@ignore_fixture_warning
@byte_content
def test_move_folder_existing_different_filesystem(
    folder: Path, in_memory_folder: Path, content: bytes
):
    def move_function():
        folder.rename(in_memory_folder, exist_ok=True)

    verify_move_existing(
        move_function,
        folder,
        in_memory_folder,
        content,
        expected_existing_error=shutil.Error,
    )


def verify_move_existing(
    move_function,
    folder: Path,
    folder2: Path,
    content: bytes,
    expected_existing_error=OSError,
):
    filename = folder.name
    subpath = folder / filename
    subpath2 = folder2 / filename
    for test_subpath in (subpath, subpath2):
        test_subpath.byte_content = content

    with pytest.raises(expected_existing_error):
        folder.rename(folder2)

    move_function()

    assert_moved(subpath, subpath2, content)
    subpath2.unlink()
    assert_empty(folder, folder2)


def assert_empty(*paths: Path):
    for path in paths:
        assert path.is_empty()


def assert_moved(source: Path, dest: Path, content: bytes):
    assert source.byte_content == b""
    assert dest.byte_content == content
