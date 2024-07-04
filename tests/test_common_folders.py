from superpathlib import Path

from tests.content import byte_content
from tests.utils import ignore_fixture_warning


@ignore_fixture_warning
@byte_content
def test_common_folder_functionality(path: Path, content: bytes) -> None:
    common_folder_path = Path.HOME / path
    common_folder_path.byte_content = content
    assert common_folder_path.byte_content == content


@ignore_fixture_warning
@byte_content
def test_instance_common_folder_functionality(path: Path, content: bytes) -> None:
    common_folder_path = Path().HOME / path
    common_folder_path.byte_content = content
    assert common_folder_path.byte_content == content


def test_common_folders() -> None:
    paths = (
        Path.HOME,
        Path.docs,
        Path.scripts,
        Path.assets,
        Path.script_assets,
        Path.draft,
    )
    for path in paths:
        assert path
