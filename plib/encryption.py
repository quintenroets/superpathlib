import subprocess
from functools import cached_property

from . import extra_functionality


class Path(extra_functionality.Path):
    @property
    def encrypted(self):
        path = self
        encryption_suffix = ".gpg"
        if path.suffix != encryption_suffix:
            path = path.with_suffix(path.suffix + encryption_suffix)
        return EncryptedPath(path)


class EncryptedPath(Path):
    @cached_property
    def password(self):
        command = 'ksshaskpass -- "Enter passphrase for file encryption: "'
        return subprocess.getoutput(command)

    @property
    def encryption_command(self):
        return *self.decryption_command, "-c"

    @property
    def decryption_command(self):
        return "gpg", "--passphrase", self.password, "--batch", "--quiet", "--yes"

    def read_bytes(self) -> bytes:
        encrypted_bytes = super().read_bytes()
        if encrypted_bytes:
            process = subprocess.Popen(
                self.decryption_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
            )
            decrypted_bytes, _ = process.communicate(input=encrypted_bytes)
        else:
            decrypted_bytes = encrypted_bytes
        return decrypted_bytes

    def write_bytes(self, data: bytes) -> int:
        process = subprocess.Popen(
            self.encryption_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
        encrypted_data = process.communicate(input=data)[0]
        return super().write_bytes(encrypted_data)

    def read_text(self, encoding: str | None = ..., errors: str | None = ...) -> str:
        return self.read_bytes().decode()

    def write_text(self, data: str, **_) -> int:
        data = data.encode()
        return self.write_bytes(data)
