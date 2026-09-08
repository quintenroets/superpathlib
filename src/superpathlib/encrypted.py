import subprocess
from functools import cache
from typing import Any

from package_utils.secrets_ import load_secret

from . import extra_functionality


class EncryptedPath(extra_functionality.Path):
    def read_bytes(self) -> bytes:
        encrypted_bytes = super().read_bytes()
        return run_gpg(encrypted_bytes) if encrypted_bytes else encrypted_bytes

    def write_bytes(self, data: bytes) -> int:  # type: ignore[override]
        encrypted_data = run_gpg(data, "-c")
        return super().write_bytes(encrypted_data)

    def read_text(
        self,
        encoding: str | None = None,  # noqa: ARG002
        errors: str | None = None,  # noqa: ARG002
        newline: str | None = None,  # noqa: ARG002
    ) -> str:
        return self.read_bytes().decode()

    def write_text(self, data: str, **_: Any) -> int:  # type: ignore[override]
        byte_data = data.encode()
        return self.write_bytes(byte_data)


def run_gpg(data: bytes, *options: str) -> bytes:
    passphrase = load_password()
    command = "gpg", "--passphrase", passphrase, "--batch", "--quiet", "--yes", *options
    process = subprocess.Popen(  # noqa: S603
        command,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    return process.communicate(input=data)[0]


@cache
def load_password() -> str:
    return load_secret("file encryption password")
