from content import byte_content
from utils import ignore_fixture_warning

from plib import Path


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
