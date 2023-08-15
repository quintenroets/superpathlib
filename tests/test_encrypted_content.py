from content import byte_content, text_content
from hypothesis import HealthCheck, settings

from plib import Path

slow_test_settings = settings(
    max_examples=2,
    deadline=3000,
    suppress_health_check=(HealthCheck.function_scoped_fixture,),
)


@slow_test_settings
@byte_content
def test_encrypted_bytes(encryption_path: Path, content: bytes):
    encryption_path.byte_content = content
    assert encryption_path.byte_content == content


@slow_test_settings
@text_content
def test_encrypted_text(encryption_path: Path, content: str):
    encryption_path.text = content
    assert encryption_path.text == content


@slow_test_settings
@byte_content
def test_encrypted_bytes_fallback(path: Path, content: bytes):
    # provided path reused across all cases for this function and exists in beginning
    # => need to delete it in the first test case
    path.unlink(missing_ok=True)

    try:
        path.encrypted.byte_content = content
        assert not path.exists()
        assert path.byte_content == content
    finally:
        path.encrypted.unlink()


@slow_test_settings
@text_content
def test_encrypted_text_fallback(path: Path, content: str):
    # provided path reused across all cases for this function and exists in beginning
    # => need to delete it in the first test case
    path.unlink(missing_ok=True)

    try:
        path.encrypted.text = content
        assert not path.exists()
        assert path.text == content
    finally:
        path.encrypted.unlink()


@slow_test_settings
@text_content
def test_no_double_extension(encryption_path, content):
    encryption_path.encrypted.text = content
    assert encryption_path.text == content
