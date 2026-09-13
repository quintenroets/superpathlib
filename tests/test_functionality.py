import os
import re
from collections.abc import Callable

import pytest

from superpathlib import Path
from tests.content import Given, slower_test_settings
from tests.utils import ignore_fixture_warning

MTIME_TOLERANCE = 0.01


def test_tempfile() -> None:
    with Path.tempfile() as path:
        assert path.exists()
    assert not path.exists()


def test_context_manager_deletes_fifo(path: Path) -> None:
    path.unlink()
    os.mkfifo(path)
    with path:
        assert path.is_fifo()
    assert not path.exists()


def test_deletion(path: Path) -> None:
    path.unlink()
    assert not path.exists()


def test_parent(path: Path) -> None:
    child_path = path / path.name
    assert child_path.parent == path


def test_tar_unpack(directory: Path) -> None:
    path = provision_archive("test.tar.gz", directory)
    path.unpack_if_archive()
    test_file = directory / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_recursive_unpack(directory: Path, directory2: Path) -> None:
    path = provision_archive("recursive.zip", directory2)
    path.unpack_if_archive(extraction_directory=directory)
    test_file = directory / "test" / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_unpack_check(directory: Path) -> None:
    non_archive_assets = Path(__file__).parent / "assets" / "non_archives"
    assert not non_archive_assets.is_empty()
    for path in non_archive_assets.iterdir():
        path.unpack_if_archive(extraction_directory=directory)
        assert directory.is_empty()


def provision_archive(name: str, directory: Path) -> Path:
    asset_path = Path(__file__).parent / "assets" / "archives" / name
    path = directory / name
    asset_path.copy_to(path)
    return path


@ignore_fixture_warning
@Given.bytes
def test_copy(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.copy_to(path2)
    assert path2.byte_content == content


@slower_test_settings
@Given.bytes
def test_copy_if_newer_copies(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.mtime = path2.mtime + 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == content


@slower_test_settings
@Given.bytes
def test_copy_if_newer_skips(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.mtime = path2.mtime - 1
    path.copy_to(path2, only_if_newer=True)
    assert path2.byte_content == b""


@slower_test_settings
@Given.bytes
def test_move(path: Path, path2: Path, content: bytes) -> None:
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@ignore_fixture_warning
@Given.bytes
def test_move_existing(path: Path, target_path: Path, content: bytes) -> None:
    path.byte_content = content
    target_path.byte_content = content
    path.rename(target_path, exist_ok=True)
    assert_moved(path, target_path, content)


@ignore_fixture_warning
@Given.bytes
def test_move_parent_not_existing(
    directory: Path,
    directory2: Path,
    content: bytes,
) -> None:
    directory.rmtree()
    path = directory / directory.name
    directory2.rmtree()
    path2 = directory2 / directory2.name
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@slower_test_settings
@Given.bytes
def test_move_directory(
    directory: Path,
    target_directory: Path,
    content: bytes,
) -> None:
    filename = directory.name
    subpath = directory / filename
    subpath.byte_content = content

    content_hash = directory.content_hash
    target_directory.rmtree()

    directory.rename(target_directory)

    assert directory.is_empty()
    assert target_directory.content_hash == content_hash


@ignore_fixture_warning
@Given.bytes
def test_move_directory_existing(
    directory: Path,
    target_directory: Path,
    content: bytes,
) -> None:
    def move_function() -> None:
        directory.rename(target_directory, exist_ok=True)

    verify_move_existing(move_function, directory, target_directory, content)


@ignore_fixture_warning
@Given.bytes
def test_replace_directory_existing(
    directory: Path,
    directory2: Path,
    content: bytes,
) -> None:
    def move_function() -> None:
        directory.replace(directory2)

    verify_move_existing(move_function, directory, directory2, content)


def verify_move_existing(
    move_function: Callable[[], None],
    directory: Path,
    directory2: Path,
    content: bytes,
) -> None:
    filename = directory.name
    subpath = directory / filename
    subpath2 = directory2 / filename
    for test_subpath in (subpath, subpath2):
        test_subpath.byte_content = content

    with pytest.raises(OSError, match=re.escape(str(directory2))):
        directory.rename(directory2)

    content_hash = directory.content_hash
    move_function()

    assert directory.is_empty()
    assert directory2.content_hash == content_hash


def assert_moved(source: Path, dest: Path, content: bytes) -> None:
    assert not source.exists()
    assert dest.byte_content == content


def test_with_non_existent_name(path: Path) -> None:
    paths: list[Path] = []
    for _ in range(5):
        new_path = path.with_nonexistent_name()
        if paths:
            assert paths[-1] != new_path
        else:
            assert new_path != path
        new_path.touch()
        paths.append(new_path)

    for created_path in paths:
        created_path.unlink()


def test_with_timestamp(path: Path) -> None:
    assert path.with_timestamp()


@ignore_fixture_warning
@Given.lines
def test_subpath(path: Path, content: list[str]) -> None:
    parts = [name for name in content if name]
    sub_path = path.subpath(*parts)
    for part in parts:
        cleaned_part = part.replace("/", "_").replace(".", "_")
        assert cleaned_part in sub_path.parts


def test_rmtree_not_existing(path: Path) -> None:
    path.unlink()
    with pytest.raises(FileNotFoundError):
        path.rmtree()


def test_rmtree_preserve_root(directory: Path) -> None:
    directory.rmtree(remove_root=False)


def test_pop_parent(directory: Path) -> None:
    grandchild = directory / "child" / "grandchild"
    grandchild.touch()
    grandchild.pop_parent()
    assert not grandchild.exists()


def test_pop_parent_same_name(directory: Path) -> None:
    grandchild = directory / "child" / "child"
    grandchild.touch()
    grandchild.pop_parent()
    assert not grandchild.exists()


def test_rmdir(directory: Path) -> None:
    directory.rmdir()


def test_touch(path: Path) -> None:
    path.touch(mtime=1)
    assert path.exists()
    assert abs(path.mtime - 1) < MTIME_TOLERANCE
