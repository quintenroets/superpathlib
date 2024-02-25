from collections.abc import Callable

import pytest
from content import (
    byte_content,
    dictionary_content,
    slower_test_settings,
    text_lines_content,
)
from superpathlib import Path
from utils import ignore_fixture_warning


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


def test_tar_unpack(directory: Path) -> None:
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "test.tar.gz"
    archive_path.unpack(directory, remove_existing=True, remove_original=False)
    test_file = directory / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_recursive_unpack(directory: Path) -> None:
    archive_assets = Path(__file__).parent / "assets" / "archives"
    archive_path = archive_assets / "recursive.zip"
    archive_path.unpack(directory, remove_existing=True, remove_original=False)
    test_file = directory / "test" / "test" / "test.txt"
    assert test_file.text.strip() == "testcontent"


def test_unpack_check(directory: Path) -> None:
    non_archive_assets = Path(__file__).parent / "assets" / "non_archives"
    assert not non_archive_assets.is_empty()
    for path in non_archive_assets.iterdir():
        path.unpack_if_archive(directory)
        assert directory.is_empty()


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
def test_move_parent_not_existing(
    directory: Path, directory2: Path, content: bytes
) -> None:
    directory.rmtree()
    path = directory / directory.name
    directory2.rmtree()
    path2 = directory2 / directory2.name
    path.byte_content = content
    path.rename(path2)
    assert_moved(path, path2, content)


@slower_test_settings
@byte_content
def test_move_directory(directory: Path, directory2: Path, content: bytes) -> None:
    filename = directory.name
    subpath = directory / filename
    subpath.byte_content = content

    content_hash = directory.content_hash
    directory2.rmtree()

    directory.rename(directory2)

    assert directory.is_empty()
    assert directory2.content_hash == content_hash


@ignore_fixture_warning
@byte_content
def test_move_directory_existing(
    directory: Path, directory2: Path, content: bytes
) -> None:
    def move_function() -> None:
        directory.rename(directory2, exist_ok=True)

    verify_move_existing(move_function, directory, directory2, content)


@ignore_fixture_warning
@byte_content
def test_replace_directory_existing(
    directory: Path, directory2: Path, content: bytes
) -> None:
    def move_function() -> None:
        directory.replace(directory2)

    verify_move_existing(move_function, directory, directory2, content)


@ignore_fixture_warning
@byte_content
def test_move_directory_different_filesystem(
    directory: Path, in_memory_directory: Path, content: bytes
) -> None:
    filename = directory.name
    subpath = directory / filename
    subpath.byte_content = content

    content_hash = directory.content_hash
    in_memory_directory.rmtree()
    directory.rename(in_memory_directory)

    in_memory_directory / filename
    assert directory.is_empty()
    assert in_memory_directory.content_hash == content_hash


@ignore_fixture_warning
@byte_content
def test_move_directory_existing_different_filesystem(
    directory: Path, in_memory_directory: Path, content: bytes
) -> None:
    def move_function() -> None:
        directory.rename(in_memory_directory, exist_ok=True)

    verify_move_existing(
        move_function,
        directory,
        in_memory_directory,
        content,
        expected_existing_error=Exception,
    )


def verify_move_existing(
    move_function: Callable[[], None],
    directory: Path,
    directory2: Path,
    content: bytes,
    expected_existing_error: type[Exception] = OSError,
) -> None:
    filename = directory.name
    subpath = directory / filename
    subpath2 = directory2 / filename
    for test_subpath in (subpath, subpath2):
        test_subpath.byte_content = content

    with pytest.raises(expected_existing_error):
        directory.rename(directory2)

    content_hash = directory.content_hash
    move_function()

    assert directory.is_empty()
    assert directory2.content_hash == content_hash


def assert_moved(source: Path, dest: Path, content: bytes) -> None:
    assert source.byte_content == b""
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


def test_load_yaml(path: Path) -> None:
    path.load_yaml()


@ignore_fixture_warning
@text_lines_content
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


@dictionary_content
def test_yaml_update(content: dict[str, str]) -> None:
    with Path.tempfile() as path:
        path.update(content)
        assert path.yaml == content


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
