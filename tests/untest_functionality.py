from collections.abc import Callable

import pytest
from content import byte_content
from utils import ignore_fixture_warning

from plib import Path


def test_tempfile() -> None:
    with Path.tempfile() as path:
        assert path.exists()
    assert not path.exists()


def test_deletion(path: Path) -> None:
    path.unlink()
    assert not path.exists()


def test_parent(path: Path) -> None:
    child_path = path / path.name
    assert child_path.parent == path


def test_tar_unpack(folder: Path) -> None:
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "test.tar.gz"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_recursive_unpack(folder: Path) -> None:
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "recursive.zip"
    archive_path.unpack(folder, remove_existing=True, remove_original=False)
    test_file = folder / "test" / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_unpack_check(folder: Path) -> None:
    non_archive_assets = Path(__file__).parent / "assets" / "non_archives"
    assert not non_archive_assets.is_empty()
    for path in non_archive_assets.iterdir():
        path.unpack_if_archive(folder)
        assert folder.is_empty()


def test_uri(path: Path) -> None:
    uri = path.as_uri()
    assert Path.from_uri(uri) == path


@ignore_fixture_warning
@byte_content
def test_copy(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.copy_to(path2)
    assert path2.byte_content == content


@ignore_fixture_warning
@byte_content
def test_copy_if_newer_copies(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.mtime = path2.mtime + 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == content


@ignore_fixture_warning
@byte_content
def test_copy_if_newer_skips(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.mtime = path2.mtime - 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == b""


@ignore_fixture_warning
@byte_content
def test_move(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@ignore_fixture_warning
@byte_content
def test_move_existing(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path2.byte_content = content
    path.rename(path2)

    assert_moved(path, path2, content)


@ignore_fixture_warning
@byte_content
def test_move_parent_not_existing(folder: Path, folder2: Path, content: bytes) -> None:
    folder.rmtree()
    path = folder / folder.name
    folder2.rmtree()
    path2 = folder2 / folder2.name
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@ignore_fixture_warning
@byte_content
def test_move_folder(folder: Path, folder2: Path, content: bytes) -> None:
    filename = folder.name
    subpath = folder / filename
    subpath.byte_content = content

    content_hash = folder.content_hash
    folder2.rmtree()

    folder.rename(folder2)

    assert folder.is_empty()
    assert folder2.content_hash == content_hash


@ignore_fixture_warning
@byte_content
def test_move_folder_existing(folder: Path, folder2: Path, content: bytes) -> None:
    def move_function() -> None:
        folder.rename(folder2, exist_ok=True)

    verify_move_existing(move_function, folder, folder2, content)


@ignore_fixture_warning
@byte_content
def test_replace_folder_existing(folder: Path, folder2: Path, content: bytes) -> None:
    def move_function() -> None:
        folder.replace(folder2)

    verify_move_existing(move_function, folder, folder2, content)


@ignore_fixture_warning
@byte_content
def test_move_folder_different_filesystem(
    folder: Path, in_memory_folder: Path, content: bytes
) -> None:
    filename = folder.name
    subpath = folder / filename
    subpath.byte_content = content

    content_hash = folder.content_hash
    in_memory_folder.rmtree()
    folder.rename(in_memory_folder)

    in_memory_folder / filename
    assert folder.is_empty()
    assert in_memory_folder.content_hash == content_hash


@ignore_fixture_warning
@byte_content
def test_move_folder_existing_different_filesystem(
    folder: Path, in_memory_folder: Path, content: bytes
) -> None:
    def move_function() -> None:
        folder.rename(in_memory_folder, exist_ok=True)

    verify_move_existing(
        move_function,
        folder,
        in_memory_folder,
        content,
        expected_existing_error=Exception,
    )


def verify_move_existing(
    move_function: Callable,
    folder: Path,
    folder2: Path,
    content: bytes,
    expected_existing_error: type[Exception] = OSError,
) -> None:
    filename = folder.name
    subpath = folder / filename
    subpath2 = folder2 / filename
    for test_subpath in (subpath, subpath2):
        test_subpath.byte_content = content

    with pytest.raises(expected_existing_error):
        folder.rename(folder2)

    content_hash = folder.content_hash
    move_function()

    assert folder.is_empty()
    assert folder2.content_hash == content_hash


def assert_moved(source: Path, dest: Path, content: bytes) -> None:
    assert source.byte_content == b""
    assert dest.byte_content == content
